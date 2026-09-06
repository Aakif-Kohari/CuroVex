"""Predicts candidate drugs for a disease using precomputed GAT node encodings.

Given a disease_id (node integer id or MONDO:* string), loads precomputed
node encodings (produced once by precompute_encodings.py), scores all Drug
nodes, and returns a ranked list. Does not import torch-geometric or pykeen —
those are only needed at training/precompute time, not at serve time.

Usage:
    python predict.py 1                    # by node_index
    python predict.py MONDO:0005015        # by mondo_id
    python predict.py MONDO:0005015 --top-k 10
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

# NO MORE IMPORTS FROM graph_utils. We are fully standalone.

_ENCODINGS_CACHE: dict = {}


def get_default_csv_paths() -> tuple[Path, Path]:
    """Get the default paths to the normalized nodes and edges CSV files.

    Duplicated here (not imported from graph_utils.py) on purpose: graph_utils.py
    imports pykeen and torch-geometric at module level for training-time use,
    and importing anything from that file — even this one small function —
    would pull that entire weight into the deployed API process.
    """
    current_dir = Path.cwd()
    candidates = [
        current_dir / "data" / "normalized",
        current_dir.parent / "kg-pipeline" / "data" / "normalized",
        current_dir.parent / "data" / "normalized",
    ]
    for base_path in candidates:
        nodes_path = base_path / "nodes.csv"
        edges_path = base_path / "edges.csv"
        if nodes_path.exists() and edges_path.exists():
            return nodes_path, edges_path
    base_path = current_dir.parent / "kg-pipeline" / "data" / "normalized"
    return base_path / "nodes.csv", base_path / "edges.csv"


def _load_encodings_and_graph(model_path: Path, data_dir: Path | None):
    cache_key = (str(model_path), str(data_dir))
    if cache_key in _ENCODINGS_CACHE:
        return _ENCODINGS_CACHE[cache_key]

    if data_dir:
        nodes_path, edges_path = data_dir / "nodes.csv", data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    # Read only the columns we need to save RAM
    nodes_df = pd.read_csv(
        nodes_path, usecols=["node_index", "name", "labels", "source_id"]
    )
    edges_df = pd.read_csv(edges_path, usecols=["source_index", "target_index", "type"])

    # Load precomputed encodings and force float32 (saves massive RAM)
    node_encodings = torch.load(
        model_path.parent / "node_encodings.pt", map_location="cpu", weights_only=True
    ).float()

    cached = (nodes_df, edges_df, node_encodings)
    _ENCODINGS_CACHE[cache_key] = cached
    return cached


def resolve_disease_id(disease_input: str, nodes_df: pd.DataFrame) -> int:
    """Resolve a disease input (name, MONDO ID, or integer) to a node_index."""
    if str(disease_input).startswith("MONDO:"):
        disease_nodes = nodes_df[
            (nodes_df["source_id"] == disease_input)
            & (nodes_df["labels"].str.contains("Disease"))
        ]
        if disease_nodes.empty:
            raise ValueError(f"Disease with ID {disease_input} not found.")
        return int(disease_nodes.iloc[0]["node_index"])

    name_match = nodes_df[
        (nodes_df["labels"].str.contains("Disease"))
        & (nodes_df["name"].str.lower() == str(disease_input).lower())
    ]
    if not name_match.empty:
        return int(name_match.iloc[0]["node_index"])

    try:
        return int(disease_input)
    except ValueError:
        raise ValueError(
            f"Invalid disease input: {disease_input}. Must be a disease name, MONDO:* ID, or integer."
        )


def predict_drugs(
    disease_id: int,
    top_k: int,
    model_path: Path,
    data_dir: Path = None,
    device: str = "cpu",
) -> list[dict]:
    """Predict top_k candidate drugs for a given disease_id."""
    nodes_df, edges_df, node_encodings = _load_encodings_and_graph(model_path, data_dir)

    if disease_id >= node_encodings.shape[0]:
        raise ValueError(f"Disease ID {disease_id} not found in graph.")

    disease_emb = node_encodings[disease_id]

    # Get all drug node indices and names efficiently
    drug_mask = nodes_df["labels"].str.contains("Drug")
    drug_indices = nodes_df.loc[drug_mask, "node_index"].astype(int).values
    drug_names = nodes_df.loc[drug_mask, "name"].values

    # Get existing treatments efficiently
    treats_mask = (edges_df["target_index"] == disease_id) & (
        edges_df["type"] == "TREATS"
    )
    existing_treats = set(
        edges_df.loc[treats_mask, "source_index"].astype(int).tolist()
    )

    # Filter out existing treats and out-of-bounds indices
    valid_mask = ~np.isin(drug_indices, list(existing_treats)) & (
        drug_indices < node_encodings.shape[0]
    )
    valid_indices = drug_indices[valid_mask]
    valid_names = drug_names[valid_mask]

    if len(valid_indices) == 0:
        return []

    # Vectorized dot product using matrix-vector multiplication (massive speedup & memory saver)
    drug_embs = node_encodings[valid_indices]
    scores = torch.mv(drug_embs, disease_emb)

    # Get top_k results efficiently
    k = min(top_k, len(scores))
    top_scores, top_idx = torch.topk(scores, k)

    results = []
    for i, idx in enumerate(top_idx.tolist()):
        results.append(
            {
                "drug_id": int(valid_indices[idx]),
                "drug_name": str(valid_names[idx]),
                "score": float(top_scores[i].item()),
                "rank": i + 1,
            }
        )

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("disease_id", type=str)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument(
        "--model-path", type=str, default="artifacts/gat_link_predictor.pt"
    )
    parser.add_argument("--data-dir", type=str, default="")
    args = parser.parse_args()

    if args.data_dir:
        data_dir = Path(args.data_dir)
        nodes_path = data_dir / "nodes.csv"
    else:
        nodes_path, _ = get_default_csv_paths()
        data_dir = None

    nodes_df = pd.read_csv(nodes_path)

    try:
        real_disease_id = resolve_disease_id(args.disease_id, nodes_df)
    except ValueError as e:
        print(f"Error: {e}")
        return

    model_path = Path(args.model_path)
    results = predict_drugs(real_disease_id, args.top_k, model_path, data_dir)

    print(f"{'Rank':<5} | {'Drug ID':<10} | {'Drug Name':<30} | {'Score':<10}")
    print("-" * 65)
    for res in results:
        print(
            f"{res['rank']:<5} | {res['drug_id']:<10} | {res['drug_name']:<30} | {res['score']:.4f}"
        )


if __name__ == "__main__":
    main()
