#!/bin/bash
set -e

# Start the Assignment Supervisor-Workers RAG stack
PYTHON_EXEC="a:/AIK20_aithucchien/Batch02-Day9_Multi-Agent_MCP-A2A/.venv/Scripts/python"

echo "Starting Supervisor-Workers RAG Server on port 10100..."
$PYTHON_EXEC server.py > logs_server.log 2> logs_server_err.log &
SERVER_PID=$!
sleep 2

echo "Starting Vite Development Web Console..."
cd web
npm run dev &
cd ..

echo ""
echo "All assignment components started:"
echo "  RAG Backend:  http://localhost:10100"
echo "  Web Console:  http://localhost:5173"
echo ""
echo "Open http://localhost:5173 in your browser and switch to 'Live A2A Backend' to test!"
echo "Press Ctrl+C to stop."

wait $SERVER_PID
