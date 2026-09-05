"""End-to-end milestone check for Phase 1.

Runs prediction for a few known diseases, takes the top 3 candidate drugs
for each, and generates path-based explanations to verify the pipeline
produces biologically plausible results.

Usage:
    python run_e2e_check.py
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to sys.path to import from explainability
sys.path.append(str(Path(__file__).resolve().parent.parent))

from graph_utils import get_default_csv_paths
from predict import predict_drugs, resolve_disease_id

from explainability.path_based import explain, format_explanation


def run_check(model_path: Path, data_dir: Path = None):
    """Run E2E check on hardcoded disease queries."""
    if data_dir:
        nodes_path = data_dir / "nodes.csv"
    else:
        nodes_path, _ = get_default_csv_paths()

    try:
        nodes_df = pd.read_csv(nodes_path)
    except FileNotFoundError:
        print(f"Error: {nodes_path} not found. Run KG pipeline first.")
        return

    # A few common diseases available in PrimeKG
    # MONDO:0005015 (Diabetes mellitus)
    # MONDO:0004975 (Alzheimer's disease)
    # MONDO:0005071 (Hypertension)
    test_diseases = ["MONDO:0005015", "MONDO:0004975", "MONDO:0005071"]

    for disease_mondo in test_diseases:
        print(f"\n{'='*80}")
        print(f"Running query for Disease: {disease_mondo}")
        print(f"{'='*80}")

        try:
            disease_id = resolve_disease_id(disease_mondo, nodes_df)
            disease_name = nodes_df[nodes_df["node_index"] == disease_id].iloc[0][
                "name"
            ]
            print(f"Resolved to node {disease_id} ({disease_name})")
        except ValueError as e:
            print(f"Skipping {disease_mondo}: {e}")
            continue

        print("\n--- Top 3 Predicted Drugs ---")
        try:
            results = predict_drugs(
                disease_id, top_k=3, model_path=model_path, data_dir=data_dir
            )
        except Exception as e:
            print(f"Prediction failed: {e}")
            continue

        for res in results:
            print(
                f"Rank {res['rank']}: Node {res['drug_id']} ({res['drug_name']}) - Score {res['score']:.4f}"
            )

        print("\n--- Explanations for Top Predictions ---")
        for res in results:
            drug_id = res["drug_id"]
            try:
                explanations = explain(drug_id, disease_id, max_hops=3)
                output = format_explanation(explanations, drug_id, disease_id)
                print(f"\n{output}")
            except Exception as e:
                print(
                    f"\nFailed to explain Drug {drug_id} -> Disease {disease_id}: {e}"
                )


def main():
    parser = argparse.ArgumentParser(description="Run E2E pipeline check.")
    parser.add_argument(
        "--model-path",
        type=str,
        default="artifacts/gat_link_predictor.pt",
        help="Path to trained GAT model",
    )
    parser.add_argument(
        "--data-dir", type=str, default="", help="Path to normalized data dir"
    )
    args = parser.parse_args()

    model_path = Path(args.model_path)
    data_dir = Path(args.data_dir) if args.data_dir else None

    run_check(model_path, data_dir)


if __name__ == "__main__":
    main()
