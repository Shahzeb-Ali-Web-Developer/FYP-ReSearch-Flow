import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, BookOpen, Users } from 'lucide-react';

const SearchBar = ({ onSearch }) => {
  const [searchValue, setSearchValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSearch = () => {
    if (searchValue.trim()) {
      onSearch(searchValue.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const suggestedTopics = [
    'Machine Learning in Finance',
    'Quantum Computing Applications',
    'AI Ethics Research',
    'Deep Learning in Healthcare',
    'Natural Language Processing'
  ];

  return (
    <div className="relative w-full max-w-4xl">
      <div
        className={`relative flex items-center bg-white border-2 rounded-lg transition-all duration-300 ${
          isFocused ? 'border-black shadow-lg' : 'border-gray-300'
        }`}
      >
        <input
          type="text"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., Deep Learning in Healthcare"
          className="w-full px-6 py-4 bg-transparent text-black placeholder-gray-400 focus:outline-none text-lg"
        />
        <button 
          onClick={handleSearch}
          disabled={!searchValue.trim()}
          className="mr-2 p-3 bg-black rounded-lg hover:bg-gray-800 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Search className="w-6 h-6 text-white" />
        </button>
      </div>
      
      {isFocused && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg border-2 border-gray-300 shadow-lg overflow-hidden z-10">
          <div className="p-2">
            <p className="px-4 py-2 text-gray-500 text-sm">Suggested Topics:</p>
            {suggestedTopics.map((topic, i) => (
              <button 
                key={i} 
                className="w-full text-left px-4 py-3 text-black hover:bg-gray-100 rounded-lg transition-colors" 
                onClick={() => {
                  setSearchValue(topic);
                  setIsFocused(false);
                  setTimeout(() => onSearch(topic), 100);
                }}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="group p-6 bg-gray-50 rounded-lg border border-gray-300 hover:border-black transition-all duration-300 hover:shadow-lg">
    <div className="flex items-center mb-4">
      <div className="p-3 bg-black rounded-lg mr-4 group-hover:scale-110 transition-transform duration-300">
        <Icon className="w-6 h-6 text-white" />
      </div>
      <h3 className="text-xl font-semibold text-black">{title}</h3>
    </div>
    <p className="text-gray-600 leading-relaxed">{description}</p>
  </div>
);

export default function Home() {
  const navigate = useNavigate();

  const handleSearch = (topic) => {
    navigate(`/results?topic=${encodeURIComponent(topic)}`);
  };

  return (
    <div className="min-h-screen relative viga-font overflow-hidden bg-white">
      <div className="relative z-10 min-h-screen flex flex-col">
        <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <div className="my-8 mx-auto">
            <h1 className="text-3xl lg:text-4xl text-black my-6 leading-tight">
              Find, Summarize & Visualize Research Papers Instantly
            </h1>

            <p className="text-xl text-gray-600 mb-12 mx-auto leading-relaxed">
              Enter a topic to get scholarly articles, summaries, and citation networks – all in one place
            </p>

            <div className="mb-16 flex justify-center">
              <SearchBar onSearch={handleSearch} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
              <div className="text-center">
                <div className="text-3xl font-bold text-black mb-2">10M+</div>
                <div className="text-gray-600">Research Papers</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-black mb-2">500K+</div>
                <div className="text-gray-600">Active Researchers</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-black mb-2">99.9%</div>
                <div className="text-gray-600">Uptime</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <FeatureCard 
                icon={Search} 
                title="Smart Search" 
                description="AI-powered search across millions of research papers with semantic understanding and relevance ranking." 
              />
              <FeatureCard 
                icon={BookOpen} 
                title="Auto Summarization" 
                description="Get key insights and summaries of complex research papers in seconds using advanced NLP." 
              />
              <FeatureCard 
                icon={Users} 
                title="Citation Networks" 
                description="Visualize connections between papers, authors, and research topics with interactive graphs." 
              />
            </div>
          </div>
        </main>

      </div>
    </div>
  );
}