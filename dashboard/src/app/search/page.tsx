"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import SearchBar from "@/components/SearchBar";
import PredictionList from "@/components/PredictionList";
import { SkeletonCard } from "@/components/SkeletonLoader";
import { getPredictions } from "@/lib/api";
import { Prediction } from "@/lib/types";

export default function SearchPage() {
  const [diseaseQuery, setDiseaseQuery] = useState("");
  const [searchTrigger, setSearchTrigger] = useState("");

  const {
    data: predictionRun,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["predictions", searchTrigger],
    queryFn: () => getPredictions(searchTrigger),
    enabled: !!searchTrigger,
  });

  const handleSearch = (query: string) => {
    setDiseaseQuery(query);
    setSearchTrigger(query);
  };

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h1 className="text-3xl font-bold mb-3">
          Find Drug Repurposing{" "}
          <span className="text-teal-400">Candidates</span>
        </h1>
        <p className="text-slate-400 max-w-xl mx-auto">
          Search for a disease to discover potential drug candidates ranked by
          our knowledge graph prediction model.
        </p>
      </motion.div>

      {/* Search Bar */}
      <div className="mb-12">
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      </div>

      {/* Results */}
      {isLoading && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-3 h-3 bg-teal-500 rounded-full animate-pulse" />
            <span className="text-sm text-slate-400">
              Analyzing knowledge graph...
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      )}

      {isError && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <span className="text-2xl">⚠️</span>
          </div>
          <h3 className="text-lg font-semibold text-red-400 mb-2">
            Search Failed
          </h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            {(error as Error)?.message ||
              "Could not fetch predictions. Please check the API connection and try again."}
          </p>
        </motion.div>
      )}

      {predictionRun && !isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold">
                Results for{" "}
                <span className="text-teal-400">{diseaseQuery}</span>
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {predictionRun.predictions.length} candidates ranked by
                prediction score
              </p>
            </div>
            <span className="text-xs text-slate-600 bg-navy-800 px-3 py-1.5 rounded-full border border-navy-700">
              Model: {predictionRun.model_version || "GAT-v1"}
            </span>
          </div>
          <PredictionList
            predictions={predictionRun.predictions}
            diseaseId={searchTrigger}
          />
        </motion.div>
      )}

      {/* Initial state */}
      {!searchTrigger && !isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center">
            <span className="text-3xl">🧬</span>
          </div>
          <h3 className="text-lg font-semibold text-slate-300 mb-2">
            Ready to Explore
          </h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Enter a disease name (e.g., &quot;Diabetes&quot;,
            &quot;Alzheimer&quot;) or a MONDO ID to discover potential drug
            repurposing candidates.
          </p>
        </motion.div>
      )}
    </div>
  );
}
