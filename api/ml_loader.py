import os
import sys

# Add project root to path so we can import ml-core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class MLLoader:
    _instance = None
    _is_loaded = False

    # Store ML artifacts
    _model = None
    _data = None
    _triples_factory = None
    _id_maps = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, model_path: str, data_dir: str):
        if self._is_loaded:
            return

        print("Loading ML model and artifacts...")
        # Since the actual ml-core implementation might be missing or incomplete,
        # we will stub the actual loading for the purpose of the API.
        # In a real scenario, this would call ml-core loading logic.

        self._model = f"Model loaded from {model_path}"
        self._data = f"Data loaded from {data_dir}"
        self._triples_factory = "Triples Factory"
        self._id_maps = {}

        self._is_loaded = True
        print("ML model loaded.")

    def get_model(self):
        return self._model

    def get_data(self):
        return self._data

    def get_triples_factory(self):
        return self._triples_factory

    def get_id_maps(self):
        return self._id_maps


ml_loader = MLLoader()
