# ReSearch Flow – AI Research Assistant

ReSearch Flow is an **AI-powered academic research assistant** designed to simplify how students and researchers discover, analyze, and organize scholarly articles.  
It integrates **web scraping**, **citation mesh visualization**, and **Generative AI** to automate the literature review process — from topic discovery to draft writing.

---

## Project Overview

**ReSearch Flow** allows users to:
- ✅ Search research articles by topic using OpenAlex API  
- ✅ View comprehensive metadata (authors, abstract, citations, venue, year, open access status)  
- ✅ Filter results by multiple criteria (year, type, fields of study, open access)  
- ✅ Explore detailed paper information in interactive panels  
- ✅ View real-time statistics and analytics  
- 📋 Explore a **Citation Mesh** (interactive graph of references) - *Planned*  
- 📋 Generate **AI-based summaries** of articles - *Planned*  
- 📋 Identify research **trends and common techniques** - *Planned*  
- 📋 Auto-generate structured drafts (Introduction, Literature Review, Methodology) - *Planned*  
- 📋 Save sessions and export findings in multiple formats - *Planned*

---

## Key Features

| # | Feature | Status | Description |
|---|----------|--------|-------------|
| 1 | **Topic-Based Article Search** | ✅ **Implemented** | Users can search for research articles by entering a topic. Results are fetched from OpenAlex API. |
| 2 | **Article Metadata Preview** | ✅ **Implemented** | Displays title, author(s), abstract, citation count, venue, year, and open access status for each result. |
| 3 | **Advanced Filtering & Search** | ✅ **Implemented** | Filter by year, publication type, fields of study, and open access status. Query builder with multiple filter conditions. |
| 4 | **Paper Detail View** | ✅ **Implemented** | Interactive slide-in panel showing complete paper details including full abstract, authors, citations, DOI, and links. |
| 5 | **Statistics Dashboard** | ✅ **Implemented** | Real-time statistics panel showing result counts, year distribution, topic distribution, and open access percentage. |
| 6 | **Database Integration** | ✅ **Implemented** | Automatic background storage of search results to Supabase PostgreSQL database with batch processing and retry logic. |
| 7 | **Authentication System** | 🔄 **In Progress** | Supabase Auth integration with email/password and OAuth providers (Google). Context and pages implemented. |
| 8 | **Citation Mesh Visualization** | 📋 **Planned** | Interactive graph showing how papers are connected through citations (D3.js / Cytoscape.js integration). |
| 9 | **AI Summary Generation** | 📋 **Planned** | Generates concise summaries (150–200 words) for each paper using LLMs (GPT, BART, PEGASUS). |
| 10 | **Trend & Technique Analysis** | 📋 **Planned** | Identifies frequently used keywords, methods, and algorithms across research papers. |
| 11 | **AI Draft Assistant** | 📋 **Planned** | Creates structured drafts for paper sections (Introduction, Literature Review, Methodology). |
| 12 | **Save & Export Workspace** | 📋 **Planned** | Save bookmarks, notes, and export as PDF/DOCX/Reference List (BibTeX, APA format). |

---

## System Architecture

The system follows an **N-Tier (Layered Architecture)** based on the **MVC principle**:

### **1. Presentation Layer (Frontend)**
- **Framework:** React.js 19 + Vite + Tailwind CSS 4  
- **UI Libraries:** Framer Motion, Three.js, Lucide React Icons  
- **Routing:** React Router v7  
- Handles UI/UX, user input, authentication, and results visualization  
- **Status:** Core search, filtering, and results display fully implemented  
- **Planned:** Graph visualization using D3.js / Cytoscape.js for citation networks

### **2. Business Logic Layer (Backend)**
- **Framework:** FastAPI (Python)  
- **API Integration:** OpenAlex API for research paper search  
- Manages topic search, data normalization, deduplication, and communication between frontend and database  
- **Background Processing:** Asynchronous paper storage to database  
- **Status:** Search and data storage fully functional  
- **Planned:** LLM integration (OpenAI GPT / PEGASUS / BART / FLAN-T5) for summarization  

### **3. Data Layer (Database)**
- **Database:** Supabase (PostgreSQL-based)  
- Stores research paper metadata, search history, and user data  
- **Features:** Batch insert with retry logic, upsert operations for deduplication  
- Supports Supabase Auth for secure user login (Google, Email/Password)  
- **Status:** Database schema and CRUD operations implemented

---

## Technology Stack

| Component | Technology | Status |
|------------|-------------|--------|
| **Frontend** | React.js 19, Vite, Tailwind CSS 4, React Router v7 | ✅ Implemented |
| **UI Libraries** | Framer Motion, Three.js, Lucide React | ✅ Implemented |
| **Backend** | FastAPI (Python), Uvicorn | ✅ Implemented |
| **API Integration** | OpenAlex API | ✅ Implemented |
| **Database** | Supabase (PostgreSQL) | ✅ Implemented |
| **Authentication** | Supabase Auth | 🔄 In Progress |
| **Graph Visualization** | D3.js / Cytoscape.js | 📋 Planned |
| **AI Models** | GPT, PEGASUS, BART, FLAN-T5 | 📋 Planned |
| **PDF Processing** | pdfplumber | ✅ Available |
| **Data Processing** | Pandas, Requests, aiohttp | ✅ Implemented |
| **Version Control** | Git + GitHub | ✅ Active |
| **Project Management** | Trello (Agile Sprints) | ✅ Active |
| **Deployment** | Docker (Containerized setup) | 📋 Planned |

