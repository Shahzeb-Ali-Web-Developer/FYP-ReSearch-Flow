# Backend Startup Script
# Make sure Python is installed and backend/.env is configured

Write-Host "Starting ReSearch Flow Backend..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "backend\src\app\main.py")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if Python is available
$pythonPath = "C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe"
if (Test-Path $pythonPath) {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} else {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Found: $pythonVersion" -ForegroundColor Green
        $pythonPath = "python"
    } catch {
        Write-Host "Error: Python not found. Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
        exit 1
    }
}

# Navigate to backend directory
Set-Location backend

# Check if dependencies are installed (using system Python)
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$hasFastAPI = & $pythonPath -m pip show fastapi 2>&1
if (-not $hasFastAPI -or $hasFastAPI -match "not found") {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & $pythonPath -m pip install --user -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check if .env file exists and has values
$envContent = Get-Content .env -ErrorAction SilentlyContinue
if (-not $envContent -or $envContent -notmatch "SUPABASE_KEY=(?!your_)") {
    Write-Host "Warning: Please update backend/.env with your Supabase service role key" -ForegroundColor Yellow
    Write-Host "Get it from: https://app.supabase.com/project/jypkyhklepfuuzpgtual/settings/api" -ForegroundColor Yellow
}

# Start the server
Write-Host "`nStarting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Health Check: http://localhost:8000/health`n" -ForegroundColor Cyan

& $pythonPath -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

