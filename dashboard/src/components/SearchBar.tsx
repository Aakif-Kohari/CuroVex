"use client";

import { useState, useCallback } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export default function SearchBar({
  onSearch,
  isLoading = false,
}: SearchBarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) {
        onSearch(query.trim());
      }
    },
    [query, onSearch],
  );

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="relative group">
        <div className="absolute inset-0 bg-teal-500/20 rounded-2xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
        <div className="relative flex items-center bg-navy-800/80 backdrop-blur-sm border border-navy-700 group-focus-within:border-teal-500/50 rounded-2xl overflow-hidden transition-all duration-300 shadow-lg group-focus-within:shadow-teal-500/10">
          <div className="pl-5 text-slate-400">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by disease name or MONDO ID (e.g. Diabetes, MONDO:0005015)"
            className="flex-1 bg-transparent px-4 py-4 text-slate-100 placeholder-slate-500 focus:outline-none text-base"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="m-2 px-6 py-2.5 bg-gradient-to-r from-teal-500 to-teal-400 hover:from-teal-400 hover:to-teal-300 text-navy-900 font-semibold rounded-xl transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-navy-900/30 border-t-navy-900 rounded-full animate-spin" />
                Searching
              </span>
            ) : (
              "Search"
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
