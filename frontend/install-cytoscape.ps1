# Install Cytoscape Packages Script
Write-Host "Installing cytoscape packages..." -ForegroundColor Yellow

$frontendPath = "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"

if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
    
    # Check if packages exist
    $cyExists = Test-Path "node_modules\cytoscape\package.json"
    $dagExists = Test-Path "node_modules\cytoscape-dagre\package.json"
    
    Write-Host "cytoscape installed: $cyExists" -ForegroundColor $(if ($cyExists) { "Green" } else { "Red" })
    Write-Host "cytoscape-dagre installed: $dagExists" -ForegroundColor $(if ($dagExists) { "Green" } else { "Red" })
    
    if (-not $cyExists -or -not $dagExists) {
        Write-Host "`nInstalling packages..." -ForegroundColor Yellow
        
        # Install cytoscape
        if (-not $cyExists) {
            Write-Host "Installing cytoscape..." -ForegroundColor Cyan
            npm install cytoscape@3.32.0 --save
        }
        
        # Install cytoscape-dagre
        if (-not $dagExists) {
            Write-Host "Installing cytoscape-dagre..." -ForegroundColor Cyan
            npm install cytoscape-dagre@2.5.0 --save
        }
        
        # Verify installation
        Write-Host "`nVerifying installation..." -ForegroundColor Yellow
        $cyFinal = Test-Path "node_modules\cytoscape\package.json"
        $dagFinal = Test-Path "node_modules\cytoscape-dagre\package.json"
        
        if ($cyFinal -and $dagFinal) {
            Write-Host "✅ SUCCESS! Both packages are installed." -ForegroundColor Green
            Write-Host "`nNow restart your frontend server: npm run dev" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Installation failed. Please check npm errors above." -ForegroundColor Red
        }
    } else {
        Write-Host "`n✅ Packages are already installed!" -ForegroundColor Green
    }
} else {
    Write-Host "Error: Frontend path not found: $frontendPath" -ForegroundColor Red
}
