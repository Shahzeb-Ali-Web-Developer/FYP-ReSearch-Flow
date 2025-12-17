# ReSearch Flow - Architecture Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSER                                 │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              REACT FRONTEND (Port 5173)                          │   │
│  │                                                                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │  Home    │  │ Results  │  │  Saved   │  │  Auth    │       │   │
│  │  │  Page    │  │  Page    │  │ Searches │  │  Pages   │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              COMPONENTS LAYER                            │   │   │
│  │  │  • SearchDropdown  • CitationMesh  • ArticleNotesModal  │   │   │
│  │  │  • Navbar  • Footer  • Toast  • AnimatedBackground      │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              SERVICES LAYER                              │   │   │
│  │  │  • api.js (API Client)                                   │   │   │
│  │  │  • supabase.js (Supabase Client)                        │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────┐   │   │
│  │  │              CONTEXTS                                     │   │   │
│  │  │  • AuthContext (User Authentication State)               │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓ HTTP/REST
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (Port 8000)                         │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      API ROUTES LAYER                            │   │
│  │  /search  /papers  /citation  /arxiv  /core  /pmc  /semantic   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SERVICES LAYER                                │   │
│  │                                                                   │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │   │
│  │  │   OpenAlex    │  │   Citation    │  │      LLM      │      │   │
│  │  │   Service     │  │   Network     │  │   Service     │      │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │   │
│  │                                                                   │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │   │
│  │  │   arXiv       │  │     CORE      │  │     PMC       │      │   │
│  │  │   Service     │  │   Service     │  │   Service     │      │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │   │
│  │                                                                   │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │   │
│  │  │   PDF         │  │ Summarization │  │   Semantic    │      │   │
│  │  │   Extractor   │  │   Service     │  │   Scholar     │      │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       CRUD LAYER                                 │   │
│  │  • papers_crud.py (Database Operations)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      UTILS LAYER                                 │   │
│  │  • dedupe.py (Deduplication)                                    │   │
│  │  • retries.py (Retry Logic)                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        SUPABASE (PostgreSQL)                             │
│                                                                           │
│  ┌──────────────────────┐         ┌──────────────────────┐             │
│  │  research_papers     │         │   saved_articles     │             │
│  │  • paperId           │         │   • id               │             │
│  │  • title             │         │   • user_id          │             │
│  │  • abstract          │         │   • paper_id         │             │
│  │  • authors (JSONB)   │         │   • title            │             │
│  │  • institutions      │         │   • notes            │             │
│  │  • referencedWorks   │         │   • timestamps       │             │
│  │  • fieldsOfStudy     │         └──────────────────────┘             │
│  │  • citationCount     │                                                │
│  │  • year, venue, etc. │         ┌──────────────────────┐             │
│  └──────────────────────┘         │   auth.users         │             │
│                                    │   (Supabase Auth)    │             │
│                                    └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL APIS                                    │
│                                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ OpenAlex │  │  arXiv   │  │   CORE   │  │   PMC    │  │ Semantic │ │
│  │   API    │  │   API    │  │   API    │  │   API    │  │ Scholar  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                                                                           │
│  ┌──────────┐  ┌──────────┐                                             │
│  │  SerpAPI │  │OpenRouter│                                             │
│  │ (Google) │  │(GPT-4o)  │                                             │
│  └──────────┘  └──────────┘                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Search Flow

```
┌─────────────┐
│    USER     │
│ enters topic│
└──────┬──────┘
       │
       ↓
┌─────────────────────────┐
│   Home.jsx              │
│   handleSearch()        │
└──────┬──────────────────┘
       │ HTTP GET /api/v1/search/fetch?topic={topic}&limit=20
       ↓
┌──────────────────────────────────────────────────────────┐
│   Backend: search.py                                      │
│   async def fetch_papers()                                │
│                                                            │
│   1. fetch_openalex_papers(topic, limit)                 │
│      ↓                                                     │
│   ┌─────────────────────────────────────────────┐       │
│   │  openalex_service.py                         │       │
│   │  • Build API request                         │       │
│   │  • Fetch from OpenAlex (paginated)          │       │
│   │  • Normalize data to standard schema         │       │
│   │  • Flatten abstract inverted index          │       │
│   │  • Extract institutions                      │       │
│   └─────────────────────────────────────────────┘       │
│      ↓                                                     │
│   2. clean_and_deduplicate(df, topic)                    │
│      ↓                                                     │
│   ┌─────────────────────────────────────────────┐       │
│   │  dedupe.py                                   │       │
│   │  • Normalize titles                          │       │
│   │  • Remove exact duplicates                   │       │
│   │  • Merge metadata                            │       │
│   └─────────────────────────────────────────────┘       │
│      ↓                                                     │
│   3. Return papers immediately to user                    │
│   4. background_tasks.add_task(store_papers_background)  │
└──────┬───────────────────────────────────────────────────┘
       │ Response: { status, count, papers: [...] }
       ↓
┌─────────────────────────┐
│   Results.jsx           │
│   Display papers        │
│   Show filters          │
│   Show statistics       │
└─────────────────────────┘

       (Background Task)
       ↓
┌──────────────────────────────────────────┐
│   store_papers_background()              │
│   • Loop through papers DataFrame        │
│   • Batch insert (50 papers at a time)  │
│   • Retry logic (3 attempts)            │
│   • Exponential backoff                 │
└──────┬───────────────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   Supabase Database     │
│   research_papers table │
└─────────────────────────┘
```

