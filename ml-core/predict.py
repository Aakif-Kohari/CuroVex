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

import pandas as pd
import torch
from graph_utils import get_default_csv_paths

_ENCODINGS_CACHE: dict = {}


def _load_encodings_and_graph(model_path: Path, data_dir: Path | None):
    cache_key = (str(model_path), str(data_dir))
    if cache_key in _ENCODINGS_CACHE:
        return _ENCODINGS_CACHE[cache_key]

    if data_dir:
        nodes_path, edges_path = data_dir / "nodes.csv", data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)
    node_encodings = torch.load(
        model_path.parent / "node_encodings.pt", map_location="cpu"
    )

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
    drug_nodes = nodes_df[nodes_df["labels"].str.contains("Drug")]

    existing_treats = {
        int(row["source_index"])
        for _, row in edges_df[
            (edges_df["target_index"] == disease_id) & (edges_df["type"] == "TREATS")
        ].iterrows()
    }

    results = []
    for _, drug_row in drug_nodes.iterrows():
        drug_idx = int(drug_row["node_index"])
        if drug_idx in existing_treats or drug_idx >= node_encodings.shape[0]:
            continue
        results.append(
            {
                "drug_id": drug_idx,
                "drug_name": drug_row["name"],
                "score": torch.dot(node_encodings[drug_idx], disease_emb).item(),
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:top_k]
    for i, res in enumerate(top_results):
        res["rank"] = i + 1
    return top_results


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
