"""Tests for the compare_methods module.

Tests the comparison logic, path fidelity computation, and output formatting
using synthetic data — no Neo4j or real model required.
"""

import pytest
import torch
import pandas as pd
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "ml-core"))
from train_gat import GATLinkPredictor

from explainability.compare_methods import (
    ComparisonRow,
    compare_single_prediction,
    compare_methods,
    format_comparison_table,
    _match_path_edges_to_graph,
)
from explainability.path_based import PathExplanation, ExplanationPath, PathNode, PathEdge


@pytest.fixture
def small_graph():
    """Same synthetic graph as counterfactual tests."""
    edge_index = torch.tensor(
        [[0, 2, 2, 3, 4, 5, 0], [2, 1, 3, 4, 1, 2, 1]], dtype=torch.long
    )
    edge_types = torch.tensor([0, 1, 2, 3, 1, 0, 4], dtype=torch.long)
    label_to_id = {str(i): i for i in range(6)}
    id_to_label = {i: str(i) for i in range(6)}
    relation_to_id = {
        "TARGETS": 0,
        "ASSOCIATED_WITH": 1,
        "INTERACTS_WITH": 2,
        "PART_OF_PATHWAY": 3,
        "PREDICTED_TREATS": 4,
    }
    return {
        "edge_index": edge_index,
        "edge_types": edge_types,
        "label_to_id": label_to_id,
        "id_to_label": id_to_label,
        "relation_to_id": relation_to_id,
    }


@pytest.fixture
def small_model():
    torch.manual_seed(42)
    return GATLinkPredictor(in_dim=16, hidden_dim=8, out_dim=16, heads=2)


@pytest.fixture
def small_features():
    torch.manual_seed(42)
    return torch.randn(6, 16)


class TestMatchPathEdgesToGraph:
    def test_maps_known_edge(self, small_graph):
        """A path with edge (0->2) should map to edge_index position 0."""
        path = ExplanationPath(
            nodes=[PathNode(0, "D", ["Drug"]), PathNode(2, "P", ["Protein"])],
            edges=[PathEdge(0, 2, "TARGETS")],
            meta_path_pattern="Drug -[TARGETS]-> Protein",
        )
        explanation = PathExplanation(
            meta_path_pattern="Drug -[TARGETS]-> Protein",
            support_count=1,
            paths=[path],
        )
        result = _match_path_edges_to_graph(
            [explanation],
            small_graph["edge_index"],
            small_graph["label_to_id"],
        )
        assert 0 in result  # edge at index 0 is (0, 2)

    def test_empty_explanations_returns_empty(self, small_graph):
        result = _match_path_edges_to_graph(
            [], small_graph["edge_index"], small_graph["label_to_id"]
        )
        assert len(result) == 0


class TestCompareSinglePrediction:
    @patch("explainability.compare_methods.path_explain")
    def test_returns_comparison_row(
        self, mock_path, small_model, small_features, small_graph
    ):
        mock_path.return_value = []
        row = compare_single_prediction(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            edge_types=small_graph["edge_types"],
            relation_to_id=small_graph["relation_to_id"],
            max_hops=2,
        )
        assert isinstance(row, ComparisonRow)
        assert isinstance(row.cf_fidelity, float)
        assert isinstance(row.path_fidelity, float)

    @patch("explainability.compare_methods.path_explain")
    def test_handles_failed_path_explanation(
        self, mock_path, small_model, small_features, small_graph
    ):
        mock_path.side_effect = Exception("Neo4j unavailable")
        row = compare_single_prediction(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        assert row.path_num_paths == 0
        assert row.path_fidelity == 0.0


class TestCompareMethods:
    @patch("explainability.compare_methods.path_explain")
    def test_returns_dataframe(
        self, mock_path, small_model, small_features, small_graph
    ):
        mock_path.return_value = []
        predictions = [
            {"drug_id": 0, "disease_id": 1},
            {"drug_id": 5, "disease_id": 1},
        ]
        df = compare_methods(
            predictions=predictions,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "cf_fidelity" in df.columns
        assert "path_fidelity" in df.columns

    @patch("explainability.compare_methods.path_explain")
    def test_empty_predictions_returns_empty_df(self, mock_path, small_model, small_features, small_graph):
        df = compare_methods(
            predictions=[],
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestFormatComparisonTable:
    def test_formats_nonempty_dataframe(self):
        df = pd.DataFrame([{
            "drug_id": 0,
            "disease_id": 1,
            "original_score": 0.85,
            "path_num_paths": 3,
            "path_fidelity": 0.72,
            "path_sparsity": 0.3,
            "cf_num_edges": 10,
            "cf_fidelity": 0.89,
            "cf_sparsity": 0.4,
        }])
        output = format_comparison_table(df)
        assert "Path-Based vs Counterfactual" in output
        assert "Mean Fidelity" in output
        assert "0.7200" in output
        assert "0.8900" in output

    def test_formats_empty_dataframe(self):
        df = pd.DataFrame()
        output = format_comparison_table(df)
        assert "No comparison results" in output
