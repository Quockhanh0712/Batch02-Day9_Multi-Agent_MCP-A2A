$pythonPath = "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A\.venv\Scripts\python.exe"

Write-Host "Starting Registry..."
Start-Process -FilePath $pythonPath -ArgumentList "-m registry" -WorkingDirectory "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Starting Tax Agent..."
Start-Process -FilePath $pythonPath -ArgumentList "-m tax_agent" -WorkingDirectory "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A" -WindowStyle Hidden

Write-Host "Starting Compliance Agent..."
Start-Process -FilePath $pythonPath -ArgumentList "-m compliance_agent" -WorkingDirectory "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Starting Law Agent..."
Start-Process -FilePath $pythonPath -ArgumentList "-m law_agent" -WorkingDirectory "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Starting Customer Agent..."
Start-Process -FilePath $pythonPath -ArgumentList "-m customer_agent" -WorkingDirectory "a:\AIK20_aithucchien\Batch02-Day9_Multi-Agent_MCP-A2A" -WindowStyle Hidden

Write-Host "All services started successfully."
