import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { searchAPI, APIError } from '../services/api';
import { 
  BookOpen, X, FileText, Link as LinkIcon, MessageSquare, Code, Download, 
  ChevronDown, Plus, Trash2, MoreVertical, ArrowUpDown, BarChart3, CheckSquare
} from 'lucide-react';
import SearchDropdown from '../components/SearchDropdown';
import { supabase } from '../lib/supabase';

// Compact paper card for the list (left column) - OpenAlex style
const PaperListItem = ({ paper, isSelected, onClick }) => {
  const authors = Array.isArray(paper.authors) && paper.authors.length > 0
    ? paper.authors.slice(0, 2).map(a => typeof a === 'string' ? a : a.name || a).join(', ') + (paper.authors.length > 2 ? ', et al.' : '')
    : 'Unknown Authors';

  const venue = paper.venue && paper.venue !== 'N/A' ? paper.venue : null;
  const year = paper.year || null;
  const citationCount = paper.citationCount || 0;
  const pdfUrl = paper.openAccessPdf || (paper.url && paper.url.toLowerCase().endsWith('.pdf') ? paper.url : null);

  return (
    <div
      onClick={onClick}
      className={`p-4 cursor-pointer border-b border-gray-200 hover:bg-gray-50 transition-colors ${
        isSelected ? 'bg-gray-100' : ''
      }`}
    >
      <h3 className="text-base font-semibold text-black mb-1.5 line-clamp-2 hover:text-gray-700 transition-colors">
        {paper.title || 'Untitled Paper'}
      </h3>

      <div className="text-sm text-gray-600 mb-2">
        {year && <span>{year}</span>}
        {year && authors && <span> · </span>}
        <span>{authors}</span>
        {venue && <span> · {venue}</span>}
      </div>

      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>Cited by {citationCount.toLocaleString()}</span>
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
  openAccessOnly,
  onToggleOpenAccess,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    year: true,
    topic: false,
    institution: false,
    type: true
  });

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

  const authors = Array.isArray(paper.authors) ? paper.authors : [];
  const venue = paper.venue && paper.venue !== 'N/A' ? paper.venue : null;
  const year = paper.year || null;
  const citationCount = paper.citationCount || 0;
  const referenceCount = paper.referenceCount || 0;
  const doi = paper.externalIds && (paper.externalIds.DOI || paper.externalIds.doi);
  const pdfUrl = paper.openAccessPdf || (paper.url && paper.url.toLowerCase().endsWith('.pdf') ? paper.url : null);
  const htmlUrl = paper.url && !pdfUrl ? paper.url : null;
  const fields = Array.isArray(paper.fieldsOfStudy) ? paper.fieldsOfStudy : [];
  const isOpenAccess = Boolean(paper.isOpenAccess);
  const [abstractExpanded, setAbstractExpanded] = useState(false);

  const abstract = paper.abstract && paper.abstract !== 'N/A' ? paper.abstract : null;
  const abstractPreview = abstract && abstract.length > 300 ? abstract.substring(0, 300) + '...' : abstract;

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
        <button className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors">
          <Code className="w-4 h-4" />
          API
        </button>
        <button className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors">
          <LinkIcon className="w-4 h-4" />
        </button>
        <button className="px-4 py-2 bg-black hover:bg-gray-800 text-white rounded text-sm flex items-center gap-2 transition-colors">
          <MessageSquare className="w-4 h-4" />
        </button>
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
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

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

      // No cache, fetch from API
      console.log('No cache found, fetching from API...');
      const response = await searchAPI.fetchPapers(topic, 100, false);
      console.log('API Response:', response);
      
      if (response.status === 'success') {
        console.log('Papers received:', response.papers.length);
        setAllPapers(response.papers);
        setPapers(response.papers);
        setStats({
          total: response.count,
          sources: response.sources
        });
        
        // Save to cache for future use
        await saveToCache(topic, response.papers);
      } else if (response.status === 'no_results') {
        setError(response.message);
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

    if (openAccessOnly) {
      filtered = filtered.filter(p => p.isOpenAccess === true);
    }

    // If no active filters at all, show all papers
    const hasStatsFilters =
      openAccessOnly || selectedYears.length > 0 || selectedTopics.length > 0 || selectedTypes.length > 0;
    console.log('Filter result:', { 
      hasActiveFilters, 
      hasStatsFilters, 
      filteredCount: filtered.length,
      allPapersCount: allPapers.length
    });
    
    if (!hasActiveFilters && !hasStatsFilters) {
      console.log('No active filters, showing all papers');
      setPapers([...allPapers]);
    } else {
      console.log('Applying filters, showing', filtered.length, 'filtered papers');
      setPapers(filtered);
    }
    setCurrentPage(1); // Reset to first page when filters change
  }, [allPapers, filters, selectedYears, selectedTopics, selectedTypes, openAccessOnly]);

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
  }, [filters, selectedYears, selectedTopics, selectedTypes, allPapers, applyFilters]);

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
                <button className="p-1.5 hover:bg-gray-100 rounded">
                  <ArrowUpDown className="w-4 h-4 text-gray-600" />
                </button>
                <button className="p-1.5 hover:bg-gray-100 rounded">
                  <Download className="w-4 h-4 text-gray-600" />
                </button>
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
                  {currentPapers.map((paper, index) => (
                    <PaperListItem
                      key={paper.paperId || `${index}-${paper.title}`}
                      paper={paper}
                      isSelected={selectedPaper && selectedPaper.paperId === paper.paperId}
                      onClick={() => setSelectedPaper(paper)}
                    />
              ))}
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
      </div>
    </div>
  );
}
