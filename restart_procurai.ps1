# Restart ProcurAI Servers
Write-Host "Cleaning up old sessions..." -ForegroundColor Cyan
Stop-Process -Id (Get-NetTCPConnection -LocalPort 3010).OwningProcess -Force -ErrorAction SilentlyContinue
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8010).OwningProcess -Force -ErrorAction SilentlyContinue

Write-Host "Starting Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; venv\Scripts\activate; uvicorn main:app --reload --port 8010"

Write-Host "Starting Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; `$env:PATH = 'C:\Program Files\nodejs;' + `$env:PATH; npm run dev"

Write-Host "Servers are starting up! Give them about 10 seconds." -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3010" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8010/docs" -ForegroundColor Cyan
