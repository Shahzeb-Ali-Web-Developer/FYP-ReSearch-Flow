# arXiv Search & Summarization Implementation

This document describes the implementation of arXiv search and PDF summarization features.

## Overview

The system now supports:
- Searching arXiv for research papers
- Displaying arXiv-specific metadata (arXiv ID, published date, abstract preview)
- Summarizing papers by extracting text from PDFs and generating structured summaries

## API Endpoints

### 1. Search arXiv Papers

**Endpoint:** `GET /api/v1/arxiv/search?query=<topic>&limit=<n>`

**Example:**
```bash
curl "http://127.0.0.1:8000/api/v1/arxiv/search?query=machine+learning&limit=20"
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 20 papers for 'machine learning'",
  "count": 20,
  "query": "machine learning",
  "papers": [
    {
      "arxiv_id": "2401.12345v1",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "published_date": "2024-01-15T10:30:00",
      "abstract": "Paper abstract...",
      "pdf_url": "https://arxiv.org/pdf/2401.12345v1.pdf",
      "abstract_url": "https://arxiv.org/abs/2401.12345v1",
      "categories": ["cs.LG", "cs.AI"],
      "source": "arXiv"
    }
  ]
}
```

### 2. Summarize Paper

**Endpoint:** `POST /api/v1/arxiv/summarize`

**Request Body:**
```json
{
  "arxiv_id": "2401.12345"  // OR
  // "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf"
}
```

**Response:**
```json
{
  "status": "success",
  "arxiv_id": "2401.12345",
  "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
  "text_length": 45230,
  "summary": {
    "problem_statement": "Summary of the problem...",
    "methodology": "Summary of methodology...",
    "key_findings": "Summary of findings...",
    "conclusion": "Summary of conclusion..."
  }
}
```

## Backend Implementation

### Services

#### 1. arXiv Service (`backend/src/app/services/arxiv_service.py`)
- Fetches papers from arXiv API (http://export.arxiv.org/api/query)
- Parses ATOM XML responses
- Extracts: title, authors, published date, abstract, arXiv ID, PDF URL, categories

#### 2. PDF Service (`backend/src/app/services/pdf_service.py`)
- Downloads PDFs from URLs
- Extracts text using PyMuPDF (fitz)
- Cleans extracted text (removes excessive whitespace, references)
- Limits processing to first 50 pages for efficiency

#### 3. Summarization Service (`backend/src/app/services/summarization_service.py`)
- Local extractive summarization (no external LLM APIs)
- Uses sentence scoring based on word frequency and position
- Extracts structured sections: problem statement, methodology, key findings, conclusion
- Can be easily replaced with LLM API in the future

### Routes

**File:** `backend/src/app/api/v1/routes/arxiv.py`
- `/api/v1/arxiv/search` - Search endpoint
- `/api/v1/arxiv/summarize` - Summarization endpoint

## Frontend Implementation

### API Service

**File:** `frontend/src/services/api.js`

Added `arxivAPI` object with:
- `searchPapers(query, limit)` - Search arXiv
- `summarizePaper(arxivId, pdfUrl)` - Summarize a paper

### Results Page

**File:** `frontend/src/pages/Results.jsx`

**Changes:**
1. Uses `arxivAPI.searchPapers()` instead of OpenAlex search
2. Updated `PaperListItem` component to:
   - Display arXiv ID
   - Show published date
   - Display abstract preview
   - Include "Summarize" button for arXiv papers
3. Added summary display below each paper
4. Added summarization state management

**Paper List Item Features:**
- Shows arXiv ID in monospace font
- Published date/year
- Author list
- Abstract preview (truncated to 200 chars)
- PDF link
- "Summarize" button (arXiv papers only)

**Summary Display:**
When a summary is generated, it appears below the paper with sections:
- Problem Statement
- Methodology
- Key Findings
- Conclusion

## Dependencies

### Backend
- `PyMuPDF` (fitz) - PDF text extraction
- `requests` - HTTP requests to arXiv API
- `xml.etree.ElementTree` - XML parsing (built-in)

### Frontend
- No new dependencies (uses existing React setup)

## Usage Flow

1. **User searches for a topic**
   - Enters query in search bar
   - Frontend calls `arxivAPI.searchPapers()`
   - Results displayed with arXiv metadata

2. **User clicks "Summarize"**
   - Frontend calls `arxivAPI.summarizePaper(arxivId)`
   - Backend:
     - Downloads PDF from arXiv
     - Extracts text using PyMuPDF
     - Generates structured summary
   - Frontend displays summary below paper

## Future Enhancements

The summarization service is designed to be easily replaceable:

1. **LLM Integration:** Replace `summarize_paper()` function in `summarization_service.py` with LLM API calls
2. **Better Text Cleaning:** Enhance PDF text extraction for better quality
3. **Caching:** Cache summaries to avoid re-processing
4. **Batch Summarization:** Allow summarizing multiple papers at once

## Notes

- PDF processing is limited to first 50 pages for performance
- Summarization uses simple extractive method (can be upgraded to abstractive with LLM)
- All arXiv papers are open access, so PDFs are always available
- The system maintains compatibility with existing OpenAlex paper format for other features

<<<<<<< HEAD

=======
>>>>>>> 19c62c6432f4465bd0724c79e5a8f133d21dc582
