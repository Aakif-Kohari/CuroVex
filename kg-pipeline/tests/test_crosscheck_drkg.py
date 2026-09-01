"""
Tests for DRKG cross-check pipeline.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from crosscheck_drkg import (
    build_report,
    get_primekg_counts_from_neo4j,
    parse_drkg,
)


class TestParseDrkg:
    """Test parsing DRKG TSV."""
    
    @pytest.fixture
    def mock_drkg_file(self, tmp_path: Path) -> Path:
        """Create a mock DRKG TSV file."""
        filepath = tmp_path / "drkg.tsv"
        content = (
            "Gene::1234\tDRUGBANK::target\tCompound::DB001\n"
            "Compound::DB001\tHetionet::treats\tDisease::MONDO:123\n"
            "Unknown::X\tsome_rel\tUnknown::Y\n"
        )
        filepath.write_text(content)
        return filepath

    def test_parses_entity_types(self, mock_drkg_file: Path):
        """Test correct entity type extraction."""
        counts = parse_drkg(mock_drkg_file)
        assert counts["entity_counts"]["Gene"] == 1
        assert counts["entity_counts"]["Compound"] == 1
        assert counts["entity_counts"]["Disease"] == 1
        
    def test_parses_relation_types(self, mock_drkg_file: Path):
        """Test correct relation type extraction."""
        counts = parse_drkg(mock_drkg_file)
        assert counts["relation_counts"]["target"] == 1
        assert counts["relation_counts"]["treats"] == 1
        
    def test_counts_triplets(self, mock_drkg_file: Path):
        """Test correct total count."""
        counts = parse_drkg(mock_drkg_file)
        assert counts["total_triplets"] == 3
        
    def test_handles_unknown_entity_types(self, mock_drkg_file: Path):
        """Test unknown types counted but not mapped."""
        counts = parse_drkg(mock_drkg_file)
        assert counts["entity_counts"]["Unknown"] == 2


class TestBuildReport:
    """Test report generation."""
    
    @pytest.fixture
    def primekg_counts(self):
        return {
            "entity_counts": {"Drug": 100, "Disease": 200, "Gene/Protein": 300},
            "relation_counts": {"TREATS": 50, "TARGETS": 60},
            "total_triplets": 1000
        }
        
    @pytest.fixture
    def drkg_counts(self):
        return {
            "entity_counts": {"Compound": 110, "Disease": 180, "Gene": 320, "Anatomy": 50},
            "relation_counts": {"treats": 60, "target": 70, "unknown_rel": 10},
            "total_triplets": 1500
        }

    def test_report_contains_all_categories(self, primekg_counts, drkg_counts):
        """Test all mapped types appear."""
        report = build_report(primekg_counts, drkg_counts)
        assert "Drug" in report
        assert "Disease" in report
        assert "Gene/Protein" in report
        assert "Anatomy" in report
        assert "TREATS" in report
        assert "TARGETS" in report
        assert "UNKNOWN_REL" in report
        
    def test_report_shows_deltas(self, primekg_counts, drkg_counts):
        """Test delta column computed correctly."""
        report = build_report(primekg_counts, drkg_counts)
        # Drug: 110 - 100 = +10
        assert "+10" in report
        # Disease: 180 - 200 = -20
        assert "-20" in report
        
    def test_report_handles_missing_categories(self, primekg_counts, drkg_counts):
        """Test types present in one but not other show as 0."""
        primekg_counts["entity_counts"]["Pathway"] = 40
        report = build_report(primekg_counts, drkg_counts)
        assert "Pathway" in report
        # Delta for pathway should be -40 (0 - 40)
        assert "-40" in report


class TestGetPrimeKGCounts:
    """Test Neo4j query aggregation."""
    
    @patch("crosscheck_drkg.GraphDatabase")
    def test_queries_node_and_edge_counts(self, mock_db):
        """Test correct Cypher queries executed."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock returns
        mock_session.run.side_effect = [
            [{"labels": ["Drug"], "cnt": 10}],
            [{"type": "TREATS", "cnt": 5}]
        ]
        
        counts = get_primekg_counts_from_neo4j()
        assert counts["entity_counts"]["Drug"] == 10
        assert counts["relation_counts"]["TREATS"] == 5
        assert counts["total_triplets"] == 5
        
    @patch("crosscheck_drkg.GraphDatabase")
    def test_aggregates_dual_labeled_nodes(self, mock_db):
        """Test Gene|Protein dual-labeled nodes handled."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_db.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_session.run.side_effect = [
            [{"labels": ["Gene", "Protein"], "cnt": 20}],
            []
        ]
        
        counts = get_primekg_counts_from_neo4j()
        assert counts["entity_counts"]["Gene/Protein"] == 20