---

### 2. Citation Mesh Flow

```
┌─────────────┐
│    USER     │
│ clicks      │
│"Citation    │
│ Mesh"       │
└──────┬──────┘
       │
       ↓
┌─────────────────────────┐
│   Results.jsx           │
│   handleCitationMesh()  │
└──────┬──────────────────┘
       │ HTTP POST /api/v1/citation/network
       │ Body: { papers: [...], max_depth: 1, max_nodes: 50 }
       ↓
┌──────────────────────────────────────────────────────────┐
│   Backend: citation.py                                    │
│   async def build_network()                               │
│                                                            │
│   ↓                                                        │
│   ┌─────────────────────────────────────────────┐       │
│   │  citation_network_service.py                 │       │
│   │                                               │       │
│   │  1. Extract paper IDs from input             │       │
│   │  2. For each paper:                          │       │
│   │     • Fetch work details from OpenAlex       │       │
│   │     • Extract referencedWorks                │       │
│   │     • Create nodes (paper objects)           │       │
│   │     • Create edges (citation links)          │       │
│   │  3. Limit to max_nodes                       │       │
│   │  4. Filter edges to valid nodes              │       │
│   │  5. Return graph data                        │       │
│   └─────────────────────────────────────────────┘       │
│      ↓                                                     │
│   Return: { nodes: [...], edges: [...], stats: {...} }  │
└──────┬───────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   CitationMesh.jsx      │
│   1. Load Cytoscape.js  │
│   2. Build elements     │
│   3. Render graph       │
│   4. Apply layout       │
│   5. Add interactions   │
└─────────────────────────┘
```

---

### 3. AI Summarization Flow

```
┌─────────────┐
│    USER     │
│ clicks      │
│"Summarize"  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────┐
│   Results.jsx           │
│   handleSummarize()     │
└──────┬──────────────────┘
       │ HTTP POST /api/v1/arxiv/summarize
       │ Body: { pdf_url: "..." }
       ↓
┌──────────────────────────────────────────────────────────┐
│   Backend: arxiv.py                                       │
│   async def summarize()                                   │
│                                                            │
│   1. extract_pdf_content(pdf_url)                        │
│      ↓                                                     │
│   ┌─────────────────────────────────────────────┐       │
│   │  pdf_extractor.py                            │       │
│   │  • Download PDF                              │       │
│   │  • Extract text with pdfplumber              │       │
│   │  • Clean and format                          │       │
│   └─────────────────────────────────────────────┘       │
│      ↓                                                     │
│   2. summarize_paper(text, use_llm=True)                 │
│      ↓                                                     │
│   ┌─────────────────────────────────────────────┐       │
│   │  summarization_service.py                    │       │
│   │  • Call summarize_with_llm()                 │       │
│   │    ↓                                          │       │
│   │  ┌──────────────────────────────────┐       │       │
│   │  │  llm_service.py                   │       │       │
│   │  │  • Build structured prompt        │       │       │
│   │  │  • Call OpenRouter API            │       │       │
│   │  │    ↓                               │       │       │
│   │  │  ┌────────────────────────┐       │       │       │
│   │  │  │  OpenRouter API         │       │       │       │
│   │  │  │  (GPT-4o-mini)          │       │       │       │
│   │  │  └────────────────────────┘       │       │       │
│   │  │    ↓                               │       │       │
│   │  │  • Parse JSON response             │       │       │
│   │  │  • Extract sections                │       │       │
│   │  └──────────────────────────────────┘       │       │
│   │    ↓                                          │       │
│   │  • Return structured summary                 │       │
│   │  • Fallback: extractive summarization       │       │
│   └─────────────────────────────────────────────┘       │
│      ↓                                                     │
│   Return: {                                               │
│     problem_statement: "...",                             │
│     methodology: "...",                                   │
│     key_findings: "...",                                  │
│     conclusion: "..."                                     │
│   }                                                        │
└──────┬───────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   Results.jsx           │
│   Display summary       │
│   in modal/panel        │
└─────────────────────────┘
```

