# Localhost Setup - COMPLETED ✅

## Setup Summary

All setup steps have been completed! Both servers should now be running.

## ✅ Completed Tasks

1. **Environment Configuration**
   - ✅ Backend `.env` created with Supabase credentials
   - ✅ Frontend `.env` configured for localhost (API URL: `http://127.0.0.1:8000/api/v1`)

2. **Dependencies Installed**
   - ✅ Frontend: All npm packages installed (`node_modules` present)
   - ✅ Backend: Python packages installed using system Python

3. **Servers Started**
   - ✅ Backend: FastAPI server running on port 8000
   - ✅ Frontend: Vite dev server running on port 5173

## 🌐 Access URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📝 Important Notes

### Backend Configuration
- Python Path: `C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe`
- Backend is using the system Python (not venv) due to venv pip issues
- Supabase key is currently set to anon key (temporary)
- For production, update `backend/.env` with service role key

### Frontend Configuration
- Using localhost backend: `http://127.0.0.1:8000/api/v1`
- Supabase credentials configured

## 🚀 How to Restart Servers

### Backend (Terminal 1)
```powershell
cd backend
C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```

## 🔧 Troubleshooting

If servers aren't responding:

1. **Check if ports are in use:**
   ```powershell
   netstat -ano | findstr ":8000"
   netstat -ano | findstr ":5173"
   ```

2. **Check server processes:**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}
   ```

3. **Restart servers:**
   - Stop any running instances
   - Use the commands above to restart

## 📋 Next Steps

1. Open http://localhost:5173 in your browser
2. Test the search functionality
3. Verify backend API at http://localhost:8000/docs

## ⚠️ Note on Supabase Key

The backend is currently using the anon key. For full functionality (especially database writes), you may need to update `backend/.env` with the service role key from:
https://app.supabase.com/project/jypkyhklepfuuzpgtual/settings/api

