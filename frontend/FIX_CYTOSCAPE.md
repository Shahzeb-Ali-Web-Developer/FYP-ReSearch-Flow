# Fix react-cytoscapejs Installation Issue

## Problem
The `react-cytoscapejs` package is not being found even though it's in package.json.

## Solution Steps

### Step 1: Stop the Frontend Server
Press `Ctrl+C` in the frontend terminal to stop the server.

### Step 2: Clean Install
Run these commands in the `frontend` folder:

```powershell
# Delete node_modules and package-lock.json
rm -r -force node_modules
rm package-lock.json

# Reinstall all packages
npm install

# Specifically install cytoscape packages
npm install react-cytoscapejs@1.2.1 cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save
```

### Step 3: Verify Installation
Check if the package exists:
```powershell
dir node_modules\react-cytoscapejs
```

If it exists, you should see files.

### Step 4: Restart Frontend
```powershell
npm run dev
```

## Alternative: If npm install fails

If the package still won't install, try:

```powershell
npm install react-cytoscapejs@1.2.1 --legacy-peer-deps --force
```

## Check package.json

Make sure these lines are in `frontend/package.json`:

```json
"dependencies": {
  "cytoscape": "^3.32.0",
  "cytoscape-dagre": "^2.5.0",
  "react-cytoscapejs": "^1.2.1",
  ...
}
```

## If Still Not Working

The issue might be related to the space in your folder path: `FYP Github`. Try:

1. Move the project to a path without spaces (e.g., `E:\FYP\FYP-ReSearch-Flow`)
2. Or use npm with the path in quotes:
   ```powershell
   cd "E:\FYP\FYP Github\FYP-ReSearch-Flow\frontend"
   npm install
   ```
