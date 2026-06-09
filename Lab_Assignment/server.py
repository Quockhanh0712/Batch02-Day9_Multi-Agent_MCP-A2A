"""FastAPI Server wrapping the Supervisor-Workers Multi-Agent RAG workflow.

Exposes port 10100 with CORS to serve the React Web Console.
"""

from __future__ import annotations

import logging
import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add local path and Day 8 path
sys.path.insert(0, os.path.dirname(__file__))

from multi_agent_rag import build_supervisor_graph

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [RAG_Server] %(levelname)s %(message)s")
logger = logging.getLogger("Lab_Assignment.server")

load_dotenv()

app = FastAPI(title="Supervisor-Workers RAG API Server", version="1.0.0")

# Enable CORS for Vite web app (running on http://localhost:5173 or other origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the graph
graph = build_supervisor_graph()

@app.post("/")
async def handle_rpc_request(request: Request):
    """Handle incoming JSON-RPC 2.0 messages from the Web Console."""
    try:
        body = await request.json()
        logger.info("Received request payload: %s", body)
        
        # Extract question
        question = ""
        params = body.get("params", {})
        message = params.get("message", {})
        parts = message.get("parts", [])
        if parts:
            question = "\n".join([p.get("text", "") for p in parts if p.get("kind") == "text"])
        
        if not question:
            # Fallback if text format differs
            question = body.get("question", "Hình phạt cho tội tàng trữ trái phép chất ma tuý?")
            
        logger.info("Executing Supervisor-Workers RAG workflow for query: '%s'", question)
        
        # Invoke LangGraph
        result = await graph.ainvoke({
            "query": question,
            "next_step": "",
            "dense_docs": None,
            "sparse_docs": None,
            "merged_docs": None,
            "final_answer": "",
        })
        
        answer = result.get("final_answer", "Không thể tạo câu trả lời.")
        logger.info("Workflow execution complete. Response length: %d chars", len(answer))
        
        # Format response matching what the Web UI expects (SendMessageSuccessResponse structure)
        return {
            "jsonrpc": "2.0",
            "id": body.get("id", "1"),
            "result": {
                "artifacts": [
                    {
                        "parts": [
                            {"text": answer}
                        ]
                    }
                ]
            }
        }
    except Exception as exc:
        logger.exception("Error processing RPC request: %s", exc)
        return {
            "jsonrpc": "2.0",
            "id": "error",
            "error": {
                "code": -32603,
                "message": f"Internal error: {exc}"
            }
        }

if __name__ == "__main__":
    PORT = 10100
    logger.info("Starting Supervisor-Workers RAG API Server on port %d", PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
