# Localhost Setup Instructions

## Prerequisites Status

✅ **Node.js**: Installed (v22.20.0)  
❌ **Python**: Not installed (Windows Store stub only)

## Completed Steps

1. ✅ Backend `.env` file created at `backend/.env`
   - **Action Required**: Replace `SUPABASE_KEY=your_supabase_service_role_key_here` with your actual Supabase service role key
   - Get it from: https://app.supabase.com/project/jypkyhklepfuuzpgtual/settings/api

2. ✅ Frontend `.env` file configured
   - `VITE_API_URL` set to `http://127.0.0.1:8000/api/v1` for localhost
   - Supabase credentials already configured

## Required Actions

### 1. Install Python 3.8+

**Option A: Download from python.org (Recommended)**
1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 for Windows
3. During installation, check "Add Python to PATH"
4. Verify installation: Open new terminal and run `python --version`

**Option B: Use Windows Store**
1. Open Microsoft Store
2. Search for "Python 3.11" or "Python 3.12"
3. Install it
4. Verify: `python --version`

### 2. Complete Frontend Dependencies Installation

The npm install was interrupted. Run this in the `frontend` directory:

```powershell
cd frontend
npm install
```

If you encounter permission errors, try:
```powershell
npm install --force
```

### 3. Install Backend Dependencies

After Python is installed, run these commands:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Note**: If you get an execution policy error when activating venv, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. Update Backend .env File

Edit `backend/.env` and replace the placeholder:
```
SUPABASE_KEY=your_actual_service_role_key_here
```

## Running the Servers

### Backend (Terminal 1)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend (Terminal 2)

```powershell
cd frontend
npm run dev
```

Frontend will be available at:
- http://localhost:5173

## Verification

1. Check backend: Open http://localhost:8000/health in browser
2. Check frontend: Open http://localhost:5173
3. Test search: Enter a topic on the home page and search

## Troubleshooting

### Python not found
- Make sure Python is added to PATH during installation
- Restart terminal after installing Python
- Try `py` instead of `python` on Windows

### npm install fails
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then run `npm install` again
- Check for permission issues with antivirus software

### Backend can't connect to Supabase
- Verify `SUPABASE_KEY` in `backend/.env` is the service role key (not anon key)
- Check Supabase project is active
- Verify network connectivity

### CORS errors
- Backend CORS is already configured for `http://localhost:5173`
- Make sure frontend is using `VITE_API_URL=http://127.0.0.1:8000/api/v1`

