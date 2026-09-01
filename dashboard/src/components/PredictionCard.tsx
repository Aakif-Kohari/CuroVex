'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Trophy } from 'lucide-react';
import { Prediction } from '@/lib/types';
import ValidationBadge from './ValidationBadge';

interface PredictionCardProps {
  prediction: Prediction;
  index: number;
  diseaseId: string;
}

const rankColors: Record<number, { bg: string; border: string; icon: string }> = {
  1: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: 'text-amber-400' },
  2: { bg: 'bg-slate-300/10', border: 'border-slate-400/30', icon: 'text-slate-300' },
  3: { bg: 'bg-orange-600/10', border: 'border-orange-600/30', icon: 'text-orange-500' },
};

export default function PredictionCard({ prediction, index, diseaseId }: PredictionCardProps) {
  const rankStyle = rankColors[prediction.rank] || {
    bg: 'bg-navy-700/50',
    border: 'border-navy-600',
    icon: 'text-slate-500',
  };

  const scorePercent = Math.min(100, Math.max(0, prediction.score * 100));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Link href={`/explanation/${prediction.id}?disease_id=${diseaseId}`}>
        <div className="group relative p-5 rounded-2xl bg-navy-800/60 backdrop-blur-sm border border-navy-700 hover:border-teal-500/40 transition-all duration-300 cursor-pointer hover:shadow-lg hover:shadow-teal-500/5 hover:-translate-y-0.5">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl ${rankStyle.bg} border ${rankStyle.border} flex items-center justify-center`}>
                {prediction.rank <= 3 ? (
                  <Trophy className={`w-4 h-4 ${rankStyle.icon}`} />
                ) : (
                  <span className="text-sm font-bold text-slate-400">#{prediction.rank}</span>
                )}
              </div>
              <div>
                <h3 className="font-semibold text-white group-hover:text-teal-400 transition-colors">
                  {prediction.drug_name || `Drug ${prediction.drug_id}`}
                </h3>
                <p className="text-xs text-slate-500">ID: {prediction.drug_id}</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-teal-400 group-hover:translate-x-1 transition-all" />
          </div>

          {/* Score bar */}
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-500">Prediction Score</span>
              <span className="text-teal-400 font-mono font-medium">{prediction.score.toFixed(4)}</span>
            </div>
            <div className="h-1.5 bg-navy-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-teal-500 to-blue-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${scorePercent}%` }}
                transition={{ delay: index * 0.05 + 0.3, duration: 0.6, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Validation badges placeholder — populated when data is available */}
          <ValidationBadge hasClinicalTrial={false} hasLiterature={false} />
        </div>
      </Link>
    </motion.div>
  );
}
