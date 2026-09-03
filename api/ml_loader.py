import logging
import os
import sys

# Add project root to path so we can import ml-core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)

class MLLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_loaded = False
            cls._instance._model = None
            cls._instance._data = None
            cls._instance._triples_factory = None
            cls._instance._id_maps = None
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

        logger.info("Loading ML model and artifacts (first request)...")
        
        # Stubbed loading for API purposes
        self._model = f"Model loaded from {self._model_path}"
        self._data = f"Data loaded from {self._data_dir}"
        self._triples_factory = "Triples Factory"
        self._id_maps = {}

        self._is_loaded = True
        logger.info("ML model loaded.")

    def get_model(self):
        self._ensure_loaded()
        return self._model

    def get_data(self):
        self._ensure_loaded()
        return self._data

    def get_triples_factory(self):
        self._ensure_loaded()
        return self._triples_factory

    def get_id_maps(self):
        self._ensure_loaded()
        return self._id_maps

ml_loader = MLLoader()
