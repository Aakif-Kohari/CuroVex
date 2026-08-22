"""Shared test fixtures for kg-pipeline tests."""

import pandas as pd
import pytest


@pytest.fixture()
def sample_primekg_df() -> pd.DataFrame:
    """A small PrimeKG-shaped DataFrame for unit tests.

    Covers all five supported node types and several relationship types,
    plus one unsupported node type (anatomy) to test filtering.
    """
    return pd.DataFrame(
        [
            # Drug → Disease (indication → TREATS)
            {
                "relation": "drug_disease",
                "display_relation": "indication",
                "x_index": 0,
                "x_id": "DB00001",
                "x_type": "drug",
                "x_name": "Lepirudin",
                "x_source": "DrugBank",
                "y_index": 1,
                "y_id": "MONDO:0005015",
                "y_type": "disease",
                "y_name": "Diabetes mellitus",
                "y_source": "MONDO",
            },
            # Drug → Gene/Protein (target → TARGETS)
            {
                "relation": "drug_protein",
                "display_relation": "target",
                "x_index": 0,
                "x_id": "DB00001",
                "x_type": "drug",
                "x_name": "Lepirudin",
                "x_source": "DrugBank",
                "y_index": 2,
                "y_id": "5972",
                "y_type": "gene/protein",
                "y_name": "REN",
                "y_source": "NCBI",
            },
            # Gene/Protein → Disease (associated with → ASSOCIATED_WITH)
            {
                "relation": "disease_protein",
                "display_relation": "associated with",
                "x_index": 2,
                "x_id": "5972",
                "x_type": "gene/protein",
                "x_name": "REN",
                "x_source": "NCBI",
                "y_index": 1,
                "y_id": "MONDO:0005015",
                "y_type": "disease",
                "y_name": "Diabetes mellitus",
                "y_source": "MONDO",
            },
            # Gene/Protein → Pathway (pathway → PART_OF_PATHWAY)
            {
                "relation": "protein_pathway",
                "display_relation": "pathway",
                "x_index": 2,
                "x_id": "5972",
                "x_type": "gene/protein",
                "x_name": "REN",
                "x_source": "NCBI",
                "y_index": 3,
                "y_id": "R-HSA-2022377",
                "y_type": "pathway",
                "y_name": "Metabolism of Angiotensinogen",
                "y_source": "Reactome",
            },
            # Drug → Effect/Phenotype (side effect → CAUSES_SIDE_EFFECT)
            {
                "relation": "drug_effect",
                "display_relation": "side effect",
                "x_index": 0,
                "x_id": "DB00001",
                "x_type": "drug",
                "x_name": "Lepirudin",
                "x_source": "DrugBank",
                "y_index": 4,
                "y_id": "C0002871",
                "y_type": "effect/phenotype",
                "y_name": "Anemia",
                "y_source": "MedDRA",
            },
            # Gene/Protein → Gene/Protein (ppi → INTERACTS_WITH)
            {
                "relation": "protein_protein",
                "display_relation": "ppi",
                "x_index": 2,
                "x_id": "5972",
                "x_type": "gene/protein",
                "x_name": "REN",
                "x_source": "NCBI",
                "y_index": 5,
                "y_id": "183",
                "y_type": "gene/protein",
                "y_name": "AGT",
                "y_source": "NCBI",
            },
            # Unsupported: anatomy node (should be dropped)
            {
                "relation": "disease_anatomy",
                "display_relation": "associated with",
                "x_index": 1,
                "x_id": "MONDO:0005015",
                "x_type": "disease",
                "x_name": "Diabetes mellitus",
                "x_source": "MONDO",
                "y_index": 100,
                "y_id": "UBERON:0001264",
                "y_type": "anatomy",
                "y_name": "Pancreas",
                "y_source": "UBERON",
            },
            # Drug → Disease (contraindication — unmapped, should be dropped)
            {
                "relation": "drug_disease",
                "display_relation": "contraindication",
                "x_index": 0,
                "x_id": "DB00001",
                "x_type": "drug",
                "x_name": "Lepirudin",
                "x_source": "DrugBank",
                "y_index": 1,
                "y_id": "MONDO:0005015",
                "y_type": "disease",
                "y_name": "Diabetes mellitus",
                "y_source": "MONDO",
            },
        ]
    )


@pytest.fixture()
def sample_nodes_df() -> pd.DataFrame:
    """Normalized nodes DataFrame matching the output of normalize_schema.py."""
    return pd.DataFrame(
        [
            {
                "node_index": 0,
                "source_id": "DB00001",
                "name": "Lepirudin",
                "labels": "Drug",
                "source": "DrugBank",
                "original_type": "drug",
            },
            {
                "node_index": 1,
                "source_id": "MONDO:0005015",
                "name": "Diabetes mellitus",
                "labels": "Disease",
                "source": "MONDO",
                "original_type": "disease",
            },
            {
                "node_index": 2,
                "source_id": "5972",
                "name": "REN",
                "labels": "Gene|Protein",
                "source": "NCBI",
                "original_type": "gene/protein",
            },
            {
                "node_index": 3,
                "source_id": "R-HSA-2022377",
                "name": "Metabolism of Angiotensinogen",
                "labels": "Pathway",
                "source": "Reactome",
                "original_type": "pathway",
            },
            {
                "node_index": 4,
                "source_id": "C0002871",
                "name": "Anemia",
                "labels": "SideEffect",
                "source": "MedDRA",
                "original_type": "effect/phenotype",
            },
            {
                "node_index": 5,
                "source_id": "183",
                "name": "AGT",
                "labels": "Gene|Protein",
                "source": "NCBI",
                "original_type": "gene/protein",
            },
        ]
    )


@pytest.fixture()
def sample_edges_df() -> pd.DataFrame:
    """Normalized edges DataFrame matching the output of normalize_schema.py."""
    return pd.DataFrame(
        [
            {
                "source_index": 0,
                "target_index": 1,
                "type": "TREATS",
                "display_relation": "indication",
            },
            {
                "source_index": 0,
                "target_index": 2,
                "type": "TARGETS",
                "display_relation": "target",
            },
            {
                "source_index": 2,
                "target_index": 1,
                "type": "ASSOCIATED_WITH",
                "display_relation": "associated with",
            },
            {
                "source_index": 2,
                "target_index": 3,
                "type": "PART_OF_PATHWAY",
                "display_relation": "pathway",
            },
            {
                "source_index": 0,
                "target_index": 4,
                "type": "CAUSES_SIDE_EFFECT",
                "display_relation": "side effect",
            },
            {
                "source_index": 2,
                "target_index": 5,
                "type": "INTERACTS_WITH",
                "display_relation": "ppi",
            },
        ]
    )
