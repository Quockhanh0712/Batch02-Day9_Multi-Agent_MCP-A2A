# Start the Assignment Supervisor-Workers RAG stack
$venvPython = "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A\.venv\Scripts\python.exe"

Write-Host "Starting Supervisor-Workers RAG Server on port 10100..." -ForegroundColor Green
Start-Process -FilePath $venvPython -ArgumentList "server.py" -NoNewWindow -RedirectStandardOutput "logs_server.log" -RedirectStandardError "logs_server_err.log"
Start-Sleep -Seconds 2

Write-Host "Starting Vite Development Web Console..." -ForegroundColor Green
Set-Location -Path "web"
Start-Process -FilePath "npm" -ArgumentList "run dev" -NoNewWindow
Set-Location -Path ".."

Write-Host "All assignment components started!" -ForegroundColor Yellow
Write-Host "  RAG Backend:  http://localhost:10100"
Write-Host "  Web Console:  http://localhost:5173"
Write-Host ""
Write-Host "Open http://localhost:5173 in your browser and switch to 'Live A2A Backend' to test!"
