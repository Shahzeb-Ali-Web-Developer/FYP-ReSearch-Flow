# Developer Guide - ReSearch Flow

## 🚀 Quick Start for New Contributors

### Prerequisites
- **Node.js**: v18+ (for frontend)
- **Python**: 3.8+ (for backend)
- **Git**: Latest version
- **Code Editor**: VS Code recommended

### Initial Setup (5 minutes)

1. **Clone Repository**
```bash
git clone https://github.com/your-org/FYP-ReSearch-Flow.git
cd FYP-ReSearch-Flow
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Environment Variables**

Create `backend/.env`:
```env
SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
SUPABASE_KEY=your_service_role_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
CORE_API_KEY=optional
SERPAPI_API_KEY=optional
```

Create `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

5. **Run Servers**
```bash
# Option 1: Automatic (Windows)
.\run-servers.ps1

# Option 2: Manual
# Terminal 1 - Backend
cd backend
uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

6. **Verify**
- Backend: http://localhost:8000/health → `{"status": "healthy"}`
- Frontend: http://localhost:5173 → Homepage should load
- API Docs: http://localhost:8000/docs → Swagger UI

---

## 📂 Project Structure Explained

### Backend Structure
```
backend/
├── src/app/
│   ├── main.py                    # FastAPI app initialization, CORS
│   ├── api/v1/
│   │   ├── api_router.py          # Central router, includes all route modules
│   │   └── routes/                # API endpoints
│   │       ├── search.py          # GET /search/fetch (OpenAlex search)
│   │       ├── papers.py          # CRUD for papers from DB
│   │       ├── citation.py        # POST /citation/network
│   │       ├── arxiv.py           # arXiv endpoints
│   │       └── ...                # Other source integrations
│   ├── core/
│   │   ├── config.py              # Settings class (loads .env)
│   │   └── logging_config.py     # Logging configuration
│   ├── crud/
│   │   └── papers_crud.py         # Database operations (insert, query)
│   ├── db/
│   │   └── client_supabase.py    # Supabase client singleton
│   ├── models/
│   │   └── pydantic_schemas.py   # Paper model definition
│   ├── services/                  # Business logic
│   │   ├── openalex_service.py   # Fetch from OpenAlex API
│   │   ├── citation_network_service.py  # Build citation graphs
│   │   ├── llm_service.py        # OpenRouter API calls
│   │   ├── summarization_service.py  # Summarization logic
│   │   ├── pdf_extractor.py      # PDF text extraction
│   │   └── ...                    # Other services
│   └── utils/
│       ├── dedupe.py              # Deduplication algorithms
│       └── retries.py             # Retry logic utilities
└── requirements.txt               # Python dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.jsx                   # React entry point, wraps App with Router
│   ├── App.jsx                    # Route definitions
│   ├── pages/                     # Full page components
│   │   ├── Home.jsx               # Landing page with search
│   │   ├── Results.jsx            # Search results (3-column layout)
│   │   ├── SavedSearches.jsx     # User's bookmarked papers
│   │   ├── AuthPage.jsx          # Login/Signup
│   │   └── AuthCallback.jsx      # OAuth redirect handler
│   ├── components/                # Reusable UI components
│   │   ├── Navbar.jsx            # Top navigation
│   │   ├── Footer.jsx            # Bottom footer
│   │   ├── SearchDropdown.jsx    # Search autocomplete
│   │   ├── CitationMesh.jsx      # Cytoscape graph component
│   │   ├── ArticleNotesModal.jsx # Notes editor modal
│   │   ├── Toast.jsx             # Notification system
│   │   └── AnimatedNetworkBackground.jsx
│   ├── layouts/
│   │   ├── MainLayout.jsx        # Layout with navbar (Outlet)
│   │   └── AuthLayout.jsx        # Layout without navbar
│   ├── contexts/
│   │   └── AuthContext.jsx       # User auth state management
│   ├── services/
│   │   └── api.js                # API client functions (fetch calls)
│   ├── lib/
│   │   └── supabase.js           # Supabase client initialization
│   └── index.css                 # Global styles + Tailwind imports
├── package.json                   # Dependencies & scripts
├── vite.config.js                # Vite configuration
└── tailwind.config.js            # Tailwind CSS configuration
```

---

## 🔧 Common Development Tasks

### 1. Add a New API Endpoint

**Example**: Add an endpoint to get paper by ID

**Backend** (`backend/src/app/api/v1/routes/papers.py`):
```python
@router.get("/{paper_id}")
async def get_paper_by_id(paper_id: str):
    """Get a single paper by OpenAlex ID"""
    try:
        response = supabase.table("research_papers")\
            .select("*")\
            .eq("paperid", paper_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Frontend** (`frontend/src/services/api.js`):
```javascript
export const searchAPI = {
  // ... existing methods
  
  async getPaperById(paperId) {
    try {
      const response = await fetch(`${API_BASE_URL}/papers/${paperId}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new APIError('Failed to fetch paper', response.status, data);
      }
      
      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Network error', 0, { originalError: error.message });
    }
  }
};
```

**Test**:
```bash
# Backend: http://localhost:8000/api/v1/papers/{paper_id}
curl http://localhost:8000/api/v1/papers/W1234567890

