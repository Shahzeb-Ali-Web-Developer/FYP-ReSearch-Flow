# Contributing to ReSearch Flow

First off, thank you for considering contributing to ReSearch Flow! This document provides guidelines for contributing to the project.

---

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Commit Guidelines](#commit-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:
- Be respectful and considerate
- Accept constructive criticism gracefully
- Focus on what is best for the project
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment or discrimination of any kind
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites
Before contributing, make sure you have:
- [x] Read the [README.md](README.md)
- [x] Read the [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- [x] Read the [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- [x] Set up your local development environment
- [x] Familiarized yourself with the codebase

### Setup Your Development Environment

1. **Fork the Repository**
   ```bash
   # Click "Fork" button on GitHub
   # Then clone your fork
   git clone https://github.com/YOUR_USERNAME/FYP-ReSearch-Flow.git
   cd FYP-ReSearch-Flow
   ```

2. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/FYP-ReSearch-Flow.git
   ```

3. **Install Dependencies**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

4. **Set Up Environment Variables**
   ```bash
   # Copy example files
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   
   # Edit with your credentials
   ```

5. **Verify Setup**
   ```bash
   # Run servers (see QUICK_START.md)
   # Backend: http://localhost:8000/health
   # Frontend: http://localhost:5173
   ```

---

## Development Workflow

### 1. Pick an Issue
- Check [GitHub Issues](https://github.com/your-org/FYP-ReSearch-Flow/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to let others know you're working on it
- Or create a new issue if you found a bug or have a feature idea

### 2. Create a Feature Branch
```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

**Branch Naming Convention**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only changes
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `chore/` - Maintenance tasks

**Examples**:
```
feature/add-bibtex-export
fix/citation-mesh-crash
docs/update-api-guide
refactor/optimize-search-query
test/add-openalex-tests
chore/update-dependencies
```

### 3. Make Your Changes
- Write clean, readable code
- Follow coding standards (see below)
- Add comments for complex logic
- Update documentation if needed
- Add tests if applicable

### 4. Test Your Changes
```bash
# Backend
cd backend
pytest  # (when tests are available)

# Frontend
cd frontend
npm run lint
npm run build  # Check for build errors

# Manual testing
# - Test the feature works as expected
# - Test edge cases
# - Test on different browsers/devices
```

### 5. Commit Your Changes
```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "feat: add BibTeX export functionality"

# See Commit Guidelines below for more details
```

### 6. Push to Your Fork
```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request
- Go to your fork on GitHub
- Click "New Pull Request"
- Select your feature branch
- Fill out the PR template
- Submit for review

---

## Coding Standards

### Python (Backend)

#### Style Guide
Follow [PEP 8](https://pep8.org/) style guide:
- 4 spaces for indentation
- Max line length: 100 characters
- Two blank lines between top-level functions/classes

#### Type Hints
Use type hints for function parameters and return values:
```python
from typing import List, Optional, Dict

def fetch_papers(
    topic: str, 
    limit: int = 20
) -> Dict[str, any]:
    """Fetch research papers."""
    pass
```

#### Docstrings
Use Google-style docstrings:
```python
def process_paper(paper_data: Dict) -> Paper:
    """Process raw paper data into Paper object.
    
    Args:
        paper_data: Dictionary containing paper metadata
        
    Returns:
        Paper object with normalized data
        
    Raises:
        ValueError: If paper_data is invalid
    """
    pass
```

#### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

#### Example
```python
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class PaperService:
    """Service for managing research papers."""
    
    MAX_BATCH_SIZE = 50  # Constant
    
    def __init__(self, api_key: str):
        """Initialize service with API key."""
        self.api_key = api_key
        self._cache = {}  # Private attribute
    
    def fetch_papers(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Fetch papers matching query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        logger.info(f"Fetching papers for query: {query}")
        
        # Implementation
        papers = self._call_api(query, limit)
        
        return papers
    
    def _call_api(self, query: str, limit: int) -> List[Dict]:
        """Private method to call external API."""
        # Implementation
        pass
```

---

### JavaScript/React (Frontend)

#### Style Guide
Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript):
- 2 spaces for indentation
- Use `const` and `let`, not `var`
- Use template literals for string interpolation
- Use arrow functions for callbacks

#### Component Structure
```jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { BookOpen } from 'lucide-react';

/**
 * PaperCard component displays paper information.
 * 
 * @param {Object} props
 * @param {Object} props.paper - Paper data object
 * @param {Function} props.onClick - Click handler
 */
const PaperCard = ({ paper, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  useEffect(() => {
    // Side effects here
  }, [paper]);
  
  const handleClick = () => {
    onClick(paper.id);
  };
  
  return (
    <div 
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="paper-card"
    >
      <h3>{paper.title}</h3>
      <p>{paper.abstract}</p>
    </div>
  );
};

PaperCard.propTypes = {
  paper: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    abstract: PropTypes.string,
  }).isRequired,
  onClick: PropTypes.func.isRequired,
};

export default PaperCard;
```

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `PaperCard.jsx`)
- **Functions/Variables**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **CSS classes**: `kebab-case` or Tailwind utilities

#### Hooks
```jsx
// Custom hooks start with 'use'
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
}
```

#### API Calls
```jsx
// Use async/await with try-catch
async function fetchPapers(topic) {
  try {
    const response = await searchAPI.fetchPapers(topic, 20);
    return response.papers;
  } catch (error) {
    console.error('Failed to fetch papers:', error);
    throw error;
  }
}
```

---

## Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Formatting, missing semicolons, etc. (no code change)
- **refactor**: Code refactoring (no functional change)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies

### Examples

**Good Commits**:
```bash
feat(search): add multi-source search support

- Integrate arXiv, CORE, PMC APIs
- Add source selection dropdown
- Update result display with source badges

Closes #45

---

fix(citation-mesh): resolve graph rendering crash for large datasets

The graph would crash when rendering >100 nodes due to memory issues.
Now implements pagination and lazy loading.

Fixes #78

---

docs(api): add examples for search endpoint

Added code examples in Python and JavaScript for the /search/fetch endpoint.

---

refactor(backend): optimize database queries

- Add indexes on frequently queried fields
- Use batch operations for bulk inserts
- Reduce N+1 queries

Performance improvement: 40% faster queries

---

test(openalex): add unit tests for service

Added tests for:
- fetch_openalex_papers()
- _flatten_abstract()
- Error handling

Coverage: 85%
```

**Bad Commits**:
```bash
# Too vague
fix: bug fix

# No description
feat: new feature

# Multiple concerns in one commit
feat: add search, fix bug, update docs

# Too long subject line
feat: add a really long description that goes way beyond the recommended character limit
```

### Commit Best Practices
1. **One logical change per commit**
   - Don't mix feature and bug fix
   - Don't mix refactoring and feature
   
2. **Write meaningful messages**
   - Explain WHAT and WHY, not HOW
   - Include context if needed
   
3. **Keep commits small**
   - Easier to review
   - Easier to revert if needed
   
4. **Reference issues**
   - Use `Closes #123` or `Fixes #456`

---

## Pull Request Process

### Before Creating PR

1. **Update from upstream**
   ```bash
   git checkout main
   git pull upstream main
   git checkout feature/your-feature
   git rebase main
   ```

2. **Run tests and linters**
   ```bash
   # Backend
   cd backend
   flake8 src/
   
   # Frontend
   cd frontend
   npm run lint
   npm run build
   ```

3. **Review your changes**
   ```bash
   git diff main
   ```

### Creating PR

1. **Use PR Template**
   Fill out all sections:
   - Description
   - Type of change
   - Checklist
   - Screenshots (if UI change)

2. **Title Format**
   ```
   feat: Add BibTeX export functionality
   fix: Resolve citation mesh rendering issue
   docs: Update API documentation
   ```

3. **Description**
   - What does this PR do?
   - Why is this change needed?
   - How was it tested?
   - Any breaking changes?

4. **Link Issues**
   ```markdown
   Closes #123
   Related to #456
   ```

### PR Template Example
```markdown
## Description
Add BibTeX export functionality for saved papers.

## Type of Change
- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
- [x] Manual testing with 10+ papers
- [x] Tested export format in LaTeX
- [x] Tested with special characters in titles

## Checklist
- [x] Code follows style guidelines
- [x] Self-review completed
- [x] Comments added for complex code
- [x] Documentation updated
- [x] No new warnings
- [x] Tests added (if applicable)

## Screenshots (if applicable)
![BibTeX Export Button](screenshot.png)

## Additional Notes
BibTeX format follows standard citation format. Tested with Overleaf and TeXworks.
```

### PR Review Process

1. **Automated Checks**
   - Linting passes
   - Build succeeds
   - Tests pass (when available)

2. **Code Review**
   - At least 1 team member reviews
   - Address review comments
   - Make requested changes

3. **Approval**
   - Reviewer approves PR
   - No merge conflicts
   - All checks pass

4. **Merge**
   - Squash and merge (default)
   - Or rebase and merge (for clean history)
   - Delete branch after merge

---

## Testing Guidelines

### Backend Testing

#### Unit Tests
```python
# backend/src/app/tests/test_openalex_service.py
import pytest
from src.app.services.openalex_service import fetch_openalex_papers

def test_fetch_openalex_papers():
    """Test fetching papers from OpenAlex."""
    df = fetch_openalex_papers("machine learning", limit=5)
    
    assert not df.empty
    assert len(df) <= 5
    assert "title" in df.columns
    assert "authors" in df.columns

def test_fetch_openalex_papers_empty_query():
    """Test with empty query."""
    df = fetch_openalex_papers("", limit=5)
    
    assert df.empty
```

#### Run Tests
```bash
cd backend
pytest
pytest -v  # Verbose
pytest --cov  # With coverage
```

---

### Frontend Testing

#### Component Tests (Future)
```jsx
// frontend/src/__tests__/PaperCard.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import PaperCard from '../components/PaperCard';

test('renders paper title', () => {
  const paper = {
    id: '1',
    title: 'Test Paper',
    authors: ['Author 1'],
  };
  
  render(<PaperCard paper={paper} onClick={() => {}} />);
  
  expect(screen.getByText('Test Paper')).toBeInTheDocument();
});

test('calls onClick when clicked', () => {
  const mockOnClick = jest.fn();
  const paper = { id: '1', title: 'Test Paper', authors: [] };
  
  render(<PaperCard paper={paper} onClick={mockOnClick} />);
  
  fireEvent.click(screen.getByText('Test Paper'));
  
  expect(mockOnClick).toHaveBeenCalledWith('1');
});
```

---

### Manual Testing Checklist

#### New Feature
- [ ] Feature works as described
- [ ] Edge cases handled
- [ ] Error handling works
- [ ] UI is responsive
- [ ] Works on different browsers
- [ ] Works on mobile devices
- [ ] No console errors
- [ ] No network errors

#### Bug Fix
- [ ] Bug is fixed
- [ ] Fix doesn't introduce new bugs
- [ ] Regression tests pass
- [ ] Related functionality still works

---

## Documentation

### When to Update Documentation

Update documentation when you:
- Add a new feature
- Change existing functionality
- Add new API endpoints
- Change database schema
- Add new dependencies
- Change configuration

### Documentation Files

| File | Update When |
|------|-------------|
| `README.md` | Add major feature, change setup |
| `PROJECT_OVERVIEW.md` | Change architecture, add component |
| `DEVELOPER_GUIDE.md` | Add development task, change workflow |
| `ARCHITECTURE_DIAGRAM.md` | Change system architecture |
| `API_DOCS.md` | Add/change API endpoint |
| `ROADMAP.md` | Complete milestone, change plan |

### Code Comments

#### When to Add Comments
- Complex algorithms
- Non-obvious logic
- Workarounds or hacks
- TODOs and FIXMEs

#### Good Comments
```python
# Calculate relevance score using TF-IDF
# Higher scores indicate better matches
score = calculate_tfidf(document, query)

# TODO: Optimize this query (currently O(n²))
for paper in papers:
    for reference in paper.references:
        # ...
```

#### Bad Comments
```python
# This is a function
def my_function():
    pass

# Increment i by 1
i += 1
```

---

## Questions?

If you have questions about contributing:
- Check existing documentation
- Ask in GitHub Issues
- Contact team members:
  - Shahzeb Ali (Backend)
  - Areesha Rizwan (Database)
  - Haroon Mahmood (Deployment)
  - Maryam Abid (Frontend)

---

Thank you for contributing to ReSearch Flow! 🎉

