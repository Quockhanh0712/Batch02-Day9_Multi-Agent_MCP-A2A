"""Runner for Supervisor-Workers Multi-Agent RAG Pipeline.

Demonstrates the supervisor-workers coordination flow on a legal query.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import locally
sys.path.insert(0, os.path.dirname(__file__))

from multi_agent_rag import build_supervisor_graph

load_dotenv()

async def main():
    print("=" * 70)
    print("SUPERVISOR-WORKERS MULTI-AGENT RAG SYSTEM (DAY 9 ASSIGNMENT)")
    print("=" * 70)
    
    question = "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?"
    print(f"\n[User Query]: {question}\n")
    
    print("Initializing LangGraph multi-agent workflow...")
    graph = build_supervisor_graph()
    
    print("Invoking graph...\n")
    result = await graph.ainvoke({
        "query": question,
        "next_step": "",
        "dense_docs": None,
        "sparse_docs": None,
        "merged_docs": None,
        "final_answer": "",
    })
    
    print("\n" + "=" * 70)
    print("FINAL RESPONSE FROM GENERATOR WORKER")
    print("=" * 70)
    print(result.get("final_answer", "No response generated."))
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
