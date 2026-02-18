const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

export const searchAPI = {
  /**
   * Fetch research papers for a given topic
   * @param {string} topic - Research topic to search
   * @param {number} limit - Number of papers to fetch (default: 20)
   * @param {boolean} extractContent - Whether to extract PDF content (default: false)
   * @returns {Promise<Object>} Response with papers array
   */
  async fetchPapers(topic, limit = 20, extractContent = false) {
    try {
      const url = new URL(`${API_BASE_URL}/search/fetch`);
      url.searchParams.append('topic', topic);
      url.searchParams.append('limit', limit);
      url.searchParams.append('extract_content', extractContent);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to fetch papers',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      // Network or other errors
      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Get stored papers from database
   * @param {string} topic - Filter by topic (optional)
   * @param {number} limit - Number of papers to retrieve
   * @param {number} offset - Pagination offset
   */
  async getStoredPapers(topic = null, limit = 50, offset = 0) {
    try {
      const url = new URL(`${API_BASE_URL}/papers`);
      if (topic) url.searchParams.append('topic', topic);
      url.searchParams.append('limit', limit);
      url.searchParams.append('offset', offset);

      const response = await fetch(url.toString());
      const data = await response.json();

      if (!response.ok) {
        throw new APIError('Failed to retrieve papers', response.status, data);
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Network error', 0, { originalError: error.message });
    }
  },

  /**
   * Get all unique topics
   */
  async getTopics() {
    try {
      const response = await fetch(`${API_BASE_URL}/papers/topics/all`);
      const data = await response.json();

      if (!response.ok) {
        throw new APIError('Failed to retrieve topics', response.status, data);
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Network error', 0, { originalError: error.message });
    }
  },

  /**
   * Get citation network for papers
   * @param {Array} papers - Array of paper objects
   * @param {number} maxDepth - Maximum depth of citation exploration (default: 1)
   * @param {number} maxNodes - Maximum number of nodes (default: 50)
   * @returns {Promise<Object>} Citation network with nodes and edges
   */
  async getCitationNetwork(papers, maxDepth = 1, maxNodes = 50) {
    try {
      const response = await fetch(`${API_BASE_URL}/citation/network`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          papers: papers,
          max_depth: maxDepth,
          max_nodes: maxNodes,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to build citation network',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Network error', 0, { originalError: error.message });
    }
  }
};

// Saved Articles API functions
export const savedArticlesAPI = {
  /**
   * Save an article to user's favorites
   * @param {string} paperId - OpenAlex paper ID
   * @param {Object} paperData - Paper data to save
   * @returns {Promise<Object>} Saved article data
   */
  async saveArticle(paperId, paperData) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new APIError('User not authenticated', 401, { requiresAuth: true });
      }

      const { data, error } = await supabase
        .from('saved_articles')
        .upsert({
          user_id: user.id,
          paper_id: paperId,
          title: paperData.title || 'Untitled Paper',
        }, {
          onConflict: 'user_id,paper_id'
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Failed to save article', 0, { originalError: error.message });
    }
  },

  /**
   * Remove an article from user's favorites
   * @param {string} paperId - OpenAlex paper ID
   * @returns {Promise<void>}
   */
  async unsaveArticle(paperId) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new APIError('User not authenticated', 401, { requiresAuth: true });
      }

      const { error } = await supabase
        .from('saved_articles')
        .delete()
        .eq('user_id', user.id)
        .eq('paper_id', paperId);

      if (error) throw error;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Failed to unsave article', 0, { originalError: error.message });
    }
  },

  /**
   * Get saved article with notes
   * @param {string} paperId - OpenAlex paper ID
   * @returns {Promise<Object|null>} Saved article data or null if not saved
   */
  async getSavedArticle(paperId) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        return null;
      }

      const { data, error } = await supabase
        .from('saved_articles')
        .select('*')
        .eq('user_id', user.id)
        .eq('paper_id', paperId)
        .single();

      if (error) {
        if (error.code === 'PGRST116') {
          // No rows returned
          return null;
        }
        throw error;
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      // Return null on error to gracefully handle unauthenticated users
      return null;
    }
  },

  /**
   * Update notes for a saved article
   * @param {string} paperId - OpenAlex paper ID
   * @param {string} notes - Notes text
   * @returns {Promise<Object>} Updated article data
   */
  async updateArticleNotes(paperId, notes) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        throw new APIError('User not authenticated', 401, { requiresAuth: true });
      }

      const { data, error } = await supabase
        .from('saved_articles')
        .update({ notes: notes || null })
        .eq('user_id', user.id)
        .eq('paper_id', paperId)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError('Failed to update notes', 0, { originalError: error.message });
    }
  },

  /**
   * Get all saved articles for current user
   * @returns {Promise<Array>} Array of saved articles
   */
  async getUserSavedArticles() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        return [];
      }

      const { data, error } = await supabase
        .from('saved_articles')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false });

      if (error) throw error;
      return data || [];
    } catch (error) {
      if (error instanceof APIError) throw error;
      return [];
    }
  }
};

