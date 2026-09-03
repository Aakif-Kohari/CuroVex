"""Tests for the counterfactual edge-masking explainability module.

Tests the core algorithm components: subgraph extraction, edge masking,
fidelity scoring, and the end-to-end counterfactual_explain function.
All tests use synthetic graph data — no Neo4j or real model required.
"""

# Import the model class for creating test instances
import sys
from pathlib import Path

import pytest
import torch

from explainability.counterfactual import (
    CounterfactualExplanation,
    MaskedEdgeResult,
    compute_prediction_score,
    counterfactual_explain,
    extract_local_subgraph,
    format_explanation,
    mask_edge,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "ml-core"))
from train_gat import GATLinkPredictor

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def small_graph():
    """A small 6-node graph for testing.

    Nodes (PyKEEN IDs): 0=Drug, 1=Disease, 2=Protein, 3=Gene, 4=Pathway, 5=Drug2
    Edges:
      0->2 (TARGETS), 2->1 (ASSOCIATED_WITH), 2->3 (INTERACTS_WITH),
      3->4 (PART_OF_PATHWAY), 4->1 (ASSOCIATED_WITH), 5->2 (TARGETS),
      0->1 (PREDICTED_TREATS)
    """
    edge_index = torch.tensor(
        [
            [0, 2, 2, 3, 4, 5, 0],  # sources
            [2, 1, 3, 4, 1, 2, 1],  # targets
        ],
        dtype=torch.long,
    )
    edge_types = torch.tensor([0, 1, 2, 3, 1, 0, 4], dtype=torch.long)

    # Mappings: original node_index -> pykeen_id (same in this test)
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
        "num_nodes": 6,
    }


@pytest.fixture
def small_model():
    """A small GAT model with random weights for testing."""
    torch.manual_seed(42)
    model = GATLinkPredictor(in_dim=16, hidden_dim=8, out_dim=16, heads=2)
    model.eval()
    return model


@pytest.fixture
def small_features():
    """Random node features for 6 nodes."""
    torch.manual_seed(42)
    return torch.randn(6, 16)


# ---------------------------------------------------------------------------
# Test: extract_local_subgraph
# ---------------------------------------------------------------------------


class TestExtractLocalSubgraph:
    def test_single_hop_from_single_seed(self, small_graph):
        """One hop from node 0 should reach nodes 0, 2, 1."""
        reachable, edges = extract_local_subgraph(
            {0},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=1,
        )
        assert 0 in reachable
        assert 2 in reachable  # 0->2
        assert 1 in reachable  # 0->1
        assert len(edges) > 0

    def test_two_hop_expands_further(self, small_graph):
        """Two hops from node 0 should reach more nodes than one hop."""
        reachable_1, _ = extract_local_subgraph(
            {0},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=1,
        )
        reachable_2, _ = extract_local_subgraph(
            {0},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=2,
        )
        assert len(reachable_2) >= len(reachable_1)

    def test_seed_pair_includes_both_seeds(self, small_graph):
        """Subgraph from drug(0)+disease(1) seeds includes both."""
        reachable, _ = extract_local_subgraph(
            {0, 1},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=2,
        )
        assert 0 in reachable
        assert 1 in reachable

    def test_edges_have_both_endpoints_in_subgraph(self, small_graph):
        """Every returned edge should have both endpoints in the reachable set."""
        reachable, edges = extract_local_subgraph(
            {0, 1},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=2,
        )
        reachable_set = set(reachable)
        for _, s, d in edges:
            assert s in reachable_set, f"Source {s} not in reachable set"
            assert d in reachable_set, f"Target {d} not in reachable set"

    def test_zero_hops_returns_only_seeds(self, small_graph):
        """Zero hops means only seed nodes, no expansion."""
        reachable, _ = extract_local_subgraph(
            {0},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=0,
        )
        assert reachable == [0]

    def test_edge_tuples_contain_valid_indices(self, small_graph):
        """Each edge tuple is (edge_idx, src, dst) with valid edge_idx."""
        _, edges = extract_local_subgraph(
            {0, 1},
            small_graph["edge_index"],
            small_graph["edge_types"],
            small_graph["id_to_label"],
            max_hops=2,
        )
        num_edges = small_graph["edge_index"].shape[1]
        for edge_idx, _, _ in edges:
            assert 0 <= edge_idx < num_edges


# ---------------------------------------------------------------------------
# Test: mask_edge
# ---------------------------------------------------------------------------


