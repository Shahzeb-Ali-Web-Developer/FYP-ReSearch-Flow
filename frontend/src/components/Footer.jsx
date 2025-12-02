import React from "react";

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white mt-8">
      <div className="max-w-7xl mx-auto px-4 py-8 text-sm text-gray-600 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h2 className="text-base font-semibold text-black mb-2">ReSearch Flow</h2>
          <p className="leading-relaxed text-gray-600">
            AI-powered assistant to explore, understand, and organize research literature using OpenAlex.
          </p>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wide text-gray-500 uppercase mb-3">Product</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:text-black">Overview</a></li>
            <li><a href="#" className="hover:text-black">Citation mesh</a></li>
            <li><a href="#" className="hover:text-black">AI summaries</a></li>
            <li><a href="#" className="hover:text-black">API</a></li>
          </ul>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wide text-gray-500 uppercase mb-3">Resources</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:text-black">Documentation</a></li>
            <li><a href="#" className="hover:text-black">Changelog</a></li>
            <li><a href="#" className="hover:text-black">FAQ</a></li>
          </ul>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wide text-gray-500 uppercase mb-3">Connect</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:text-black">Contact</a></li>
            <li><a href="#" className="hover:text-black">GitHub</a></li>
            <li><a href="#" className="hover:text-black">Twitter / X</a></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-gray-200 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col md:flex-row items-center justify-between text-xs text-gray-500">
          <p>
            &copy; {new Date().getFullYear()} ReSearch Flow. Built as an academic project.
          </p>
          <div className="flex items-center gap-4 mt-2 md:mt-0">
            <a href="#" className="hover:text-black">Privacy</a>
            <a href="#" className="hover:text-black">Terms</a>
          </div>
        </div>
      </div>
    </footer>
  );
}