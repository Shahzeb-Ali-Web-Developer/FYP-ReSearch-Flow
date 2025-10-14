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
      const url = new URL(`${API_BASE_URL}/api/v1/search/fetch`);
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
  }
};

export { APIError };