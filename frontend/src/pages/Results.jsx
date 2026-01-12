import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { searchAPI, savedArticlesAPI, arxivAPI, coreAPI, pmcAPI, semanticScholarAPI, googleScholarAPI, APIError } from '../services/api';
import { 
  BookOpen, X, FileText, MessageSquare, Code, Download, 
  ChevronDown, Plus, Trash2, MoreVertical, ArrowUpDown, BarChart3, CheckSquare, Network,
  Check, Bookmark, Share2, Copy, CheckCircle, Building2, Send, Bot, User
} from 'lucide-react';
import SearchDropdown from '../components/SearchDropdown';
import CitationMesh from '../components/CitationMesh';
import ArticleNotesModal from '../components/ArticleNotesModal';
import { ToastContainer, useToast } from '../components/Toast';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Compact paper card for the list (left column) - arXiv style
const PaperListItem = ({ paper, isSelected, onClick }) => {
  // Support both arXiv and OpenAlex paper formats
  const authors = Array.isArray(paper.authors) && paper.authors.length > 0
    ? paper.authors.slice(0, 2).map(a => typeof a === 'string' ? a : a.name || a).join(', ') + (paper.authors.length > 2 ? ', et al.' : '')
    : 'Unknown Authors';

  const isArxiv = paper.source === 'arXiv' || paper.arxiv_id;
  const isCore = paper.source === 'CORE' || paper.core_id;
  const isPmc = paper.source === 'PMC' || paper.pmc_id;
  const isSemanticScholar = paper.source === 'Semantic Scholar' || paper.semantic_scholar_id || (paper.paperId && !paper.arxiv_id && !paper.core_id && !paper.pmc_id && !paper.google_scholar_id);
  const isGoogleScholar = paper.source === 'Google Scholar' || paper.google_scholar_id;
  const arxivId = paper.arxiv_id;
  const coreId = paper.core_id;
  const pmcId = paper.pmc_id;
  const semanticScholarId = paper.semantic_scholar_id || paper.paperId;
  const googleScholarId = paper.google_scholar_id;
  const publishedDate = paper.published_date ? new Date(paper.published_date).getFullYear() : null;
  const year = paper.year || publishedDate;
  const venue = paper.venue && paper.venue !== 'N/A' ? paper.venue : null;
  const citationCount = paper.citationCount || 0;
  const pdfUrl = paper.pdf_url || paper.openAccessPdf || (paper.url && paper.url.toLowerCase().endsWith('.pdf') ? paper.url : null);
  const abstract = paper.abstract || '';
  const abstractPreview = abstract.length > 200 ? abstract.substring(0, 200) + '...' : abstract;

  return (
    <div className={`border-b border-gray-200 ${isSelected ? 'bg-gray-100' : 'bg-white'}`}>
      <div
        onClick={onClick}
        className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors`}
      >
        <h3 className="text-base font-semibold text-black mb-1.5 line-clamp-2 hover:text-gray-700 transition-colors">
          {paper.title || 'Untitled Paper'}
        </h3>

        <div className="text-sm text-gray-600 mb-2">
          {arxivId && <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">arXiv:{arxivId}</span>}
          {coreId && <span className="font-mono text-xs bg-blue-100 px-1.5 py-0.5 rounded text-blue-800">CORE</span>}
          {pmcId && <span className="font-mono text-xs bg-green-100 px-1.5 py-0.5 rounded text-green-800">PMC:{pmcId}</span>}
          {isSemanticScholar && !arxivId && !coreId && !pmcId && !isGoogleScholar && <span className="font-mono text-xs bg-purple-100 px-1.5 py-0.5 rounded text-purple-800">Semantic Scholar</span>}
          {isGoogleScholar && <span className="font-mono text-xs bg-orange-100 px-1.5 py-0.5 rounded text-orange-800">Google Scholar</span>}
          {year && <span className="ml-2">{year}</span>}
          {authors && <span className="ml-2">{authors}</span>}
          {venue && <span className="ml-2"> · {venue}</span>}
        </div>

        {abstract && (
          <div className="text-sm text-gray-600 mb-2 line-clamp-2">
            {abstractPreview}
          </div>
        )}

        <div className="flex items-center justify-between text-sm text-gray-500">
          {!isArxiv && <span>Cited by {citationCount.toLocaleString()}</span>}
          {pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-black hover:text-gray-700 font-medium"
            >
              PDF
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

// Stats Panel Component (Right Column)
const StatsPanel = ({
  papers,
  stats,
  onClose,
  selectedYears,
  setSelectedYears,
  selectedTopics,
  setSelectedTopics,
  selectedTypes,
  setSelectedTypes,
  selectedInstitutions,
  setSelectedInstitutions,
  openAccessOnly,
  onToggleOpenAccess,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    year: true,
    topic: false,
    institution: true,  // Expanded by default
    type: true
  });

  // Memoize stats calculations - only recalculate when papers change
  const { openAccessCount, openAccessPercent, sortedYears, maxYearCount, yearDistribution, sortedTopics, sortedInstitutions, sortedTypes } = useMemo(() => {
    // Calculate stats from papers
    const openAccessCount = papers.filter(p => p.isOpenAccess).length;
    const openAccessPercent = papers.length > 0 ? Math.round((openAccessCount / papers.length) * 100) : 0;
    
    // Group by year
    const yearDistribution = {};
    papers.forEach(p => {
      if (p.year) {
        yearDistribution[p.year] = (yearDistribution[p.year] || 0) + 1;
      }
    });
    const sortedYears = Object.keys(yearDistribution).sort((a, b) => b - a).slice(0, 10);
    const maxYearCount = Math.max(...Object.values(yearDistribution), 1);

    // Group by fields of study
    const topicCounts = {};
    papers.forEach(p => {
      if (Array.isArray(p.fieldsOfStudy)) {
        p.fieldsOfStudy.forEach(field => {
          topicCounts[field] = (topicCounts[field] || 0) + 1;
        });
      }
    });
    const sortedTopics = Object.entries(topicCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Group by institutions - optimized for instant loading
    const institutionCounts = {};
    papers.forEach(p => {
      if (Array.isArray(p.institutions)) {
        p.institutions.forEach(inst => {
          if (inst && inst.trim()) {
            institutionCounts[inst] = (institutionCounts[inst] || 0) + 1;
          }
        });
      }
    });
    const sortedInstitutions = Object.entries(institutionCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    // Group by type
    const typeCounts = {};
    papers.forEach(p => {
      const type = p.publicationTypes && p.publicationTypes.length > 0 
        ? p.publicationTypes[0] 
        : 'article';
      typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    const sortedTypes = Object.entries(typeCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    return {
      openAccessCount,
      openAccessPercent,
      sortedYears,
      maxYearCount,
      yearDistribution,
      sortedTopics,
      sortedInstitutions,
      sortedTypes
    };
  }, [papers]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="w-full md:w-80 bg-white border-l border-gray-200 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between z-10">
        <h2 className="text-lg font-semibold text-black">Stats</h2>
        <div className="flex items-center gap-2">
          <button className="p-1.5 hover:bg-gray-100 rounded">
            <Plus className="w-4 h-4 text-gray-600" />
          </button>
          <button className="p-1.5 hover:bg-gray-100 rounded">
            <Download className="w-4 h-4 text-gray-600" />
          </button>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded">
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-6 md:space-y-4">
        {/* Top row: Total results and Open Access */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Total Results */}
          <div className="border border-gray-200 rounded-lg p-4 md:col-span-1">
            <p className="text-2xl font-semibold text-black">
              {papers.length.toLocaleString()} results
            </p>
          </div>

          {/* Open Access */}
          <button
            type="button"
            onClick={onToggleOpenAccess}
            className={`border border-gray-200 rounded-lg p-4 flex flex-col items-center justify-center cursor-pointer transition-colors ${
              openAccessOnly ? 'bg-black text-white' : 'bg-white hover:bg-gray-50'
            }`}
          >
            <div
              className={`w-20 h-20 rounded-full border-[10px] flex items-center justify-center mb-2 ${
                openAccessOnly ? 'border-white' : 'border-gray-300'
              }`}
            >
              <span className={`text-xl font-bold ${openAccessOnly ? 'text-white' : 'text-black'}`}>
                {openAccessPercent}%
              </span>
            </div>
            <p className={`text-sm font-medium ${openAccessOnly ? 'text-white' : 'text-black'}`}>
              Open Access
            </p>
            <p className={`text-sm ${openAccessOnly ? 'text-gray-200' : 'text-gray-600'}`}>
              {openAccessCount.toLocaleString()}
            </p>
          </button>
        </div>

        {/* Year Distribution */}
        <div className="border-b border-gray-200 pb-4 pt-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-black">Year</span>
            </div>
            <button onClick={() => toggleSection('year')}>
              <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${expandedSections.year ? '' : '-rotate-90'}`} />
            </button>
          </div>
          {expandedSections.year && (
            <div className="space-y-2">
              {sortedYears.map(year => {
                const count = yearDistribution[year];
                const width = (count / maxYearCount) * 100;
                const isSelected = selectedYears.includes(parseInt(year));
                return (
                  <label key={year} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded -ml-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => {
                        const yearNum = parseInt(year);
                        if (e.target.checked) {
                          setSelectedYears([...selectedYears, yearNum]);
                        } else {
                          setSelectedYears(selectedYears.filter(y => y !== yearNum));
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                    <div className="flex-1 bg-gray-200 rounded h-4 overflow-hidden">
                      <div 
                        className={`h-full rounded ${isSelected ? 'bg-black' : 'bg-gray-400'}`}
                        style={{ width: `${width}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-12 text-right">{year}</span>
                  </label>
                );
              })}
              <button className="text-xs text-gray-500 hover:text-black mt-2">More...</button>
            </div>
          )}
        </div>

        {/* Institution */}
        <div className="border-b border-gray-200 pb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-black">Institution</span>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-1 hover:bg-gray-100 rounded">
                <MoreVertical className="w-4 h-4 text-gray-600" />
              </button>
              <button onClick={() => toggleSection('institution')}>
                <X className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>
          {expandedSections.institution && (
            <div className="space-y-1">
              {sortedInstitutions.length > 0 ? (
                <>
                  {sortedInstitutions.map(([institution, count]) => (
                    <label key={institution} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                      <input
                        type="checkbox"
                        checked={selectedInstitutions.includes(institution)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedInstitutions([...selectedInstitutions, institution]);
                          } else {
                            setSelectedInstitutions(selectedInstitutions.filter(i => i !== institution));
                          }
                        }}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700 flex-1">{institution}</span>
                      <span className="text-sm text-gray-500">{count.toLocaleString()}</span>
                    </label>
                  ))}
                  {sortedInstitutions.length >= 10 && (
                    <button className="text-xs text-gray-500 hover:text-black mt-2">More...</button>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-500 py-2">No institution data available</p>
              )}
            </div>
          )}
        </div>

        {/* Type */}
        <div className="border-b border-gray-200 pb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-black">Type</span>
            </div>
            <div className="flex items-center gap-2">
              <button className="p-1 hover:bg-gray-100 rounded">
                <MoreVertical className="w-4 h-4 text-gray-600" />
              </button>
              <button onClick={() => toggleSection('type')}>
                <X className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>
          {expandedSections.type && (
            <div className="space-y-1">
              {sortedTypes.map(([type, count]) => (
                <label key={type} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTypes([...selectedTypes, type]);
                      } else {
                        setSelectedTypes(selectedTypes.filter(t => t !== type));
                      }
                    }}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700 flex-1 capitalize">{type}</span>
                  <span className="text-sm text-gray-500">{count.toLocaleString()}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Detailed slide-in panel (right column)
const DetailPanel = ({ paper, onClose }) => {
  if (!paper) return null;

  const { user, isAuthenticated } = useAuth();
  const { toasts, showToast, removeToast } = useToast();
  const navigate = useNavigate();

  const authors = Array.isArray(paper.authors) ? paper.authors : [];
  const venue = paper.venue && paper.venue !== 'N/A' ? paper.venue : null;
  const year = paper.year || null;
  const citationCount = paper.citationCount || 0;
  const referenceCount = paper.referenceCount || 0;
  const doi = paper.externalIds && (paper.externalIds.DOI || paper.externalIds.doi);
  const pdfUrl = paper.pdf_url || paper.openAccessPdf || (paper.url && paper.url.toLowerCase().endsWith('.pdf') ? paper.url : null);
  const htmlUrl = paper.url && !pdfUrl ? paper.url : null;
  const fields = Array.isArray(paper.fieldsOfStudy) ? paper.fieldsOfStudy : [];
  const isOpenAccess = Boolean(paper.isOpenAccess);
  const [abstractExpanded, setAbstractExpanded] = useState(false);

  // State for saved articles functionality
  const [isSaved, setIsSaved] = useState(false);
  const [savedArticleId, setSavedArticleId] = useState(null);
  const [notes, setNotes] = useState('');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [showLinkDropdown, setShowLinkDropdown] = useState(false);
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [pdfContent, setPdfContent] = useState(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const abstract = paper.abstract && paper.abstract !== 'N/A' ? paper.abstract : null;
  const abstractPreview = abstract && abstract.length > 300 ? abstract.substring(0, 300) + '...' : abstract;

  const paperId = paper.paperId || paper.id || paper.core_id || paper.pmc_id || paper.semantic_scholar_id || paper.google_scholar_id;
  const isArxiv = paper.source === 'arXiv' || paper.arxiv_id;
  const isCore = paper.source === 'CORE' || paper.core_id;
  const isPmc = paper.source === 'PMC' || paper.pmc_id;
  const isSemanticScholar = paper.source === 'Semantic Scholar' || paper.semantic_scholar_id || (paper.paperId && !paper.arxiv_id && !paper.core_id && !paper.pmc_id && !paper.google_scholar_id);
  const isGoogleScholar = paper.source === 'Google Scholar' || paper.google_scholar_id;
  const arxivId = paper.arxiv_id;
  const coreId = paper.core_id;
  const pmcId = paper.pmc_id;
  const semanticScholarId = paper.semantic_scholar_id || paper.paperId;
  const googleScholarId = paper.google_scholar_id;
  const pdfUrlForExtract = paper.pdf_url || paper.openAccessPdf || pdfUrl;

  // Reset PDF content, summary, and chat when paper changes
  useEffect(() => {
    setPdfContent(null);
    setSummary(null);
    setSummarizing(false);
    setShowChat(false);
    setChatMessages([]);
    setChatInput('');
  }, [paper]);

  // Check if article is saved when component mounts or paper changes
  useEffect(() => {
    const checkSavedStatus = async () => {
      if (!isAuthenticated || !paperId) {
        setLoadingSaved(false);
        return;
      }

      try {
        const savedArticle = await savedArticlesAPI.getSavedArticle(paperId);
        if (savedArticle) {
          setIsSaved(true);
          setSavedArticleId(savedArticle.id);
          setNotes(savedArticle.notes || '');
        } else {
          setIsSaved(false);
          setSavedArticleId(null);
          setNotes('');
        }
      } catch (error) {
        console.error('Error checking saved status:', error);
      } finally {
        setLoadingSaved(false);
      }
    };

    checkSavedStatus();
  }, [paperId, isAuthenticated]);

  // Close link dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showLinkDropdown && !event.target.closest('.link-dropdown-container')) {
        setShowLinkDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showLinkDropdown]);

  // API Button Handler - Copy JSON to clipboard
  const handleCopyJSON = async () => {
    try {
      const jsonData = JSON.stringify(paper, null, 2);
      await navigator.clipboard.writeText(jsonData);
      showToast('Paper data copied to clipboard as JSON', 'success');
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      showToast('Failed to copy to clipboard', 'error');
    }
  };

  // Link Button Handlers
  const handleCopyURL = async () => {
    const urlToCopy = htmlUrl || paper.url || window.location.href;
    try {
      await navigator.clipboard.writeText(urlToCopy);
      setCopiedToClipboard(true);
      showToast('URL copied to clipboard', 'success');
      setTimeout(() => setCopiedToClipboard(false), 2000);
      setShowLinkDropdown(false);
    } catch (error) {
      console.error('Error copying URL:', error);
      showToast('Failed to copy URL', 'error');
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: paper.title || 'Research Paper',
      text: paper.abstract ? paper.abstract.substring(0, 200) : '',
      url: htmlUrl || paper.url || window.location.href,
    };

    try {
      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        showToast('Article shared successfully', 'success');
      } else {
        // Fallback to copy URL
        await handleCopyURL();
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error sharing:', error);
        // Fallback to copy URL
        await handleCopyURL();
      }
    }
    setShowLinkDropdown(false);
  };

  // Message/Save Button Handlers
  const handleSaveArticle = async () => {
    if (!isAuthenticated) {
      showToast('Please log in to save articles', 'info');
      navigate('/auth?mode=login');
      return;
    }

    try {
      if (isSaved) {
        await savedArticlesAPI.unsaveArticle(paperId);
        setIsSaved(false);
        setSavedArticleId(null);
        setNotes('');
        showToast('Article removed from saved', 'success');
      } else {
        const savedArticle = await savedArticlesAPI.saveArticle(paperId, paper);
        setIsSaved(true);
        setSavedArticleId(savedArticle.id);
        showToast('Article saved to favorites', 'success');
      }
    } catch (error) {
      console.error('Error saving article:', error);
      if (error instanceof APIError && error.status === 401) {
        showToast('Please log in to save articles', 'info');
        navigate('/auth?mode=login');
      } else {
        showToast('Failed to save article', 'error');
      }
    }
  };

  const handleOpenNotes = () => {
    if (!isAuthenticated) {
      showToast('Please log in to add notes', 'info');
      navigate('/auth?mode=login');
      return;
    }

    // If not saved, save it first
    if (!isSaved) {
      handleSaveArticle().then(() => {
        setShowNotesModal(true);
      });
    } else {
      setShowNotesModal(true);
    }
  };

  const handleSaveNotes = async (newNotes) => {
    try {
      await savedArticlesAPI.updateArticleNotes(paperId, newNotes);
      setNotes(newNotes);
      showToast('Notes saved successfully', 'success');
    } catch (error) {
      console.error('Error saving notes:', error);
      showToast('Failed to save notes', 'error');
      throw error;
    }
  };

  // Handle summarization - extracts PDF and generates summary in one step
  const handleSummarize = async () => {
    // Check if PDF is available for extraction
    if (!pdfUrlForExtract) {
      // For Semantic Scholar or Google Scholar papers, if no PDF but have abstract, provide helpful message
      if ((isSemanticScholar || isGoogleScholar) && abstract) {
        showToast('PDF not available for this paper. Summarization requires PDF access.', 'info');
      } else {
        showToast('No PDF URL available for this paper', 'error');
      }
      return;
    }

    // Check if already summarized
    if (summary) {
      return; // Already summarized
    }

    setSummarizing(true);
    try {
      let response;
      // Use appropriate API based on source - all APIs can handle any PDF URL
      // But we use the source-specific API for consistency
      if (isArxiv) {
        response = await arxivAPI.summarizePaper(arxivId || null, pdfUrlForExtract || null);
      } else if (isCore) {
        response = await coreAPI.summarizePaper(pdfUrlForExtract);
      } else if (isPmc) {
        response = await pmcAPI.summarizePaper(pdfUrlForExtract);
      } else if (isSemanticScholar) {
        // Semantic Scholar API works with any PDF URL from any source
        response = await semanticScholarAPI.summarizePaper(pdfUrlForExtract);
      } else if (isGoogleScholar) {
        // Google Scholar API works with any PDF URL from any source
        response = await googleScholarAPI.summarizePaper(pdfUrlForExtract);
      } else {
        // Fallback to Semantic Scholar API (works with any PDF URL)
        response = await semanticScholarAPI.summarizePaper(pdfUrlForExtract);
      }
      
      if (response.status === 'success') {
        // Set summary if available
        if (response.summary) {
          setSummary(response.summary);
        }
        
        // Also set PDF content if returned
        if (response.full_text) {
          setPdfContent(response.full_text);
        }
        
        showToast('PDF extracted and summary generated successfully using AI (GPT-4)', 'success');
      } else {
        showToast('Failed to generate summary', 'error');
      }
    } catch (error) {
      console.error('Error summarizing paper:', error);
      
      // Handle specific PDF not available errors
      if (error.status === 404 || (error.details && error.details.error === 'PDF not available')) {
        const errorMessage = error.details?.message || error.message || 'PDF is not available for this paper.';
        showToast(errorMessage, 'error');
      } else {
        // Generic error handling
        const errorMessage = error.message || error.details?.message || 'Failed to summarize paper. Please try again.';
        showToast(`Failed to summarize: ${errorMessage}`, 'error');
      }
    } finally {
      setSummarizing(false);
    }
  };

  // Handle chat question
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    
    if (!pdfContent) {
      showToast('Please generate summary first to extract paper content', 'info');
      return;
    }

    const userQuestion = chatInput.trim();
    setChatInput('');
    
    // Add user message to chat
    const userMessage = { role: 'user', content: userQuestion };
    setChatMessages(prev => [...prev, userMessage]);
    setChatLoading(true);

    try {
      // Build conversation history (last 10 messages to keep context manageable)
      const history = chatMessages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      let response;
      // Use appropriate API based on source
      if (isArxiv) {
        response = await arxivAPI.askQuestion(arxivId || null, pdfUrlForExtract || null, userQuestion, history);
      } else if (isCore) {
        response = await coreAPI.askQuestion(pdfUrlForExtract, userQuestion, history);
      } else if (isPmc) {
        response = await pmcAPI.askQuestion(pdfUrlForExtract, userQuestion, history);
      } else if (isSemanticScholar) {
        // Semantic Scholar API works with any PDF URL from any source
        response = await semanticScholarAPI.askQuestion(pdfUrlForExtract, userQuestion, history);
      } else if (isGoogleScholar) {
        // Google Scholar API works with any PDF URL from any source
        response = await googleScholarAPI.askQuestion(pdfUrlForExtract, userQuestion, history);
      } else {
        // Fallback to Semantic Scholar API (works with any PDF URL)
        response = await semanticScholarAPI.askQuestion(pdfUrlForExtract, userQuestion, history);
      }
      
      if (response.status === 'success' && response.answer) {
        const assistantMessage = { role: 'assistant', content: response.answer };
        setChatMessages(prev => [...prev, assistantMessage]);
      } else {
        showToast('Failed to get answer', 'error');
        setChatMessages(prev => prev.slice(0, -1)); // Remove user message on error
      }
    } catch (error) {
      console.error('Error asking question:', error);
      showToast(`Failed to get answer: ${error.message}`, 'error');
      setChatMessages(prev => prev.slice(0, -1)); // Remove user message on error
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-white border-l border-gray-200 z-50 overflow-y-auto shadow-2xl">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-start justify-between">
        <div className="flex-1 pr-4">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 uppercase">Work</span>
          </div>
          <h2 className="text-xl font-semibold text-black leading-tight">
            {paper.title || 'Untitled Paper'}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* Action Buttons */}
      <div className="p-4 border-b border-gray-200 flex flex-wrap gap-2">
        {htmlUrl && (
          <a
            href={htmlUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors"
          >
            <FileText className="w-4 h-4" />
            HTML
          </a>
        )}
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors"
          >
            <Download className="w-4 h-4" />
            PDF
          </a>
        )}
        <button
          onClick={handleCopyJSON}
          className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors"
          title="Copy paper data as JSON"
        >
          <Code className="w-4 h-4" />
          JSON
        </button>
        <div className="relative link-dropdown-container">
          <button
            onClick={() => setShowLinkDropdown(!showLinkDropdown)}
            className={`px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors ${showLinkDropdown ? 'bg-gray-800' : ''}`}
            title="Copy URL or Share"
          >
            {copiedToClipboard ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <Share2 className="w-4 h-4" />
            )}
            <span>Share</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showLinkDropdown ? 'rotate-180' : ''}`} />
          </button>
          {showLinkDropdown && (
            <div className="absolute top-full left-0 mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
              <button
                onClick={handleCopyURL}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-gray-700"
              >
                <Copy className="w-4 h-4" />
                Copy URL
              </button>
              <button
                onClick={handleShare}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-gray-700"
              >
                <Share2 className="w-4 h-4" />
                Share
              </button>
            </div>
          )}
        </div>
        <button
          onClick={isSaved ? handleOpenNotes : handleSaveArticle}
          className={`px-4 py-2 rounded text-sm flex items-center gap-2 transition-colors ${
            isSaved
              ? 'bg-gray-100 hover:bg-gray-200 text-black border border-gray-300'
              : 'bg-black hover:bg-gray-800 text-white'
          }`}
          title={isSaved ? 'View/Edit Notes' : 'Save Article'}
          disabled={loadingSaved}
        >
          {isSaved ? (
            <>
              <Bookmark className="w-4 h-4 fill-current" />
              <span>Saved</span>
            </>
          ) : (
            <>
              <Bookmark className="w-4 h-4" />
              <span>Save</span>
            </>
          )}
        </button>
        {isSaved && notes && (
          <button
            onClick={handleOpenNotes}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-black rounded text-sm flex items-center gap-2 transition-colors border border-gray-300"
            title="View Notes"
          >
            <FileText className="w-4 h-4" />
            Notes
          </button>
        )}
        {/* Show summarize button if: PDF available OR (Semantic Scholar/Google Scholar paper with abstract) */}
        {(pdfUrlForExtract || (isSemanticScholar && abstract) || (isGoogleScholar && abstract)) && (
          <>
            <button
              onClick={handleSummarize}
              disabled={summarizing || summary}
              className={`px-4 py-2 rounded text-sm flex items-center gap-2 transition-colors ${
                summary
                  ? 'bg-gray-100 hover:bg-gray-200 text-black border border-gray-300'
                  : 'bg-black hover:bg-gray-800 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={summary ? 'Summary already generated' : pdfUrlForExtract ? 'Extract PDF and generate AI summary (GPT-4)' : ((isSemanticScholar || isGoogleScholar) && abstract ? 'PDF not available - only abstract available' : 'Extract PDF and generate AI summary')}
            >
              {summarizing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  <span>Extracting & Summarizing...</span>
                </>
              ) : summary ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Summarized</span>
                </>
              ) : (
                <>
                  <MessageSquare className="w-4 h-4" />
                  <span>Summarize with AI</span>
                </>
              )}
            </button>
            {pdfContent && summary && (
              <button
                onClick={() => {
                  setShowChat(!showChat);
                }}
                className={`px-4 py-2 rounded text-sm flex items-center gap-2 transition-colors ${
                  showChat
                    ? 'bg-gray-100 hover:bg-gray-200 text-black border border-gray-300'
                    : 'bg-black hover:bg-gray-800 text-white'
                }`}
                title="Ask questions about this paper"
              >
                <Bot className="w-4 h-4" />
                <span>Ask about this paper</span>
              </button>
            )}
          </>
        )}
      </div>

      {/* Metadata */}
      <div className="p-4 space-y-4">
        {year && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Year</span>
            <p className="text-black mt-1">{year}</p>
          </div>
        )}

        <div>
          <span className="text-xs text-gray-500 uppercase">Type</span>
          <p className="text-black mt-1">
            {paper.publicationTypes && paper.publicationTypes.length > 0
              ? paper.publicationTypes.join(', ')
              : 'Article'}
          </p>
        </div>

        {abstract && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Abstract</span>
            <p className="text-gray-700 mt-1 leading-relaxed whitespace-pre-wrap">
              {abstractExpanded ? abstract : abstractPreview}
            </p>
            {abstract.length > 300 && (
              <button
                onClick={() => setAbstractExpanded(!abstractExpanded)}
                className="text-black hover:text-gray-700 text-sm mt-2 underline"
              >
                {abstractExpanded ? 'less' : 'more'}
              </button>
            )}
          </div>
        )}

        {venue && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Source</span>
            <p className="text-black mt-1">{venue}</p>
          </div>
        )}

        {authors.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Authors</span>
            <div className="mt-1 space-y-1">
              {authors.slice(0, 5).map((author, idx) => (
                <p key={idx} className="text-black">
                  {typeof author === 'string' ? author : author.name || author}
                </p>
              ))}
              {authors.length > 5 && (
                <button className="text-black hover:text-gray-700 text-sm underline">
                  +{authors.length - 5} more
                </button>
              )}
            </div>
          </div>
        )}

        <div>
          <span className="text-xs text-gray-500 uppercase">Language</span>
          <p className="text-black mt-1">English</p>
      </div>

        <div className="grid grid-cols-2 gap-4">
          {referenceCount > 0 && (
            <div>
              <span className="text-xs text-gray-500 uppercase">Cites</span>
              <p className="text-black mt-1">{referenceCount.toLocaleString()}</p>
          </div>
        )}
          {citationCount > 0 && (
            <div>
              <span className="text-xs text-gray-500 uppercase">Cited by</span>
              <p className="text-black mt-1">{citationCount.toLocaleString()}</p>
          </div>
        )}
      </div>

        {isOpenAccess && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Open Access</span>
            <p className="text-black mt-1">Yes</p>
          </div>
        )}

        {fields.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 uppercase">Topic</span>
            <div className="mt-1 flex flex-wrap gap-2">
              {fields.map((field, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm border border-gray-300"
                >
                  {field}
        </span>
              ))}
            </div>
          </div>
        )}

        {doi && (
          <div>
            <span className="text-xs text-gray-500 uppercase">DOI</span>
            <a
              href={`https://doi.org/${doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-black hover:text-gray-700 mt-1 block underline"
            >
              {doi}
            </a>
          </div>
        )}

        {paper.url && paper.url !== 'N/A' && (
          <div>
            <span className="text-xs text-gray-500 uppercase">URL</span>
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
              className="text-black hover:text-gray-700 mt-1 block break-all underline"
          >
              {paper.url}
          </a>
          </div>
        )}
      </div>

      {/* Chat Interface */}
      {showChat && pdfContent && (
        <div className="p-4 border-t-2 border-purple-300 bg-purple-50">
          <div className="flex items-center gap-2 mb-3">
            <Bot className="w-5 h-5 text-purple-600" />
            <h3 className="text-base font-semibold text-black">Ask about this paper</h3>
          </div>
          
          {/* Chat Messages */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-[400px] overflow-y-auto mb-3 space-y-4">
            {chatMessages.length === 0 ? (
              <div className="text-center text-gray-500 text-sm py-8">
                <Bot className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>Ask any question about this research paper</p>
                <p className="text-xs mt-1">Example: "What is the main contribution?" or "Explain the methodology"</p>
              </div>
            ) : (
              chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === 'user' ? 'bg-black text-white' : 'bg-purple-100 text-purple-600'
                  }`}>
                    {msg.role === 'user' ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div className={`flex-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <div className={`inline-block p-3 rounded-lg max-w-[85%] ${
                      msg.role === 'user'
                        ? 'bg-black text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
            {chatLoading && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Chat Input */}
          <form onSubmit={handleChatSubmit} className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question about this paper..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={chatLoading}
            />
            <button
              type="submit"
              disabled={!chatInput.trim() || chatLoading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      )}

      {/* AI Summary Display */}
      {summary && (
        <div className="p-4 border-t-2 border-blue-300 bg-blue-50">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-semibold text-black">AI Summary (Generated by ChatGPT)</h3>
          </div>
          <div className="space-y-4">
            {summary.problem_statement && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Problem Statement</h4>
                <p className="text-sm text-gray-600 leading-relaxed">{summary.problem_statement}</p>
              </div>
            )}
            {summary.methodology && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Methodology</h4>
                <p className="text-sm text-gray-600 leading-relaxed">{summary.methodology}</p>
              </div>
            )}
            {summary.key_findings && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Findings</h4>
                <p className="text-sm text-gray-600 leading-relaxed">{summary.key_findings}</p>
              </div>
            )}
            {summary.conclusion && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Conclusion</h4>
                <p className="text-sm text-gray-600 leading-relaxed">{summary.conclusion}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Full PDF Content Display */}
      {pdfContent && (
        <div className="p-4 border-t-2 border-gray-300 bg-gray-50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-black" />
              <h3 className="text-base font-semibold text-black">Extracted PDF Content</h3>
            </div>
            <span className="text-xs text-gray-500 font-medium">
              {pdfContent.length.toLocaleString()} characters | {pdfContent.split(/\s+/).length.toLocaleString()} words
            </span>
          </div>
          <div className="bg-white border-2 border-gray-300 rounded-lg p-4 max-h-[600px] overflow-y-auto shadow-inner">
            <div className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
              {pdfContent}
            </div>
          </div>
        </div>
      )}

      {/* Toast Container */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />

      {/* Notes Modal */}
      <ArticleNotesModal
        isOpen={showNotesModal}
        onClose={() => setShowNotesModal(false)}
        paper={paper}
        notes={notes}
        onSave={handleSaveNotes}
      />
    </div>
  );
};

// Filter criteria structure
const createFilter = (field, operator, value) => ({
  id: Date.now() + Math.random(),
  field,
  operator,
  value
});

export default function Results() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const topic = searchParams.get('topic');

  const [allPapers, setAllPapers] = useState([]); // All fetched papers
  const [papers, setPapers] = useState([]); // Filtered papers
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [showStatsPanel, setShowStatsPanel] = useState(true);
  const [showCitationMesh, setShowCitationMesh] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Sorting state
  const [sortOption, setSortOption] = useState('relevance');
  const [showSortDropdown, setShowSortDropdown] = useState(false);
  
  // Export dropdown state
  const [showExportDropdown, setShowExportDropdown] = useState(false);

  // Sorting options configuration
  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'citations', label: 'Citation Count' },
    { value: 'title', label: 'Title' },
    { value: 'year', label: 'Year' },
  ];

  // Query builder state
  const [filters, setFilters] = useState(() => {
    const initialFilters = [];
    if (topic) {
      initialFilters.push(createFilter('title_abstract', 'includes', topic));
    }
    return initialFilters;
  });
  const [searchQuery, setSearchQuery] = useState(topic || '');
  
  // Stats panel filter state
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedInstitutions, setSelectedInstitutions] = useState([]);
  const [openAccessOnly, setOpenAccessOnly] = useState(false);
  const [fromCache, setFromCache] = useState(false);

  // Check if papers exist in Supabase for this topic (with 3-day freshness check)
  const CACHE_MAX_AGE_DAYS = 3;
  
  const checkCache = async (query) => {
    const normalizedQuery = query?.toLowerCase().trim() || '';
    console.log('Checking Supabase for topic:', normalizedQuery);
    
    try {
      const { data, error } = await supabase
        .from('research_papers')
        .select('*')
        .eq('topic', normalizedQuery)
        .limit(100);

      if (error) {
        console.log('Supabase lookup error:', error.message);
        return null;
      }
      
      if (!data || data.length === 0) {
        console.log('No papers found in Supabase for this topic');
        return null;
      }

      // Check freshness - use the most recent inserted_at
      const mostRecent = data.reduce((latest, row) => {
        const rowDate = new Date(row.inserted_at);
        return rowDate > latest ? rowDate : latest;
      }, new Date(0));
      
      const ageInDays = (Date.now() - mostRecent.getTime()) / (1000 * 60 * 60 * 24);
      console.log('Cache age:', ageInDays.toFixed(1), 'days');
      
      if (ageInDays > CACHE_MAX_AGE_DAYS) {
        console.log('Cache is stale (>', CACHE_MAX_AGE_DAYS, 'days), fetching fresh data');
        // Keep old data, will add new data alongside it
        return null;
      }

      console.log('Found fresh papers in Supabase:', data.length);
      
      // Map database columns back to expected paper format
      const papers = data.map(row => ({
        paperId: row.paperid,
        title: row.title,
        abstract: row.abstract,
        authors: row.authors,
        year: row.year,
        venue: row.venue,
        citationCount: row.citationcount,
        referenceCount: row.referencecount,
        url: row.url,
        openAccessPdf: row.openaccesspdf,
        isOpenAccess: row.isopenaccess,
        fieldsOfStudy: row.fieldsofstudy,
        publicationTypes: row.publicationtypes,
        institutions: row.institutions || [],  // Handle institutions field
        externalIds: row.externalids,
        source: row.source
      }));
      
      return { papers, results_count: papers.length };
    } catch (err) {
      console.log('Supabase unavailable:', err.message);
      return null;
    }
  };

  // Save papers to Supabase after fetching from API
  const saveToCache = async (query, papers) => {
    const normalizedQuery = query?.toLowerCase().trim() || '';
    console.log('Saving papers to Supabase:', papers.length, 'for topic:', normalizedQuery);
    
    try {
      // Map papers to match your table columns
      const papersToSave = papers.map(paper => ({
        paperid: paper.paperId || paper.id,
        title: paper.title,
        abstract: paper.abstract,
        authors: paper.authors,
        year: paper.year,
        venue: paper.venue,
        citationcount: paper.citationCount,
        referencecount: paper.referenceCount,
        url: paper.url,
        openaccesspdf: paper.openAccessPdf,
        isopenaccess: paper.isOpenAccess,
        fieldsofstudy: paper.fieldsOfStudy,
        publicationtypes: paper.publicationTypes,
        institutions: paper.institutions || [],  // Include institutions field
        externalids: paper.externalIds,
        source: paper.source || 'OpenAlex',
        topic: normalizedQuery,
        inserted_at: new Date().toISOString()
      }));

      const { error } = await supabase
        .from('research_papers')
        .insert(papersToSave);
      
      if (error) {
        console.log('Error saving to Supabase:', error.message);
      } else {
        console.log('Successfully saved', papers.length, 'papers to Supabase');
      }
    } catch (err) {
      console.log('Save to Supabase failed:', err.message);
    }
  };

  const fetchPapers = async () => {
    setLoading(true);
    setError(null);
    setSelectedPaper(null);
    setFromCache(false);

    try {
      // First, check if we have cached results
      const cachedData = await checkCache(topic);
      
      if (cachedData && cachedData.papers && cachedData.papers.length > 0) {
        console.log('Using cached results:', cachedData.papers.length, 'papers');
        setAllPapers(cachedData.papers);
        setPapers(cachedData.papers);
        setStats({
          total: cachedData.results_count,
          sources: ['Cache']
        });
        setFromCache(true);
        setLoading(false);
        return;
      }

      // No cache, fetch from all APIs (arXiv, CORE, PMC, Semantic Scholar, Google Scholar)
      console.log('No cache found, fetching from all APIs...');
      
      // Fetch from all sources in parallel
      const [arxivResponse, coreResponse, pmcResponse, semanticResponse, googleScholarResponse] = await Promise.allSettled([
        arxivAPI.searchPapers(topic, 20).catch(err => ({ status: 'error', error: err })),
        coreAPI.searchPapers(topic, 20).catch(err => ({ status: 'error', error: err })),
        pmcAPI.searchPapers(topic, 20).catch(err => ({ status: 'error', error: err })),
        semanticScholarAPI.searchPapers(topic, 20).catch(err => ({ status: 'error', error: err })),
        googleScholarAPI.searchPapers(topic, 20).catch(err => ({ status: 'error', error: err }))
      ]);
      
      const allPapersList = [];
      const sources = [];
      
      // Process arXiv results
      if (arxivResponse.status === 'fulfilled' && arxivResponse.value.status === 'success') {
        allPapersList.push(...arxivResponse.value.papers);
        sources.push('arXiv');
        console.log('arXiv papers received:', arxivResponse.value.papers.length);
      }
      
      // Process CORE results
      if (coreResponse.status === 'fulfilled' && coreResponse.value.status === 'success') {
        allPapersList.push(...coreResponse.value.papers);
        sources.push('CORE');
        console.log('CORE papers received:', coreResponse.value.papers.length);
      }
      
      // Process PMC results
      if (pmcResponse.status === 'fulfilled' && pmcResponse.value.status === 'success') {
        allPapersList.push(...pmcResponse.value.papers);
        sources.push('PMC');
        console.log('PMC papers received:', pmcResponse.value.papers.length);
      }
      
      // Process Semantic Scholar results
      if (semanticResponse.status === 'fulfilled' && semanticResponse.value.status === 'success') {
        allPapersList.push(...semanticResponse.value.papers);
        sources.push('Semantic Scholar');
        console.log('Semantic Scholar papers received:', semanticResponse.value.papers.length);
      }
      
      // Process Google Scholar results
      if (googleScholarResponse.status === 'fulfilled' && googleScholarResponse.value.status === 'success') {
        allPapersList.push(...googleScholarResponse.value.papers);
        sources.push('Google Scholar');
        console.log('Google Scholar papers received:', googleScholarResponse.value.papers.length);
      }
      
      // Process Google Scholar results
      if (googleScholarResponse.status === 'fulfilled' && googleScholarResponse.value.status === 'success') {
        allPapersList.push(...googleScholarResponse.value.papers);
        sources.push('Google Scholar');
        console.log('Google Scholar papers received:', googleScholarResponse.value.papers.length);
      }
      
      if (allPapersList.length > 0) {
        console.log('Total papers received:', allPapersList.length);
        setAllPapers(allPapersList);
        setPapers(allPapersList);
        setStats({
          total: allPapersList.length,
          sources: sources
        });
        
        // Save to cache for future use
        await saveToCache(topic, allPapersList);
      } else {
        setError('No papers found. Please try a different search term.');
        setAllPapers([]);
        setPapers([]);
      }
    } catch (err) {
      console.error('Error fetching papers:', err);
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Sort papers function (priority: open access + has PDF to the top)
  const sortPapers = useCallback((papersToSort, sortBy) => {
    const sorted = [...papersToSort];

    const getPriority = (p) => {
      const hasPdf =
        Boolean(p.openAccessPdf) ||
        (p.url && typeof p.url === 'string' && p.url.toLowerCase().endsWith('.pdf'));
      const isOA = Boolean(p.isOpenAccess);
      // Priority 2: OA + PDF, 1: either, 0: neither
      return (isOA ? 1 : 0) + (hasPdf ? 1 : 0);
    };

    sorted.sort((a, b) => {
      const priorityDiff = getPriority(b) - getPriority(a);
      if (priorityDiff !== 0) return priorityDiff;

      switch (sortBy) {
        case 'citations':
          return (b.citationCount || 0) - (a.citationCount || 0);
        case 'year':
          return (b.year || 0) - (a.year || 0);
        case 'title':
          return (a.title || '').localeCompare(b.title || '');
        case 'relevance':
        default:
          return 0; // keep original order when equal priority
      }
    });

    return sorted;
  }, []);

  const applyFilters = useCallback(() => {
    console.log('applyFilters called:', { allPapersCount: allPapers.length });
    
    if (allPapers.length === 0) {
      console.log('No papers to filter');
      setPapers([]);
      return;
    }

    let filtered = [...allPapers];
    let hasActiveFilters = false;
    console.log('Starting with', filtered.length, 'papers');

    // Apply query builder filters
    filters.forEach(filter => {
      const filterValue = filter.value ? filter.value.toString().trim() : '';
      if (!filterValue) return; // Skip empty filters
      
      hasActiveFilters = true;

      if (filter.field === 'title_abstract') {
        const searchTerm = filter.value.toLowerCase();
        if (filter.operator === 'includes') {
          filtered = filtered.filter(p => 
            (p.title && p.title.toLowerCase().includes(searchTerm)) ||
            (p.abstract && p.abstract.toLowerCase().includes(searchTerm))
          );
        } else if (filter.operator === 'equals') {
          filtered = filtered.filter(p => 
            (p.title && p.title.toLowerCase() === searchTerm) ||
            (p.abstract && p.abstract.toLowerCase() === searchTerm)
          );
        }
      } else if (filter.field === 'open_access' && filter.operator === 'is') {
        if (filter.value.toLowerCase().includes('open access')) {
          filtered = filtered.filter(p => p.isOpenAccess === true);
        }
      } else if (filter.field === 'year') {
        const yearValue = parseInt(filter.value);
        if (!isNaN(yearValue)) {
          if (filter.operator === 'is') {
            filtered = filtered.filter(p => p.year === yearValue);
          } else if (filter.operator === '>') {
            filtered = filtered.filter(p => p.year && p.year > yearValue);
          } else if (filter.operator === '<') {
            filtered = filtered.filter(p => p.year && p.year < yearValue);
          }
        }
      } else if (filter.field === 'venue') {
        const venueTerm = filter.value.toLowerCase();
        if (filter.operator === 'includes') {
          filtered = filtered.filter(p => 
            p.venue && p.venue.toLowerCase().includes(venueTerm)
          );
        } else if (filter.operator === 'equals') {
          filtered = filtered.filter(p => 
            p.venue && p.venue.toLowerCase() === venueTerm
          );
        }
      }
    });

    // Apply stats panel filters
    if (selectedYears.length > 0) {
      filtered = filtered.filter(p => selectedYears.includes(p.year));
    }

    if (selectedTopics.length > 0) {
      filtered = filtered.filter(p => 
        p.fieldsOfStudy && p.fieldsOfStudy.some(field => selectedTopics.includes(field))
      );
    }

    if (selectedTypes.length > 0) {
      filtered = filtered.filter(p => {
        const type = p.publicationTypes && p.publicationTypes.length > 0 
          ? p.publicationTypes[0] 
          : 'article';
        return selectedTypes.includes(type);
      });
    }

    if (selectedInstitutions.length > 0) {
      filtered = filtered.filter(p => 
        p.institutions && Array.isArray(p.institutions) && 
        p.institutions.some(inst => selectedInstitutions.includes(inst))
      );
    }

    if (openAccessOnly) {
      filtered = filtered.filter(p => p.isOpenAccess === true);
    }

    // If no active filters at all, show all papers
    const hasStatsFilters =
      openAccessOnly || selectedYears.length > 0 || selectedTopics.length > 0 || selectedTypes.length > 0 || selectedInstitutions.length > 0;
    console.log('Filter result:', { 
      hasActiveFilters, 
      hasStatsFilters, 
      filteredCount: filtered.length,
      allPapersCount: allPapers.length
    });
    
    let result;
    if (!hasActiveFilters && !hasStatsFilters) {
      console.log('No active filters, showing all papers');
      result = [...allPapers];
    } else {
      console.log('Applying filters, showing', filtered.length, 'filtered papers');
      result = filtered;
    }
    
    // Apply sorting
    const sortedResult = sortPapers(result, sortOption);
    setPapers(sortedResult);
    setCurrentPage(1); // Reset to first page when filters change
  }, [allPapers, filters, selectedYears, selectedTopics, selectedTypes, selectedInstitutions, openAccessOnly, sortOption, sortPapers]);

  useEffect(() => {
    if (!topic) {
      navigate('/');
      return;
    }

    setSearchQuery(topic);
    
    // Update the filter input to match the new topic
    setFilters(prevFilters => {
      const titleFilter = prevFilters.find(f => f.field === 'title_abstract');
      if (titleFilter) {
        // Update existing title_abstract filter
        return prevFilters.map(f => 
          f.field === 'title_abstract' ? { ...f, value: topic } : f
        );
      } else {
        // Add new title_abstract filter
        return [createFilter('title_abstract', 'includes', topic), ...prevFilters];
      }
    });
    
    fetchPapers();
  }, [topic]);

  // Apply filters whenever filters, stats filters, or allPapers change
  useEffect(() => {
    if (allPapers.length > 0) {
      applyFilters();
    } else {
      // If no papers, ensure papers state is empty
      setPapers([]);
    }
  }, [filters, selectedYears, selectedTopics, selectedTypes, selectedInstitutions, openAccessOnly, allPapers, applyFilters]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showSortDropdown && !event.target.closest('.sort-dropdown-container')) {
        setShowSortDropdown(false);
      }
      if (showExportDropdown && !event.target.closest('.export-dropdown-container')) {
        setShowExportDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showSortDropdown, showExportDropdown]);

  const addFilter = () => {
    setFilters([...filters, createFilter('title_abstract', 'includes', '')]);
  };

  const removeFilter = (filterId) => {
    setFilters(filters.filter(f => f.id !== filterId));
  };

  const updateFilter = (filterId, field, operator, value) => {
    setFilters(filters.map(f => 
      f.id === filterId ? { ...f, field, operator, value } : f
    ));
  };

  const handleSearch = (query) => {
    setSearchQuery(query);
    // Update the first title_abstract filter if it exists
    const titleFilter = filters.find(f => f.field === 'title_abstract');
    if (titleFilter) {
      updateFilter(titleFilter.id, 'title_abstract', 'includes', query);
    } else {
      setFilters([createFilter('title_abstract', 'includes', query), ...filters]);
    }
  };


  // Export to Excel function
  const exportToExcel = () => {
    if (papers.length === 0) {
      alert('No papers to export');
      return;
    }

    // Prepare data for Excel - flatten the paper objects
    const excelData = papers.map((paper, index) => ({
      'S.No': index + 1,
      'Title': paper.title || 'N/A',
      'Authors': Array.isArray(paper.authors) 
        ? paper.authors.map(a => typeof a === 'string' ? a : a.name || a).join('; ')
        : 'N/A',
      'Year': paper.year || 'N/A',
      'Venue/Journal': paper.venue || 'N/A',
      'Citation Count': paper.citationCount || 0,
      'Reference Count': paper.referenceCount || 0,
      'Abstract': paper.abstract || 'N/A',
      'Fields of Study': Array.isArray(paper.fieldsOfStudy) 
        ? paper.fieldsOfStudy.join('; ') 
        : 'N/A',
      'Publication Types': Array.isArray(paper.publicationTypes) 
        ? paper.publicationTypes.join('; ') 
        : 'N/A',
      'DOI': paper.externalIds?.DOI || paper.externalIds?.doi || 'N/A',
      'URL': paper.url || 'N/A',
      'PDF URL': paper.openAccessPdf || 'N/A',
      'Open Access': paper.isOpenAccess ? 'Yes' : 'No',
      'Paper ID': paper.paperId || 'N/A',
      'Source': paper.source || 'N/A'
    }));

    // Create workbook and worksheet
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(excelData);

    // Set column widths for better readability
    const columnWidths = [
      { wch: 6 },   // S.No
      { wch: 60 },  // Title
      { wch: 40 },  // Authors
      { wch: 8 },   // Year
      { wch: 30 },  // Venue
      { wch: 12 },  // Citation Count
      { wch: 12 },  // Reference Count
      { wch: 80 },  // Abstract
      { wch: 30 },  // Fields of Study
      { wch: 20 },  // Publication Types
      { wch: 30 },  // DOI
      { wch: 50 },  // URL
      { wch: 50 },  // PDF URL
      { wch: 12 },  // Open Access
      { wch: 25 },  // Paper ID
      { wch: 15 },  // Source
    ];
    worksheet['!cols'] = columnWidths;

    // Add metadata sheet
    const metadataSheet = XLSX.utils.json_to_sheet([
      { 'Property': 'Search Query', 'Value': topic || 'N/A' },
      { 'Property': 'Total Results', 'Value': papers.length },
      { 'Property': 'Export Date', 'Value': new Date().toLocaleString() },
      { 'Property': 'Open Access Papers', 'Value': papers.filter(p => p.isOpenAccess).length },
      { 'Property': 'Average Citations', 'Value': Math.round(papers.reduce((sum, p) => sum + (p.citationCount || 0), 0) / papers.length) || 0 },
      { 'Property': 'Year Range', 'Value': `${Math.min(...papers.filter(p => p.year).map(p => p.year))} - ${Math.max(...papers.filter(p => p.year).map(p => p.year))}` },
      { 'Property': 'Current Sort', 'Value': sortOptions.find(o => o.value === sortOption)?.label || 'Default' },
      { 'Property': 'Active Filters', 'Value': filters.length > 0 ? filters.map(f => `${f.field} ${f.operator} "${f.value}"`).join('; ') : 'None' },
    ]);
    metadataSheet['!cols'] = [{ wch: 20 }, { wch: 60 }];

    // Add sheets to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Research Papers');
    XLSX.utils.book_append_sheet(workbook, metadataSheet, 'Search Metadata');

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 10);
    const sanitizedTopic = (topic || 'research').replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30);
    const filename = `${sanitizedTopic}_papers_${timestamp}.xlsx`;

    // Export the file
    XLSX.writeFile(workbook, filename);
  };

  // Export to PDF function
  const exportToPDF = () => {
    if (papers.length === 0) {
      alert('No papers to export');
      return;
    }

    // Create PDF document (landscape for more columns)
    const doc = new jsPDF('landscape', 'mm', 'a4');
    
    // Add title
    const sanitizedTopic = (topic || 'Research Papers').slice(0, 50);
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text(`Research Papers: ${sanitizedTopic}`, 14, 15);
    
    // Add metadata
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(100);
    doc.text(`Generated: ${new Date().toLocaleString()} | Total: ${papers.length} papers | Open Access: ${papers.filter(p => p.isOpenAccess).length}`, 14, 22);
    doc.setTextColor(0);

    // Prepare table data
    const tableData = papers.map((paper, index) => [
      index + 1,
      (paper.title || 'N/A').slice(0, 80) + ((paper.title?.length > 80) ? '...' : ''),
      Array.isArray(paper.authors) 
        ? paper.authors.slice(0, 3).map(a => typeof a === 'string' ? a : a.name || a).join(', ') + (paper.authors.length > 3 ? '...' : '')
        : 'N/A',
      paper.year || 'N/A',
      paper.citationCount || 0,
      paper.isOpenAccess ? 'Yes' : 'No',
      (paper.venue || 'N/A').slice(0, 30) + ((paper.venue?.length > 30) ? '...' : ''),
    ]);

    // Create table
    autoTable(doc, {
      startY: 28,
      head: [['#', 'Title', 'Authors', 'Year', 'Citations', 'Open Access', 'Venue']],
      body: tableData,
      headStyles: {
        fillColor: [0, 0, 0],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 9,
      },
      bodyStyles: {
        fontSize: 8,
        cellPadding: 2,
      },
      columnStyles: {
        0: { cellWidth: 10 },  // #
        1: { cellWidth: 80 },  // Title
        2: { cellWidth: 50 },  // Authors
        3: { cellWidth: 15 },  // Year
        4: { cellWidth: 18 },  // Citations
        5: { cellWidth: 18 },  // Open Access
        6: { cellWidth: 45 },  // Venue
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245],
      },
      margin: { top: 28 },
      didDrawPage: (data) => {
        // Add page number footer
        const pageCount = doc.getNumberOfPages();
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(
          `Page ${data.pageNumber} of ${pageCount}`,
          doc.internal.pageSize.width / 2,
          doc.internal.pageSize.height - 10,
          { align: 'center' }
        );
      },
    });

    // Generate filename
    const timestamp = new Date().toISOString().slice(0, 10);
    const filenameTopic = (topic || 'research').replace(/[^a-zA-Z0-9]/g, '_').slice(0, 30);
    const filename = `${filenameTopic}_papers_${timestamp}.pdf`;

    // Save the PDF
    doc.save(filename);
  };

  // Pagination
  const totalPages = Math.ceil(papers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentPapers = papers.slice(startIndex, endIndex);

  return (
    <div className="min-h-screen bg-white">
      {/* Query Builder / Filter Area */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-3">
          {/* Dropdown Row */}
          <div className="flex items-center gap-2 mb-2">
            <SearchDropdown 
              topic={topic} 
              searchQuery={searchQuery}
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {filters.map((filter, index) => (
              <React.Fragment key={filter.id}>
                {index > 0 && (
                  <button className="text-sm px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50">
                    and
                  </button>
                )}
                <select
                  value={filter.field}
                  onChange={(e) => updateFilter(filter.id, e.target.value, filter.operator, filter.value)}
                  className="text-sm border border-gray-300 rounded px-3 py-1.5"
                >
                  <option value="title_abstract">Q Title & Abstract</option>
                  <option value="open_access">Work</option>
                  <option value="year">Year</option>
                  <option value="venue">Venue</option>
                </select>
                <select
                  value={filter.operator}
                  onChange={(e) => updateFilter(filter.id, filter.field, e.target.value, filter.value)}
                  className="text-sm border border-gray-300 rounded px-3 py-1.5"
                >
                  {filter.field === 'open_access' ? (
                    <option value="is">is</option>
                  ) : filter.field === 'year' ? (
                    <>
                      <option value="is">is</option>
                      <option value=">">greater than</option>
                      <option value="<">less than</option>
                    </>
                  ) : (
                    <>
                      <option value="includes">includes</option>
                      <option value="equals">equals</option>
                    </>
                  )}
                </select>
                {filter.field === 'open_access' ? (
                  <input
                    type="text"
                    value={filter.value}
                    onChange={(e) => updateFilter(filter.id, filter.field, filter.operator, e.target.value)}
                    className="text-sm border border-gray-300 rounded px-3 py-1.5"
                    placeholder="open access"
                  />
                ) : (
                  <input
                    type={filter.field === 'year' ? 'number' : 'text'}
                    value={filter.value}
                    onChange={(e) => updateFilter(filter.id, filter.field, filter.operator, e.target.value)}
                    className="text-sm border border-gray-300 rounded px-3 py-1.5 flex-1 min-w-[200px]"
                    placeholder={filter.field === 'title_abstract' ? 'Enter search term...' : ''}
                  />
                )}
                {index === filters.length - 1 && (
                  <>
                    <button
                      onClick={addFilter}
                      className="p-2 bg-black text-white rounded-full hover:bg-gray-800"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                    {filters.length > 1 && (
            <button
                        onClick={() => removeFilter(filter.id)}
                        className="p-2 border border-gray-300 rounded hover:bg-gray-50"
            >
                        <Trash2 className="w-4 h-4 text-gray-600" />
            </button>
                    )}
                  </>
                )}
              </React.Fragment>
            ))}
          </div>
          </div>
        </div>

        {/* Main Content */}
      <div className="flex">
        {/* Left Column - Works List */}
        <div className="flex-1 overflow-y-auto bg-white">
          <div className="max-w-4xl mx-auto">
            {/* Works Header */}
            <div className="border-b border-gray-200 p-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-black">Works</h2>
              <div className="flex items-center gap-2">
                {papers.length > 0 && (
                  <button
                    onClick={() => setShowCitationMesh(true)}
                    className="px-3 py-1.5 bg-black text-white rounded text-sm hover:bg-gray-800 transition-colors flex items-center gap-2"
                    title="View Citation Network"
                  >
                    <Network className="w-4 h-4" />
                    Citation Mesh
                  </button>
                )}
                {/* Sort Dropdown */}
                <div className="relative sort-dropdown-container">
                  <button 
                    onClick={() => setShowSortDropdown(!showSortDropdown)}
                    className={`p-1.5 hover:bg-gray-100 rounded flex items-center gap-1 ${showSortDropdown ? 'bg-gray-100' : ''}`}
                    title="Sort results"
                  >
                    <ArrowUpDown className="w-4 h-4 text-gray-600" />
                    <ChevronDown className={`w-3 h-3 text-gray-600 transition-transform ${showSortDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {/* Dropdown Menu */}
                  {showSortDropdown && (
                    <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
                      <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b border-gray-100">
                        Sort by
                      </div>
                      {sortOptions.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => {
                            setSortOption(option.value);
                            setShowSortDropdown(false);
                          }}
                          className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center justify-between ${
                            sortOption === option.value ? 'bg-gray-50 text-black font-medium' : 'text-gray-700'
                          }`}
                        >
                          <span>{option.label}</span>
                          {sortOption === option.value && (
                            <Check className="w-4 h-4 text-black" />
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Export Dropdown */}
                <div className="relative export-dropdown-container">
                  <button 
                    onClick={() => setShowExportDropdown(!showExportDropdown)}
                    className={`p-1.5 hover:bg-gray-100 rounded flex items-center gap-1 ${showExportDropdown ? 'bg-gray-100' : ''}`}
                    title="Export results"
                  >
                    <Download className="w-4 h-4 text-gray-600" />
                    <ChevronDown className={`w-3 h-3 text-gray-600 transition-transform ${showExportDropdown ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {/* Export Dropdown Menu */}
                  {showExportDropdown && (
                    <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
                      <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase border-b border-gray-100">
                        Export as
                      </div>
                      <button
                        onClick={() => {
                          exportToPDF();
                          setShowExportDropdown(false);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-gray-700"
                      >
                        <FileText className="w-4 h-4" />
                        Download PDF
                      </button>
                      <button
                        onClick={() => {
                          exportToExcel();
                          setShowExportDropdown(false);
                        }}
                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-gray-700"
                      >
                        <BarChart3 className="w-4 h-4" />
                        Export to Excel
                      </button>
                    </div>
                  )}
                </div>
                <button className="p-1.5 hover:bg-gray-100 rounded">
                  <MoreVertical className="w-4 h-4 text-gray-600" />
                </button>
              </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
                <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-black mb-4"></div>
                <p className="text-black text-lg">Searching research papers...</p>
                <p className="text-gray-600 text-sm mt-2">This may take a few moments</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center m-4">
                <p className="text-red-700 text-lg mb-4">{error}</p>
              <button
                onClick={fetchPapers}
                  className="px-6 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Debug Info - Remove in production */}
          {!loading && (
            <div className="p-2 bg-gray-100 text-xs m-4 rounded">
              Debug: loading={loading ? 'true' : 'false'}, error={error ? 'yes' : 'no'}, 
              papers={papers.length}, allPapers={allPapers.length}, 
              currentPapers={currentPapers.length}, currentPage={currentPage}
            </div>
          )}

            {/* Results List */}
          {!loading && !error && papers.length > 0 && (
              <>
                <div className="border-b border-gray-200">
                  {currentPapers.map((paper, index) => {
                    const paperId = paper.arxiv_id || paper.paperId || `${index}-${paper.title}`;
                    return (
                      <PaperListItem
                        key={paperId}
                        paper={paper}
                        isSelected={selectedPaper && (selectedPaper.arxiv_id || selectedPaper.paperId) === paperId}
                        onClick={() => setSelectedPaper(paper)}
                      />
                    );
                  })}
            </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="p-4 flex items-center justify-center gap-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ←
                    </button>
                    {Array.from({ length: Math.min(10, totalPages) }, (_, i) => i + 1).map(page => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-3 py-1.5 border rounded ${
                          currentPage === page
                            ? 'bg-black text-white border-black'
                            : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                    {totalPages > 10 && <span className="px-2 text-gray-500">...</span>}
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      →
                    </button>
                  </div>
                )}
              </>
          )}

          {/* No Results */}
          {!loading && !error && papers.length === 0 && (
            <div className="text-center py-20">
              <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 text-lg">No papers found for this topic</p>
            </div>
          )}
        </div>
        </div>

        {/* Right Column - Stats Panel */}
        {showStatsPanel && (
          <StatsPanel 
            papers={papers} 
            stats={stats}
            onClose={() => setShowStatsPanel(false)}
            selectedYears={selectedYears}
            setSelectedYears={setSelectedYears}
            selectedTopics={selectedTopics}
            setSelectedTopics={setSelectedTopics}
            selectedTypes={selectedTypes}
            setSelectedTypes={setSelectedTypes}
            selectedInstitutions={selectedInstitutions}
            setSelectedInstitutions={setSelectedInstitutions}
            openAccessOnly={openAccessOnly}
            onToggleOpenAccess={() => setOpenAccessOnly(!openAccessOnly)}
          />
        )}

        {/* Detail Panel Overlay */}
        {selectedPaper && (
          <>
            <DetailPanel paper={selectedPaper} onClose={() => setSelectedPaper(null)} />
            <div
              className="fixed inset-0 bg-black/30 z-40 md:hidden"
              onClick={() => setSelectedPaper(null)}
            ></div>
          </>
        )}

        {/* Citation Mesh Overlay */}
        {showCitationMesh && (
          <CitationMesh
            papers={allPapers}
            onClose={() => setShowCitationMesh(false)}
            onNodeClick={(nodeData) => {
              // Find the paper in allPapers and show its details
              const paper = allPapers.find(p => 
                (p.paperId || p.id) === nodeData.paperId
              );
              if (paper) {
                setSelectedPaper(paper);
                setShowCitationMesh(false);
              }
            }}
          />
        )}
      </div>
    </div>
  );
}
