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

export { APIError };