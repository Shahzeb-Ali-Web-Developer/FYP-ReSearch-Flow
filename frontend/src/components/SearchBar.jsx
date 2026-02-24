import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Clock, TrendingUp, X, Sparkles } from 'lucide-react';
import { useSearchHistory } from '../hooks/useSearchHistory';

const SearchBar = ({ onSearch, initialValue = '', placeholder = "Search topics, or ask a question...", size = "large" }) => {
    const [searchValue, setSearchValue] = useState(initialValue);
    const [isFocused, setIsFocused] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const [highlightedIndex, setHighlightedIndex] = useState(-1);
    const inputRef = useRef(null);
    const dropdownRef = useRef(null);
    const { getSuggestions, recordSearch, searchHistory, clearHistory } = useSearchHistory();

    useEffect(() => {
        setSearchValue(initialValue);
    }, [initialValue]);

    // Detect if the query looks like a natural language question/statement
    const isSemanticQuery = (query) => {
        const q = query.trim().toLowerCase();
        return /^(what|how|why|which|where|when|who|can|does|is|are|show|find|explain|compare|analyze|list)\b/.test(q)
            || q.includes('?')
            || q.split(' ').length > 5;
    };

    // Lightly clean a natural language query
    const cleanQueryForSearch = (query) => {
        const q = query.trim();
        if (!isSemanticQuery(q)) return q;

        const cleaned = q
            .replace(/^(what(?:'s|\s+is|\s+are)?|how\s+(?:does|do|is|are|can)?|why\s+(?:does|do|is|are)?|show\s+me|find\s+me|tell\s+me\s+about|explain|list|compare|analyze)\s+/i, '')
            .replace(/\?+$/, '')
            .trim();

        return cleaned.length >= 3 ? cleaned : q;
    };

    // Fetch suggestions
    const updateSuggestions = useCallback(async (value) => {
        const newSuggestions = await getSuggestions(value, 8);
        setSuggestions(newSuggestions);
        setHighlightedIndex(-1);
    }, [getSuggestions]);

    // Instant update on focus or clear, debounced on typing
    useEffect(() => {
        if (searchValue.trim() === '') {
            updateSuggestions('');
            return;
        }

        const timeoutId = setTimeout(() => {
            updateSuggestions(searchValue);
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [searchValue, updateSuggestions]);

    const handleSearch = useCallback((queryOverride) => {
        const raw = queryOverride || searchValue;
        if (!raw.trim()) return;

        recordSearch(raw.trim());
        const searchTerm = cleanQueryForSearch(raw.trim());
        onSearch(searchTerm);
        setIsFocused(false);
    }, [searchValue, onSearch, recordSearch]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                const selected = suggestions[highlightedIndex];
                setSearchValue(selected.text);
                handleSearch(selected.text);
            } else {
                handleSearch();
            }
            e.preventDefault();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            setHighlightedIndex(prev =>
                prev < suggestions.length - 1 ? prev + 1 : 0
            );
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setHighlightedIndex(prev =>
                prev > 0 ? prev - 1 : suggestions.length - 1
            );
        } else if (e.key === 'Escape') {
            setIsFocused(false);
            inputRef.current?.blur();
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setSearchValue(suggestion.text);
        handleSearch(suggestion.text);
    };

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (
                dropdownRef.current && !dropdownRef.current.contains(e.target) &&
                inputRef.current && !inputRef.current.contains(e.target)
            ) {
                setIsFocused(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const showDropdown = isFocused && (suggestions.length > 0);
    const isNLP = searchValue.trim().length > 0 && isSemanticQuery(searchValue);

    const containerPadding = size === "small" ? "px-4 py-2" : "px-6 py-4";
    const iconSize = size === "small" ? "w-5 h-5" : "w-6 h-6";
    const fontSize = size === "small" ? "text-base" : "text-lg";

    return (
        <div className={`relative w-full ${size === "small" ? "max-w-2xl" : "max-w-4xl"} z-50`}>
            <div
                className={`relative flex items-center bg-white border-2 rounded-lg transition-all duration-300 ${isFocused ? 'border-black shadow-lg' : 'border-gray-300'
                    }`}
            >
                <input
                    ref={inputRef}
                    type="text"
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className={`w-full ${containerPadding} bg-transparent text-black placeholder-gray-400 focus:outline-none ${fontSize}`}
                />
                {searchValue && (
                    <button
                        onClick={() => { setSearchValue(''); inputRef.current?.focus(); }}
                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
                <button
                    onClick={() => handleSearch()}
                    disabled={!searchValue.trim()}
                    className="mr-2 p-2 bg-black rounded-lg hover:bg-gray-800 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                    <Search className={`${iconSize} text-white`} />
                </button>
            </div>

            {isNLP && size !== "small" && (
                <div className="absolute -bottom-7 left-2 flex items-center gap-1.5 text-xs text-gray-500">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    <span>Semantic search — smart keyword extraction active</span>
                </div>
            )}

            {showDropdown && (
                <div
                    ref={dropdownRef}
                    className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg border-2 border-gray-200 shadow-xl overflow-hidden z-50"
                    style={{ animation: 'fadeSlideDown 0.15s ease-out' }}
                >
                    <div className="max-h-[360px] overflow-y-auto">
                        {suggestions.length > 0 ? (
                            <div className="py-1">
                                {suggestions.some(s => s.type === 'history') && (
                                    <div className="flex items-center justify-between px-4 pt-2 pb-1">
                                        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Recent Searches</p>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                clearHistory();
                                            }}
                                            className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                                        >
                                            Clear all
                                        </button>
                                    </div>
                                )}

                                {suggestions.filter(s => s.type === 'history').map((suggestion, idx) => {
                                    const globalIdx = suggestions.indexOf(suggestion);
                                    return (
                                        <button
                                            key={`history-${suggestion.id || idx}`}
                                            className={`w-full text-left px-4 py-2.5 flex items-center gap-3 transition-colors ${highlightedIndex === globalIdx ? 'bg-gray-100' : 'hover:bg-gray-50'
                                                }`}
                                            onClick={() => handleSuggestionClick(suggestion)}
                                            onMouseEnter={() => setHighlightedIndex(globalIdx)}
                                        >
                                            <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                            <span className="text-gray-800 truncate">{suggestion.text}</span>
                                        </button>
                                    );
                                })}

                                {suggestions.some(s => s.type === 'suggestion') && (
                                    <div className="px-4 pt-3 pb-1">
                                        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Suggested Topics</p>
                                    </div>
                                )}

                                {suggestions.filter(s => s.type === 'suggestion').map((suggestion, idx) => {
                                    const globalIdx = suggestions.indexOf(suggestion);
                                    return (
                                        <button
                                            key={`suggestion-${idx}`}
                                            className={`w-full text-left px-4 py-2.5 flex items-center gap-3 transition-colors ${highlightedIndex === globalIdx ? 'bg-gray-100' : 'hover:bg-gray-50'
                                                }`}
                                            onClick={() => handleSuggestionClick(suggestion)}
                                            onMouseEnter={() => setHighlightedIndex(globalIdx)}
                                        >
                                            <TrendingUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                            <div className="flex flex-col overflow-hidden">
                                                <span className="text-gray-800 truncate">{suggestion.text}</span>
                                                {suggestion.hint && (
                                                    <span className="text-[10px] text-gray-400 uppercase tracking-tight">{suggestion.hint}</span>
                                                )}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        ) : null}
                    </div>
                </div>
            )}

            <style>{`
        @keyframes fadeSlideDown {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div>
    );
};

export default SearchBar;
