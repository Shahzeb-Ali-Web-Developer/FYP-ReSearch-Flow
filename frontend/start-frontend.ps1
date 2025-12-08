# Frontend Startup Script
# Run this from the frontend directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ReSearch Flow - Frontend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set execution policy for this process
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies (this will take a few minutes)..." -ForegroundColor Yellow
    Write-Host ""
    npm install --legacy-peer-deps
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Installation failed. Please run manually:" -ForegroundColor Red
        Write-Host "   npm install --legacy-peer-deps" -ForegroundColor White
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Verify Vite is installed
if (-not (Test-Path "node_modules\vite")) {
    Write-Host ""
    Write-Host "❌ Vite not found. Installing..." -ForegroundColor Yellow
    npm install vite --legacy-peer-deps
}

Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the dev server
npm run dev