# Frontend:
import { searchAPI } from '../services/api';
const paper = await searchAPI.getPaperById('W1234567890');
console.log(paper);
```

---

### 2. Add a New Frontend Component

**Example**: Create a PaperCard component

**File**: `frontend/src/components/PaperCard.jsx`
```jsx
import React from 'react';
import { BookOpen, ExternalLink } from 'lucide-react';

const PaperCard = ({ paper, onClick }) => {
  const authors = paper.authors.slice(0, 3).join(', ') + 
    (paper.authors.length > 3 ? ', et al.' : '');
  
  return (
    <div 
      onClick={onClick}
      className="border border-gray-300 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
    >
      <h3 className="text-lg font-semibold text-black mb-2">
        {paper.title}
      </h3>
      
      <div className="flex items-center text-sm text-gray-600 mb-2">
        <BookOpen className="w-4 h-4 mr-1" />
        <span>{authors}</span>
      </div>
      
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-500">{paper.year}</span>
        
        {paper.url && (
          <a 
            href={paper.url} 
            target="_blank" 
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center text-black hover:text-gray-700"
          >
            View <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        )}
      </div>
    </div>
  );
};

export default PaperCard;
```

**Usage** (in another component):
```jsx
import PaperCard from '../components/PaperCard';

function Results() {
  const [papers, setPapers] = useState([]);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {papers.map(paper => (
        <PaperCard 
          key={paper.paperId} 
          paper={paper}
          onClick={() => handlePaperClick(paper)}
        />
      ))}
    </div>
  );
}
```

---

### 3. Add Database Table or Column

**Example**: Add a `rating` column to `saved_articles`

**SQL** (`database/add_rating_column.sql`):
```sql
-- Add rating column
ALTER TABLE saved_articles 
ADD COLUMN rating INTEGER CHECK (rating >= 1 AND rating <= 5);

-- Add index for faster queries
CREATE INDEX idx_saved_articles_rating ON saved_articles(rating);

-- Update RLS policies if needed
-- (Existing policies automatically apply to new columns)
```

**Apply in Supabase**:
1. Go to https://app.supabase.com
2. Select your project
3. SQL Editor → New query
4. Paste SQL and Run

**Update Backend** (`backend/src/app/crud/papers_crud.py`):
```python
# Add to insert/update operations
record = {
    "user_id": user.id,
    "paper_id": paperId,
    "title": paperData.title,
    "notes": paperData.notes,
    "rating": paperData.rating,  # New field
}
```

**Update Frontend** (`frontend/src/services/api.js`):
```javascript
async saveArticle(paperId, paperData) {
  const { data, error } = await supabase
    .from('saved_articles')
    .upsert({
      user_id: user.id,
      paper_id: paperId,
      title: paperData.title,
      notes: paperData.notes,
      rating: paperData.rating  // New field
    })
    .select()
    .single();
  
  if (error) throw error;
  return data;
}
```

---

### 4. Add New External API Integration

**Example**: Add IEEE Xplore API

**Backend** (`backend/src/app/services/ieee_service.py`):
```python
import requests
import pandas as pd
from ..core.config import settings

