import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { searchAPI, APIError } from '../services/api';
import { ArrowLeft, ExternalLink, BookOpen, Calendar, Users, Award } from 'lucide-react';
import AnimatedNetworkBackground from '../components/AnimatedNetworkBackground';

const PaperCard = ({ paper }) => {
  const authors = Array.isArray(paper.authors) 
    ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ', et al.' : '')
    : 'Unknown Authors';

  return (
    <div className="group p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 hover:border-purple-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10">
      {/* Paper Title */}
      <h3 className="text-xl tracking-wide text-white mb-3 group-hover:text-purple-400 transition-colors line-clamp-2">
        {paper.title || 'Untitled Paper'}
      </h3>

      {/* Authors */}
      <div className="flex items-center text-gray-400 text-sm mb-2">
        <Users className="w-4 h-4 mr-2" />
        <span className="line-clamp-1">{authors}</span>
      </div>

      {/* Year & Citations */}
      <div className="flex items-center space-x-4 text-gray-400 text-sm mb-4">
        {paper.year && (
          <div className="flex items-center">
            <Calendar className="w-4 h-4 mr-1" />
            <span>{paper.year}</span>
          </div>
        )}
        {paper.citationCount !== undefined && (
          <div className="flex items-center">
            <Award className="w-4 h-4 mr-1" />
            <span>{paper.citationCount} citations</span>
          </div>
        )}
      </div>

      {/* Abstract */}
      {paper.abstract && paper.abstract !== 'N/A' && (
        <p className="text-gray-300 text-sm mb-4 line-clamp-3">
          {paper.abstract}
        </p>
      )}

      {/* Venue/Source */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-purple-400 flex items-center">
          <BookOpen className="w-4 h-4 mr-1" />
          {paper.source || 'Unknown Source'}
        </span>
        
        {/* View Paper Link */}
        {paper.url && paper.url !== 'N/A' && (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-blue-400 hover:text-blue-300 transition-colors"
          >
            View Paper
            <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        )}
      </div>
    </div>
  );
};

export default function Results() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const topic = searchParams.get('topic');

  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!topic) {
      navigate('/');
      return;
    }

    fetchPapers();
  }, [topic]); // Added missing dependency warning fix

  const fetchPapers = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await searchAPI.fetchPapers(topic, 20, false);
      
      if (response.status === 'success') {
        setPapers(response.papers);
        setStats({
          total: response.count,
          sources: response.sources
        });
      } else if (response.status === 'no_results') {
        setError(response.message);
        setPapers([]);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Error fetching papers:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative viga-font overflow-hidden">
      <AnimatedNetworkBackground />

      <div className="relative z-10 min-h-screen">
        {/* Header */}
        <div className="p-6 border-b border-white/10 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-white hover:text-purple-400 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Search
            </button>
            <h1 className="text-2xl font-bold text-white">ReSearch Flow</h1>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto p-6">
          {/* Topic Header */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              Topic: <span className="text-purple-400">"{topic}"</span>
            </h2>
            {stats && (
              <p className="text-gray-400">
                Showing {stats.total} results from {stats.sources.semantic_scholar} Semantic Scholar 
                and {stats.sources.google_scholar} Google Scholar papers
              </p>
            )}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mb-4"></div>
              <p className="text-white text-lg">Searching research papers...</p>
              <p className="text-gray-400 text-sm mt-2">This may take a few moments</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-2xl p-6 text-center">
              <p className="text-red-400 text-lg mb-4">{error}</p>
              <button
                onClick={fetchPapers}
                className="px-6 py-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Results Grid */}
          {!loading && !error && papers.length > 0 && (
            <div className="grid grid-cols-1 gap-6">
              {papers.map((paper, index) => (
                <PaperCard key={paper.paperId || index} paper={paper} />
              ))}
            </div>
          )}

          {/* No Results */}
          {!loading && !error && papers.length === 0 && (
            <div className="text-center py-20">
              <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">No papers found for this topic</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}