---

## Core Functional Workflow

### Current Implementation ✅

1. User enters a topic on the home page  
2. FastAPI backend queries **OpenAlex API** for research papers  
3. Results are normalized, deduplicated, and returned immediately  
4. Papers are stored in Supabase database asynchronously (background task)  
5. User views results with filtering options (year, type, open access, fields of study)  
6. User can click papers to view detailed metadata in slide-in panel  
7. Statistics panel shows real-time analytics of search results  

### Planned Features 📋

4. LLM generates summaries and key insights for papers  
5. Citation Mesh is generated and rendered in React (D3.js / Cytoscape.js)  
6. User can bookmark, save notes, and export findings in multiple formats  

---

## Team Members

| Name | Roll No. | Role |
|------|-----------|------|
| **Shahzeb Ali** | BSDSF22M054 | Backend Development |
| **Areesha Rizwan** | BSDSF22M048 | Database Administration |
| **Haroon Mahmood** | BSDSF22M020 | Web Deployment |
| **Maryam Abid** | BSDSF22M028 | Front End Development |

**Supervisor:** Dr. Khurram Shahzad  
**Department:** Data Science, FCIT – University of the Punjab, Lahore  
**Batch:** BS Data Science (2022–2026)

---

## Project Deliverables (as per FYP Guidebook)

- **Deliverable 1:** User Stories & UI/UX Design (Figma)  
- **Deliverable 2:** Project Sprint Documentation  
- **Prototype 1:** Main User Story Implementation  
- **Final Version:** Fully integrated, containerized system with AI backend and React frontend  

---

## Agile Workflow

- **Project Management:** Trello Board (Backlog → In Progress → Done)  
- **Version Control:** GitHub (feature branches + pull requests)  
- **Sprints:** 2-week cycles  
- **Reviews:** Weekly with supervisor  
- **Documentation:** GitHub Wiki + PDF reports

---

## Current Progress Summary

### ✅ Completed Features

- **Search Functionality:** Topic-based search via OpenAlex API with real-time results
- **Results Display:** Comprehensive paper listing with metadata (title, authors, abstract, citations, venue, year)
- **Advanced Filtering:** Multi-criteria filtering by year, publication type, fields of study, and open access status
- **Paper Details:** Interactive detail panel with full paper information
- **Statistics Dashboard:** Real-time analytics showing result counts, distributions, and trends
- **Database Integration:** Automatic background storage with batch processing and error handling
- **Data Deduplication:** Smart deduplication based on paper titles and metadata
- **Responsive UI:** Modern, clean interface with mobile support
- **Authentication Setup:** Supabase Auth context and pages implemented

### 🔄 In Progress

- **Authentication Integration:** Connecting auth system with protected routes and user sessions
- **Paper CRUD API:** Expanding backend endpoints for retrieving stored papers

### 📋 Planned Features

- **Citation Mesh Visualization:** Interactive graph network using D3.js or Cytoscape.js
- **AI Summarization:** Integration with LLMs (GPT, BART, PEGASUS) for paper summaries
- **Trend Analysis:** Keyword extraction and technique identification
- **AI Draft Assistant:** Automated draft generation for paper sections
- **Export Functionality:** PDF, DOCX, and reference list (BibTeX, APA) export
- **User Workspace:** Save searches, bookmarks, and notes
- **Docker Deployment:** Containerized setup for easy deployment

---

## Challenges & Mitigation

| Challenge | Mitigation | Status |
|-----------|------------|--------|
| API rate limits | Using OpenAlex (free, no API key required) + background processing | ✅ Resolved |
| Data deduplication | Title-based normalization and fuzzy matching | ✅ Implemented |
| Database performance | Batch inserts with retry logic and error handling | ✅ Implemented |
| AI summarization cost | Plan to use open-source models (BART, PEGASUS) | 📋 Planned |
| Citation mesh scalability | Graph optimization + lazy loading strategies | 📋 Planned |
| Time constraints | Agile sprints + incremental milestones | ✅ Active |

---

## Future Enhancements

- **Semantic Search:** Vector-based search using Sentence-BERT for improved relevance
- **Chrome Extension:** Real-time citation mesh exploration while browsing papers
- **Collaborative Features:** Shared workspaces with team notes and highlights
- **Advanced Export:** LaTeX, BibTeX, APA, MLA format support
- **User Dashboards:** Personalized dashboards with saved projects, search history, and AI suggestions
- **Real-time Updates:** WebSocket integration for live collaboration
- **Mobile App:** Native mobile application for iOS and Android

---

## License

This project is developed as part of the **Final Year Project (Capstone I & II)** under the  
**Department of Data Science, University of the Punjab, Lahore.**  
All rights reserved © 2025 — *Team ReSearch Flow*.

---

## Links

-  **University Portal:** [FCIT – University of the Punjab](https://pucit.edu.pk)  
-  **Project Management:** [Trello Board (Internal)]  
-  **GitHub Repository:** *(this repo)*  
-  **Documentation:** [Proposal PDF] | [User Stories PDF] | [Architecture DOCX]

---
