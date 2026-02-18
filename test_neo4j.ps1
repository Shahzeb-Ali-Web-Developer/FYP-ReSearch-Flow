# Test Neo4j Connection Script
Write-Host "Testing Neo4j Integration..." -ForegroundColor Cyan
Write-Host ""

# Test 1: Check Neo4j Status
Write-Host "1. Checking Neo4j status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/citation/stats" -Method Get
    if ($response.neo4j_available -eq $true) {
        Write-Host "   ✓ Neo4j Connected!" -ForegroundColor Green
        Write-Host "   Papers: $($response.papers)" -ForegroundColor White
        Write-Host "   Citations: $($response.citations)" -ForegroundColor White
    } else {
        Write-Host "   ✗ Neo4j Not Connected" -ForegroundColor Red
        Write-Host "   $($response.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Backend not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. To populate Neo4j, search for papers in the frontend!" -ForegroundColor Cyan
Write-Host "   Example: Search for 'machine learning'" -ForegroundColor White
Write-Host ""
Write-Host "3. To view the graph, open Neo4j Browser:" -ForegroundColor Cyan
Write-Host "   http://localhost:7474" -ForegroundColor White
Write-Host "   (Neo4j Desktop: Click 'Open' button next to database)" -ForegroundColor Gray
Write-Host ""

