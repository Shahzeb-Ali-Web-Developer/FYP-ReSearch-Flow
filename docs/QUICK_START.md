# Quick Start Guide

## The Problem
The servers weren't running because Python dependencies weren't installed.

## Solution - Run This Command

Open PowerShell in the project root and run:

```powershell
.\run-servers.ps1
```

This script will:
1. ✅ Check and install backend dependencies if needed
2. ✅ Check and install frontend dependencies if needed  
3. ✅ Start both servers in separate windows

## Manual Method (If Script Doesn't Work)

### Step 1: Install Backend Dependencies
```powershell
cd backend
C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r requirements.txt
```

### Step 2: Start Backend (Terminal 1)
```powershell
cd backend
C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3: Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```

## Verify Servers Are Running

1. **Backend**: Open http://localhost:8000/health in browser
   - Should show: `{"status":"healthy"}`

2. **Frontend**: Open http://localhost:5173 in browser
   - Should show the ReSearch Flow homepage

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
- Run: `C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r backend\requirements.txt`

### "Port already in use"
- Kill the process using the port:
  ```powershell
  # Find process on port 8000
  netstat -ano | findstr ":8000"
  # Kill it (replace PID with actual process ID)
  taskkill /PID <PID> /F
  ```

### Frontend won't start
- Make sure you're in the `frontend` directory
- Try: `npm install` first, then `npm run dev`

