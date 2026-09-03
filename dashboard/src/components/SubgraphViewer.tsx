"use client";

import { useMemo } from "react";
import { Explanation } from "@/lib/types";

// Lazy import cytoscape to avoid SSR issues
let CytoscapeComponent: any = null;
if (typeof window !== "undefined") {
  try {
    CytoscapeComponent = require("react-cytoscapejs").default;
  } catch {
    // Will render fallback
  }
}

interface SubgraphViewerProps {
  explanation: Explanation;
}

const labelColors: Record<string, string> = {
  Drug: "#3b82f6", // blue
  Disease: "#ef4444", // red
  Gene: "#22c55e", // green
  Protein: "#a855f7", // purple
  Pathway: "#f97316", // orange
  SideEffect: "#eab308", // yellow
};

function getNodeColor(labels: string[]): string {
  for (const label of labels) {
    if (labelColors[label]) return labelColors[label];
  }
  return "#64748b"; // slate default
}

function getEdgeColor(fidelity?: number): string {
  if (fidelity === undefined || fidelity === null) return "#475569";
  const abs = Math.abs(fidelity);
  if (abs >= 0.5) return "#ef4444"; // red for high impact
  if (abs >= 0.2) return "#f97316"; // orange for medium
  return "#64748b"; // gray for low
}

function getEdgeWidth(fidelity?: number): number {
  if (fidelity === undefined || fidelity === null) return 2;
  return Math.max(1, Math.min(6, Math.abs(fidelity) * 8));
}

export default function SubgraphViewer({ explanation }: SubgraphViewerProps) {
  const elements = useMemo(() => {
    const { nodes, edges, masked_edges } = explanation.subgraph;
    if (!nodes || !edges) return [];

    // Build fidelity lookup for counterfactual edges
    const fidelityMap = new Map<string, number>();
    if (masked_edges) {
      for (const me of masked_edges) {
        fidelityMap.set(`${me.source_id}-${me.target_id}`, me.fidelity);
      }
    }

    const cyNodes = nodes.map((node) => ({
      data: {
        id: String(node.id),
        label: node.name || String(node.id),
        nodeLabels: node.labels || [],
      },
      style: {
        "background-color": getNodeColor(node.labels || []),
      },
    }));

    const cyEdges = edges.map((edge, idx) => {
      const key = `${edge.source_id}-${edge.target_id}`;
      const fidelity = fidelityMap.get(key);
      return {
        data: {
          id: `e${idx}`,
          source: String(edge.source_id),
          target: String(edge.target_id),
          label: edge.type || "",
          fidelity,
        },
        style: {
          "line-color": getEdgeColor(fidelity),
          "target-arrow-color": getEdgeColor(fidelity),
          width: getEdgeWidth(fidelity),
        },
      };
    });

    return [...cyNodes, ...cyEdges];
  }, [explanation]);

  const stylesheet = useMemo(
    () => [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "text-valign": "bottom" as const,
          "text-halign": "center" as const,
          "font-size": "10px",
          color: "#cbd5e1",
          "text-margin-y": 6,
          width: 30,
          height: 30,
          "border-width": 2,
          "border-color": "#1e293b",
        },
      },
      {
        selector: "edge",
        style: {
          label: "data(label)",
          "font-size": "8px",
          color: "#94a3b8",
          "text-rotation": "autorotate" as const,
          "curve-style": "bezier" as const,
          "target-arrow-shape": "triangle" as const,
        },
      },
    ],
    [],
  );

  if (!CytoscapeComponent || elements.length === 0) {
    return (
      <div className="h-96 bg-navy-800/50 border border-navy-700 rounded-2xl flex items-center justify-center">
        <p className="text-slate-500 text-sm">
          {elements.length === 0
            ? "No subgraph data available"
            : "Loading graph viewer..."}
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-[500px] bg-navy-800/30 border border-navy-700 rounded-2xl overflow-hidden">
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        layout={{ name: "cose", animate: true, animationDuration: 500 }}
        style={{ width: "100%", height: "100%" }}
        userPanningEnabled={true}
        userZoomingEnabled={true}
        boxSelectionEnabled={false}
      />
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-navy-900/90 backdrop-blur-sm border border-navy-700 rounded-lg p-3 text-xs">
        <p className="text-slate-400 font-medium mb-2">Node Types</p>
        <div className="grid grid-cols-3 gap-x-4 gap-y-1">
          {Object.entries(labelColors).map(([label, color]) => (
            <div key={label} className="flex items-center gap-1.5">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-slate-400">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
