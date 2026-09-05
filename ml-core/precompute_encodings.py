"""Precomputes full-graph GAT node encodings once, so the deployed API can
serve /predictions without importing torch-geometric or pykeen, or running
a live forward pass. Run this once against an already-trained model.

Usage:
    python precompute_encodings.py --model-path artifacts/gat_link_predictor.pt
"""

import argparse
from pathlib import Path

import pandas as pd
import torch
from graph_utils import (
    build_pyg_data,
    get_default_csv_paths,
    get_node_id_maps,
    load_triples_from_csv,
)
from train_gat import GATLinkPredictor


def precompute(model_path: Path, data_dir: Path | None, device: str = "cpu") -> Path:
    if data_dir:
        nodes_path, edges_path = data_dir / "nodes.csv", data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()

    nodes_df = pd.read_csv(nodes_path)
    entity_embeddings = torch.load(
        model_path.parent / "best_embeddings.pt", map_location=device
    )

    model = GATLinkPredictor(
        in_dim=entity_embeddings.shape[1],
        hidden_dim=128,
        out_dim=entity_embeddings.shape[1],
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device).eval()

    triples_factory = load_triples_from_csv(nodes_path, edges_path)
    id_to_label = get_node_id_maps(triples_factory)[
        "id_to_label"
    ]  # pykeen_id -> str(node_index)
    data = build_pyg_data(triples_factory, entity_embeddings).to(device)

    with torch.no_grad():
        z = model.encode(data.x, data.edge_index)

    # Re-index from pykeen's internal ID order into plain node_index order —
    # this happens once, here, using the authoritative mapping, so the saved
    # tensor is self-describing: row i is node_index i, no pykeen needed to read it back.
    num_nodes = int(nodes_df["node_index"].max()) + 1
    node_encodings = torch.zeros(num_nodes, z.shape[1])
    for pykeen_id, label in id_to_label.items():
        node_encodings[int(label)] = z[pykeen_id]

    out_path = model_path.parent / "node_encodings.pt"
    torch.save(node_encodings, out_path)
    print(f"Saved {out_path} (shape: {node_encodings.shape})")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", type=str, default="artifacts/gat_link_predictor.pt"
    )
    parser.add_argument("--data-dir", type=str, default="")
    args = parser.parse_args()
    precompute(Path(args.model_path), Path(args.data_dir) if args.data_dir else None)


if __name__ == "__main__":
    main()