---

### 4. Authentication Flow

```
┌─────────────┐
│    USER     │
│ clicks      │
│"Sign In"    │
└──────┬──────┘
       │
       ↓
┌─────────────────────────┐
│   AuthPage.jsx          │
│   Email/Password form   │
│   or Google OAuth       │
└──────┬──────────────────┘
       │
       ↓
┌─────────────────────────────────────────┐
│   Supabase Auth                          │
│                                           │
│   Email/Password:                         │
│   • signInWithPassword()                 │
│   • signUpWithPassword()                 │
│                                           │
│   Google OAuth:                           │
│   • signInWithOAuth({ provider: 'google'})│
│   • Redirect to Google                   │
│   • Redirect back to /auth/callback      │
└──────┬──────────────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   AuthCallback.jsx      │
│   Extract session       │
│   from URL hash         │
└──────┬──────────────────┘
       │
       ↓
┌─────────────────────────┐
│   AuthContext.jsx       │
│   Update user state     │
│   Store in context      │
└──────┬──────────────────┘
       │
       ↓
┌─────────────────────────┐
│   Navigate to /         │
│   User is logged in     │
│   Access protected      │
│   features              │
└─────────────────────────┘
```

---

### 5. Save Article Flow

```
┌─────────────┐
│    USER     │
│ clicks      │
│"Save"       │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│   Results.jsx                        │
│   handleSaveArticle(paper)           │
│                                       │
│   savedArticlesAPI.saveArticle(      │
│     paperId, paperData               │
│   )                                   │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────┐
│   api.js                             │
│   savedArticlesAPI.saveArticle()     │
│                                       │
│   1. Get current user from auth      │
│   2. Supabase upsert to              │
│      saved_articles table            │
│   3. Return saved article data       │
└──────┬──────────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   Supabase Database     │
│   saved_articles table  │
│   • user_id             │
│   • paper_id            │
│   • title               │
│   • notes (optional)    │
└─────────────────────────┘
       │
       ↓
┌─────────────────────────┐
│   Results.jsx           │
│   Update UI state       │
│   Show "Saved" badge    │
└─────────────────────────┘
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND COMPONENTS                         │
│                                                                      │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐               │
│  │   Navbar   │────│ AuthContext│────│  Footer    │               │
│  └────────────┘    └────────────┘    └────────────┘               │
│                            │                                         │
│        ┌───────────────────┼───────────────────┐                   │
│        │                   │                   │                   │
│  ┌──────────┐      ┌──────────────┐    ┌──────────────┐          │
│  │   Home   │      │   Results    │    │SavedSearches │          │
│  │   Page   │      │    Page      │    │    Page      │          │
│  └──────────┘      └──────┬───────┘    └──────────────┘          │
│                            │                                         │
│        ┌───────────────────┼───────────────────────────┐           │
│        │                   │                           │           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │SearchDropdown│  │CitationMesh  │  │ArticleNotesModal     │    │
│  └─────────────┘  └──────────────┘  └──────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     API SERVICE LAYER                      │    │
│  │  • searchAPI                                               │    │
│  │  • savedArticlesAPI                                        │    │
│  │  • arxivAPI, coreAPI, pmcAPI, etc.                        │    │
│  └──────────────────────────────────────────────────────────┘    │
│                            │                                         │
│                            ↓ HTTP                                   │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────┼────────────────────────────────────────┐
│                     BACKEND SERVICES                                 │
│                            │                                         │
│  ┌────────────────────────┼────────────────────────────────────┐  │
│  │              API ROUTES (FastAPI)                            │  │
│  │  • /search  • /papers  • /citation  • /arxiv  • /pmc       │  │
│  └────────────────────────┬────────────────────────────────────┘  │
│                            │                                         │
│        ┌───────────────────┼───────────────────┐                   │
│        │                   │                   │                   │
│  ┌──────────┐      ┌──────────────┐    ┌──────────────┐          │
│  │OpenAlex  │      │   Citation   │    │     LLM      │          │
│  │ Service  │      │   Network    │    │   Service    │          │
│  └──────────┘      └──────────────┘    └──────────────┘          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                     CRUD LAYER                             │    │
│  │  • papers_crud.py                                          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                            │                                         │
│                            ↓                                         │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────┼────────────────────────────────────────┐
│                       DATABASE LAYER                                 │
│                                                                      │
│  ┌────────────────────┐          ┌────────────────────┐           │
│  │ research_papers    │          │  saved_articles    │           │
│  └────────────────────┘          └────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Dependencies

```
┌────────────────────────────────────────────────────────────────┐
│                       FRONTEND STACK                            │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  React 19                                                       │
│    ├── React Router v7 (Routing)                               │
│    ├── React Context API (State Management)                    │
│    └── React Hooks (useState, useEffect, useCallback, etc.)    │
│                                                                  │
│  Vite (Build Tool)                                              │
│    └── @vitejs/plugin-react                                     │
│                                                                  │
│  Tailwind CSS 4                                                 │
│    └── @tailwindcss/vite                                        │
│                                                                  │
│  UI Libraries                                                   │
│    ├── Framer Motion (Animations)                              │
│    ├── Lucide React (Icons)                                    │
│    ├── Three.js (3D Effects)                                   │
│    └── Cytoscape.js (Graph Visualization)                      │
│        └── cytoscape-dagre (Layout Algorithm)                  │
│                                                                  │
│  Supabase                                                       │
│    └── @supabase/supabase-js (Client SDK)                      │
│                                                                  │
│  Export Libraries                                               │
│    ├── jsPDF (PDF Generation)                                  │
│    ├── jspdf-autotable (PDF Tables)                            │
│    └── xlsx (Excel Export)                                     │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                        BACKEND STACK                            │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FastAPI (Web Framework)                                        │
│    ├── Uvicorn (ASGI Server)                                   │
│    ├── Pydantic (Data Validation)                              │
│    └── pydantic-settings (Configuration)                       │
│                                                                  │
│  HTTP Clients                                                   │
│    ├── requests (Synchronous)                                  │
│    └── aiohttp (Asynchronous)                                  │
│                                                                  │
│  PDF Processing                                                 │
│    ├── pdfplumber (Text Extraction)                            │
│    └── PyMuPDF (Alternative PDF Library)                       │
│                                                                  │
│  Data Processing                                                │
│    ├── pandas (DataFrames)                                     │
│    └── fuzzywuzzy (Fuzzy Matching)                             │
│                                                                  │
│  Database                                                       │
│    └── supabase-py (Supabase Client)                           │
│                                                                  │
│  Web Scraping (Optional)                                        │
│    ├── beautifulsoup4 (HTML Parsing)                           │
│    └── serpapi (Google Scholar)                                │
│                                                                  │
│  Caching (Future)                                               │
│    └── redis (In-memory Cache)                                 │
│                                                                  │
│  Environment                                                    │
│    └── python-dotenv (Load .env files)                         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │  OpenAlex API        │      │  OpenRouter API      │       │
│  │  (Research Papers)   │      │  (LLM / GPT-4o-mini) │       │
│  └──────────────────────┘      └──────────────────────┘       │
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │  arXiv API           │      │  CORE API            │       │
│  │  (Preprints)         │      │  (Open Access)       │       │
│  └──────────────────────┘      └──────────────────────┘       │
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │  PMC API             │      │  Semantic Scholar    │       │
│  │  (Biomedical)        │      │  (Citations)         │       │
│  └──────────────────────┘      └──────────────────────┘       │
│                                                                  │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │  SerpAPI             │      │  Supabase            │       │
│  │  (Google Scholar)    │      │  (Database + Auth)   │       │
│  └──────────────────────┘      └──────────────────────┘       │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture (Planned)

