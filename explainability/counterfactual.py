"""Counterfactual edge-masking explanations for drug-disease predictions.

The novel contribution of CuroVex: for a given (drug_id, disease_id) prediction,
masks one graph edge at a time from the local subgraph, re-runs the GAT model,
and measures how much the prediction score changes (fidelity). Edges whose
removal collapses the prediction are the ones that actually mattered — this is
a testable claim, not just a plausible-looking path.

Usage:
    python counterfactual.py 0 1
    python counterfactual.py 0 1 --max-hops 2 --max-edges 50
"""

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import torch

# Add parent dirs so we can import ml-core and explainability modules
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "ml-core"))

from graph_utils import (
    build_pyg_data,
    get_default_csv_paths,
    get_node_id_maps,
    load_triples_from_csv,
)
from train_gat import GATLinkPredictor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MaskedEdgeResult:
    """Result of masking a single edge and re-running the model."""

    source_id: int
    target_id: int
    edge_type: str
    original_score: float
    masked_score: float
    score_delta: float  # original - masked (positive = edge mattered)
    fidelity: float  # score_delta / |original_score|


@dataclass
class CounterfactualExplanation:
    """Complete counterfactual explanation for a drug-disease prediction."""

    drug_id: int
    disease_id: int
    original_score: float
    masked_edges: list[MaskedEdgeResult] = field(default_factory=list)
    overall_fidelity: float = 0.0  # mean fidelity across all masked edges
    sparsity: float = 0.0  # fraction of edges with fidelity > threshold
    subgraph: dict = field(default_factory=dict)  # JSON-serializable for frontend


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def extract_local_subgraph(
    node_ids: set[int],
    edge_index: torch.Tensor,
    edge_types: torch.Tensor | None,
    id_to_label: dict[int, str],
    max_hops: int = 2,
) -> tuple[list[int], list[tuple[int, int, int]]]:
    """Extract edges within max_hops of seed node_ids.

    Args:
        node_ids: Set of PyKEEN entity IDs (seed nodes).
        edge_index: [2, num_edges] tensor.
        edge_types: [num_edges] tensor of relation type indices (optional).
        id_to_label: Mapping from PyKEEN ID to original label.
        max_hops: Number of BFS expansion hops from seed nodes.

    Returns:
        Tuple of (reachable_node_ids, subgraph_edges) where each edge
        is (edge_idx_in_original, source_pykeen_id, target_pykeen_id).
    """
    src = edge_index[0].tolist()
    dst = edge_index[1].tolist()

    # BFS expansion from seed nodes
    frontier = set(node_ids)
    visited = set(node_ids)

    for _ in range(max_hops):
        next_frontier: set[int] = set()
        for i in range(len(src)):
            if src[i] in frontier and dst[i] not in visited:
                next_frontier.add(dst[i])
            if dst[i] in frontier and src[i] not in visited:
                next_frontier.add(src[i])
        visited |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    # Collect edges where BOTH endpoints are in the visited set
    subgraph_edges: list[tuple[int, int, int]] = []
    for i in range(len(src)):
        if src[i] in visited and dst[i] in visited:
            subgraph_edges.append((i, src[i], dst[i]))

    return list(visited), subgraph_edges


def mask_edge(edge_index: torch.Tensor, edge_idx: int) -> torch.Tensor:
    """Remove a single edge from edge_index by its positional index.

    Args:
        edge_index: [2, num_edges] tensor.
        edge_idx: Index of the edge to remove.

    Returns:
        New edge_index tensor with the edge removed.
    """
    mask = torch.ones(edge_index.shape[1], dtype=torch.bool)
    mask[edge_idx] = False
    return edge_index[:, mask]


def compute_prediction_score(
    model: GATLinkPredictor,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    drug_pykeen_id: int,
    disease_pykeen_id: int,
) -> float:
    """Compute the GAT prediction score for a drug-disease pair.

    Args:
        model: Trained GATLinkPredictor.
        x: Node feature tensor.
        edge_index: [2, num_edges] tensor.
        drug_pykeen_id: PyKEEN entity ID of the drug.
        disease_pykeen_id: PyKEEN entity ID of the disease.

    Returns:
        Prediction score (dot product of encoded embeddings).
    """
    model.eval()
    with torch.no_grad():
        z = model.encode(x, edge_index)
        score = torch.dot(z[drug_pykeen_id], z[disease_pykeen_id]).item()
    return score


