"""Predicts candidate drugs for a disease using the trained GAT model.

Given a disease_id (Neo4j node integer id or MONDO:* string), loads the
trained model, scores all Drug nodes, and returns a ranked list.

Usage:
    python predict.py 1                    # by node_index
    python predict.py MONDO:0005015        # by mondo_id
    python predict.py MONDO:0005015 --top-k 10
"""

import argparse
from pathlib import Path
import pandas as pd
import torch

from graph_utils import get_default_csv_paths, load_triples_from_csv, build_pyg_data, get_node_id_maps
from train_gat import GATLinkPredictor

def resolve_disease_id(disease_input: str, nodes_df: pd.DataFrame) -> int:
    """Resolve a disease input (MONDO ID or integer) to a node_index."""
    if str(disease_input).startswith("MONDO:"):
        disease_nodes = nodes_df[
            (nodes_df['source_id'] == disease_input) & 
            (nodes_df['labels'].str.contains('Disease'))
        ]
        if disease_nodes.empty:
            raise ValueError(f"Disease with ID {disease_input} not found.")
        return int(disease_nodes.iloc[0]['node_index'])
    else:
        try:
            return int(disease_input)
        except ValueError:
            raise ValueError(f"Invalid disease input: {disease_input}. Must be MONDO:* or integer.")

def predict_drugs(disease_id: int, top_k: int, model_path: Path, data_dir: Path = None, device: str = "cpu") -> list[dict]:
    """Predict top_k candidate drugs for a given disease_id."""
    if data_dir:
        nodes_path = data_dir / "nodes.csv"
        edges_path = data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()
        
    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)
    
    embeddings_path = model_path.parent / "best_embeddings.pt"
    entity_embeddings = torch.load(embeddings_path, map_location=device)
    
    in_dim = entity_embeddings.shape[1]
    # We don't have access to hidden_dim used in training easily, assume 128 for now
    # Could load from meta or config in real scenario
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
    
    with torch.no_grad():
        z = model.encode(data.x, data.edge_index)
        
    disease_str_id = str(disease_id)
    if disease_str_id not in label_to_id:
        raise ValueError(f"Disease ID {disease_id} not found in graph.")
        
    disease_pykeen_id = label_to_id[disease_str_id]
    disease_emb = z[disease_pykeen_id]
    
    drug_nodes = nodes_df[nodes_df['labels'].str.contains('Drug')]
    
    existing_treats = set()
    treats_edges = edges_df[
        (edges_df['target_index'] == disease_id) & 
        (edges_df['type'] == 'TREATS')
    ]
    for _, row in treats_edges.iterrows():
        existing_treats.add(int(row['source_index']))
        
    results = []
    
    for _, drug_row in drug_nodes.iterrows():
        drug_idx = int(drug_row['node_index'])
        if drug_idx in existing_treats:
            continue
            
        drug_str_id = str(drug_idx)
        if drug_str_id not in label_to_id:
            continue
            
        drug_pykeen_id = label_to_id[drug_str_id]
        drug_emb = z[drug_pykeen_id]
        
        score = torch.dot(drug_emb, disease_emb).item()
        
        results.append({
            "drug_id": drug_idx,
            "drug_name": drug_row['name'],
            "score": score
        })
        
    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:top_k]
    
    for i, res in enumerate(top_results):
        res["rank"] = i + 1
        
    return top_results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("disease_id", type=str)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--model-path", type=str, default="artifacts/gat_link_predictor.pt")
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
        print(f"{res['rank']:<5} | {res['drug_id']:<10} | {res['drug_name']:<30} | {res['score']:.4f}")

if __name__ == "__main__":
    main()
