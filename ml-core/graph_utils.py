"""Graph loading utilities for ML training and inference.

Provides functions to load the CuroVex knowledge graph as PyKEEN
TriplesFactory or PyTorch Geometric Data objects, from either
normalized CSV files (primary) or Neo4j (optional).
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pykeen.triples import TriplesFactory
from torch_geometric.data import Data

load_dotenv()

def get_default_csv_paths() -> tuple[Path, Path]:
    """Get the default paths to the normalized nodes and edges CSV files."""
    current_dir = Path.cwd()
    paths = [
        current_dir / "data" / "normalized",
        current_dir.parent / "kg-pipeline" / "data" / "normalized",
        current_dir.parent / "data" / "normalized"
    ]
    
    for base_path in paths:
        nodes_path = base_path / "nodes.csv"
        edges_path = base_path / "edges.csv"
        if nodes_path.exists() and edges_path.exists():
            return nodes_path, edges_path
            
    # Default fallback
    base_path = current_dir.parent / "kg-pipeline" / "data" / "normalized"
    return base_path / "nodes.csv", base_path / "edges.csv"

def load_triples_from_csv(nodes_path: Path, edges_path: Path) -> TriplesFactory:
    """Load graph triples from normalized CSV files.
    
    Args:
        nodes_path: Path to nodes.csv
        edges_path: Path to edges.csv
        
    Returns:
        PyKEEN TriplesFactory
    """
    edges_df = pd.read_csv(edges_path)
    
    head = edges_df['source_index'].astype(str).values
    relation = edges_df['type'].values
    tail = edges_df['target_index'].astype(str).values
    
    triples = np.column_stack((head, relation, tail))
    return TriplesFactory.from_labeled_triples(triples)

def load_triples_from_neo4j() -> TriplesFactory:
    """Load graph triples directly from Neo4j database.
    
    Returns:
        PyKEEN TriplesFactory
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "curovex_neo4j_dev")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    query = "MATCH (h)-[r]->(t) RETURN h.id AS h, type(r) AS r, t.id AS t"
    
    records = []
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            records.append([str(record["h"]), record["r"], str(record["t"])])
            
    driver.close()
    
    triples = np.array(records)
    return TriplesFactory.from_labeled_triples(triples)

def build_pyg_data(triples_factory: TriplesFactory, entity_embeddings: torch.Tensor) -> Data:
    """Build a PyTorch Geometric Data object.
    
    Args:
        triples_factory: The PyKEEN TriplesFactory
        entity_embeddings: Tensor of node features [num_entities, dim]
        
    Returns:
        PyG Data object
    """
    mapped_triples = triples_factory.mapped_triples
    
    edge_index = mapped_triples[:, [0, 2]].t().contiguous()
    edge_type = mapped_triples[:, 1].contiguous()
    
    return Data(
        x=entity_embeddings,
        edge_index=edge_index,
        edge_type=edge_type,
        num_nodes=triples_factory.num_entities,
        num_relations=triples_factory.num_relations
    )

def get_node_id_maps(triples_factory: TriplesFactory) -> dict:
    """Get mappings between original node indices and PyKEEN entity IDs.
    
    Args:
        triples_factory: The PyKEEN TriplesFactory
        
    Returns:
        Dict with 'label_to_id' and 'id_to_label' mappings
    """
    label_to_id = triples_factory.entity_to_id
    id_to_label = {v: k for k, v in label_to_id.items()}
    return {
        "label_to_id": label_to_id,
        "id_to_label": id_to_label
    }

def get_drug_disease_node_ids(nodes_path: Path) -> tuple[set[int], set[int]]:
    """Get sets of node indices for Drug and Disease nodes.
    
    Args:
        nodes_path: Path to nodes.csv
        
    Returns:
        Tuple of (drug_indices, disease_indices)
    """
    nodes_df = pd.read_csv(nodes_path)
    
    drugs = set(nodes_df[nodes_df['labels'].str.contains('Drug')]['node_index'].tolist())
    diseases = set(nodes_df[nodes_df['labels'].str.contains('Disease')]['node_index'].tolist())
    
    return drugs, diseases
