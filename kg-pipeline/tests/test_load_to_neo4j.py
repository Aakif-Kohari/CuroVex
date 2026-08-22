"""Tests for load_to_neo4j.py."""

from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest

from load_to_neo4j import (
    DEFAULT_BATCH_SIZE,
    batched,
    build_constraint_queries,
    build_edge_merge_query,
    build_index_queries,
    build_node_merge_query,
    create_constraints_and_indexes,
    load_edges,
    load_nodes,
)


# ---------------------------------------------------------------------------
# batched
# ---------------------------------------------------------------------------


class TestBatched:
    """Tests for the batch-splitting utility."""

    def test_exact_division(self) -> None:
        """List divides evenly into batches."""
        result = batched([1, 2, 3, 4], 2)
        assert result == [[1, 2], [3, 4]]

    def test_remainder(self) -> None:
        """Last batch contains the remainder."""
        result = batched([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_single_batch(self) -> None:
        """Entire list fits in one batch."""
        result = batched([1, 2, 3], 10)
        assert result == [[1, 2, 3]]

    def test_empty_list(self) -> None:
        """Empty list produces empty result."""
        result = batched([], 5)
        assert result == []

    def test_batch_size_one(self) -> None:
        """Batch size of 1 produces one item per batch."""
        result = batched([1, 2, 3], 1)
        assert result == [[1], [2], [3]]


# ---------------------------------------------------------------------------
# Cypher query builders
# ---------------------------------------------------------------------------


class TestBuildConstraintQueries:
    """Tests for constraint query generation."""

    def test_returns_six_constraints(self) -> None:
        """One uniqueness constraint per node label."""
        queries = build_constraint_queries()
        assert len(queries) == 6

    def test_all_idempotent(self) -> None:
        """All constraints use IF NOT EXISTS for safe re-runs."""
        for query in build_constraint_queries():
            assert "IF NOT EXISTS" in query

    def test_covers_all_labels(self) -> None:
        """Constraints cover all six CuroVex node labels."""
        queries = build_constraint_queries()
        all_text = " ".join(queries)
        for label in ["Drug", "Disease", "Gene", "Protein", "Pathway", "SideEffect"]:
            assert f"(n:{label})" in all_text


class TestBuildIndexQueries:
    """Tests for index query generation."""

    def test_all_idempotent(self) -> None:
        """All indexes use IF NOT EXISTS."""
        for query in build_index_queries():
            assert "IF NOT EXISTS" in query

    def test_drug_name_indexed(self) -> None:
        """Drug.name has an index."""
        queries = build_index_queries()
        assert any("Drug" in q and "name" in q for q in queries)

    def test_drugbank_id_indexed(self) -> None:
        """Drug.drugbank_id has an index."""
        queries = build_index_queries()
        assert any("drugbank_id" in q for q in queries)


class TestBuildNodeMergeQuery:
    """Tests for node MERGE query generation."""

    def test_drug_query(self) -> None:
        """Drug merge query sets drugbank_id."""
        query = build_node_merge_query("Drug")
        assert "MERGE (n:Drug" in query
        assert "drugbank_id" in query

    def test_disease_query(self) -> None:
        """Disease merge query sets mondo_id."""
        query = build_node_merge_query("Disease")
        assert "MERGE (n:Disease" in query
        assert "mondo_id" in query

    def test_gene_protein_dual_label(self) -> None:
        """Gene|Protein merge query MERGEs on :Gene and SETs :Protein."""
        query = build_node_merge_query("Gene|Protein")
        assert "MERGE (n:Gene" in query
        assert "n:Protein" in query
        assert "entrez_id" in query

    def test_pathway_query(self) -> None:
        """Pathway merge query sets reactome_id."""
        query = build_node_merge_query("Pathway")
        assert "MERGE (n:Pathway" in query
        assert "reactome_id" in query

    def test_sideeffect_query(self) -> None:
        """SideEffect merge query sets meddra_id."""
        query = build_node_merge_query("SideEffect")
        assert "MERGE (n:SideEffect" in query
        assert "meddra_id" in query


class TestBuildEdgeMergeQuery:
    """Tests for edge MERGE query generation."""

    def test_treats_query(self) -> None:
        """TREATS merge query uses correct relationship type."""
        query = build_edge_merge_query("TREATS")
        assert "MERGE (src)-[r:TREATS]->(tgt)" in query

    def test_targets_query(self) -> None:
        """TARGETS merge query uses correct relationship type."""
        query = build_edge_merge_query("TARGETS")
        assert "MERGE (src)-[r:TARGETS]->(tgt)" in query

    def test_all_queries_have_merge(self) -> None:
        """All relationship types produce MERGE-based queries."""
        for rel in [
            "TREATS",
            "TARGETS",
            "ASSOCIATED_WITH",
            "PART_OF_PATHWAY",
            "CAUSES_SIDE_EFFECT",
            "INTERACTS_WITH",
        ]:
            query = build_edge_merge_query(rel)
            assert "MERGE" in query
            assert rel in query


# ---------------------------------------------------------------------------
# Loading logic (with mocked Neo4j session)
# ---------------------------------------------------------------------------


class TestCreateConstraintsAndIndexes:
    """Tests for constraint/index creation with mocked session."""

    def test_runs_all_queries(self) -> None:
        """All constraint and index queries are executed."""
        mock_session = MagicMock()

        create_constraints_and_indexes(mock_session)

        expected_count = len(build_constraint_queries()) + len(
            build_index_queries()
        )
        assert mock_session.run.call_count == expected_count


class TestLoadNodes:
    """Tests for node loading with mocked session."""

    def test_loads_all_label_groups(
        self, sample_nodes_df: pd.DataFrame
    ) -> None:
        """Calls session.run for each label group."""
        mock_session = MagicMock()

        counts = load_nodes(mock_session, sample_nodes_df, batch_size=100)

        # Should have loaded all label groups
        assert "Drug" in counts
        assert "Disease" in counts
        assert "Gene|Protein" in counts
        assert "Pathway" in counts
        assert "SideEffect" in counts
        assert sum(counts.values()) == len(sample_nodes_df)

    def test_respects_batch_size(self) -> None:
        """Large datasets are split into batches."""
        # Create 5 nodes
        nodes_df = pd.DataFrame(
            {
                "node_index": range(5),
                "source_id": [f"id_{i}" for i in range(5)],
                "name": [f"Node {i}" for i in range(5)],
                "labels": ["Drug"] * 5,
                "source": ["test"] * 5,
                "original_type": ["drug"] * 5,
            }
        )
        mock_session = MagicMock()

        load_nodes(mock_session, nodes_df, batch_size=2)

        # 5 nodes / batch_size 2 = 3 batches
        assert mock_session.run.call_count == 3


class TestLoadEdges:
    """Tests for edge loading with mocked session."""

    def test_loads_all_relationship_types(
        self, sample_edges_df: pd.DataFrame
    ) -> None:
        """Calls session.run for each relationship type."""
        mock_session = MagicMock()

        counts = load_edges(mock_session, sample_edges_df, batch_size=100)

        assert "TREATS" in counts
        assert "TARGETS" in counts
        assert "ASSOCIATED_WITH" in counts
        assert "PART_OF_PATHWAY" in counts
        assert "CAUSES_SIDE_EFFECT" in counts
        assert "INTERACTS_WITH" in counts
        assert sum(counts.values()) == len(sample_edges_df)


# ---------------------------------------------------------------------------
# Integration test (requires running Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestNeo4jIntegration:
    """Integration tests that require a running Neo4j instance.

    Run with: pytest -m integration
    Requires: docker compose up -d (Neo4j on bolt://localhost:7687)
    """

    def test_load_and_query(
        self,
        sample_nodes_df: pd.DataFrame,
        sample_edges_df: pd.DataFrame,
    ) -> None:
        """Load sample data and verify it's queryable."""
        from neo4j import GraphDatabase

        from load_to_neo4j import get_neo4j_config

        config = get_neo4j_config()
        driver = GraphDatabase.driver(
            config["uri"], auth=(config["user"], config["password"])
        )

        try:
            driver.verify_connectivity()
        except Exception:
            pytest.skip("Neo4j is not reachable — skipping integration test")

        with driver.session() as session:
            # Clean up any previous test data
            session.run("MATCH (n) DETACH DELETE n")

            create_constraints_and_indexes(session)
            load_nodes(session, sample_nodes_df, batch_size=100)
            load_edges(session, sample_edges_df, batch_size=100)

            # Verify node counts
            result = session.run("MATCH (n) RETURN count(n) AS cnt")
            node_count = result.single()["cnt"]
            assert node_count == 6

            # Verify edge counts
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            edge_count = result.single()["cnt"]
            assert edge_count == 6

            # Verify dual-labeled gene/protein node
            result = session.run(
                "MATCH (n:Gene:Protein {id: 2}) RETURN n.name AS name"
            )
            record = result.single()
            assert record is not None
            assert record["name"] == "REN"

            # Verify TREATS relationship
            result = session.run(
                "MATCH (:Drug)-[r:TREATS]->(:Disease) RETURN count(r) AS cnt"
            )
            assert result.single()["cnt"] == 1

            # Clean up
            session.run("MATCH (n) DETACH DELETE n")

        driver.close()

    def test_idempotent_load(
        self,
        sample_nodes_df: pd.DataFrame,
        sample_edges_df: pd.DataFrame,
    ) -> None:
        """Loading the same data twice produces the same graph (MERGE)."""
        from neo4j import GraphDatabase

        from load_to_neo4j import get_neo4j_config

        config = get_neo4j_config()
        driver = GraphDatabase.driver(
            config["uri"], auth=(config["user"], config["password"])
        )

        try:
            driver.verify_connectivity()
        except Exception:
            pytest.skip("Neo4j is not reachable — skipping integration test")

        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            create_constraints_and_indexes(session)

            # Load twice
            load_nodes(session, sample_nodes_df, batch_size=100)
            load_edges(session, sample_edges_df, batch_size=100)
            load_nodes(session, sample_nodes_df, batch_size=100)
            load_edges(session, sample_edges_df, batch_size=100)

            # Same counts — MERGE is idempotent
            result = session.run("MATCH (n) RETURN count(n) AS cnt")
            assert result.single()["cnt"] == 6

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            assert result.single()["cnt"] == 6

            session.run("MATCH (n) DETACH DELETE n")

        driver.close()
