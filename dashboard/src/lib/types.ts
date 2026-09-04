export interface Prediction {
  id: string;
  drug_id: string;
  disease_id: string;
  drug_name?: string;
  score: number;
  rank: number;
}

export interface PredictionRun {
  id: string;
  disease_id: string;
  model_version: string;
  started_at: string;
  completed_at: string | null;
  predictions: Prediction[];
}

export interface PathNode {
  id: number;
  name: string;
  labels: string[];
}

export interface PathEdge {
  source_id: number;
  target_id: number;
  type: string;
}

export interface MaskedEdge {
  source_id: number;
  target_id: number;
  edge_type: string;
  score_delta: number;
  fidelity: number;
}

export interface Explanation {
  id: string;
  prediction_id: string;
  method: 'path_based' | 'counterfactual';
  fidelity_score: number | null;
  subgraph: {
    nodes: PathNode[];
    edges: PathEdge[];
    meta_path_pattern?: string;
    masked_edges?: MaskedEdge[];
  };
}

export interface ExplanationResponse {
  prediction_id: string;
  explanations: Explanation[];
}

export interface ValidationResult {
  id: string;
  prediction_id: string;
  has_clinical_trial: boolean;
  has_literature_support: boolean;
  evidence_url: string | null;
}
