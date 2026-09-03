"""Comparison of path-based vs counterfactual explanations.

Runs both explanation methods on a shared set of drug-disease predictions,
computes fidelity and sparsity metrics for each, and outputs a comparison
table. This is the quantitative backbone of the project's research paper.

Usage:
    python compare_methods.py --predictions-file results.csv
    python compare_methods.py --disease-id 3 --top-k 5
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import torch

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "ml-core"))

from graph_utils import (
    build_pyg_data,
    get_default_csv_paths,
    get_node_id_maps,
    load_triples_from_csv,
)
from train_gat import GATLinkPredictor

from explainability.counterfactual import (
    compute_prediction_score,
    counterfactual_explain,
    extract_local_subgraph,
)
from explainability.path_based import explain as path_explain

logger = logging.getLogger(__name__)


@dataclass
class ComparisonRow:
    """One row in the comparison table: metrics for a single prediction."""

    drug_id: int
    disease_id: int
    original_score: float
    # Path-based metrics
    path_num_paths: int
    path_fidelity: float  # fidelity of the path-based explanation
    path_sparsity: float  # fraction of edges on paths vs total subgraph
    # Counterfactual metrics
    cf_num_edges: int
    cf_fidelity: float  # overall fidelity from counterfactual
    cf_sparsity: float  # fraction of significant edges


def compute_path_fidelity(
    drug_id: int,
    disease_id: int,
    model: GATLinkPredictor,
    x: torch.Tensor,
    edge_index: torch.Tensor,
    edge_types: torch.Tensor | None,
    label_to_id: dict[str, int],
    id_to_label: dict[int, str],
    path_edge_ids: set[int],
    max_hops: int = 2,
) -> float:
    """Compute path-based fidelity by masking all edges NOT on explanation paths.

    Fidelity here measures: if we keep ONLY the path edges and mask everything
    else in the subgraph, how much of the original prediction is retained?
    High retention means the paths are sufficient (good fidelity).

    Args:
        drug_id: Original node index of the drug.
        disease_id: Original node index of the disease.
        model: Trained GAT model.
        x: Node features.
        edge_index: Full edge_index.
        edge_types: Edge type tensor (optional).
        label_to_id: Label-to-ID mapping.
        id_to_label: ID-to-label mapping.
        path_edge_ids: Set of edge indices that are on explanation paths.
        max_hops: Subgraph extraction radius.

    Returns:
        Path fidelity score (1.0 means paths fully explain the prediction).
    """
    drug_pykeen_id = label_to_id[str(drug_id)]
    disease_pykeen_id = label_to_id[str(disease_id)]

    original_score = compute_prediction_score(
        model, x, edge_index, drug_pykeen_id, disease_pykeen_id
    )

    if abs(original_score) < 1e-10:
        return 0.0

    # Get local subgraph edges
    seed_nodes = {drug_pykeen_id, disease_pykeen_id}
    _, subgraph_edges = extract_local_subgraph(
        seed_nodes, edge_index, edge_types, id_to_label, max_hops
    )

    # Mask all non-path edges in the subgraph
    non_path_edge_indices = [
        edge_idx for edge_idx, _, _ in subgraph_edges if edge_idx not in path_edge_ids
    ]

    if not non_path_edge_indices:
        return 1.0  # All edges are path edges

    # Create edge_index with non-path edges removed
    mask = torch.ones(edge_index.shape[1], dtype=torch.bool)
    for idx in non_path_edge_indices:
        mask[idx] = False
    masked_ei = edge_index[:, mask]

    masked_score = compute_prediction_score(
        model, x, masked_ei, drug_pykeen_id, disease_pykeen_id
    )

    # Fidelity: how much score is retained when keeping only path edges
    fidelity = masked_score / abs(original_score)
    return fidelity


def _match_path_edges_to_graph(
    path_explanations: list,
    edge_index: torch.Tensor,
    label_to_id: dict[str, int],
) -> set[int]:
    """Map path-based explanation edges back to edge_index positions.

    Args:
        path_explanations: List of PathExplanation objects.
        edge_index: Full edge_index tensor.
        label_to_id: Label-to-ID mapping.

    Returns:
        Set of edge indices in edge_index that appear in any explanation path.
    """
    src_list = edge_index[0].tolist()
    dst_list = edge_index[1].tolist()

    path_edge_ids: set[int] = set()

    for explanation in path_explanations:
        for path in explanation.paths:
            for edge in path.edges:
                # Map original node IDs to PyKEEN IDs
                src_str = str(edge.source_id)
                dst_str = str(edge.target_id)

                if src_str in label_to_id and dst_str in label_to_id:
                    src_pk = label_to_id[src_str]
                    dst_pk = label_to_id[dst_str]

                    # Find matching edge in edge_index
                    for i in range(len(src_list)):
                        if src_list[i] == src_pk and dst_list[i] == dst_pk:
                            path_edge_ids.add(i)
                            break

    return path_edge_ids


def compare_single_prediction(
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
) -> ComparisonRow:
    """Run both explanation methods on a single prediction and compare.

    Args:
        drug_id: Node index of the drug.
        disease_id: Node index of the disease.
        model: Trained GAT model.
        x: Node features.
        edge_index: Edge index.
        label_to_id: Label-to-ID mapping.
        id_to_label: ID-to-label mapping.
        edge_types: Edge type tensor.
        relation_to_id: Relation name to ID mapping.
        nodes_df: Nodes DataFrame for metadata.
        max_hops: Subgraph radius.
        max_edges: Max edges for counterfactual.

    Returns:
        ComparisonRow with metrics for both methods.
    """
    # 1. Path-based explanation
    try:
        path_explanations = path_explain(drug_id, disease_id, max_hops=min(max_hops, 3))
        path_num_paths = sum(exp.support_count for exp in path_explanations)
    except Exception as e:
        logger.warning("Path-based explanation failed for (%s, %s): %s", drug_id, disease_id, e)
        path_explanations = []
        path_num_paths = 0

    # 2. Counterfactual explanation
    cf_result = counterfactual_explain(
        drug_id=drug_id,
        disease_id=disease_id,
        model=model,
        x=x,
        edge_index=edge_index,
        label_to_id=label_to_id,
        id_to_label=id_to_label,
        edge_types=edge_types,
        relation_to_id=relation_to_id,
        nodes_df=nodes_df,
        max_hops=max_hops,
        max_edges=max_edges,
    )

    # 3. Compute path-based fidelity
    path_edge_ids = _match_path_edges_to_graph(
        path_explanations, edge_index, label_to_id
    )

    if path_edge_ids:
        path_fidelity = compute_path_fidelity(
            drug_id,
            disease_id,
            model,
            x,
            edge_index,
            edge_types,
            label_to_id,
            id_to_label,
            path_edge_ids,
            max_hops,
        )
    else:
        path_fidelity = 0.0

    # 4. Path sparsity: path edges / total subgraph edges
    drug_pykeen_id = label_to_id[str(drug_id)]
    disease_pykeen_id = label_to_id[str(disease_id)]
    _, subgraph_edges = extract_local_subgraph(
        {drug_pykeen_id, disease_pykeen_id},
        edge_index,
        edge_types,
        id_to_label,
        max_hops,
    )
    total_subgraph_edges = len(subgraph_edges)
    path_sparsity = (
        len(path_edge_ids) / total_subgraph_edges if total_subgraph_edges > 0 else 0.0
    )

    return ComparisonRow(
        drug_id=drug_id,
        disease_id=disease_id,
        original_score=cf_result.original_score,
        path_num_paths=path_num_paths,
        path_fidelity=path_fidelity,
        path_sparsity=path_sparsity,
        cf_num_edges=len(cf_result.masked_edges),
        cf_fidelity=cf_result.overall_fidelity,
        cf_sparsity=cf_result.sparsity,
    )


def compare_methods(
    predictions: list[dict],
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
) -> pd.DataFrame:
    """Run both methods on a list of predictions and produce a comparison table.

    Args:
        predictions: List of dicts with at least 'drug_id' and 'disease_id' keys.
        model: Trained GAT model.
        x: Node features.
        edge_index: Edge index.
        label_to_id: Label-to-ID mapping.
        id_to_label: ID-to-label mapping.
        edge_types: Edge type tensor.
        relation_to_id: Relation name to ID mapping.
        nodes_df: Nodes DataFrame.
        max_hops: Subgraph radius.
        max_edges: Max edges for counterfactual.

    Returns:
        DataFrame with per-prediction comparison metrics.
    """
    rows: list[dict] = []

    for i, pred in enumerate(predictions):
        drug_id = pred["drug_id"]
        disease_id = pred["disease_id"]
        logger.info(
            "Comparing methods for prediction %d/%d: Drug %d -> Disease %d",
            i + 1,
            len(predictions),
            drug_id,
            disease_id,
        )

        try:
            row = compare_single_prediction(
                drug_id=drug_id,
                disease_id=disease_id,
                model=model,
                x=x,
                edge_index=edge_index,
                label_to_id=label_to_id,
                id_to_label=id_to_label,
                edge_types=edge_types,
                relation_to_id=relation_to_id,
                nodes_df=nodes_df,
                max_hops=max_hops,
                max_edges=max_edges,
            )
            rows.append({
                "drug_id": row.drug_id,
                "disease_id": row.disease_id,
                "original_score": row.original_score,
                "path_num_paths": row.path_num_paths,
                "path_fidelity": row.path_fidelity,
                "path_sparsity": row.path_sparsity,
                "cf_num_edges": row.cf_num_edges,
                "cf_fidelity": row.cf_fidelity,
                "cf_sparsity": row.cf_sparsity,
            })
        except Exception as e:
            logger.error(
                "Failed to compare Drug %d -> Disease %d: %s", drug_id, disease_id, e
            )

    df = pd.DataFrame(rows)
    return df


def format_comparison_table(df: pd.DataFrame) -> str:
    """Format the comparison DataFrame for CLI output.

    Args:
        df: DataFrame from compare_methods().

    Returns:
        Formatted string with per-prediction and aggregate results.
    """
    if df.empty:
        return "No comparison results available."

    lines = ["=== Fidelity/Sparsity Comparison: Path-Based vs Counterfactual ===", ""]

    # Per-prediction table
    header = (
        f"{'Drug':<8} | {'Disease':<8} | {'Score':<8} | "
        f"{'PB Fid.':<8} | {'PB Spar.':<8} | "
        f"{'CF Fid.':<8} | {'CF Spar.':<8}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for _, row in df.iterrows():
        lines.append(
            f"{int(row['drug_id']):<8} | {int(row['disease_id']):<8} | "
            f"{row['original_score']:<8.4f} | "
            f"{row['path_fidelity']:<8.4f} | {row['path_sparsity']:<8.4f} | "
            f"{row['cf_fidelity']:<8.4f} | {row['cf_sparsity']:<8.4f}"
        )

    # Aggregate statistics
    lines.extend([
        "",
        "--- Aggregate Statistics ---",
        "",
        f"{'Metric':<25} | {'Path-Based':<15} | {'Counterfactual':<15}",
        "-" * 60,
        f"{'Mean Fidelity':<25} | {df['path_fidelity'].mean():<15.4f} | "
        f"{df['cf_fidelity'].mean():<15.4f}",
        f"{'Std Fidelity':<25} | {df['path_fidelity'].std():<15.4f} | "
        f"{df['cf_fidelity'].std():<15.4f}",
        f"{'Mean Sparsity':<25} | {df['path_sparsity'].mean():<15.4f} | "
        f"{df['cf_sparsity'].mean():<15.4f}",
        f"{'Std Sparsity':<25} | {df['path_sparsity'].std():<15.4f} | "
        f"{df['cf_sparsity'].std():<15.4f}",
        f"{'Num Predictions':<25} | {len(df):<15} | {len(df):<15}",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare path-based and counterfactual explanations."
    )
    parser.add_argument(
        "--predictions-file",
        type=str,
        default="",
        help="CSV with drug_id, disease_id columns",
    )
    parser.add_argument(
        "--disease-id",
        type=int,
        default=None,
        help="Generate predictions for this disease and compare",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of predictions to compare")
    parser.add_argument("--max-hops", type=int, default=2, help="Subgraph hops")
    parser.add_argument("--max-edges", type=int, default=50, help="Max edges to mask")
    parser.add_argument(
        "--model-path",
        type=str,
        default="artifacts/gat_link_predictor.pt",
    )
    parser.add_argument("--data-dir", type=str, default="")
    parser.add_argument("--output-csv", type=str, default="comparison_results.csv")
    parser.add_argument("--device", type=str, default="cpu")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    # Load model and data
    model_path = Path(args.model_path)
    if args.data_dir:
        data_dir = Path(args.data_dir)
        nodes_path = data_dir / "nodes.csv"
        edges_path = data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    nodes_df = pd.read_csv(nodes_path)

    embeddings_path = model_path.parent / "best_embeddings.pt"
    entity_embeddings = torch.load(embeddings_path, map_location=args.device)

    in_dim = entity_embeddings.shape[1]
    model = GATLinkPredictor(in_dim=in_dim, hidden_dim=128, out_dim=in_dim)
    model.load_state_dict(torch.load(model_path, map_location=args.device))
    model.eval()

    triples_factory = load_triples_from_csv(nodes_path, edges_path)
    id_maps = get_node_id_maps(triples_factory)
    data = build_pyg_data(triples_factory, entity_embeddings)

    # Get predictions to compare
    if args.predictions_file:
        pred_df = pd.read_csv(args.predictions_file)
        predictions = pred_df[["drug_id", "disease_id"]].to_dict("records")
    elif args.disease_id is not None:
        from predict import predict_drugs

        results = predict_drugs(
            args.disease_id, args.top_k, model_path, data_dir=Path(args.data_dir) if args.data_dir else None
        )
        predictions = [
            {"drug_id": r["drug_id"], "disease_id": args.disease_id} for r in results
        ]
    else:
        parser.error("Provide either --predictions-file or --disease-id")
        return

    # Run comparison
    comparison_df = compare_methods(
        predictions=predictions,
        model=model,
        x=data.x,
        edge_index=data.edge_index,
        label_to_id=id_maps["label_to_id"],
        id_to_label=id_maps["id_to_label"],
        edge_types=data.edge_type if hasattr(data, "edge_type") else None,
        relation_to_id=triples_factory.relation_to_id,
        nodes_df=nodes_df,
        max_hops=args.max_hops,
        max_edges=args.max_edges,
    )

    # Output
    print(format_comparison_table(comparison_df))

    output_path = Path(args.output_csv)
    comparison_df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
