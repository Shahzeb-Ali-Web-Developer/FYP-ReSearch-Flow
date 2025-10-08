import React, { useState } from 'react';
import { Search, BookOpen, Users } from 'lucide-react';
import AnimatedNetworkBackground from "../components/AnimatedNetworkBackground";

const SearchBar = () => {
  const [searchValue, setSearchValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="relative w-full max-w-4xl">
      <div
        className={`relative flex items-center bg-white/10 backdrop-blur-md rounded-full border transition-all duration-300 ${
          isFocused ? 'border-blue-400 shadow-lg shadow-purple-500/25' : 'border-white/20'
        }`}
      >
        <input
          type="text"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="e.g., Deep Learning in Healthcare"
          className="w-full px-6 py-4 bg-transparent text-white placeholder-gray-400 focus:outline-none text-lg"
        />
        <button className="mr-2 p-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full hover:from-purple-700 hover:to-blue-700 transition-all duration-300 hover:scale-105">
          <Search className="w-6 h-6 text-white" />
        </button>
      </div>
      {isFocused && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 overflow-hidden z-10">
          <div className="p-2">
            {['Machine Learning in Finance', 'Quantum Computing Applications', 'AI Ethics Research'].map((s, i) => (
              <button key={i} className="w-full text-left px-4 py-3 text-white hover:bg-white/10 rounded-xl transition-colors" onClick={() => { setSearchValue(s); setIsFocused(false); }}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="group p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 hover:border-purple-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10">
    <div className="flex items-center mb-4">
      <div className="p-3 bg-purple-600  rounded-full mr-4 group-hover:scale-110 transition-transform duration-300">
        <Icon className="w-6 h-6 text-white" />
      </div>
      <h3 className="text-xl font-semibold text-white">{title}</h3>
    </div>
    <p className="text-gray-300 leading-relaxed">{description}</p>
  </div>
);

export default function Home() {
  

  return (
    <div className="min-h-screen relative viga-font overflow-hidden">
      <AnimatedNetworkBackground />

      <div className="relative z-10 min-h-screen flex flex-col">
        

        <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <div className="my-8 mx-auto ">
            <h1 className="text-3xl lg:text-4xl text-white my-6 leading-tight">
              Find, Summarize &{' '}
              <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                Visualize
              </span>{' '}
              Research Papers Instantly
            </h1>

            <p className="text-xl text-gray-300 mb-12 mx-auto leading-relaxed">
              Enter a topic to get scholarly articles, summaries, and citation networks – all in one place
            </p>

            <div className="mb-16 flex justify-center">
              <SearchBar />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">10M+</div>
                <div className="text-gray-400">Research Papers</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">500K+</div>
                <div className="text-gray-400">Active Researchers</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">99.9%</div>
                <div className="text-gray-400">Uptime</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <FeatureCard icon={Search} title="Smart Search" description="AI-powered search across millions of research papers with semantic understanding and relevance ranking." />
              <FeatureCard icon={BookOpen} title="Auto Summarization" description="Get key insights and summaries of complex research papers in seconds using advanced NLP." />
              <FeatureCard icon={Users} title="Citation Networks" description="Visualize connections between papers, authors, and research topics with interactive graphs." />
            </div>
          </div>
        </main>

        <footer className="p-6 text-center text-gray-400">
          <div className="flex flex-col md:flex-row items-center justify-between max-w-6xl mx-auto">
            <p>&copy; 2024 ReSearch Flow. All rights reserved.</p>
            <div className="flex items-center space-x-6 mt-4 md:mt-0">
              <a href="#" className="hover:text-green-400 transition-colors">Privacy</a>
              <a href="#" className="hover:text-green-400 transition-colors">Terms</a>
              <a href="#" className="hover:text-green-400 transition-colors">Support</a>
            </div>
          </div>
        </footer>
      </div>

      
    </div>
  );
}
