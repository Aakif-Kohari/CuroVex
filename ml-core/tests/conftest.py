import pytest
import pandas as pd
import torch
from pathlib import Path
from train_gat import GATLinkPredictor

@pytest.fixture
def sample_nodes_df():
    return pd.DataFrame([
        {"node_index": 0, "source_id": "DB00001", "name": "DrugA", "labels": "Drug", "source": "DrugBank", "original_type": "drug"},
        {"node_index": 1, "source_id": "DB00002", "name": "DrugB", "labels": "Drug", "source": "DrugBank", "original_type": "drug"},
        {"node_index": 2, "source_id": "DB00003", "name": "DrugC", "labels": "Drug", "source": "DrugBank", "original_type": "drug"},
        {"node_index": 3, "source_id": "MONDO:0005015", "name": "Diabetes", "labels": "Disease", "source": "MONDO", "original_type": "disease"},
        {"node_index": 4, "source_id": "MONDO:0004975", "name": "Alzheimer", "labels": "Disease", "source": "MONDO", "original_type": "disease"},
        {"node_index": 5, "source_id": "5972", "name": "REN", "labels": "Gene|Protein", "source": "NCBI", "original_type": "gene/protein"},
        {"node_index": 6, "source_id": "183", "name": "AGT", "labels": "Gene|Protein", "source": "NCBI", "original_type": "gene/protein"},
        {"node_index": 7, "source_id": "R-HSA-2022377", "name": "Metabolism", "labels": "Pathway", "source": "Reactome", "original_type": "pathway"},
    ])

@pytest.fixture
def sample_edges_df():
    return pd.DataFrame([
        {"source_index": 0, "target_index": 3, "type": "TREATS", "display_relation": "indication"},
        {"source_index": 0, "target_index": 5, "type": "TARGETS", "display_relation": "target"},
        {"source_index": 1, "target_index": 5, "type": "TARGETS", "display_relation": "target"},
        {"source_index": 5, "target_index": 3, "type": "ASSOCIATED_WITH", "display_relation": "associated with"},
        {"source_index": 5, "target_index": 4, "type": "ASSOCIATED_WITH", "display_relation": "associated with"},
        {"source_index": 5, "target_index": 7, "type": "PART_OF_PATHWAY", "display_relation": "pathway"},
        {"source_index": 5, "target_index": 6, "type": "INTERACTS_WITH", "display_relation": "ppi"},
    ])

@pytest.fixture
def sample_triples_csv(tmp_path, sample_nodes_df, sample_edges_df):
    nodes_path = tmp_path / "nodes.csv"
    edges_path = tmp_path / "edges.csv"
    sample_nodes_df.to_csv(nodes_path, index=False)
    sample_edges_df.to_csv(edges_path, index=False)
    return nodes_path, edges_path

@pytest.fixture
def mock_embeddings():
    torch.manual_seed(42)
    return torch.rand((8, 16))

@pytest.fixture
def mock_gat_model():
    model = GATLinkPredictor(in_dim=16, hidden_dim=16, out_dim=16, heads=2)
    return model
