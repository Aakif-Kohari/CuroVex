"use client";

import { motion } from "framer-motion";

interface ExplanationToggleProps {
  activeMethod: "path_based" | "counterfactual";
  onToggle: (method: "path_based" | "counterfactual") => void;
}

const tabs = [
  {
    id: "path_based" as const,
    label: "Path-Based",
    description: "Meta-path reasoning",
  },
  {
    id: "counterfactual" as const,
    label: "Counterfactual",
    description: "Edge-masking fidelity",
  },
];

export default function ExplanationToggle({
  activeMethod,
  onToggle,
}: ExplanationToggleProps) {
  return (
    <div className="inline-flex bg-navy-800/80 backdrop-blur-sm border border-navy-700 rounded-xl p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onToggle(tab.id)}
          className="relative px-5 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200"
        >
          {activeMethod === tab.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute inset-0 bg-teal-500/20 border border-teal-500/30 rounded-lg"
              transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
            />
          )}
          <span
            className={`relative z-10 ${
              activeMethod === tab.id
                ? "text-teal-400"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </span>
        </button>
      ))}
    </div>
  );
}