def fetch_ieee_papers(query: str, limit: int = 20) -> pd.DataFrame:
    """Fetch papers from IEEE Xplore API"""
    url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    
    params = {
        "apikey": settings.IEEE_API_KEY,
        "querytext": query,
        "max_records": limit,
        "sort_order": "desc",
        "sort_field": "article_number"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        papers = []
        for article in data.get("articles", []):
            paper = {
                "paperId": article.get("doi"),
                "title": article.get("title"),
                "abstract": article.get("abstract"),
                "authors": [a.get("full_name") for a in article.get("authors", {}).get("authors", [])],
                "url": article.get("pdf_url") or article.get("html_url"),
                "year": article.get("publication_year"),
                "venue": article.get("publication_title"),
                "publicationTypes": ["article"],
                "citationCount": article.get("citing_paper_count", 0),
                "source": "IEEE Xplore",
                "topic": query
            }
            papers.append(paper)
        
        return pd.DataFrame(papers)
    except Exception as e:
        logging.error(f"IEEE API error: {e}")
        return pd.DataFrame()
```

**Add Route** (`backend/src/app/api/v1/routes/ieee.py`):
```python
from fastapi import APIRouter, HTTPException
from ....services.ieee_service import fetch_ieee_papers

router = APIRouter()

@router.get("/search")
async def search_ieee(query: str, limit: int = 20):
    """Search IEEE Xplore"""
    try:
        df = fetch_ieee_papers(query, limit)
        
        if df.empty:
            return {
                "status": "no_results",
                "message": f"No papers found for '{query}'",
                "count": 0,
                "papers": []
            }
        
        papers_list = df.to_dict('records')
        
        return {
            "status": "success",
            "count": len(papers_list),
            "papers": papers_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Register Router** (`backend/src/app/api/v1/api_router.py`):
```python
from src.app.api.v1.routes.ieee import router as ieee_router

api_router.include_router(ieee_router, prefix="/ieee", tags=["IEEE Xplore"])
```

**Frontend API Client** (`frontend/src/services/api.js`):
```javascript
export const ieeeAPI = {
  async searchPapers(query, limit = 20) {
    const url = new URL(`${API_BASE_URL}/ieee/search`);
    url.searchParams.append('query', query);
    url.searchParams.append('limit', limit);
    
    const response = await fetch(url.toString());
    const data = await response.json();
    
    if (!response.ok) {
      throw new APIError('Failed to search IEEE', response.status, data);
    }
    
    return data;
  }
};
```

---

### 5. Debug Backend Issues

**Enable Debug Logging**:

`backend/src/app/core/logging_config.py`:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Use pdb Debugger**:
```python
# In your code
import pdb; pdb.set_trace()

# When code hits this line, you get interactive debugger
# Commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# q - quit
```

**Check Logs**:
```bash
# Backend terminal will show detailed logs
# Look for ERROR or WARNING messages
```

**Test API with curl**:
```bash
# GET endpoint
curl http://localhost:8000/api/v1/search/fetch?topic=machine%20learning&limit=5

# POST endpoint
curl -X POST http://localhost:8000/api/v1/citation/network \
  -H "Content-Type: application/json" \
  -d '{"papers": [...], "max_depth": 1, "max_nodes": 50}'
```

---

### 6. Debug Frontend Issues

**React Developer Tools**:
- Install: Chrome Extension "React Developer Tools"
- Inspect component state, props, context

**Console Logging**:
```jsx
// Debug component renders
useEffect(() => {
  console.log('Component mounted/updated', { papers, filters });
}, [papers, filters]);

// Debug API calls
searchAPI.fetchPapers(topic)
  .then(data => {
    console.log('API response:', data);
    setPapers(data.papers);
  })
  .catch(error => {
    console.error('API error:', error);
  });
```

**Check Network Tab**:
1. Open DevTools (F12)
2. Network tab
3. Filter: XHR/Fetch
4. Click request to see details (Headers, Payload, Response)

**Common Issues**:

| Issue | Solution |
|-------|----------|
| CORS error | Check backend CORS settings in `main.py` |
| 404 on API call | Verify `VITE_API_URL` in `.env` |
| Component not re-rendering | Check state updates, dependency arrays |
| "Cannot read property of undefined" | Add optional chaining (`paper?.title`) |

---

## 🧪 Testing

### Backend Testing

**Manual Testing with FastAPI Docs**:
1. Go to http://localhost:8000/docs
2. Expand endpoint
3. Click "Try it out"
4. Enter parameters
5. Execute and see response

**Unit Tests** (Future):
```python
# backend/src/app/tests/test_search.py
import pytest
from src.app.services.openalex_service import fetch_openalex_papers

def test_fetch_openalex_papers():
    df = fetch_openalex_papers("machine learning", limit=5)
    assert not df.empty
    assert len(df) <= 5
    assert "title" in df.columns
    assert "authors" in df.columns
```

Run tests:
```bash
cd backend
pytest
```

### Frontend Testing

**Manual Testing Checklist**:
- [ ] Search returns results
- [ ] Filters work correctly
- [ ] Citation mesh renders
- [ ] Save article functionality
- [ ] Notes save and load
- [ ] Export to PDF/Excel
- [ ] Authentication flow
- [ ] Responsive design (mobile, tablet, desktop)

**Component Tests** (Future):
```jsx
// frontend/src/__tests__/PaperCard.test.jsx
import { render, screen } from '@testing-library/react';
import PaperCard from '../components/PaperCard';

test('renders paper title', () => {
  const paper = {
    title: 'Test Paper',
    authors: ['Author 1'],
    year: 2024
  };
  
  render(<PaperCard paper={paper} />);
  expect(screen.getByText('Test Paper')).toBeInTheDocument();
});
```

---

## 🎨 Styling Guidelines

### Tailwind CSS Classes

**Common Patterns**:
```jsx
// Container
<div className="max-w-7xl mx-auto px-4 py-8">

// Card
<div className="bg-white rounded-lg border border-gray-300 shadow-lg p-6">

// Button
<button className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">

// Input
<input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-black">

// Grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

**Color Scheme**:
- Primary: Black (`text-black`, `bg-black`)
- Secondary: Gray shades (`gray-100`, `gray-300`, `gray-600`)
- Accent: As needed (blue, green for specific elements)

### Custom Fonts

**Viga Font** (used in project):
```jsx
<div className="viga-font">Your Text</div>
```

Added in `index.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Viga&display=swap');

.viga-font {
  font-family: 'Viga', sans-serif;
}
```

---

## 🔐 Environment Variables

### Required Variables

**Backend** (`backend/.env`):
```env
# Supabase (Required)
SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
SUPABASE_KEY=your_service_role_key_here

# LLM Service (Required for summarization)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional APIs
CORE_API_KEY=optional_core_api_key
SERPAPI_API_KEY=optional_serpapi_key
```

**Frontend** (`frontend/.env`):
```env
# Backend API
VITE_API_URL=http://127.0.0.1:8000/api/v1

# Supabase (Required)
VITE_SUPABASE_URL=https://jypkyhklepfuuzpgtual.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

### Get API Keys

| Service | URL | Notes |
|---------|-----|-------|
| Supabase | https://app.supabase.com | Create project, get keys from Settings → API |
| OpenRouter | https://openrouter.ai | Sign up, generate API key |
| CORE | https://core.ac.uk/services/api | Register for API key |
| SerpAPI | https://serpapi.com | Sign up for Google Scholar access |

---

## 📦 Dependencies Management

### Backend Dependencies

**Add New Package**:
```bash
pip install package-name
pip freeze > requirements.txt
```

**Update All Packages**:
```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Frontend Dependencies

**Add New Package**:
```bash
npm install package-name
# or
npm install package-name --save-dev  # for dev dependencies
```

**Update Package**:
```bash
npm update package-name
```

**Update All Packages**:
```bash
npm update
```

**Audit Security**:
```bash
npm audit
npm audit fix
```

---

## 🐛 Common Issues & Solutions

### Backend Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| ModuleNotFoundError | Missing dependencies | `pip install -r requirements.txt` |
| Supabase connection error | Wrong credentials | Check `SUPABASE_KEY` in `.env` |
| CORS error | Frontend not allowed | Add frontend URL to CORS in `main.py` |
| Port already in use | Previous server running | Kill process: `taskkill /PID xxx /F` (Windows) |

### Frontend Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| npm install fails | Corrupted cache | `npm cache clean --force`, retry |
| Module not found | Missing import | Check import path, install package |
| API calls fail | Wrong API URL | Check `VITE_API_URL` in `.env` |
| Blank page | JavaScript error | Check browser console for errors |
| Cytoscape not loading | Missing package | `npm install cytoscape cytoscape-dagre` |

---

## 🚢 Git Workflow

### Branch Naming Convention
```
feature/add-export-functionality
fix/citation-mesh-layout-bug
docs/update-api-documentation
refactor/optimize-search-query
```

### Commit Message Format
```
feat: add export to BibTeX functionality
fix: resolve duplicate papers in search results
docs: update installation instructions
refactor: optimize database query performance
style: format code with prettier
test: add unit tests for search service
chore: update dependencies
```

### Typical Workflow
```bash
# 1. Create feature branch
git checkout -b feature/add-bookmark-filter

# 2. Make changes
# ... edit files ...

# 3. Stage changes
git add .

# 4. Commit
git commit -m "feat: add filter for bookmarked papers"

# 5. Push to remote
git push origin feature/add-bookmark-filter

# 6. Create Pull Request on GitHub
# 7. After review and merge, delete branch
git checkout main
git pull origin main
git branch -d feature/add-bookmark-filter
```

---

## 📚 Useful Resources

### Official Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Supabase**: https://supabase.com/docs
- **Cytoscape.js**: https://js.cytoscape.org/

### API Documentation
- **OpenAlex**: https://docs.openalex.org/
- **arXiv**: https://arxiv.org/help/api/
- **CORE**: https://core.ac.uk/documentation/api
- **Semantic Scholar**: https://api.semanticscholar.org/

### Learning Resources
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **React Tutorial**: https://react.dev/learn
- **Tailwind CSS Basics**: https://tailwindcss.com/docs/utility-first

---

## 🤝 Getting Help

### Internal Communication
- **Trello**: Task tracking and discussion
- **GitHub Issues**: Bug reports and feature requests
- **Team Meetings**: Weekly with supervisor

### External Resources
- **Stack Overflow**: https://stackoverflow.com
- **GitHub Discussions**: Project discussions
- **Discord/Slack**: Team chat (if available)

---

## ✅ Pre-Commit Checklist

Before committing code:
- [ ] Code runs without errors locally
- [ ] Backend: No linter warnings (`flake8` or similar)
- [ ] Frontend: No ESLint errors (`npm run lint`)
- [ ] New features tested manually
- [ ] Environment variables documented if added
- [ ] Comments added for complex logic
- [ ] Commit message follows convention

---

This developer guide provides everything you need to contribute effectively to ReSearch Flow!

