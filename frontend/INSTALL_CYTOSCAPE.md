# Install Cytoscape - Quick Fix

## The Problem
Cytoscape packages are in `package.json` but not installed in `node_modules`.

## Solution

### Step 1: Stop Frontend Server
Press `Ctrl+C` in the frontend terminal.

### Step 2: Install Packages
Run these commands in the `frontend` folder:

```powershell
cd "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"
npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save
```

### Step 3: Verify Installation
Check if packages exist:
```powershell
dir node_modules\cytoscape
dir node_modules\cytoscape-dagre
```

If you see folders, packages are installed.

### Step 4: Restart Frontend
```powershell
npm run dev
```

## Alternative: Clean Install

If the above doesn't work:

```powershell
cd "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"

# Delete node_modules and package-lock.json
rm -r -force node_modules
rm package-lock.json

# Reinstall everything
npm install

# Specifically install cytoscape
npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save

# Restart
npm run dev
```

## Verify It Works

After restarting, the Citation Mesh should work without the error message.
