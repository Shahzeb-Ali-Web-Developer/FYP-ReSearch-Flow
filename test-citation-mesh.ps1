Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Citation Mesh Testing Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test Backend
Write-Host "[1/4] Testing Backend Health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "  ✅ Backend is RUNNING!" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Backend Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Make sure backend is running on port 8000" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test Citation API
Write-Host "[2/4] Testing Citation Network API..." -ForegroundColor Yellow
$testBody = @{
    papers = @(
        @{
            paperId = "https://openalex.org/W2741809807"
            title = "Test Paper"
            referencedWorks = @("https://openalex.org/W1234567890")
        }
    )
    max_depth = 1
    max_nodes = 50
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/citation/network" `
        -Method Post `
        -Body $testBody `
        -ContentType "application/json" `
        -TimeoutSec 15
    
    Write-Host "  ✅ Citation API works!" -ForegroundColor Green
    Write-Host "  Nodes: $($response.network.stats.totalNodes)" -ForegroundColor Gray
    Write-Host "  Edges: $($response.network.stats.totalEdges)" -ForegroundColor Gray
    Write-Host "  Root Nodes: $($response.network.stats.rootNodes)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Citation API Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "  Response: $responseBody" -ForegroundColor Yellow
    }
}
Write-Host ""

# Test Frontend
Write-Host "[3/4] Testing Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
    Write-Host "  ✅ Frontend is RUNNING!" -ForegroundColor Green
    Write-Host "  Status Code: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Frontend Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Make sure frontend is running on port 5173" -ForegroundColor Yellow
}
Write-Host ""

# Check API Documentation
Write-Host "[4/4] Checking API Documentation..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    if ($response.Content -match "Citation Network") {
        Write-Host "  ✅ Citation Network endpoint found in docs!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Docs accessible but Citation Network not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Cannot access API docs" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host "2. Search for a topic (e.g., 'machine learning')" -ForegroundColor White
Write-Host "3. Click the 'Citation Mesh' button on Results page" -ForegroundColor White
Write-Host "4. You should see the interactive citation graph!" -ForegroundColor White
Write-Host ""
