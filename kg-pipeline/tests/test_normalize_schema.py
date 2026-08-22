"""Tests for normalize_schema.py."""

from pathlib import Path

import pandas as pd
import pytest

from normalize_schema import (
    DISPLAY_RELATION_MAP,
    NODE_TYPE_MAP,
    extract_edges,
    extract_nodes,
    normalize,
)


# ---------------------------------------------------------------------------
# extract_nodes
# ---------------------------------------------------------------------------


class TestExtractNodes:
    """Tests for node extraction and deduplication."""

    def test_extracts_supported_types(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """Only supported node types are kept."""
        nodes = extract_nodes(sample_primekg_df)

        # anatomy (index 100) should be dropped
        assert 100 not in nodes["node_index"].values

        # All supported indices should be present
        for idx in [0, 1, 2, 3, 4, 5]:
            assert idx in nodes["node_index"].values

    def test_deduplicates_nodes(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """Nodes appearing in multiple rows are deduplicated."""
        nodes = extract_nodes(sample_primekg_df)

        # Drug node (index 0) appears in multiple rows but should only
        # appear once in the output
        assert nodes["node_index"].value_counts()[0] == 1

    def test_gene_protein_dual_label(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """gene/protein type gets both Gene and Protein labels."""
        nodes = extract_nodes(sample_primekg_df)

        gene_protein_nodes = nodes[nodes["original_type"] == "gene/protein"]
        for _, row in gene_protein_nodes.iterrows():
            assert row["labels"] == "Gene|Protein"

    def test_drug_label(self, sample_primekg_df: pd.DataFrame) -> None:
        """drug type maps to Drug label."""
        nodes = extract_nodes(sample_primekg_df)

        drug_nodes = nodes[nodes["original_type"] == "drug"]
        for _, row in drug_nodes.iterrows():
            assert row["labels"] == "Drug"

    def test_disease_label(self, sample_primekg_df: pd.DataFrame) -> None:
        """disease type maps to Disease label."""
        nodes = extract_nodes(sample_primekg_df)

        disease_nodes = nodes[nodes["original_type"] == "disease"]
        for _, row in disease_nodes.iterrows():
            assert row["labels"] == "Disease"

    def test_effect_phenotype_maps_to_sideeffect(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """effect/phenotype type maps to SideEffect label."""
        nodes = extract_nodes(sample_primekg_df)

        se_nodes = nodes[nodes["original_type"] == "effect/phenotype"]
        for _, row in se_nodes.iterrows():
            assert row["labels"] == "SideEffect"

    def test_pathway_label(self, sample_primekg_df: pd.DataFrame) -> None:
        """pathway type maps to Pathway label."""
        nodes = extract_nodes(sample_primekg_df)

        pathway_nodes = nodes[nodes["original_type"] == "pathway"]
        for _, row in pathway_nodes.iterrows():
            assert row["labels"] == "Pathway"

    def test_source_id_preserved(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """Source database IDs are preserved in the source_id column."""
        nodes = extract_nodes(sample_primekg_df)

        drug = nodes[nodes["node_index"] == 0].iloc[0]
        assert drug["source_id"] == "DB00001"

        disease = nodes[nodes["node_index"] == 1].iloc[0]
        assert disease["source_id"] == "MONDO:0005015"

    def test_all_node_type_mappings_covered(self) -> None:
        """Every entry in NODE_TYPE_MAP produces valid label strings."""
        for primekg_type, labels in NODE_TYPE_MAP.items():
            assert len(labels) >= 1
            for label in labels:
                assert label[0].isupper(), f"Label {label} should be capitalized"


# ---------------------------------------------------------------------------
# extract_edges
# ---------------------------------------------------------------------------


class TestExtractEdges:
    """Tests for edge extraction and mapping."""

    def test_maps_all_relationship_types(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """All six CuroVex relationship types are produced from sample data."""
        nodes = extract_nodes(sample_primekg_df)
        valid_indices = set(nodes["node_index"].values)
        edges = extract_edges(sample_primekg_df, valid_indices)

        expected_types = {
            "TREATS",
            "TARGETS",
            "ASSOCIATED_WITH",
            "PART_OF_PATHWAY",
            "CAUSES_SIDE_EFFECT",
            "INTERACTS_WITH",
        }
        actual_types = set(edges["type"].values)
        assert actual_types == expected_types

    def test_drops_unsupported_nodes(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """Edges involving unsupported node types (anatomy) are dropped."""
        nodes = extract_nodes(sample_primekg_df)
        valid_indices = set(nodes["node_index"].values)
        edges = extract_edges(sample_primekg_df, valid_indices)

        # The anatomy edge (index 100) should not appear
        all_indices = set(edges["source_index"]) | set(edges["target_index"])
        assert 100 not in all_indices

    def test_drops_unmapped_relations(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """Edges with unmapped display_relation (contraindication) are dropped."""
        nodes = extract_nodes(sample_primekg_df)
        valid_indices = set(nodes["node_index"].values)
        edges = extract_edges(sample_primekg_df, valid_indices)

        # "contraindication" is not in DISPLAY_RELATION_MAP
        assert "contraindication" not in edges["display_relation"].values

    def test_indication_maps_to_treats(
        self, sample_primekg_df: pd.DataFrame
    ) -> None:
        """display_relation 'indication' maps to TREATS."""
        nodes = extract_nodes(sample_primekg_df)
        valid_indices = set(nodes["node_index"].values)
        edges = extract_edges(sample_primekg_df, valid_indices)

        treats_edges = edges[edges["type"] == "TREATS"]
        assert len(treats_edges) == 1
        assert treats_edges.iloc[0]["source_index"] == 0  # Drug
        assert treats_edges.iloc[0]["target_index"] == 1  # Disease

    def test_deduplicates_edges(self) -> None:
        """Duplicate edges (same source, target, type) are removed."""
        # Two identical edges
        df = pd.DataFrame(
            [
                {
                    "relation": "drug_disease",
                    "display_relation": "indication",
                    "x_index": 0,
                    "x_id": "DB00001",
                    "x_type": "drug",
                    "x_name": "DrugA",
                    "x_source": "DrugBank",
                    "y_index": 1,
                    "y_id": "MONDO:0001",
                    "y_type": "disease",
                    "y_name": "DiseaseA",
                    "y_source": "MONDO",
                },
                {
                    "relation": "drug_disease",
                    "display_relation": "indication",
                    "x_index": 0,
                    "x_id": "DB00001",
                    "x_type": "drug",
                    "x_name": "DrugA",
                    "x_source": "DrugBank",
                    "y_index": 1,
                    "y_id": "MONDO:0001",
                    "y_type": "disease",
                    "y_name": "DiseaseA",
                    "y_source": "MONDO",
                },
            ]
        )
        valid_indices = {0, 1}
        edges = extract_edges(df, valid_indices)
        assert len(edges) == 1

    def test_edge_count(self, sample_primekg_df: pd.DataFrame) -> None:
        """Correct number of edges after filtering.

        Sample data has 8 rows:
        - 6 valid mapped edges
        - 1 anatomy edge (dropped — endpoint filtered)
        - 1 contraindication (dropped — unmapped relation)
        """
        nodes = extract_nodes(sample_primekg_df)
        valid_indices = set(nodes["node_index"].values)
        edges = extract_edges(sample_primekg_df, valid_indices)

        assert len(edges) == 6


# ---------------------------------------------------------------------------
# normalize (full pipeline)
# ---------------------------------------------------------------------------


class TestNormalize:
    """Tests for the full normalization pipeline."""

    def test_end_to_end(
        self, sample_primekg_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Full pipeline reads a CSV and produces nodes.csv + edges.csv."""
        # Write sample data as input CSV
        input_path = tmp_path / "raw" / "kg.csv"
        input_path.parent.mkdir(parents=True)
        sample_primekg_df.to_csv(input_path, index=False)

        output_dir = tmp_path / "normalized"

        nodes_path, edges_path = normalize(
            input_path=input_path, output_dir=output_dir
        )

        assert nodes_path.exists()
        assert edges_path.exists()

        nodes = pd.read_csv(nodes_path)
        edges = pd.read_csv(edges_path)

        # 6 unique supported nodes (indices 0-5), anatomy (100) dropped
        assert len(nodes) == 6
        # 6 valid edges out of 8 input rows
        assert len(edges) == 6

    def test_exits_when_input_missing(self, tmp_path: Path) -> None:
        """Exits with error when input file doesn't exist."""
        with pytest.raises(SystemExit):
            normalize(
                input_path=tmp_path / "nonexistent.csv",
                output_dir=tmp_path / "out",
            )
