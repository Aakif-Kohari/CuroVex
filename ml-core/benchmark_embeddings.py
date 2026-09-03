"""Benchmarks KG embedding models via PyKEEN and selects the best by MRR.

Trains TransE, RotatE, ComplEx, and DistMult on the CuroVex knowledge graph,
evaluates each on a held-out test set, logs results to MLflow, and saves the
best model's entity embeddings.

Usage:
    python benchmark_embeddings.py
    python benchmark_embeddings.py --embedding-dim 128 --epochs 100
"""

import argparse
import json
import time
from pathlib import Path

import mlflow
import torch
from dotenv import load_dotenv
from graph_utils import get_default_csv_paths, load_triples_from_csv
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

load_dotenv()

MODELS = ["TransE", "RotatE", "ComplEx", "DistMult"]

def benchmark_all(triples_factory: TriplesFactory, embedding_dim: int, num_epochs: int, device: str) -> dict:
    """Benchmark multiple models and return their metrics."""
    training, testing, validation = triples_factory.split([0.8, 0.1, 0.1])
    results = {}
    
    for model_name in MODELS:
        with mlflow.start_run(run_name=f"benchmark_{model_name}"):
            mlflow.log_param("model", model_name)
            mlflow.log_param("embedding_dim", embedding_dim)
            mlflow.log_param("epochs", num_epochs)
            
            result = pipeline(
                model=model_name,
                training=training,
                testing=testing,
                validation=validation,
                model_kwargs={"embedding_dim": embedding_dim},
                training_kwargs={"num_epochs": num_epochs},
                device=device
            )
            
            result.metric_results.to_dict()
            
            mrr = result.metric_results.get_metric('both.realistic.inverse_harmonic_mean_rank')
            hits_at_1 = result.metric_results.get_metric('both.realistic.hits_at_1')
            hits_at_3 = result.metric_results.get_metric('both.realistic.hits_at_3')
            hits_at_10 = result.metric_results.get_metric('both.realistic.hits_at_10')
            
            summary_metrics = {
                "mrr": mrr,
                "hits_at_1": hits_at_1,
                "hits_at_3": hits_at_3,
                "hits_at_10": hits_at_10
            }
            
            mlflow.log_metrics(summary_metrics)
            
            results[model_name] = {
                "metrics": summary_metrics,
                "pipeline_result": result
            }
            
    return results

def select_best_model(results: dict) -> str:
    """Select the model with the highest MRR."""
    best_model = None
    best_mrr = -1.0
    
    for model_name, data in sorted(results.items()):
        mrr = data["metrics"]["mrr"]
        if mrr > best_mrr:
            best_mrr = mrr
            best_model = model_name
            
    return best_model

def save_best_embeddings(pipeline_result, output_dir: Path):
    """Save the best model's embeddings and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract entity embedding matrix
    embeddings = pipeline_result.model.entity_representations[0](indices=None).detach().cpu()
    
    # Save embeddings
    torch.save(embeddings, output_dir / "best_embeddings.pt")
    
    # Save metadata
    meta = {
        "model_name": pipeline_result.model.__class__.__name__,
        "embedding_dim": embeddings.shape[1],
        "timestamp": time.time()
    }
    
    with open(output_dir / "best_model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Benchmark KG embedding models.")
    parser.add_argument("--embedding-dim", type=int, default=128, help="Embedding dimension")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--device", type=str, default="auto", help="Device to use")
    parser.add_argument("--data-dir", type=str, default="", help="Path to data directory")
    args = parser.parse_args()
    
    if args.data_dir:
        data_dir = Path(args.data_dir)
        nodes_path = data_dir / "nodes.csv"
        edges_path = data_dir / "edges.csv"
    else:
        nodes_path, edges_path = get_default_csv_paths()
        
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
    triples_factory = load_triples_from_csv(nodes_path, edges_path)
    
    mlflow.set_experiment("curovex-embeddings")
    
    results = benchmark_all(triples_factory, args.embedding_dim, args.epochs, device)
    
    best_model = select_best_model(results)
    print(f"Best model: {best_model} with MRR: {results[best_model]['metrics']['mrr']:.4f}")
    
    output_dir = Path("artifacts")
    save_best_embeddings(results[best_model]["pipeline_result"], output_dir)
    
if __name__ == "__main__":
    main()
