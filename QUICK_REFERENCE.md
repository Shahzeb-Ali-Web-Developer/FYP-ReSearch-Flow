# Quick Reference Card - ReSearch Flow

Quick commands and references for daily development.

---

## 🚀 Quick Start Commands

### Start Development Servers

**Windows (PowerShell)**:
```powershell
.\run-servers.ps1
```

**Manual Start**:
```bash
# Terminal 1 - Backend
cd backend
uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Verify**:
- Backend: http://localhost:8000/health
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 📂 Project Structure (Quick View)

```
FYP-ReSearch-Flow/
├── backend/src/app/
│   ├── main.py              # FastAPI app
│   ├── api/v1/routes/       # API endpoints
│   ├── services/            # Business logic
│   ├── crud/                # Database operations
│   └── models/              # Data models
│
├── frontend/src/
│   ├── pages/               # Full pages
│   ├── components/          # Reusable components
│   ├── services/api.js      # API client
│   └── contexts/            # Global state
│
└── database/                # SQL schemas
```

---

## 🔑 Environment Variables

### Backend `.env`
```env
SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
SUPABASE_KEY=your_service_role_key
OPENROUTER_API_KEY=your_key
```

### Frontend `.env`
```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

---

## 🌿 Git Workflow (Quick)

```bash
# 1. Create branch
git checkout -b feature/your-feature

# 2. Make changes
# ... edit files ...

# 3. Commit
git add .
git commit -m "feat: add your feature"

# 4. Push
git push origin feature/your-feature

# 5. Create PR on GitHub
```

---

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore

Examples:
feat(search): add multi-source search
fix(citation): resolve graph crash
docs(api): update endpoint docs
```

---

## 🎯 Common Development Tasks

### Add New API Endpoint

**1. Create route** (`backend/src/app/api/v1/routes/your_route.py`):
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/your-endpoint")
async def your_function():
    return {"message": "Hello"}
```

**2. Register route** (`backend/src/app/api/v1/api_router.py`):
```python
from .routes.your_route import router as your_router
api_router.include_router(your_router, prefix="/your-prefix")
```

**3. Add frontend client** (`frontend/src/services/api.js`):
```javascript
export const yourAPI = {
  async yourMethod() {
    const response = await fetch(`${API_BASE_URL}/your-prefix/your-endpoint`);
    return response.json();
  }
};
```

---

### Add New React Component

**1. Create component** (`frontend/src/components/YourComponent.jsx`):
```jsx
import React from 'react';

const YourComponent = ({ prop1, prop2 }) => {
  return (
    <div className="your-classes">
      {prop1}
    </div>
  );
};

export default YourComponent;
```

**2. Use component**:
```jsx
import YourComponent from '../components/YourComponent';

function ParentComponent() {
  return <YourComponent prop1="value" prop2={123} />;
}
```

---

### Add Database Column

**1. Write SQL** (`database/add_your_column.sql`):
```sql
ALTER TABLE your_table 
ADD COLUMN your_column TEXT;

CREATE INDEX idx_your_column ON your_table(your_column);
```

**2. Run in Supabase**:
- Go to https://app.supabase.com
- SQL Editor → New query → Paste → Run

**3. Update backend model** (`backend/src/app/models/pydantic_schemas.py`):
```python
class YourModel(BaseModel):
    # ... existing fields
    your_column: Optional[str]
```

**4. Update CRUD operations** (`backend/src/app/crud/your_crud.py`):
```python
record = {
    # ... existing fields
    "your_column": data.your_column
}
```

---

## 🐛 Debugging

### Backend Issues

**Check logs**:
```bash
# Terminal running uvicorn
# Look for ERROR or WARNING
```

**Test endpoint**:
```bash
curl http://localhost:8000/api/v1/your-endpoint
```

**Python debugger**:
```python
import pdb; pdb.set_trace()
# n - next line
# s - step into
# c - continue
# p variable - print variable
```

---

### Frontend Issues

**Check console**:
- Open DevTools (F12)
- Console tab
- Look for errors

**Check network**:
- DevTools → Network tab
- Filter: XHR/Fetch
- Click request → see details

**React DevTools**:
- Install Chrome extension
- Inspect component state/props

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose
pytest --cov              # With coverage
pytest test_file.py       # Specific file
```

### Frontend
```bash
cd frontend
npm run lint              # Check linting
npm run build             # Check build
npm test                  # Run tests (when available)
```

---

## 📦 Dependencies

### Add Backend Package
```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1
pip install package-name
pip freeze > requirements.txt
```

### Add Frontend Package
```bash
cd frontend
npm install package-name
# or
npm install package-name --save-dev
```

---

## 🎨 Styling (Tailwind)

### Common Classes
```jsx
// Container
<div className="max-w-7xl mx-auto px-4 py-8">

// Card
<div className="bg-white rounded-lg border border-gray-300 shadow-lg p-6">

// Button
<button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800">

// Input
<input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-black">

// Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

---

## 🔗 Useful URLs

### Development
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Supabase Dashboard**: https://app.supabase.com

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Tailwind**: https://tailwindcss.com/docs
- **Supabase**: https://supabase.com/docs

### APIs
- **OpenAlex**: https://docs.openalex.org/
- **arXiv**: https://arxiv.org/help/api/
- **Cytoscape.js**: https://js.cytoscape.org/

---

## 📞 Team Contacts

| Name | Role | Area |
|------|------|------|
| Shahzeb Ali | Backend | FastAPI, Services, APIs |
| Areesha Rizwan | Database | Supabase, SQL, CRUD |
| Haroon Mahmood | Deployment | Docker, CI/CD, DevOps |
| Maryam Abid | Frontend | React, UI/UX, Components |

**Supervisor**: Dr. Khurram Shahzad

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `taskkill /PID xxx /F` (Windows) or `kill -9 xxx` (Linux) |
| ModuleNotFoundError | `pip install -r requirements.txt` |
| npm install fails | `npm cache clean --force`, retry |
| CORS error | Check `allow_origins` in `backend/src/app/main.py` |
| Supabase error | Verify API keys in `.env` |

---

## 📋 Code Snippets

### Async API Call (Backend)
```python
import aiohttp

async def fetch_data(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### React State Hook
```jsx
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
  setLoading(true);
  fetchData()
    .then(setData)
    .catch(setError)
    .finally(() => setLoading(false));
}, []);
```

### Supabase Query (Backend)
```python
from src.app.db.client_supabase import supabase

response = supabase.table("research_papers")\
    .select("*")\
    .eq("topic", "machine learning")\
    .order("year", desc=True)\
    .limit(10)\
    .execute()

papers = response.data
```

---

## 🔐 Security Checklist

- [ ] Never commit `.env` files
- [ ] Never commit API keys
- [ ] Use environment variables
- [ ] Validate user input
- [ ] Use HTTPS in production
- [ ] Enable RLS on Supabase tables

---

## ✅ Pre-Commit Checklist

- [ ] Code runs without errors
- [ ] Tests pass (if applicable)
- [ ] Linting passes
- [ ] No console.log() left in code
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Meaningful commit message

---

## 🎯 Quick Links

- **[Full Documentation](PROJECT_OVERVIEW.md)**
- **[Developer Guide](DEVELOPER_GUIDE.md)**
- **[Contributing Guidelines](CONTRIBUTING.md)**
- **[Roadmap](ROADMAP.md)**
- **[GitHub Repo](https://github.com/your-org/FYP-ReSearch-Flow)**
- **[Trello Board](https://trello.com/your-board)**

---

**Last Updated**: December 17, 2025

*Print this page or bookmark it for quick reference during development!*