// arXiv API functions
export const arxivAPI = {
  /**
   * Search arXiv for papers
   * @param {string} query - Search query/topic
   * @param {number} limit - Number of results (default: 20)
   * @returns {Promise<Object>} Response with papers array
   */
  async searchPapers(query, limit = 20) {
    try {
      const url = new URL(`${API_BASE_URL}/arxiv/search`);
      url.searchParams.append('query', query);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to search arXiv',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract full PDF content from arXiv
   * @param {string} arxivId - arXiv ID (e.g., "1234.5678") OR pdfUrl
   * @param {string} pdfUrl - Optional PDF URL (alternative to arxivId)
   * @returns {Promise<Object>} Full extracted text from PDF
   */
  async extractPdfContent(arxivId = null, pdfUrl = null) {
    try {
      const requestBody = {};
      if (arxivId) {
        requestBody.arxiv_id = arxivId;
      } else if (pdfUrl) {
        requestBody.pdf_url = pdfUrl;
      } else {
        throw new APIError('Either arxivId or pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/arxiv/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract PDF content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Summarize a paper from arXiv
   * @param {string} arxivId - arXiv ID (e.g., "1234.5678") OR pdfUrl
   * @param {string} pdfUrl - Optional PDF URL (alternative to arxivId)
   * @returns {Promise<Object>} Summary with structured sections
   */
  async summarizePaper(arxivId = null, pdfUrl = null) {
    try {
      const requestBody = {};
      if (arxivId) {
        requestBody.arxiv_id = arxivId;
      } else if (pdfUrl) {
        requestBody.pdf_url = pdfUrl;
      } else {
        throw new APIError('Either arxivId or pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/arxiv/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to summarize paper',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Ask a question about a paper
   * @param {string} arxivId - arXiv ID (e.g., "1234.5678") OR pdfUrl
   * @param {string} pdfUrl - Optional PDF URL (alternative to arxivId)
   * @param {string} question - Question to ask about the paper
   * @param {Array} conversationHistory - Optional conversation history
   * @returns {Promise<Object>} Answer to the question
   */
  async askQuestion(arxivId = null, pdfUrl = null, question = "", conversationHistory = []) {
    try {
      const requestBody = {};
      if (arxivId) {
        requestBody.arxiv_id = arxivId;
      } else if (pdfUrl) {
        requestBody.pdf_url = pdfUrl;
      } else {
        throw new APIError('Either arxivId or pdfUrl must be provided', 400);
      }

      requestBody.question = question;
      if (conversationHistory && conversationHistory.length > 0) {
        requestBody.conversation_history = conversationHistory;
      }

      const response = await fetch(`${API_BASE_URL}/arxiv/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to get answer',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  }
};

// CORE API functions
export const coreAPI = {
  /**
   * Search CORE for papers
   * @param {string} query - Search query/topic
   * @param {number} limit - Number of results (default: 20)
   * @returns {Promise<Object>} Response with papers array
   */
  async searchPapers(query, limit = 20) {
    try {
      const url = new URL(`${API_BASE_URL}/core/search`);
      url.searchParams.append('query', query);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to search CORE',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract full PDF content from CORE paper
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Full extracted text from PDF
   */
  async extractPdfContent(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/core/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract PDF content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Summarize a paper from CORE
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Summary with structured sections
   */
  async summarizePaper(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/core/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to summarize paper',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Ask a question about a CORE paper
   * @param {string} pdfUrl - PDF URL
   * @param {string} question - Question to ask about the paper
   * @param {Array} conversationHistory - Optional conversation history
   * @returns {Promise<Object>} Answer to the question
   */
  async askQuestion(pdfUrl, question = "", conversationHistory = []) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const requestBody = {
        pdf_url: pdfUrl,
        question: question
      };

      if (conversationHistory && conversationHistory.length > 0) {
        requestBody.conversation_history = conversationHistory;
      }

      const response = await fetch(`${API_BASE_URL}/core/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to get answer',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  }
};

// PubMed Central (PMC) API functions
export const pmcAPI = {
  /**
   * Search PMC for papers
   * @param {string} query - Search query/topic
   * @param {number} limit - Number of results (default: 20)
   * @returns {Promise<Object>} Response with papers array
   */
  async searchPapers(query, limit = 20) {
    try {
      const url = new URL(`${API_BASE_URL}/pmc/search`);
      url.searchParams.append('query', query);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to search PMC',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract full PDF content from PMC paper
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Full extracted text from PDF
   */
  async extractPdfContent(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/pmc/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract PDF content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Summarize a paper from PMC
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Summary with structured sections
   */
  async summarizePaper(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/pmc/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to summarize paper',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Ask a question about a PMC paper
   * @param {string} pdfUrl - PDF URL
   * @param {string} question - Question to ask about the paper
   * @param {Array} conversationHistory - Optional conversation history
   * @returns {Promise<Object>} Answer to the question
   */
  async askQuestion(pdfUrl, question = "", conversationHistory = []) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const requestBody = {
        pdf_url: pdfUrl,
        question: question
      };

      if (conversationHistory && conversationHistory.length > 0) {
        requestBody.conversation_history = conversationHistory;
      }

      const response = await fetch(`${API_BASE_URL}/pmc/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to get answer',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  }
};

// Semantic Scholar API functions
export const semanticScholarAPI = {
  /**
   * Search Semantic Scholar for papers
   * @param {string} query - Search query/topic
   * @param {number} limit - Number of results (default: 20)
   * @returns {Promise<Object>} Response with papers array
   */
  async searchPapers(query, limit = 20) {
    try {
      const url = new URL(`${API_BASE_URL}/semantic-scholar/search`);
      url.searchParams.append('query', query);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to search Semantic Scholar',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract full PDF content from any paper (works with any source)
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Full extracted text from PDF
   */
  async extractPdfContent(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/semantic-scholar/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract PDF content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Summarize a paper from any source (works with any PDF URL)
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Summary with structured sections
   */
  async summarizePaper(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/semantic-scholar/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to summarize paper',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract structured content from a PDF with heading/subheading/body classification
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Structured blocks with type classification
   */
  async extractStructuredContent(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/semantic-scholar/extract-structured`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract structured content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Ask a question about a paper from any source
   * @param {string} pdfUrl - PDF URL
   * @param {string} question - Question to ask about the paper
   * @param {Array} conversationHistory - Optional conversation history
   * @returns {Promise<Object>} Answer to the question
   */
  async askQuestion(pdfUrl, question = "", conversationHistory = []) {

    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const requestBody = {
        pdf_url: pdfUrl,
        question: question
      };

      if (conversationHistory && conversationHistory.length > 0) {
        requestBody.conversation_history = conversationHistory;
      }

      const response = await fetch(`${API_BASE_URL}/semantic-scholar/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to get answer',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  }
};

// Google Scholar API functions (using SerpAPI)
export const googleScholarAPI = {
  /**
   * Search Google Scholar for papers
   * @param {string} query - Search query/topic
   * @param {number} limit - Number of results (default: 20)
   * @returns {Promise<Object>} Response with papers array
   */
  async searchPapers(query, limit = 20) {
    try {
      const url = new URL(`${API_BASE_URL}/google-scholar/search`);
      url.searchParams.append('query', query);
      url.searchParams.append('limit', limit);

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to search Google Scholar',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Extract full PDF content from any paper (works with any source)
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Full extracted text from PDF
   */
  async extractPdfContent(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/google-scholar/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to extract PDF content',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Summarize a paper from any source (works with any PDF URL)
   * @param {string} pdfUrl - PDF URL
   * @returns {Promise<Object>} Summary with structured sections
   */
  async summarizePaper(pdfUrl) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const response = await fetch(`${API_BASE_URL}/google-scholar/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pdf_url: pdfUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to summarize paper',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  },

  /**
   * Ask a question about a paper from any source
   * @param {string} pdfUrl - PDF URL
   * @param {string} question - Question to ask about the paper
   * @param {Array} conversationHistory - Optional conversation history
   * @returns {Promise<Object>} Answer to the question
   */
  async askQuestion(pdfUrl, question = "", conversationHistory = []) {
    try {
      if (!pdfUrl) {
        throw new APIError('pdfUrl must be provided', 400);
      }

      const requestBody = {
        pdf_url: pdfUrl,
        question: question
      };

      if (conversationHistory && conversationHistory.length > 0) {
        requestBody.conversation_history = conversationHistory;
      }

      const response = await fetch(`${API_BASE_URL}/google-scholar/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(
          data.detail?.message || 'Failed to get answer',
          response.status,
          data.detail
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(
        'Network error: Could not connect to server',
        0,
        { originalError: error.message }
      );
    }
  }
};

export { APIError };