"""Supervisor-Workers Multi-Agent RAG Pipeline.

Supervisor:
  - Coordinated Router (coordinating tasks).

Workers:
  1. Dense Retrieval Worker: Runs semantic search via Weaviate.
  2. Sparse Retrieval Worker: Runs lexical search via BM25.
  3. Reranker & Fallback Worker: Merges, scores, reranks, and fallbacks to PageIndex if needed.
  4. Generation Worker: Reorders documents, drafts Vietnamese answers with citations.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import Annotated, Any, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

# Add Day 8 folder path to sys.path
DAY8_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Day08_RAG_pipeline_cohort2"))
sys.path.insert(0, DAY8_PATH)

from common.llm import get_llm
from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank, rerank_rrf
from src.task8_pageindex_vectorless import pageindex_search

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("Lab_Assignment.multi_agent_rag")

load_dotenv()

def _last_wins(left: Any, right: Any) -> Any:
    return right if right is not None else left

class AgentState(TypedDict):
    query: str
    next_step: Annotated[str, _last_wins]
    dense_docs: Annotated[list[dict], _last_wins]
    sparse_docs: Annotated[list[dict], _last_wins]
    merged_docs: Annotated[list[dict], _last_wins]
    final_answer: Annotated[str, _last_wins]

# =============================================================================
# 1. SUPERVISOR NODE
# =============================================================================
def supervisor_node(state: AgentState) -> dict:
    """Supervisor determines the next agent or task to execute."""
    query = state.get("query", "")
    dense = state.get("dense_docs")
    sparse = state.get("sparse_docs")
    merged = state.get("merged_docs")
    answer = state.get("final_answer")

    logger.info("--- Supervisor orchestrating ---")
    
    if dense is None or sparse is None:
        logger.info("Supervisor -> Delegating retrieval to Dense & Sparse Workers in parallel.")
        return {"next_step": "retrieve"}
        
    if merged is None:
        logger.info("Supervisor -> Retrieval completed. Delegating to Reranker & Fallback Worker.")
        return {"next_step": "rerank"}
        
    if not answer:
        logger.info("Supervisor -> Context reranked. Delegating to Generation Worker.")
        return {"next_step": "generate"}
        
    logger.info("Supervisor -> Task finished. Heading to END.")
    return {"next_step": "end"}


def routing_decision(state: AgentState) -> str:
    """Conditional edges router mapping Supervisor next_step to graph nodes."""
    ns = state.get("next_step", "end")
    if ns == "retrieve":
        # Parallel execution to both workers using default LangGraph behaviour
        # Wait, in LangGraph we return list of node names to run in parallel
        return "retrieve"
    elif ns == "rerank":
        return "reranker_worker"
    elif ns == "generate":
        return "generator_worker"
    return END

# =============================================================================
# 2. WORKERS
# =============================================================================

def dense_retrieval_worker(state: AgentState) -> dict:
    """Worker 1: Dense Semantic Search via Weaviate."""
    query = state["query"]
    logger.info("Dense Worker: Performing semantic search...")
    # Retrieve up to 24 chunks
    results = semantic_search(query, top_k=24)
    logger.info("Dense Worker: Retrieved %d chunks.", len(results))
    return {"dense_docs": results}


def sparse_retrieval_worker(state: AgentState) -> dict:
    """Worker 2: Sparse Lexical Search via BM25."""
    query = state["query"]
    logger.info("Sparse Worker: Performing BM25 lexical search...")
    # Retrieve up to 24 chunks
    results = lexical_search(query, top_k=24)
    logger.info("Sparse Worker: Retrieved %d chunks.", len(results))
    return {"sparse_docs": results}


def reranker_fallback_worker(state: AgentState) -> dict:
    """Worker 3: Merges dense/sparse results, scores, boosts, reranks, fallbacks to PageIndex."""
    query = state["query"]
    dense_results = state.get("dense_docs", [])
    sparse_results = state.get("sparse_docs", [])
    
    logger.info("Reranker Worker: Merging and reranking results...")
    
    # 1. Merge using RRF
    merged = rerank_rrf([dense_results, sparse_results], top_k=24)
    
    # Normalize score
    max_possible_rrf = 2.0 / (60 + 1)
    for item in merged:
        item["source"] = "hybrid"
        item["score"] = min(1.0, item["score"] / max_possible_rrf)
        
    # Boost legal keywords
    legal_keywords = ["luật", "hình phạt", "điều", "bộ luật", "nghị định", "thông tư", "tội", "quy định", "pháp luật"]
    is_legal_query = any(k in query.lower() for k in legal_keywords)
    if is_legal_query:
        for item in merged:
            if item.get("metadata", {}).get("type") == "legal":
                item["score"] = min(1.0, item["score"] * 1.5)
                
    # Boost exact matches for articles like "Điều 249"
    article_matches = re.findall(r"Điều\s+(\d+)", query, re.IGNORECASE)
    has_exact_match = False
    if article_matches:
        for match in article_matches:
            target = f"Điều {match}"
            for item in merged:
                if item.get("metadata", {}).get("article") == target:
                    item["score"] = 1.0
                    has_exact_match = True
                    
    merged.sort(key=lambda x: x["score"], reverse=True)
    
    # 2. Rerank
    if merged and not has_exact_match:
        final_results = rerank(query, merged, top_k=5, method="mmr")
    else:
        final_results = merged[:5]
        
    # 3. Fallback to PageIndex if best score < 0.3
    if not final_results or final_results[0]["score"] < 0.3:
        best_score = final_results[0]["score"] if final_results else 0.0
        logger.warning("Reranker Worker: Best score (%.3f) < threshold (0.3). Fallback to PageIndex Vectorless Search.", best_score)
        final_results = pageindex_search(query, top_k=5)
        for item in final_results:
            item["source"] = "pageindex"
            
    logger.info("Reranker Worker: Final context has %d documents.", len(final_results))
    return {"merged_docs": final_results}


def generation_worker(state: AgentState) -> dict:
    """Worker 4: Reorders context and calls LLM to generate Vietnamese answer with citations."""
    query = state["query"]
    chunks = state.get("merged_docs", [])
    
    logger.info("Generator Worker: Generating Vietnamese response...")
    
    # 1. Reorder for Lost in the Middle
    if len(chunks) > 2:
        reordered = [None] * len(chunks)
        left = 0
        right = len(chunks) - 1
        for i, chunk in enumerate(chunks):
            if i % 2 == 0:
                reordered[left] = chunk
                left += 1
            else:
                reordered[right] = chunk
                right -= 1
        chunks = reordered

    # 2. Format context
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    context_str = "\n---\n".join(context_parts)
    
    # 3. Prompting
    system_prompt = (
        "Answer the following question comprehensively in Vietnamese.\n"
        "For every statement of fact or claim, immediately insert a citation in brackets "
        "linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3] "
        "or [VnExpress, 2024]).\n\n"
        "If the information is not explicitly stated in the provided context or knowledge "
        "base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than "
        "guessing.\n\n"
        "Rules:\n"
        "- Only use information from the provided context\n"
        "- Every factual claim MUST have a citation\n"
        "- If context is insufficient, say so clearly\n"
        "- Structure your answer with clear paragraphs"
    )
    
    user_message = f"Context:\n{context_str}\n\n---\n\nQuestion: {query}"
    
    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    response = llm.invoke(messages)
    return {"final_answer": response.content}

# =============================================================================
# 3. BUILD GRAPH
# =============================================================================
def build_supervisor_graph() -> Any:
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("dense_retriever", dense_retrieval_worker)
    workflow.add_node("sparse_retriever", sparse_retrieval_worker)
    workflow.add_node("reranker_worker", reranker_fallback_worker)
    workflow.add_node("generator_worker", generation_worker)
    
    # Define execution paths
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes conditionally
    workflow.add_conditional_edges(
        "supervisor",
        routing_decision,
        {
            "retrieve": "dense_retriever",  # We will chain them or run them
            "reranker_worker": "reranker_worker",
            "generator_worker": "generator_worker",
            END: END
        }
    )
    
    # Connect retrieval workers to each other or back to supervisor
    # Since we want to run them, we can run dense -> sparse -> supervisor
    workflow.add_edge("dense_retriever", "sparse_retriever")
    workflow.add_edge("sparse_retriever", "supervisor")
    
    # Connect workers back to supervisor for coordination
    workflow.add_edge("reranker_worker", "supervisor")
    workflow.add_edge("generator_worker", "supervisor")
    
    return workflow.compile()
