'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

import ExplanationToggle from '@/components/ExplanationToggle';
import SubgraphViewer from '@/components/SubgraphViewer';
import FidelityBadge from '@/components/FidelityBadge';
import { SkeletonGraph } from '@/components/SkeletonLoader';
import { getExplanations, getValidation } from '@/lib/api';
import { Explanation } from '@/lib/types';

export default function ExplanationPage() {
  const params = useParams();
  const predictionId = params.predictionId as string;
  const [activeMethod, setActiveMethod] = useState<'path_based' | 'counterfactual'>('counterfactual');

  const {
    data: explanationData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['explanations', predictionId],
    queryFn: () => getExplanations(predictionId),
    enabled: !!predictionId,
  });

  const { data: validationData } = useQuery({
    queryKey: ['validation', predictionId],
    queryFn: () => getValidation(predictionId),
    enabled: !!predictionId,
  });

  const activeExplanation: Explanation | undefined = explanationData?.explanations?.find(
    (e) => e.method === activeMethod
  );

  const otherExplanation: Explanation | undefined = explanationData?.explanations?.find(
    (e) => e.method !== activeMethod
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back nav */}
      <Link
        href="/search"
        className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-teal-400 transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Results
      </Link>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-2xl font-bold mb-2">
          Explanation for Prediction{' '}
          <span className="text-teal-400 font-mono text-lg">
            {predictionId.slice(0, 8)}...
          </span>
        </h1>
        <p className="text-slate-400 text-sm">
          Compare path-based and counterfactual explanations for this drug-disease prediction.
        </p>
      </motion.div>

      {/* Toggle */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <ExplanationToggle activeMethod={activeMethod} onToggle={setActiveMethod} />
        {activeExplanation && (
          <FidelityBadge score={activeExplanation.fidelity_score} size="md" />
        )}
      </div>

      {/* Loading */}
      {isLoading && <SkeletonGraph />}

      {/* Error */}
      {isError && (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <span className="text-2xl">⚠️</span>
          </div>
          <h3 className="text-lg font-semibold text-red-400 mb-2">Failed to load explanations</h3>
          <p className="text-sm text-slate-500">
            Could not retrieve explanation data for this prediction.
          </p>
        </div>
      )}

      {/* Explanation Content */}
      {activeExplanation && (
        <motion.div
          key={activeMethod}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          {/* Graph Visualization */}
          <SubgraphViewer explanation={activeExplanation} />

          {/* Method details */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Active method info */}
            <div className="bg-navy-800/50 border border-navy-700 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-3 text-teal-400">
                {activeMethod === 'path_based' ? 'Path-Based Reasoning' : 'Counterfactual Analysis'}
              </h3>
              <p className="text-sm text-slate-400 mb-4">
                {activeMethod === 'path_based'
                  ? 'Shows the meta-paths connecting the drug to the disease in the knowledge graph. Paths with higher support counts indicate stronger biological reasoning.'
                  : 'Tests whether each explanation edge actually matters by removing it and measuring the prediction score change. High fidelity means the edge is critical to the prediction.'}
              </p>

              {activeMethod === 'counterfactual' && activeExplanation.subgraph.masked_edges && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-slate-300 mb-2">
                    Top Impact Edges ({activeExplanation.subgraph.masked_edges.length} analyzed)
                  </h4>
                  <div className="max-h-60 overflow-y-auto space-y-1.5 pr-2">
                    {activeExplanation.subgraph.masked_edges.slice(0, 10).map((edge, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between text-xs bg-navy-900/50 rounded-lg px-3 py-2 border border-navy-700"
                      >
                        <span className="text-slate-400 font-mono">
                          {edge.source_id} → {edge.target_id}
                        </span>
                        <span className="text-slate-500">{edge.edge_type}</span>
                        <span
                          className={`font-mono font-medium ${
                            Math.abs(edge.fidelity) >= 0.3
                              ? 'text-red-400'
                              : Math.abs(edge.fidelity) >= 0.1
                              ? 'text-amber-400'
                              : 'text-slate-500'
                          }`}
                        >
                          {edge.fidelity > 0 ? '+' : ''}
                          {edge.fidelity.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeMethod === 'path_based' && activeExplanation.subgraph.meta_path_pattern && (
                <div className="bg-navy-900/50 rounded-lg p-3 border border-navy-700">
                  <p className="text-xs font-mono text-teal-400">
                    {activeExplanation.subgraph.meta_path_pattern}
                  </p>
                </div>
              )}
            </div>

            {/* Comparison panel */}
            <div className="bg-navy-800/50 border border-navy-700 rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-3">Method Comparison</h3>
              <div className="space-y-4">
                {explanationData?.explanations?.map((exp) => (
                  <div
                    key={exp.method}
                    className={`p-4 rounded-xl border transition-colors cursor-pointer ${
                      exp.method === activeMethod
                        ? 'bg-teal-500/5 border-teal-500/30'
                        : 'bg-navy-900/30 border-navy-700 hover:border-navy-600'
                    }`}
                    onClick={() => setActiveMethod(exp.method)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">
                          {exp.method === 'path_based' ? 'Path-Based' : 'Counterfactual'}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {exp.method === 'path_based'
                            ? 'Connection paths in the graph'
                            : 'Edge removal impact analysis'}
                        </p>
                      </div>
                      <FidelityBadge score={exp.fidelity_score} size="sm" />
                    </div>
                  </div>
                ))}
              </div>

              {/* Validation status */}
              {validationData && (
                <div className="mt-6 pt-4 border-t border-navy-700">
                  <h4 className="text-sm font-medium text-slate-300 mb-3">External Validation</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          validationData.has_clinical_trial ? 'bg-emerald-400' : 'bg-slate-600'
                        }`}
                      />
                      <span className="text-slate-400">
                        {validationData.has_clinical_trial
                          ? 'Clinical trial found'
                          : 'No clinical trial found'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          validationData.has_literature_support ? 'bg-blue-400' : 'bg-slate-600'
                        }`}
                      />
                      <span className="text-slate-400">
                        {validationData.has_literature_support
                          ? 'Supporting literature found'
                          : 'No supporting literature'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* No explanations found */}
      {!isLoading && !isError && !activeExplanation && (
        <div className="text-center py-16">
          <h3 className="text-lg font-semibold text-slate-300 mb-2">No Explanations Available</h3>
          <p className="text-sm text-slate-500">
            Explanations have not been generated yet for this prediction.
          </p>
        </div>
      )}
    </div>
  );
}
