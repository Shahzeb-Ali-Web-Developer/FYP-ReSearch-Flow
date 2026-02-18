import React, { useState, useMemo } from 'react';
import { FileText, List, AlignLeft, ChevronDown, ChevronRight } from 'lucide-react';

/**
 * FormattedPaperContent - Renders structured PDF content with proper formatting.
 * Accepts blocks from the backend structured extraction endpoint.
 * Each block has { type: "heading"|"subheading"|"body", text: "..." }
 * 
 * Features:
 * - Headings rendered as styled section headers
 * - Subheadings rendered as subsection headers
 * - Body text rendered as properly spaced paragraphs
 * - References section detected and styled distinctly
 * - Table of contents generated from headings/subheadings
 * - Toggle between formatted and raw view
 */

// Common academic section patterns for detection
const REFERENCE_PATTERNS = /^(references|bibliography|works cited|cited literature|literature cited)$/i;
const KNOWN_SECTIONS = /^(abstract|introduction|background|related work|methodology|methods|materials and methods|results|discussion|conclusion|conclusions|acknowledgements?|appendix|supplementary|funding|declarations?|data availability|author contributions?)$/i;

export default function FormattedPaperContent({ blocks, rawText, totalCharacters }) {
    const [viewMode, setViewMode] = useState('formatted'); // 'formatted' | 'raw'
    const [tocOpen, setTocOpen] = useState(true);

    // Build table of contents from heading/subheading blocks
    const tableOfContents = useMemo(() => {
        if (!blocks || blocks.length === 0) return [];
        return blocks
            .map((block, index) => {
                if (block.type === 'heading' || block.type === 'subheading') {
                    return {
                        id: `section-${index}`,
                        text: block.text.length > 80 ? block.text.substring(0, 80) + '…' : block.text,
                        type: block.type,
                        index,
                    };
                }
                return null;
            })
            .filter(Boolean);
    }, [blocks]);

    // Detect if a block is in the references section
    const referenceSectionStart = useMemo(() => {
        if (!blocks) return -1;
        return blocks.findIndex(
            (block) =>
                (block.type === 'heading' || block.type === 'subheading') &&
                REFERENCE_PATTERNS.test(block.text.trim())
        );
    }, [blocks]);

    // Compute word count from blocks
    const wordCount = useMemo(() => {
        if (!blocks) return 0;
        return blocks.reduce((count, block) => count + block.text.split(/\s+/).length, 0);
    }, [blocks]);

    const scrollToSection = (id) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    // Render a single structured block
    const renderBlock = (block, index) => {
        const isInReferences = referenceSectionStart !== -1 && index > referenceSectionStart;
        const sectionId = `section-${index}`;
        const isKnownSection = KNOWN_SECTIONS.test(block.text.trim());

        if (block.type === 'heading') {
            return (
                <h2
                    key={index}
                    id={sectionId}
                    className={`text-lg font-bold text-gray-900 mt-8 mb-3 pb-2 border-b-2 scroll-mt-4 ${isKnownSection ? 'border-blue-400 text-blue-900' : 'border-gray-200'
                        }`}
                >
                    {block.text}
                </h2>
            );
        }

        if (block.type === 'subheading') {
            // Check if this is the References heading
            if (REFERENCE_PATTERNS.test(block.text.trim())) {
                return (
                    <h3
                        key={index}
                        id={sectionId}
                        className="text-base font-bold text-gray-800 mt-8 mb-3 pb-2 border-b-2 border-amber-400 scroll-mt-4"
                    >
                        📚 {block.text}
                    </h3>
                );
            }

            return (
                <h3
                    key={index}
                    id={sectionId}
                    className={`text-base font-semibold mt-6 mb-2 scroll-mt-4 ${isKnownSection ? 'text-blue-800' : 'text-gray-800'
                        }`}
                >
                    {block.text}
                </h3>
            );
        }

        // Body text
        if (isInReferences) {
            // References get a special compact, indented style
            return (
                <p
                    key={index}
                    className="text-sm text-gray-600 leading-relaxed pl-4 py-1.5 border-l-2 border-gray-200 mb-2 hover:border-amber-400 hover:bg-amber-50/30 transition-colors"
                >
                    {block.text}
                </p>
            );
        }

        return (
            <p
                key={index}
                className="text-sm text-gray-700 leading-[1.8] mb-4 text-justify"
            >
                {block.text}
            </p>
        );
    };

    // Raw text view
    const renderRawView = () => {
        const text = rawText || (blocks ? blocks.map((b) => b.text).join('\n\n') : '');
        return (
            <div className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed p-4">
                {text}
            </div>
        );
    };

    if (!blocks || blocks.length === 0) {
        return (
            <div className="p-4 text-center text-gray-500">
                <FileText className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>No structured content available</p>
            </div>
        );
    }

    return (
        <div className="border-t-2 border-gray-300 bg-gray-50">
            {/* Header bar */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
                <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-black" />
                    <h3 className="text-base font-semibold text-black">Full Paper Content</h3>
                </div>
                <div className="flex items-center gap-3">
                    {/* Stats */}
                    <span className="text-xs text-gray-500 font-medium hidden sm:inline">
                        {(totalCharacters || 0).toLocaleString()} chars · {wordCount.toLocaleString()} words · {blocks.length} sections
                    </span>
                    {/* View toggle */}
                    <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
                        <button
                            onClick={() => setViewMode('formatted')}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'formatted'
                                    ? 'bg-white text-black shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <AlignLeft className="w-3.5 h-3.5" />
                            Formatted
                        </button>
                        <button
                            onClick={() => setViewMode('raw')}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${viewMode === 'raw'
                                    ? 'bg-white text-black shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <FileText className="w-3.5 h-3.5" />
                            Raw
                        </button>
                    </div>
                </div>
            </div>

            {viewMode === 'raw' ? (
                <div className="bg-white border-2 border-gray-200 rounded-lg m-4 max-h-[700px] overflow-y-auto shadow-inner">
                    {renderRawView()}
                </div>
            ) : (
                <div className="flex">
                    {/* Table of Contents sidebar */}
                    {tableOfContents.length > 2 && (
                        <div className="w-64 flex-shrink-0 border-r border-gray-200 bg-white hidden lg:block">
                            <div className="sticky top-0 p-3">
                                <button
                                    onClick={() => setTocOpen(!tocOpen)}
                                    className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2 hover:text-black transition-colors w-full"
                                >
                                    <List className="w-4 h-4" />
                                    <span>Contents</span>
                                    {tocOpen ? (
                                        <ChevronDown className="w-3.5 h-3.5 ml-auto" />
                                    ) : (
                                        <ChevronRight className="w-3.5 h-3.5 ml-auto" />
                                    )}
                                </button>
                                {tocOpen && (
                                    <nav className="space-y-0.5 max-h-[600px] overflow-y-auto">
                                        {tableOfContents.map((item) => (
                                            <button
                                                key={item.id}
                                                onClick={() => scrollToSection(item.id)}
                                                className={`block w-full text-left text-xs py-1.5 px-2 rounded hover:bg-gray-100 transition-colors truncate ${item.type === 'heading'
                                                        ? 'font-medium text-gray-800'
                                                        : 'text-gray-500 pl-4'
                                                    }`}
                                                title={item.text}
                                            >
                                                {item.text}
                                            </button>
                                        ))}
                                    </nav>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Main content */}
                    <div className="flex-1 max-h-[700px] overflow-y-auto">
                        <div className="max-w-3xl mx-auto px-6 py-6">
                            {blocks.map((block, index) => renderBlock(block, index))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
