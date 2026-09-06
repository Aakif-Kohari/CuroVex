import logging
import os
import sys
from pathlib import Path

# Add project root to path so we can import ml-core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../ml-core"))
)

logger = logging.getLogger(__name__)


class MLLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_loaded = False
            cls._instance._model = None
            cls._instance._x = None
            cls._instance._edge_index = None
            cls._instance._label_to_id = None
            cls._instance._id_to_label = None
            cls._instance._relation_to_id = None
            cls._instance._nodes_df = None
            cls._instance._model_path = ""
            cls._instance._data_dir = ""
        return cls._instance

    def load(self, model_path: str = "", data_dir: str = ""):
        """Store paths but do NOT load yet (Lazy Loading)."""
        self._model_path = model_path
        self._data_dir = data_dir
        logger.info(f"ML paths registered (lazy): model={model_path}, data={data_dir}")

    def _ensure_loaded(self):
        """Actually load everything on first real use."""
        if self._is_loaded:
            return

        logger.info("Loading ML model and graph artifacts (first request)...")
        import pandas as pd
        import torch
        from graph_utils import (
            build_pyg_data,
            get_default_csv_paths,
            get_node_id_maps,
            load_triples_from_csv,
        )
        from train_gat import GATLinkPredictor

        model_path = (
            Path(self._model_path)
            if self._model_path
            else Path("ml-core/artifacts/gat_link_predictor.pt")
        )
        if self._data_dir:
            data_dir = Path(self._data_dir)
            nodes_path = data_dir / "nodes.csv"
            edges_path = data_dir / "edges.csv"
        else:
            nodes_path, edges_path = get_default_csv_paths()

        self._nodes_df = pd.read_csv(nodes_path)

        embeddings_path = model_path.parent / "best_embeddings.pt"
        entity_embeddings = torch.load(
            embeddings_path, map_location="cpu", weights_only=True
        )
        if entity_embeddings.is_complex():
            entity_embeddings = torch.view_as_real(entity_embeddings).flatten(1)

        entity_embeddings = entity_embeddings.float()  # Force float32 to save RAM

        in_dim = entity_embeddings.shape[1]
        model = GATLinkPredictor(in_dim=in_dim, hidden_dim=128, out_dim=in_dim)
        model.load_state_dict(
            torch.load(model_path, map_location="cpu", weights_only=True)
        )
        model.eval()
        self._model = model

        triples_factory = load_triples_from_csv(nodes_path, edges_path)
        id_maps = get_node_id_maps(triples_factory)
        self._label_to_id = id_maps["label_to_id"]
        self._id_to_label = id_maps["id_to_label"]
        self._relation_to_id = triples_factory.relation_to_id

        data = build_pyg_data(triples_factory, entity_embeddings)
        self._x = data.x
        self._edge_index = data.edge_index

        self._is_loaded = True
        logger.info("ML model and graph loaded successfully.")

    def get_model(self):
        self._ensure_loaded()
        return self._model

    def get_x(self):
        self._ensure_loaded()
        return self._x

    def get_edge_index(self):
        self._ensure_loaded()
        return self._edge_index

    def get_label_to_id(self):
        self._ensure_loaded()
        return self._label_to_id

    def get_id_to_label(self):
        self._ensure_loaded()
        return self._id_to_label

    def get_relation_to_id(self):
        self._ensure_loaded()
        return self._relation_to_id

    def get_nodes_df(self):
        self._ensure_loaded()
        return self._nodes_df


ml_loader = MLLoader()