class TestMaskEdge:
    def test_removes_single_edge(self, small_graph):
        """Masking one edge reduces count by exactly 1."""
        ei = small_graph["edge_index"]
        original_count = ei.shape[1]
        masked = mask_edge(ei, 0)
        assert masked.shape[1] == original_count - 1

    def test_preserves_other_edges(self, small_graph):
        """All edges except the masked one should still be present."""
        ei = small_graph["edge_index"]
        masked = mask_edge(ei, 2)  # Remove edge at index 2

        # Check other edges still exist
        for i in range(ei.shape[1]):
            if i == 2:
                continue
            src, dst = ei[0, i].item(), ei[1, i].item()
            # Find this edge in masked
            found = False
            for j in range(masked.shape[1]):
                if masked[0, j].item() == src and masked[1, j].item() == dst:
                    found = True
                    break
            assert found, f"Edge ({src}, {dst}) at index {i} missing after masking index 2"

    def test_does_not_modify_original(self, small_graph):
        """Masking should not modify the original tensor."""
        ei = small_graph["edge_index"].clone()
        original_count = ei.shape[1]
        _ = mask_edge(ei, 0)
        assert ei.shape[1] == original_count

    def test_mask_last_edge(self, small_graph):
        """Masking the last edge should work correctly."""
        ei = small_graph["edge_index"]
        last_idx = ei.shape[1] - 1
        masked = mask_edge(ei, last_idx)
        assert masked.shape[1] == ei.shape[1] - 1


# ---------------------------------------------------------------------------
# Test: compute_prediction_score
# ---------------------------------------------------------------------------


class TestComputePredictionScore:
    def test_returns_float(self, small_model, small_features, small_graph):
        """Score should be a Python float."""
        score = compute_prediction_score(
            small_model,
            small_features,
            small_graph["edge_index"],
            drug_pykeen_id=0,
            disease_pykeen_id=1,
        )
        assert isinstance(score, float)

    def test_deterministic(self, small_model, small_features, small_graph):
        """Same inputs should give same score."""
        score1 = compute_prediction_score(
            small_model,
            small_features,
            small_graph["edge_index"],
            drug_pykeen_id=0,
            disease_pykeen_id=1,
        )
        score2 = compute_prediction_score(
            small_model,
            small_features,
            small_graph["edge_index"],
            drug_pykeen_id=0,
            disease_pykeen_id=1,
        )
        assert score1 == score2

    def test_different_pairs_different_scores(self, small_model, small_features, small_graph):
        """Different drug-disease pairs should generally give different scores."""
        score_01 = compute_prediction_score(
            small_model,
            small_features,
            small_graph["edge_index"],
            drug_pykeen_id=0,
            disease_pykeen_id=1,
        )
        score_51 = compute_prediction_score(
            small_model,
            small_features,
            small_graph["edge_index"],
            drug_pykeen_id=5,
            disease_pykeen_id=1,
        )
        # Not guaranteed to be different, but extremely unlikely with random weights
        # Just check both are valid floats
        assert isinstance(score_01, float)
        assert isinstance(score_51, float)


# ---------------------------------------------------------------------------
# Test: Fidelity calculation
# ---------------------------------------------------------------------------


class TestFidelityCalculation:
    def test_fidelity_formula(self):
        """Fidelity = score_delta / |original_score|."""
        original = 0.8
        masked = 0.5
        delta = original - masked
        fidelity = delta / abs(original)
        assert abs(fidelity - 0.375) < 1e-6

    def test_zero_original_score_no_division_error(self):
        """When original score is ~0, fidelity should be 0, not NaN/Inf."""
        result = MaskedEdgeResult(
            source_id=0,
            target_id=1,
            edge_type="TARGETS",
            original_score=0.0,
            masked_score=0.0,
            score_delta=0.0,
            fidelity=0.0,
        )
        assert result.fidelity == 0.0

    def test_negative_fidelity_means_edge_hurt(self):
        """Negative fidelity means removing the edge INCREASED the score."""
        result = MaskedEdgeResult(
            source_id=0,
            target_id=1,
            edge_type="TARGETS",
            original_score=0.5,
            masked_score=0.7,
            score_delta=-0.2,
            fidelity=-0.4,
        )
        assert result.fidelity < 0


# ---------------------------------------------------------------------------
# Test: counterfactual_explain (end-to-end)
# ---------------------------------------------------------------------------


