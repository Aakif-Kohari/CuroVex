"use client";

import { Prediction } from "@/lib/types";
import PredictionCard from "./PredictionCard";

interface PredictionListProps {
  predictions: Prediction[];
  diseaseId: string;
}

export default function PredictionList({
  predictions,
  diseaseId,
}: PredictionListProps) {
  if (predictions.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-navy-800 border border-navy-700 flex items-center justify-center">
          <span className="text-2xl">🔬</span>
        </div>
        <h3 className="text-lg font-semibold text-slate-300 mb-2">
          No predictions found
        </h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          No drug candidates were found for this disease query. Try a different
          disease name or MONDO ID.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {predictions.map((prediction, index) => (
        <PredictionCard
          key={prediction.id}
          prediction={prediction}
          index={index}
          diseaseId={diseaseId}
        />
      ))}
    </div>
  );
}
