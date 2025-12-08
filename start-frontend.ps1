# Frontend Startup Script

Write-Host "Starting ReSearch Flow Frontend..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version
    Write-Host "Found Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js not found. Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Navigate to frontend directory
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: frontend/.env file not found. Creating template..." -ForegroundColor Yellow
    @"
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
VITE_API_URL=http://127.0.0.1:8000/api/v1
"@ | Out-File -FilePath .env -Encoding utf8
    Write-Host "Please update frontend/.env with your Supabase credentials" -ForegroundColor Yellow
}

# Start the development server
Write-Host "`nStarting Vite development server on http://localhost:5173" -ForegroundColor Green
Write-Host "Make sure the backend is running on http://localhost:8000`n" -ForegroundColor Cyan

npm run dev

