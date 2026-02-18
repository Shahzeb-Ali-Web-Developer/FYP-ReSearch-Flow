# Run Both Servers Script
# This script will install dependencies and start both servers in separate windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ReSearch Flow - Server Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = "C:\Python314\python.exe"

# Check Python
if (-not (Test-Path $pythonPath)) {
    Write-Host "❌ Python not found at: $pythonPath" -ForegroundColor Red
    Write-Host "Please update the pythonPath in this script" -ForegroundColor Yellow
    exit 1
}

# Check if dependencies are installed
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
$hasFastAPI = & $pythonPath -m pip show fastapi 2>&1
if ($hasFastAPI -match "not found" -or -not $hasFastAPI) {
    Write-Host "Installing backend dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    & $pythonPath -m pip install -r backend\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "✅ Backend dependencies already installed" -ForegroundColor Green
}

# Check frontend dependencies
Write-Host "Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "frontend\node_modules\react")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting servers in separate windows..." -ForegroundColor Cyan
Write-Host ""

# Get absolute paths
$backendPath = (Resolve-Path "backend").Path
$frontendPath = (Resolve-Path "frontend").Path

# Start backend in new window
Write-Host "🚀 Starting Backend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$backendPath'
`$pythonPath = '$pythonPath'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  ReSearch Flow - Backend Server' -ForegroundColor Cyan  
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting FastAPI server on http://127.0.0.1:8000' -ForegroundColor Green
Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Yellow
Write-Host 'Health: http://localhost:8000/health' -ForegroundColor Yellow
Write-Host ''
& `$pythonPath -m uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000
"@

Start-Sleep -Seconds 2

# Start frontend in new window
Write-Host "🚀 Starting Frontend Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd '$frontendPath'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  ReSearch Flow - Frontend Server' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting Vite dev server on http://localhost:5173' -ForegroundColor Green
Write-Host ''
npm run dev
"@

Write-Host ""
Write-Host "✅ Servers are starting in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your application:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this window (servers will keep running)..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