def _build_subgraph_json(
    subgraph_edges: list[tuple[int, int, int]],
    reachable_nodes: list[int],
    id_to_label: dict[int, str],
    nodes_df: pd.DataFrame | None,
    edge_types: torch.Tensor | None,
    relation_to_id: dict[str, int] | None,
) -> dict:
    """Build a JSON-serializable subgraph representation for the frontend.

    Args:
        subgraph_edges: List of (edge_idx, src_pykeen_id, dst_pykeen_id).
        reachable_nodes: List of PyKEEN entity IDs in the subgraph.
        id_to_label: Mapping from PyKEEN ID to original node label/index.
        nodes_df: Optional DataFrame of nodes with name/labels columns.
        edge_types: Optional tensor of edge type indices.
        relation_to_id: Optional mapping from relation name to ID.

    Returns:
        Dict with 'nodes' and 'edges' lists.
    """
    id_to_relation = {}
    if relation_to_id:
        id_to_relation = {v: k for k, v in relation_to_id.items()}

    nodes = []
    for nid in reachable_nodes:
        label = id_to_label.get(nid, str(nid))
        node_info: dict = {"id": nid, "original_id": label}
        if nodes_df is not None:
            try:
                node_idx = int(label)
                matches = nodes_df[nodes_df["node_index"] == node_idx]
                if not matches.empty:
                    row = matches.iloc[0]
                    node_info["name"] = row.get("name", label)
                    node_info["labels"] = str(row.get("labels", "")).split("|")
            except (ValueError, KeyError):
                pass
        nodes.append(node_info)

    edges = []
    for edge_idx, s, d in subgraph_edges:
        edge_info: dict = {
            "source_id": s,
            "target_id": d,
            "edge_idx": edge_idx,
        }
        if edge_types is not None and edge_idx < len(edge_types):
            etype_id = edge_types[edge_idx].item()
            edge_info["type"] = id_to_relation.get(etype_id, str(etype_id))
        edges.append(edge_info)

    return {"nodes": nodes, "edges": edges}


