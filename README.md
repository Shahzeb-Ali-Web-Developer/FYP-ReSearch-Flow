# 🚀 ReSearch Flow  
### AI-Powered Academic Research Assistant  

ReSearch Flow is a full-stack AI-driven platform designed to simplify and accelerate the academic literature review process. It integrates multi-source research retrieval, intelligent deduplication, AI summarization, conversational Q&A, citation network visualization, and draft generation into a single unified system.

---

## 📌 Problem Statement

Modern research workflows are fragmented across multiple platforms such as Google Scholar, PubMed, and arXiv. Researchers face challenges including:

- Switching between multiple databases  
- Duplicate results across sources  
- Time-consuming paper analysis  
- Lack of visualization for citation relationships  
- No unified AI-assisted research workflow  

---

## 💡 Solution

ReSearch Flow provides an **end-to-end research assistant** that:

- Aggregates papers from multiple academic sources  
- Removes duplicates intelligently  
- Generates AI-powered summaries  
- Enables conversational Q&A on papers (RAG)  
- Visualizes citation relationships  
- Assists in research draft writing  

---

## ✨ Key Features

### 🔍 Multi-Source Search
- OpenAlex, arXiv, CORE, PubMed, Semantic Scholar, Google Scholar  
- Parallel API calls with progressive loading  

### 🧠 AI Summarization
- GPT-4o based structured summaries  
- Extracts insights from full PDF content  

### 💬 RAG-based Chat
- Ask questions about any paper  
- Hybrid retrieval (Pinecone + BM25)  
- Context-aware responses  

### 🕸️ Citation Mesh
- Interactive graph visualization (Cytoscape.js)  
- Metrics: PageRank, Influence Score, Citation Velocity  

### 📝 Draft Generation
- AI-generated structured drafts  
- Uses both text + figures (Vision AI)  

### 🗂️ User Workspace
- Save articles  
- Manage search history  
- Add personal notes  

### ⚡ Performance Optimization
- Background caching (Supabase)  
- Redis-based chat session storage  

---

## 🏗️ System Architecture
Frontend (React + Vite)
↓
Backend (FastAPI)
↓
AI Layer (LangChain + GPT-4o)
↓
Databases (Supabase, Pinecone, Redis)
↓
External APIs (OpenAlex, arXiv, etc.)


---

## 🧰 Tech Stack

### 🌐 Frontend
- React 19 + Vite  
- Tailwind CSS  
- Framer Motion  
- Cytoscape.js  

### ⚙️ Backend
- FastAPI (Python 3.11)  
- PyMuPDF (PDF parsing)  
- Pandas  

### 🤖 AI & ML
- OpenAI GPT-4o  
- LangChain  
- Pinecone (Vector DB)  
- BM25 Retriever  

### 🗄️ Database & Storage
- Supabase (PostgreSQL + Auth)  
- Upstash Redis  
- Neo4j (optional)  

---

## 🗃️ Database Design

The system uses a hybrid approach:

- **Structured Data** → Supabase (users, saved searches, history)  
- **Cached Papers** → research_papers table  
- **Vector Embeddings** → Pinecone  
- **Session Data** → Redis  

---

## 🔄 Workflow Overview

1. User enters search query  
2. System queries multiple APIs in parallel  
3. Results are deduplicated  
4. Cached in database  
5. AI modules process data (summary, chat, draft)  
6. Results are displayed with interactive visualizations  

---

## 📊 Results & Performance

- ⚡ First results: ~1.8 seconds  
- 🔁 Full results: 6–9 seconds  
- 🧹 Deduplication: ~38% reduction  
- 🤖 RAG Accuracy:  
  - 74% Correct  
  - 18% Partial  
  - 8% Incorrect  

---

## 🔐 Authentication

- Supabase Auth (JWT-based)  
- Google OAuth support  
- Row-Level Security (RLS)  

---

## 🧪 Testing

- Unit testing for all core modules  
- Integration testing for full workflows  
- Manual evaluation with real academic datasets  

---

## 🚧 Limitations

- Requires open-access PDFs for full AI analysis  
- API rate limits (especially Google Scholar)  
- Initial RAG indexing delay for new papers  

---

## 🔮 Future Work

- Semantic vector search (Sentence-BERT)  
- Multi-modal RAG (text + figures)  
- Chrome extension  
- Collaborative research workspace  
- Mobile app  
- OCR for scanned PDFs  

---

## 👨‍💻 Team

- **Haroon Mahmood (BSDSF22M020)**  
- **Maryam Abid (BSDSF22M028)**  
- **Areesha Rizwan (BSDSF22M048)**  
- **Shahzeb Ali (BSDSF22M054)**  

---

## 🎓 Supervisor

**Dr. Khurram Shahzad**  
Faculty of Computing & Information Technology  
University of the Punjab, Lahore  

---

## 📜 License

This project is developed for academic purposes as a Final Year Project.  

The system follows a modular layered architecture:
