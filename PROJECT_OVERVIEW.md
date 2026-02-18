# ReSearch Flow - Complete Project Overview

## 📋 Table of Contents
1. [Project Summary](#project-summary)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Key Features & Implementation Status](#key-features--implementation-status)
6. [Core Components Deep Dive](#core-components-deep-dive)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)
9. [Data Flow](#data-flow)
10. [Development Workflow](#development-workflow)
11. [Contributing Guidelines](#contributing-guidelines)

---

## 🎯 Project Summary

**ReSearch Flow** is an AI-powered academic research assistant designed to simplify how students and researchers discover, analyze, and organize scholarly articles. It's a Final Year Project (FYP) for BS Data Science students at the University of the Punjab, Lahore.

### Team Members
- **Shahzeb Ali** (BSDSF22M054) - Backend Development
- **Areesha Rizwan** (BSDSF22M048) - Database Administration
- **Haroon Mahmood** (BSDSF22M020) - Web Deployment
- **Maryam Abid** (BSDSF22M028) - Frontend Development

**Supervisor**: Dr. Khurram Shahzad

### Core Objectives
1. Automate literature review process
2. Provide citation network visualization
3. Enable AI-powered paper summarization
4. Facilitate research paper discovery and organization

---

## 🏗️ System Architecture

The project follows an **N-Tier (Layered) Architecture** based on MVC principles:

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│         React 19 + Vite + Tailwind CSS 4                    │
│  (UI/UX, User Input, Authentication, Visualization)         │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
│                    FastAPI (Python)                          │
│  (Search, Normalization, Deduplication, LLM Integration)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                               │
│            Supabase (PostgreSQL-based)                       │
│  (Paper Metadata, Search History, User Data, Auth)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL APIS                               │
│    OpenAlex | arXiv | CORE | PMC | Semantic Scholar        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 19 with Vite
- **Styling**: Tailwind CSS 4
- **Routing**: React Router v7
- **State Management**: React Context API
- **UI Libraries**: 
  - Framer Motion (animations)
  - Lucide React (icons)
  - Three.js (3D background effects)
  - Cytoscape.js (citation network visualization)
- **Auth**: Supabase Auth (@supabase/supabase-js)
- **Export**: jsPDF, xlsx

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn (ASGI server)
- **HTTP Client**: requests, aiohttp (async)
- **PDF Processing**: pdfplumber, PyMuPDF
- **Data Processing**: pandas
- **Configuration**: pydantic-settings
- **API Integration**: 
  - OpenAlex (primary)
  - arXiv, CORE, PMC, Semantic Scholar
  - SerpAPI (Google Scholar)

### Database & Authentication
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth (Email/Password, Google OAuth)
- **ORM**: Supabase Python Client

### AI/ML (In Progress)
- **LLM Provider**: OpenRouter API
- **Models**: GPT-4o-mini (OpenAI)
- **Planned**: BART, PEGASUS, FLAN-T5 (open-source alternatives)

### Development Tools
- **Version Control**: Git + GitHub
- **Project Management**: Trello (Agile Sprints)
- **API Documentation**: FastAPI auto-generated docs

---

## 📁 Project Structure

```
FYP-ReSearch-Flow/
│
├── backend/                       # Python FastAPI Backend
│   ├── src/
│   │   └── app/
│   │       ├── main.py           # FastAPI application entry point
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── api_router.py        # Main API router
│   │       │       └── routes/
│   │       │           ├── search.py        # Search endpoint (OpenAlex)
│   │       │           ├── papers.py        # Paper CRUD operations
│   │       │           ├── citation.py      # Citation network
│   │       │           ├── arxiv.py         # arXiv integration
│   │       │           ├── core.py          # CORE integration
│   │       │           ├── pmc.py           # PMC integration
│   │       │           ├── semantic_scholar.py
│   │       │           └── google_scholar.py
│   │       ├── core/
│   │       │   ├── config.py               # Settings & environment
│   │       │   └── logging_config.py
│   │       ├── crud/
│   │       │   └── papers_crud.py          # Database operations
│   │       ├── db/
│   │       │   └── client_supabase.py      # Supabase client
│   │       ├── models/
│   │       │   └── pydantic_schemas.py     # Data models
│   │       ├── services/
│   │       │   ├── openalex_service.py     # OpenAlex API client
│   │       │   ├── citation_network_service.py
│   │       │   ├── llm_service.py          # LLM integration
│   │       │   ├── summarization_service.py
│   │       │   ├── pdf_service.py
│   │       │   ├── pdf_extractor.py
│   │       │   ├── arxiv_service.py
│   │       │   ├── core_service.py
│   │       │   ├── pmc_service.py
│   │       │   ├── semantic_scholar_service.py
│   │       │   └── google_scholar_service.py
│   │       └── utils/
│   │           ├── dedupe.py               # Deduplication logic
│   │           └── retries.py              # Retry utilities
│   ├── requirements.txt                    # Python dependencies
│   └── .env                               # Environment variables
│
├── frontend/                      # React Frontend
│   ├── src/
│   │   ├── main.jsx                       # React entry point
│   │   ├── App.jsx                        # Main app component
│   │   ├── pages/
│   │   │   ├── Home.jsx                   # Landing page
│   │   │   ├── Results.jsx                # Search results & filters
│   │   │   ├── SavedSearches.jsx          # User's saved papers
│   │   │   ├── AuthPage.jsx               # Login/Signup
│   │   │   ├── AuthCallback.jsx           # OAuth callback
│   │   │   ├── Pricing.jsx
│   │   │   └── Payment.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── SearchDropdown.jsx
│   │   │   ├── CitationMesh.jsx           # Cytoscape graph
│   │   │   ├── ArticleNotesModal.jsx      # Notes editor
│   │   │   ├── Toast.jsx                  # Notifications
│   │   │   └── AnimatedNetworkBackground.jsx
│   │   ├── layouts/
│   │   │   ├── MainLayout.jsx             # With navbar
│   │   │   └── AuthLayout.jsx             # Without navbar
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx            # Authentication state
│   │   ├── services/
│   │   │   └── api.js                     # API client functions
│   │   ├── lib/
│   │   │   └── supabase.js                # Supabase client
│   │   └── index.css                      # Global styles
│   ├── package.json
│   ├── vite.config.js
│   └── .env                               # Environment variables
│
├── database/                      # Database Schemas
│   ├── saved_articles_schema.sql
│   ├── add_institutions_column.sql
│   └── README.md
│
├── README.md                      # Main project README
├── QUICK_START.md                 # Quick start guide
├── SETUP_INSTRUCTIONS.md          # Detailed setup
├── run-servers.ps1                # Start both servers
└── .env.example                   # Environment template
```

---

## ✅ Key Features & Implementation Status

| Feature | Status | Description |
|---------|--------|-------------|
| **Topic-Based Search** | ✅ Implemented | Search papers using OpenAlex API |
| **Article Metadata Display** | ✅ Implemented | Title, authors, abstract, citations, venue, year |
| **Advanced Filtering** | ✅ Implemented | Filter by year, type, fields of study, open access |
| **Paper Detail View** | ✅ Implemented | Interactive slide-in panel with full details |
| **Statistics Dashboard** | ✅ Implemented | Real-time analytics and distributions |
| **Database Integration** | ✅ Implemented | Auto-save to Supabase with batch processing |
| **Authentication** | ✅ Implemented | Supabase Auth (Email, Google OAuth) |
| **Citation Mesh** | ✅ Implemented | Interactive graph with Cytoscape.js |
| **Save Articles** | ✅ Implemented | Bookmark papers with notes |
| **Export Functionality** | ✅ Implemented | Export as PDF, Excel |
| **Multi-Source Search** | 🔄 In Progress | arXiv, CORE, PMC, Semantic Scholar |
| **AI Summarization** | 🔄 In Progress | LLM-powered paper summaries |
| **PDF Extraction** | ✅ Implemented | Extract text from PDFs |
| **Chat with Papers** | 🔄 In Progress | Ask questions about papers |
| **Trend Analysis** | 📋 Planned | Keyword extraction, technique identification |
| **Draft Generation** | 📋 Planned | Auto-generate Introduction, Literature Review |

---

## 🔍 Core Components Deep Dive

### 1. Search & Data Fetching (`search.py`, `openalex_service.py`)

**Primary Data Source**: OpenAlex API (free, no API key required)

**Flow**:
1. User enters topic on Home page
2. Frontend calls `/api/v1/search/fetch?topic={topic}&limit=20`
3. Backend fetches from OpenAlex using `fetch_openalex_papers()`
4. Results are normalized to standard schema
5. Deduplication applied (`clean_and_deduplicate()`)
6. Results returned immediately to user
7. Background task stores papers in Supabase asynchronously

**Key Functions**:
- `fetch_openalex_papers()`: Fetches and normalizes OpenAlex data
- `_flatten_abstract()`: Converts inverted index to readable text
- Supports pagination (50 results per page, up to 200 total)

### 2. Data Deduplication (`dedupe.py`)

**Purpose**: Remove duplicate papers from multiple sources

**Strategy**:
- Title-based normalization (lowercase, remove special chars)
- Fuzzy matching for similar titles
- Merge metadata from duplicates
- Prefer papers with more complete data

### 3. Database Operations (`papers_crud.py`)

**Features**:
- Batch insert with retry logic (50 papers per batch)
- Exponential backoff on failures
- Individual insert fallback
- Upsert operations (update if exists)
- Handles JSON fields (authors, institutions, references)

**Schema** (`research_papers` table):
```sql
- paperId (TEXT, PRIMARY KEY)
- title (TEXT)
- abstract (TEXT)
- authors (JSONB)
- url (TEXT)
- year (INTEGER)
- venue (TEXT)
- publicationTypes (JSONB)
- citationCount (INTEGER)
- referenceCount (INTEGER)
- referencedWorks (JSONB)  -- List of OpenAlex IDs
- isOpenAccess (BOOLEAN)
- openAccessPdf (TEXT)
- externalIds (JSONB)
- fieldsOfStudy (JSONB)
- institutions (JSONB)
- source (TEXT)
- topic (TEXT)
- content (TEXT)
- inserted_at (TIMESTAMP)
```

### 4. Citation Network (`citation_network_service.py`, `CitationMesh.jsx`)

**Backend**:
- Fetches referenced works from OpenAlex
- Builds graph with nodes (papers) and edges (citations)
- Supports depth control (1 level = direct citations)
- Limits nodes to prevent performance issues

**Frontend**:
- Cytoscape.js for graph rendering
- Multiple layouts: concentric, dagre, cose
- Interactive: zoom, pan, click nodes
- Node colors based on citation count
- Full paper titles displayed
- Export as PNG

### 5. AI Summarization (`llm_service.py`, `summarization_service.py`)

**Primary Method**: OpenRouter API (GPT-4o-mini)

**Structured Output**:
```json
{
  "problem_statement": "...",
  "methodology": "...",
  "key_findings": "...",
  "conclusion": "..."
}
```

**Fallback**: Extractive summarization (sentence scoring)

**Features**:
- PDF content extraction
- Long text truncation (100K chars)
- JSON response parsing
- Retry logic for API failures

### 6. Frontend Pages

#### Home Page (`Home.jsx`)
- Hero section with search bar
- Suggested topics
- Feature cards
- Animated background (Three.js)

#### Results Page (`Results.jsx`)
- Three-column layout:
  - Left: Paper list (arXiv-style compact cards)
  - Middle: Selected paper details
  - Right: Statistics & filters
- Real-time filtering
- Export to PDF/Excel
- Citation mesh viewer
- Save/bookmark papers
- Notes modal

#### Saved Searches Page (`SavedSearches.jsx`)
- User's bookmarked papers
- Notes management
- Search within saved papers

---

## 🔌 API Endpoints

### Search
```
GET  /api/v1/search/fetch
     ?topic={topic}&limit={limit}&extract_content={bool}
```

### Papers
```
GET  /api/v1/papers
     ?topic={topic}&limit={limit}&offset={offset}
GET  /api/v1/papers/topics/all
```

### Citation Network
```
POST /api/v1/citation/network
     Body: { papers: [...], max_depth: 1, max_nodes: 50 }
```

### arXiv
```
GET  /api/v1/arxiv/search?query={query}&limit={limit}
POST /api/v1/arxiv/extract
     Body: { arxiv_id: "..." } or { pdf_url: "..." }
POST /api/v1/arxiv/summarize
     Body: { arxiv_id: "..." } or { pdf_url: "..." }
POST /api/v1/arxiv/ask
     Body: { arxiv_id: "...", question: "...", conversation_history: [...] }
```

### CORE, PMC, Semantic Scholar, Google Scholar
- Similar endpoints to arXiv (search, extract, summarize, ask)
- Use respective API services

---

## 🗄️ Database Schema

### `research_papers` Table
- Primary storage for fetched papers
- Normalized schema compatible with all sources
- JSONB columns for flexible data (authors, institutions, references)
- Full-text search capabilities

### `saved_articles` Table
```sql
- id (UUID, PRIMARY KEY)
- user_id (UUID, FOREIGN KEY -> auth.users)
- paper_id (TEXT)
- title (TEXT)
- notes (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- UNIQUE(user_id, paper_id)
```

**RLS Policies**: Users can only access their own saved articles

**Triggers**: Auto-update `updated_at` on modification

---

## 🔄 Data Flow

### Search Flow
```
User Input (Topic)
    ↓
Frontend (Home.jsx)
    ↓ HTTP GET /api/v1/search/fetch
Backend (search.py)
    ↓
OpenAlex API (fetch_openalex_papers)
    ↓
Normalization & Deduplication (dedupe.py)
    ↓
Return to Frontend (immediate)
    ↓
Background Task (store_papers_background)
    ↓
Supabase Database (batch insert)
```

### Citation Network Flow
```
User Clicks "Citation Mesh"
    ↓
Frontend (Results.jsx)
    ↓ HTTP POST /api/v1/citation/network
Backend (citation_network_service.py)
    ↓
OpenAlex API (fetch referenced works)
    ↓
Build Graph (nodes + edges)
    ↓
Return to Frontend
    ↓
Cytoscape.js Rendering (CitationMesh.jsx)
```

### Summarization Flow
```
User Clicks "Summarize"
    ↓
Frontend (Results.jsx)
    ↓ HTTP POST /api/v1/arxiv/summarize
Backend (arxiv.py)
    ↓
PDF Extraction (pdf_extractor.py)
    ↓
LLM Service (llm_service.py)
    ↓ OpenRouter API
GPT-4o-mini
    ↓
Structured Summary (JSON)
    ↓
Return to Frontend
    ↓
Display in UI
```

---

## 💻 Development Workflow

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/your-repo/FYP-ReSearch-Flow.git
cd FYP-ReSearch-Flow
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Environment Variables**

Backend `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
OPENROUTER_API_KEY=your_openrouter_key
CORE_API_KEY=optional
SERPAPI_API_KEY=optional
```

Frontend `.env`:
```
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Running Servers

**Quick Start** (PowerShell):
```powershell
.\run-servers.ps1
```

**Manual**:
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

### Git Workflow

1. **Feature Branches**
```bash
git checkout -b feature/your-feature-name
```

2. **Commit Convention**
```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in search"
git commit -m "docs: update README"
```

3. **Pull Request**
- Create PR to `main` branch
- Add description and screenshots
- Request review from team members

### Code Style

**Python (Backend)**:
- PEP 8 style guide
- Type hints for function parameters
- Docstrings for all functions

**JavaScript (Frontend)**:
- ESLint configuration
- Functional components with hooks
- PropTypes or TypeScript (future)

---

## 🤝 Contributing Guidelines

### For Team Members

1. **Pick a Task from Trello**
   - Move card to "In Progress"
   - Assign yourself

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/task-name
   ```

3. **Implement & Test**
   - Write code
   - Test locally
   - Check for linter errors

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: implement X"
   git push origin feature/task-name
   ```

5. **Create Pull Request**
   - Add description
   - Link Trello card
   - Request review

6. **Review & Merge**
   - Address feedback
   - Merge to main
   - Move Trello card to "Done"

### Areas for Contribution

#### Backend
- [ ] Implement trend analysis algorithms
- [ ] Add more data source integrations
- [ ] Optimize database queries
- [ ] Add caching layer (Redis)
- [ ] Improve error handling
- [ ] Add rate limiting

#### Frontend
- [ ] Enhance UI/UX with more animations
- [ ] Add dark mode
- [ ] Implement advanced search filters
- [ ] Create user dashboard
- [ ] Add collaborative features
- [ ] Mobile responsiveness improvements

#### AI/ML
- [ ] Fine-tune summarization prompts
- [ ] Add multiple LLM model support
- [ ] Implement semantic search (embeddings)
- [ ] Create research trend prediction
- [ ] Add citation recommendation system

#### DevOps
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production deployment
- [ ] Monitoring and logging
- [ ] Backup strategies

---

## 📚 Additional Resources

- **OpenAlex API Docs**: https://docs.openalex.org/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **Supabase Docs**: https://supabase.com/docs
- **Cytoscape.js Docs**: https://js.cytoscape.org/

---

## 📞 Contact

For questions or issues, contact the team:
- Shahzeb Ali (Backend)
- Areesha Rizwan (Database)
- Haroon Mahmood (Deployment)
- Maryam Abid (Frontend)

**Supervisor**: Dr. Khurram Shahzad  
**Department**: Data Science, FCIT – University of the Punjab, Lahore

---

**Last Updated**: December 17, 2025