def counterfactual_explain(
    drug_id: int,
    disease_id: int,
    model: GATLinkPredictor,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    label_to_id: dict[str, int],
    id_to_label: dict[int, str],
    edge_types: torch.Tensor | None = None,
    relation_to_id: dict[str, int] | None = None,
    nodes_df: pd.DataFrame | None = None,
    max_hops: int = 2,
    max_edges: int = 50,
    fidelity_threshold: float = 0.05,
) -> CounterfactualExplanation:
    """Generate a counterfactual explanation by edge masking.

    For each edge in the local subgraph, masks it, re-runs the model,
    and records how much the prediction score changes.

    Args:
        drug_id: Original node index of the drug.
        disease_id: Original node index of the disease.
        model: Trained GATLinkPredictor.
        x: Node feature tensor [num_nodes, dim].
        edge_index: [2, num_edges] tensor.
        label_to_id: Mapping from original label to PyKEEN entity ID.
        id_to_label: Mapping from PyKEEN ID to original label.
        edge_types: Optional [num_edges] tensor of relation type indices.
        relation_to_id: Optional mapping from relation name to ID.
        nodes_df: Optional DataFrame for node metadata.
        max_hops: BFS radius for local subgraph extraction.
        max_edges: Maximum edges to evaluate (safety cap).
        fidelity_threshold: Minimum fidelity to count as significant.

    Returns:
        CounterfactualExplanation with per-edge fidelity scores.
    """
    drug_str = str(drug_id)
    disease_str = str(disease_id)

    if drug_str not in label_to_id:
        raise ValueError(f"Drug ID {drug_id} not found in graph entity mapping.")
    if disease_str not in label_to_id:
        raise ValueError(f"Disease ID {disease_id} not found in graph entity mapping.")

    drug_pykeen_id = label_to_id[drug_str]
    disease_pykeen_id = label_to_id[disease_str]

    # 1. Compute original prediction score
    original_score = compute_prediction_score(
        model, x, edge_index, drug_pykeen_id, disease_pykeen_id
    )

    # 2. Extract local subgraph
    seed_nodes = {drug_pykeen_id, disease_pykeen_id}
    reachable_nodes, subgraph_edges = extract_local_subgraph(
        seed_nodes, edge_index, edge_types, id_to_label, max_hops
    )

    # 3. Build subgraph JSON for frontend
    subgraph_json = _build_subgraph_json(
        subgraph_edges,
        reachable_nodes,
        id_to_label,
        nodes_df,
        edge_types,
        relation_to_id,
    )

    # 4. Apply safety cap on number of edges
    edges_to_mask = subgraph_edges[:max_edges]
    if len(subgraph_edges) > max_edges:
        logger.warning(
            "Subgraph has %d edges, capping at %d (max_edges). "
            "Increase max_edges or reduce max_hops for full coverage.",
            len(subgraph_edges),
            max_edges,
        )

    # 5. Mask each edge and measure score change
    id_to_relation = {}
    if relation_to_id:
        id_to_relation = {v: k for k, v in relation_to_id.items()}

    masked_results: list[MaskedEdgeResult] = []

    for edge_idx, src_id, dst_id in edges_to_mask:
        # Create masked edge_index
        masked_ei = mask_edge(edge_index, edge_idx)

        # Re-run model on masked graph
        masked_score = compute_prediction_score(
            model, x, masked_ei, drug_pykeen_id, disease_pykeen_id
        )

        # Compute fidelity
        score_delta = original_score - masked_score
        if abs(original_score) > 1e-10:
            fidelity = score_delta / abs(original_score)
        else:
            fidelity = 0.0

        # Determine edge type string
        edge_type_str = "UNKNOWN"
        if edge_types is not None and edge_idx < len(edge_types):
            etype_id = edge_types[edge_idx].item()
            edge_type_str = id_to_relation.get(etype_id, str(etype_id))

        masked_results.append(
            MaskedEdgeResult(
                source_id=src_id,
                target_id=dst_id,
                edge_type=edge_type_str,
                original_score=original_score,
                masked_score=masked_score,
                score_delta=score_delta,
                fidelity=fidelity,
            )
        )

    # 6. Sort by fidelity (highest impact first)
    masked_results.sort(key=lambda r: abs(r.fidelity), reverse=True)

    # 7. Compute aggregate metrics
    if masked_results:
        overall_fidelity = sum(abs(r.fidelity) for r in masked_results) / len(
            masked_results
        )
        significant_edges = sum(
            1 for r in masked_results if abs(r.fidelity) > fidelity_threshold
        )
        sparsity = significant_edges / len(masked_results)
    else:
        overall_fidelity = 0.0
        sparsity = 0.0

    return CounterfactualExplanation(
        drug_id=drug_id,
        disease_id=disease_id,
        original_score=original_score,
        masked_edges=masked_results,
        overall_fidelity=overall_fidelity,
        sparsity=sparsity,
        subgraph=subgraph_json,
    )


# ---------------------------------------------------------------------------
# Convenience wrapper (loads model from disk, mirrors predict.py interface)
# ---------------------------------------------------------------------------