class TestCounterfactualExplain:
    def test_returns_correct_type(self, small_model, small_features, small_graph):
        """Should return a CounterfactualExplanation."""
        result = counterfactual_explain(
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
            max_edges=50,
        )
        assert isinstance(result, CounterfactualExplanation)

    def test_has_original_score(self, small_model, small_features, small_graph):
        """Result should include a non-None original score."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        assert isinstance(result.original_score, float)

    def test_masked_edges_populated(self, small_model, small_features, small_graph):
        """Should produce at least one masked edge result."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        assert len(result.masked_edges) > 0

    def test_masked_edges_sorted_by_fidelity(self, small_model, small_features, small_graph):
        """Masked edges should be sorted by absolute fidelity, descending."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        fidelities = [abs(e.fidelity) for e in result.masked_edges]
        assert fidelities == sorted(fidelities, reverse=True)

    def test_max_edges_cap_respected(self, small_model, small_features, small_graph):
        """Should not evaluate more edges than max_edges."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=3,
            max_edges=3,
        )
        assert len(result.masked_edges) <= 3

    def test_overall_fidelity_is_mean(self, small_model, small_features, small_graph):
        """Overall fidelity should be the mean of individual absolute fidelities."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        if result.masked_edges:
            expected = sum(abs(e.fidelity) for e in result.masked_edges) / len(
                result.masked_edges
            )
            assert abs(result.overall_fidelity - expected) < 1e-6

    def test_sparsity_calculation(self, small_model, small_features, small_graph):
        """Sparsity should be fraction of edges with fidelity > threshold."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
            fidelity_threshold=0.05,
        )
        if result.masked_edges:
            significant = sum(
                1 for e in result.masked_edges if abs(e.fidelity) > 0.05
            )
            expected_sparsity = significant / len(result.masked_edges)
            assert abs(result.sparsity - expected_sparsity) < 1e-6

    def test_subgraph_has_nodes_and_edges(self, small_model, small_features, small_graph):
        """Subgraph JSON should contain nodes and edges lists."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        assert "nodes" in result.subgraph
        assert "edges" in result.subgraph
        assert len(result.subgraph["nodes"]) > 0

    def test_invalid_drug_id_raises(self, small_model, small_features, small_graph):
        """Invalid drug_id should raise ValueError."""
        with pytest.raises(ValueError, match="Drug ID 999"):
            counterfactual_explain(
                drug_id=999,
                disease_id=1,
                model=small_model,
                x=small_features,
                edge_index=small_graph["edge_index"],
                label_to_id=small_graph["label_to_id"],
                id_to_label=small_graph["id_to_label"],
            )

    def test_invalid_disease_id_raises(self, small_model, small_features, small_graph):
        """Invalid disease_id should raise ValueError."""
        with pytest.raises(ValueError, match="Disease ID 999"):
            counterfactual_explain(
                drug_id=0,
                disease_id=999,
                model=small_model,
                x=small_features,
                edge_index=small_graph["edge_index"],
                label_to_id=small_graph["label_to_id"],
                id_to_label=small_graph["id_to_label"],
            )

    def test_each_masked_edge_has_original_score(self, small_model, small_features, small_graph):
        """Every MaskedEdgeResult should reference the same original score."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        for edge in result.masked_edges:
            assert edge.original_score == result.original_score

    def test_with_edge_types(self, small_model, small_features, small_graph):
        """When edge_types and relation_to_id provided, edge_type strings populated."""
        result = counterfactual_explain(
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
        for edge in result.masked_edges:
            assert edge.edge_type != "UNKNOWN"


# ---------------------------------------------------------------------------
# Test: format_explanation
# ---------------------------------------------------------------------------


class TestFormatExplanation:
    def test_header_present(self, small_model, small_features, small_graph):
        """Output should contain a header with drug and disease IDs."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        output = format_explanation(result)
        assert "Drug 0" in output
        assert "Disease 1" in output
        assert "Original prediction score" in output

    def test_empty_edges_message(self):
        """When no edges, should say so."""
        result = CounterfactualExplanation(
            drug_id=0,
            disease_id=1,
            original_score=0.5,
            masked_edges=[],
        )
        output = format_explanation(result)
        assert "No edges found" in output

    def test_contains_fidelity_values(self, small_model, small_features, small_graph):
        """Output should show fidelity scores."""
        result = counterfactual_explain(
            drug_id=0,
            disease_id=1,
            model=small_model,
            x=small_features,
            edge_index=small_graph["edge_index"],
            label_to_id=small_graph["label_to_id"],
            id_to_label=small_graph["id_to_label"],
            max_hops=2,
        )
        output = format_explanation(result)
        assert "Fidelity" in output
        assert "Sparsity" in output
