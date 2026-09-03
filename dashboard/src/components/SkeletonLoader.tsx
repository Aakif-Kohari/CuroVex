"use client";

interface SkeletonProps {
  className?: string;
}

export function SkeletonCard({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-navy-800/50 border border-navy-700 rounded-2xl p-6 ${className}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 bg-navy-700 rounded-xl" />
        <div className="w-20 h-6 bg-navy-700 rounded-full" />
      </div>
      <div className="space-y-3">
        <div className="h-5 bg-navy-700 rounded w-3/4" />
        <div className="h-4 bg-navy-700 rounded w-1/2" />
      </div>
      <div className="flex gap-2 mt-4">
        <div className="w-24 h-6 bg-navy-700 rounded-full" />
        <div className="w-20 h-6 bg-navy-700 rounded-full" />
      </div>
    </div>
  );
}

export function SkeletonGraph({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-navy-800/50 border border-navy-700 rounded-2xl p-6 ${className}`}
    >
      <div className="h-96 bg-navy-700 rounded-xl flex items-center justify-center">
        <div className="text-slate-600 text-sm">Loading graph...</div>
      </div>
    </div>
  );
}

export function SkeletonText({
  lines = 3,
  className = "",
}: SkeletonProps & { lines?: number }) {
  return (
    <div className={`animate-pulse space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-navy-700 rounded"
          style={{ width: `${85 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
