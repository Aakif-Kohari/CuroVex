'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, FlaskConical, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Trial {
  nctId: string;
  title: string;
  status: string;
  phase: string;
}

interface Article {
  pmid: string;
  title: string;
  authors: string;
  pub_date: string;
  source: string;
}

interface EvidencePanelProps {
  trials?: Trial[];
  articles?: Article[];
  evidenceUrl?: string | null;
}

export default function EvidencePanel({ trials = [], articles = [], evidenceUrl }: EvidencePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasEvidence = trials.length > 0 || articles.length > 0;

  if (!hasEvidence) return null;

  return (
    <div className="mt-3 border border-navy-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-navy-800/50 hover:bg-navy-800 transition-colors text-sm"
      >
        <span className="text-slate-300 font-medium">
          Supporting Evidence ({trials.length + articles.length} sources)
        </span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-slate-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-500" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-3 space-y-4 bg-navy-900/50">
              {/* Clinical Trials */}
              {trials.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-emerald-400 mb-2">
                    <FlaskConical className="w-4 h-4" />
                    Clinical Trials ({trials.length})
                  </h4>
                  <div className="space-y-2">
                    {trials.map((trial) => (
                      <div key={trial.nctId} className="text-xs bg-navy-800/50 rounded-lg p-3 border border-navy-700">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-slate-300 leading-relaxed">{trial.title}</p>
                          <a
                            href={`https://clinicaltrials.gov/study/${trial.nctId}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-teal-400 hover:text-teal-300 shrink-0"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                        <div className="flex gap-3 mt-2 text-slate-500">
                          <span className="font-mono">{trial.nctId}</span>
                          <span>Phase: {trial.phase}</span>
                          <span>Status: {trial.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* PubMed Articles */}
              {articles.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-2 text-sm font-semibold text-blue-400 mb-2">
                    <BookOpen className="w-4 h-4" />
                    Literature ({articles.length})
                  </h4>
                  <div className="space-y-2">
                    {articles.map((article) => (
                      <div key={article.pmid} className="text-xs bg-navy-800/50 rounded-lg p-3 border border-navy-700">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-slate-300 leading-relaxed">{article.title}</p>
                          <a
                            href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-teal-400 hover:text-teal-300 shrink-0"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                        <div className="flex gap-3 mt-2 text-slate-500">
                          <span>{article.authors}</span>
                          <span>{article.pub_date}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