def explain_from_disk(
    drug_id: int,
    disease_id: int,
    model_path: Path | None = None,
    data_dir: Path | None = None,
    max_hops: int = 2,
    max_edges: int = 50,
    device: str = "cpu",
) -> CounterfactualExplanation:
    """High-level wrapper that loads model + data from disk and runs explanation.

    Args:
        drug_id: Original node index of the drug.
        disease_id: Original node index of the disease.
        model_path: Path to trained GAT model weights.
        data_dir: Path to directory containing nodes.csv and edges.csv.
        max_hops: BFS radius for subgraph extraction.
        max_edges: Maximum edges to evaluate.
        device: PyTorch device string.

    Returns:
        CounterfactualExplanation.
    """
    if model_path is None:
        model_path = Path("artifacts/gat_link_predictor.pt")

    if data_dir:
        nodes_path = data_dir / "nodes.csv"
        edges_path = data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    nodes_df = pd.read_csv(nodes_path)

    embeddings_path = model_path.parent / "best_embeddings.pt"
    entity_embeddings = torch.load(embeddings_path, map_location=device)

    in_dim = entity_embeddings.shape[1]
    hidden_dim = 128

    model = GATLinkPredictor(in_dim=in_dim, hidden_dim=hidden_dim, out_dim=in_dim)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    triples_factory = load_triples_from_csv(nodes_path, edges_path)
    id_maps = get_node_id_maps(triples_factory)
    label_to_id = id_maps["label_to_id"]
    id_to_label = id_maps["id_to_label"]

    data = build_pyg_data(triples_factory, entity_embeddings).to(device)

    relation_to_id = triples_factory.relation_to_id

    return counterfactual_explain(
        drug_id=drug_id,
        disease_id=disease_id,
        model=model,
        x=data.x,
        edge_index=data.edge_index,
        label_to_id=label_to_id,
        id_to_label=id_to_label,
        edge_types=data.edge_type if hasattr(data, "edge_type") else None,
        relation_to_id=relation_to_id,
        nodes_df=nodes_df,
        max_hops=max_hops,
        max_edges=max_edges,
    )


# ---------------------------------------------------------------------------
# CLI formatting
# ---------------------------------------------------------------------------


def format_explanation(explanation: CounterfactualExplanation) -> str:
    """Format the counterfactual explanation for CLI output."""
    lines = [
        f"=== Counterfactual Explanation: Drug {explanation.drug_id} -> "
        f"Disease {explanation.disease_id} ===",
        "",
        f"Original prediction score: {explanation.original_score:.4f}",
        f"Overall fidelity:          {explanation.overall_fidelity:.4f}",
        f"Sparsity:                  {explanation.sparsity:.4f} "
        f"({int(explanation.sparsity * len(explanation.masked_edges))}"
        f"/{len(explanation.masked_edges)} significant edges)",
        "",
    ]

    if not explanation.masked_edges:
        lines.append("No edges found in local subgraph.")
        return "\n".join(lines)

    lines.append(
        f"{'Rank':<5} | {'Source':<8} | {'Target':<8} | "
        f"{'Type':<20} | {'Δ Score':<10} | {'Fidelity':<10}"
    )
    lines.append("-" * 75)

    for i, edge in enumerate(explanation.masked_edges, 1):
        lines.append(
            f"{i:<5} | {edge.source_id:<8} | {edge.target_id:<8} | "
            f"{edge.edge_type:<20} | {edge.score_delta:+.4f}    | "
            f"{edge.fidelity:+.4f}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for counterfactual explanations."""
    parser = argparse.ArgumentParser(
        description="Counterfactual edge-masking explanations for drug-disease predictions."
    )
    parser.add_argument("drug_id", type=int, help="Node index of the drug")
    parser.add_argument("disease_id", type=int, help="Node index of the disease")
    parser.add_argument(
        "--max-hops",
        type=int,
        default=2,
        help="Max BFS hops for subgraph (default: 2)",
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=50,
        help="Max edges to evaluate (default: 50)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="artifacts/gat_link_predictor.pt",
        help="Path to trained GAT model",
    )
    parser.add_argument("--data-dir", type=str, default="", help="Data directory")
    parser.add_argument(
        "--device", type=str, default="cpu", help="PyTorch device (default: cpu)"
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    data_dir = Path(args.data_dir) if args.data_dir else None
    model_path = Path(args.model_path)

    explanation = explain_from_disk(
        drug_id=args.drug_id,
        disease_id=args.disease_id,
        model_path=model_path,
        data_dir=data_dir,
        max_hops=args.max_hops,
        max_edges=args.max_edges,
        device=args.device,
    )

    print(format_explanation(explanation))


if __name__ == "__main__":
    main()
