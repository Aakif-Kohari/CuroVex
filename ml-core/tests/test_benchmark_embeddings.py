import json
from unittest.mock import MagicMock, patch

import torch
from benchmark_embeddings import benchmark_all, save_best_embeddings, select_best_model


class TestSelectBestModel:
    def test_selects_highest_mrr(self):
        results = {
            "ModelA": {"metrics": {"mrr": 0.5}},
            "ModelB": {"metrics": {"mrr": 0.8}},
            "ModelC": {"metrics": {"mrr": 0.6}},
        }
        assert select_best_model(results) == "ModelB"

    def test_handles_single_model(self):
        results = {"ModelA": {"metrics": {"mrr": 0.5}}}
        assert select_best_model(results) == "ModelA"

    def test_handles_tied_scores(self):
        results = {
            "ModelA": {"metrics": {"mrr": 0.8}},
            "ModelB": {"metrics": {"mrr": 0.8}},
        }
        # Returns first in alphabetical order since sorted(results.items()) is used
        assert select_best_model(results) == "ModelA"


class TestBenchmarkAll:
    @patch("benchmark_embeddings.pipeline")
    @patch("benchmark_embeddings.mlflow")
    def test_trains_all_four_models(self, mock_mlflow, mock_pipeline):
        mock_pipeline_result = MagicMock()
        mock_pipeline_result.metric_results.get_metric.return_value = 0.5
        mock_pipeline_result.metric_results.to_dict.return_value = {}
        mock_pipeline.return_value = mock_pipeline_result

        mock_tf = MagicMock()
        mock_tf.split.return_value = (MagicMock(), MagicMock(), MagicMock())

        benchmark_all(mock_tf, 16, 1, "cpu")

        assert mock_pipeline.call_count == 4
        from benchmark_embeddings import MODELS

        called_models = [call[1]["model"] for call in mock_pipeline.call_args_list]
        assert set(called_models) == set(MODELS)

    @patch("benchmark_embeddings.pipeline")
    @patch("benchmark_embeddings.mlflow")
    def test_returns_metrics_for_each_model(self, mock_mlflow, mock_pipeline):
        mock_pipeline_result = MagicMock()
        mock_pipeline_result.metric_results.get_metric.return_value = 0.5
        mock_pipeline.return_value = mock_pipeline_result

        mock_tf = MagicMock()
        mock_tf.split.return_value = (MagicMock(), MagicMock(), MagicMock())

        results = benchmark_all(mock_tf, 16, 1, "cpu")
        from benchmark_embeddings import MODELS

        for model in MODELS:
            assert model in results
            assert "mrr" in results[model]["metrics"]

    @patch("benchmark_embeddings.pipeline")
    @patch("benchmark_embeddings.mlflow")
    def test_logs_to_mlflow(self, mock_mlflow, mock_pipeline):
        mock_pipeline_result = MagicMock()
        mock_pipeline_result.metric_results.get_metric.return_value = 0.5
        mock_pipeline.return_value = mock_pipeline_result

        mock_tf = MagicMock()
        mock_tf.split.return_value = (MagicMock(), MagicMock(), MagicMock())

        benchmark_all(mock_tf, 16, 1, "cpu")
        assert mock_mlflow.log_metrics.called


class TestSaveBestEmbeddings:
    def test_saves_embedding_file(self, tmp_path):
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.__class__.__name__ = "TransE"
        mock_rep = MagicMock()
        mock_rep.return_value.detach.return_value.cpu.return_value = torch.rand(
            (10, 16)
        )
        mock_model.entity_representations = [mock_rep]
        mock_result.model = mock_model

        save_best_embeddings(mock_result, tmp_path)

        assert (tmp_path / "best_embeddings.pt").exists()

    def test_saves_metadata_json(self, tmp_path):
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.__class__.__name__ = "TransE"
        mock_rep = MagicMock()
        mock_rep.return_value.detach.return_value.cpu.return_value = torch.rand(
            (10, 16)
        )
        mock_model.entity_representations = [mock_rep]
        mock_result.model = mock_model

        save_best_embeddings(mock_result, tmp_path)

        meta_path = tmp_path / "best_model_meta.json"
        assert meta_path.exists()
        with open(meta_path, "r") as f:
            meta = json.load(f)
            assert meta["model_name"] == "TransE"
            assert meta["embedding_dim"] == 16
            assert "timestamp" in meta

    def test_embedding_shape(self, tmp_path):
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.__class__.__name__ = "TransE"
        mock_rep = MagicMock()
        expected_tensor = torch.rand((10, 16))
        mock_rep.return_value.detach.return_value.cpu.return_value = expected_tensor
        mock_model.entity_representations = [mock_rep]
        mock_result.model = mock_model

        save_best_embeddings(mock_result, tmp_path)

        saved_tensor = torch.load(tmp_path / "best_embeddings.pt")
        assert saved_tensor.shape == (10, 16)