```
┌────────────────────────────────────────────────────────────────┐
│                         CLOUD PROVIDERS                         │
│                                                                  │
│  ┌────────────────────┐      ┌────────────────────┐           │
│  │   Vercel           │      │   Railway          │           │
│  │   (Frontend)       │      │   (Backend)        │           │
│  │                    │      │                    │           │
│  │  • React App       │◄────►│  • FastAPI         │           │
│  │  • Static Assets   │ CORS │  • Python Runtime  │           │
│  │  • CDN             │      │  • Auto-scaling    │           │
│  └────────────────────┘      └────────────────────┘           │
│                                        │                         │
│                                        ↓                         │
│                              ┌────────────────────┐            │
│                              │   Supabase         │            │
│                              │   (Database+Auth)  │            │
│                              │                    │            │
│                              │  • PostgreSQL      │            │
│                              │  • Auth Service    │            │
│                              │  • Storage         │            │
│                              └────────────────────┘            │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

Alternative: Docker Containerization

┌────────────────────────────────────────────────────────────────┐
│                      DOCKER COMPOSE SETUP                       │
│                                                                  │
│  ┌────────────────────┐      ┌────────────────────┐           │
│  │  frontend:5173     │      │  backend:8000      │           │
│  │  (React + Nginx)   │◄────►│  (FastAPI)         │           │
│  └────────────────────┘      └────────────────────┘           │
│                                        │                         │
│                                        ↓                         │
│                              ┌────────────────────┐            │
│                              │   Supabase         │            │
│                              │   (Cloud)          │            │
│                              └────────────────────┘            │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

This architecture document provides visual representations of how all components interact within the ReSearch Flow system.

