$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
Write-Host "Starting ProcurAI Frontend with Node $(node -v)..."
npm.cmd run dev
