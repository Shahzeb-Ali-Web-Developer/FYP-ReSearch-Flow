# ReSearch Flow – AI Research Assistant

ReSearch Flow is an **AI-powered academic research assistant** designed to simplify how students and researchers discover, analyze, and organize scholarly articles.  
It integrates **web scraping**, **citation mesh visualization**, and **Generative AI** to automate the literature review process — from topic discovery to draft writing.

---

## Project Overview

**ReSearch Flow** allows users to:
- Search research articles by topic  
- View key metadata (authors, abstract, citations)  
- Explore a **Citation Mesh** (interactive graph of references)  
- Generate **AI-based summaries** of articles  
- Identify research **trends and common techniques**  
- Auto-generate structured drafts (Introduction, Literature Review, Methodology)  
- Save sessions and export findings in multiple formats

---

## Key Features

| # | Feature | Description |
|---|----------|-------------|
| 1 | **Topic-Based Article Search** | Users can search for research articles by entering a topic. Results are fetched via open APIs and scraping. |
| 2 | **Article Metadata Preview** | Displays title, author(s), abstract snippet, and citation count for each result. |
| 3 | **Citation Mesh Visualization** | Interactive graph showing how papers are connected through citations. |
| 4 | **AI Summary Generation** | Generates concise summaries (150–200 words) for each paper. |
| 5 | **Trend & Technique Analysis** | Identifies frequently used keywords, methods, and algorithms. |
| 6 | **AI Draft Assistant** | Creates structured drafts for paper sections (Intro, Literature Review, Methodology). |
| 7 | **Save & Export Workspace** | Save bookmarks, notes, and export as PDF/DOCX/Reference List. |

---

## System Architecture

The system follows an **N-Tier (Layered Architecture)** based on the **MVC principle**:

### **1. Presentation Layer (Frontend)**
- **Framework:** React.js + Tailwind CSS  
- Handles UI/UX, visualizations, user input, and authentication  
- Integrates graph visualization using **D3.js / Cytoscape.js**

### **2. Business Logic Layer (Backend)**
- **Framework:** FastAPI  
- Manages topic search, web scraping, summarization, and communication between frontend and database  
- Integrates **LLMs (OpenAI GPT / PEGASUS / BART / FLAN-T5)** for summarization  

### **3. Data Layer (Database)**
- **Database:** Supabase (PostgreSQL-based)  
- Stores user accounts, search history, metadata, references, and notes  
- Supports Supabase Auth for secure user login (Google, Email/Password)

---

## Technology Stack

| Component | Technology |
|------------|-------------|
| **Frontend** | React.js, Tailwind CSS, D3.js / Cytoscape.js |
| **Backend** | FastAPI (Python) |
| **Database** | Supabase (PostgreSQL) |
| **AI Models** | GPT, PEGASUS, BART, FLAN-T5, TextRank |
| **Web Scraping** | BeautifulSoup, Playwright |
| **Version Control** | Git + GitHub |
| **Project Management** | Trello (Agile Sprints) |
| **Deployment** | Docker (Containerized setup) |

---

## Core Functional Workflow

1. User enters a topic  
2. FastAPI backend scrapes open-access sources (arXiv, Semantic Scholar, CORE API)  
3. Articles + metadata stored in Supabase  
4. LLM generates summaries and key insights  
5. Citation Mesh is generated and rendered in React  
6. User can explore, bookmark, summarize, and export results  

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

## Challenges & Mitigation

| Challenge | Mitigation |
|------------|-------------|
| Web scraping restrictions | Focus on open-access APIs + caching |
| AI summarization cost | Use open-source models (BART, PEGASUS) |
| Citation mesh scalability | Graph optimization + lazy loading |
| Time constraints | Agile sprints + incremental milestones |

---

## Future Enhancements

- Semantic vector-based search (e.g., Sentence-BERT)
- Chrome Extension for real-time mesh exploration
- Collaborative workspace (shared notes, highlights)
- Export to LaTeX & reference management formats (APA, BibTeX)
- User dashboards with saved projects and AI suggestions

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
