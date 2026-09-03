"use client";

interface FidelityBadgeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
}

export default function FidelityBadge({
  score,
  size = "md",
}: FidelityBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <div className="flex items-center gap-2 text-slate-500 text-sm">
        <div className="w-8 h-8 rounded-full border-2 border-slate-700 flex items-center justify-center">
          <span className="text-xs">—</span>
        </div>
        <span>N/A</span>
      </div>
    );
  }

  const clampedScore = Math.max(0, Math.min(1, Math.abs(score)));
  const percentage = Math.round(clampedScore * 100);

  // Color coding: high (green), medium (yellow), low (red)
  let color: string;
  let bgColor: string;
  let label: string;
  if (clampedScore >= 0.7) {
    color = "text-emerald-400";
    bgColor = "stroke-emerald-400";
    label = "High";
  } else if (clampedScore >= 0.3) {
    color = "text-amber-400";
    bgColor = "stroke-amber-400";
    label = "Medium";
  } else {
    color = "text-red-400";
    bgColor = "stroke-red-400";
    label = "Low";
  }

  const sizeConfig = {
    sm: {
      container: "w-8 h-8",
      text: "text-[10px]",
      radius: 12,
      strokeWidth: 2,
    },
    md: { container: "w-14 h-14", text: "text-sm", radius: 22, strokeWidth: 3 },
    lg: { container: "w-20 h-20", text: "text-lg", radius: 32, strokeWidth: 4 },
  };

  const cfg = sizeConfig[size];
  const circumference = 2 * Math.PI * cfg.radius;
  const dashoffset = circumference * (1 - clampedScore);

  return (
    <div
      className="flex items-center gap-3"
      title={`Fidelity: ${score.toFixed(4)} — ${label} impact`}
    >
      <div
        className={`relative ${cfg.container} flex items-center justify-center`}
      >
        <svg
          className="transform -rotate-90 w-full h-full"
          viewBox={`0 0 ${(cfg.radius + cfg.strokeWidth) * 2} ${(cfg.radius + cfg.strokeWidth) * 2}`}
        >
          <circle
            cx={cfg.radius + cfg.strokeWidth}
            cy={cfg.radius + cfg.strokeWidth}
            r={cfg.radius}
            className="stroke-navy-700"
            fill="none"
            strokeWidth={cfg.strokeWidth}
          />
          <circle
            cx={cfg.radius + cfg.strokeWidth}
            cy={cfg.radius + cfg.strokeWidth}
            r={cfg.radius}
            className={bgColor}
            fill="none"
            strokeWidth={cfg.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
            style={{ transition: "stroke-dashoffset 0.8s ease-in-out" }}
          />
        </svg>
        <span className={`absolute ${cfg.text} font-bold ${color}`}>
          {percentage}
        </span>
      </div>
      {size !== "sm" && (
        <div>
          <p className={`${cfg.text} font-semibold ${color}`}>
            {label} Fidelity
          </p>
          <p className="text-xs text-slate-500">{score.toFixed(4)}</p>
        </div>
      )}
    </div>
  );
}
