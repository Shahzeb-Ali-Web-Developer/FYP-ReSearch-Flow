# Manual Installation Fix for Cytoscape

## The Problem
Cytoscape packages are not installing properly, likely due to the space in your folder path: `FYP Github`

## Solution: Manual Installation Steps

### Step 1: Stop Frontend Server
Press `Ctrl+C` in the frontend terminal.

### Step 2: Navigate to Frontend Folder
```powershell
cd "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"
```

### Step 3: Delete node_modules (if needed)
```powershell
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue
```

### Step 4: Install Cytoscape Packages
```powershell
npm install cytoscape@3.32.0 --save
npm install cytoscape-dagre@2.5.0 --save
```

### Step 5: Verify Installation
```powershell
Test-Path node_modules\cytoscape\package.json
Test-Path node_modules\cytoscape-dagre\package.json
```

Both should return `True`.

### Step 6: Restart Frontend
```powershell
npm run dev
```

## Alternative: Use Full Path with Quotes

If npm install still fails, try:

```powershell
cd /d "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"
npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save --legacy-peer-deps
```

## Check Installation

After installing, verify:
```powershell
dir node_modules\cytoscape
dir node_modules\cytoscape-dagre
```

If you see folders with files, installation was successful.

## If Still Not Working

The component now uses dynamic imports, so it should work even if there are installation issues. However, for best results, make sure the packages are in `node_modules`.
