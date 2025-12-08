# Fix Cytoscape Installation - Step by Step

## The Problem
Cytoscape packages are not installing in `node_modules`, causing Vite to fail.

## Solution: Manual Installation

### Step 1: Stop Frontend Server
Press `Ctrl+C` in your frontend terminal.

### Step 2: Open PowerShell in Frontend Folder
```powershell
cd "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"
```

### Step 3: Check Current State
```powershell
# Check if packages exist
Test-Path node_modules\cytoscape
Test-Path node_modules\cytoscape-dagre
```

### Step 4: Install Packages (Try Each Method)

**Method 1: Standard Install**
```powershell
npm install cytoscape@3.32.0 --save
npm install cytoscape-dagre@2.5.0 --save
```

**Method 2: With Flags**
```powershell
npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save --legacy-peer-deps --force
```

**Method 3: Clean Install**
```powershell
# Delete node_modules
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue

# Reinstall all packages
npm install

# Install cytoscape
npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save
```

### Step 5: Verify Installation
```powershell
# Check if folders exist
dir node_modules\cytoscape
dir node_modules\cytoscape-dagre

# Check package.json files
Test-Path node_modules\cytoscape\package.json
Test-Path node_modules\cytoscape-dagre\package.json
```

Both should return `True`.

### Step 6: Clear Vite Cache
```powershell
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue
```

### Step 7: Restart Frontend
```powershell
npm run dev
```

## If Still Not Working

Check npm version and try:
```powershell
npm --version
npm cache clean --force
npm install cytoscape@3.32.0 --save --verbose
```

Look for any error messages in the output.
