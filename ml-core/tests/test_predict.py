from pathlib import Path
from unittest.mock import patch

import pytest
from predict import _ENCODINGS_CACHE, predict_drugs, resolve_disease_id


@pytest.fixture(autouse=True)
def clear_cache():
    _ENCODINGS_CACHE.clear()
    yield
    _ENCODINGS_CACHE.clear()


class TestResolveDiseaseId:
    def test_resolves_mondo_id(self, sample_nodes_df):
        assert resolve_disease_id("MONDO:0005015", sample_nodes_df) == 3

    def test_resolves_integer_id(self, sample_nodes_df):
        assert resolve_disease_id("3", sample_nodes_df) == 3

    def test_raises_on_unknown_mondo(self, sample_nodes_df):
        with pytest.raises(ValueError, match="not found"):
            resolve_disease_id("MONDO:9999999", sample_nodes_df)

    def test_raises_on_invalid_input(self, sample_nodes_df):
        with pytest.raises(ValueError, match="Invalid disease input"):
            resolve_disease_id("not-an-int", sample_nodes_df)


class TestPredictDrugs:
    @patch("predict.torch.load")
    def test_returns_ranked_list(
        self, mock_torch_load, sample_triples_csv, mock_node_encodings
    ):
        mock_torch_load.return_value = mock_node_encodings
        nodes_path, _edges_path = sample_triples_csv
        data_dir = nodes_path.parent

        results = predict_drugs(
            4, top_k=10, model_path=Path("dummy_model.pt"), data_dir=data_dir
        )

        assert len(results) > 0
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @patch("predict.torch.load")
    def test_filters_existing_treats(
        self, mock_torch_load, sample_triples_csv, mock_node_encodings
    ):
        mock_torch_load.return_value = mock_node_encodings
        nodes_path, _edges_path = sample_triples_csv
        data_dir = nodes_path.parent

        results = predict_drugs(
            3, top_k=10, model_path=Path("dummy_model.pt"), data_dir=data_dir
        )

        drug_ids = [r["drug_id"] for r in results]
        assert 0 not in drug_ids

    @patch("predict.torch.load")
    def test_respects_top_k(
        self, mock_torch_load, sample_triples_csv, mock_node_encodings
    ):
        mock_torch_load.return_value = mock_node_encodings
        nodes_path, _edges_path = sample_triples_csv
        data_dir = nodes_path.parent

        results = predict_drugs(
            4, top_k=1, model_path=Path("dummy_model.pt"), data_dir=data_dir
        )
        assert len(results) == 1

    @patch("predict.torch.load")
    def test_result_structure(
        self, mock_torch_load, sample_triples_csv, mock_node_encodings
    ):
        mock_torch_load.return_value = mock_node_encodings
        nodes_path, _edges_path = sample_triples_csv
        data_dir = nodes_path.parent

        results = predict_drugs(
            4, top_k=10, model_path=Path("dummy_model.pt"), data_dir=data_dir
        )

        for res in results:
            assert "drug_id" in res
            assert "drug_name" in res
            assert "score" in res
            assert "rank" in res

    @patch("predict.torch.load")
    def test_all_results_are_drugs(
        self, mock_torch_load, sample_triples_csv, mock_node_encodings
    ):
        mock_torch_load.return_value = mock_node_encodings
        nodes_path, _edges_path = sample_triples_csv
        data_dir = nodes_path.parent

        results = predict_drugs(
            4, top_k=10, model_path=Path("dummy_model.pt"), data_dir=data_dir
        )

        drug_ids = [r["drug_id"] for r in results]
        for did in drug_ids:
            assert did in [0, 1, 2]
