from unittest.mock import MagicMock, patch

from explainability.path_based import (
    ExplanationPath,
    PathEdge,
    PathNode,
    explain,
    extract_meta_path_pattern,
    find_paths,
    format_explanation,
    group_by_pattern,
)


class TestExtractMetaPathPattern:
    def test_two_hop_pattern(self):
        nodes = [
            PathNode(0, "D", ["Drug"]),
            PathNode(1, "P", ["Protein"]),
            PathNode(2, "Dis", ["Disease"])
        ]
        edges = [
            PathEdge(0, 1, "TARGETS"),
            PathEdge(1, 2, "ASSOCIATED_WITH")
        ]
        path = ExplanationPath(nodes, edges, "")
        assert extract_meta_path_pattern(path) == "Drug -[TARGETS]-> Protein -[ASSOCIATED_WITH]-> Disease"

    def test_uses_first_label(self):
        nodes = [
            PathNode(0, "D", ["Drug"]),
            PathNode(1, "G", ["Gene", "Protein"]),
            PathNode(2, "Dis", ["Disease"])
        ]
        edges = [
            PathEdge(0, 1, "TARGETS"),
            PathEdge(1, 2, "ASSOCIATED_WITH")
        ]
        path = ExplanationPath(nodes, edges, "")
        assert extract_meta_path_pattern(path) == "Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease"

    def test_single_hop_pattern(self):
        nodes = [
            PathNode(0, "D", ["Drug"]),
            PathNode(1, "Dis", ["Disease"])
        ]
        edges = [
            PathEdge(0, 1, "TREATS")
        ]
        path = ExplanationPath(nodes, edges, "")
        assert extract_meta_path_pattern(path) == "Drug -[TREATS]-> Disease"


class TestGroupByPattern:
    def test_groups_same_patterns(self, sample_explanation_paths):
        explanations = group_by_pattern(sample_explanation_paths[:2])
        assert len(explanations) == 1
        assert explanations[0].support_count == 2
        assert len(explanations[0].paths) == 2

    def test_sorts_by_support(self, sample_explanation_paths):
        explanations = group_by_pattern(sample_explanation_paths)
        assert len(explanations) == 2
        assert explanations[0].support_count == 2
        assert explanations[1].support_count == 1
        assert explanations[0].meta_path_pattern == "Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease"

    def test_different_patterns_separate(self, sample_explanation_paths):
        explanations = group_by_pattern([sample_explanation_paths[0], sample_explanation_paths[2]])
        assert len(explanations) == 2
        assert explanations[0].support_count == 1
        assert explanations[1].support_count == 1


class TestExplain:
    @patch("explainability.path_based.find_paths")
    def test_returns_grouped_explanations(self, mock_find, sample_explanation_paths):
        mock_find.return_value = sample_explanation_paths
        explanations = explain(0, 1)
        assert len(explanations) == 2
        assert explanations[0].support_count == 2
        mock_find.assert_called_once_with(0, 1, 3)

    @patch("explainability.path_based.find_paths")
    def test_empty_when_no_paths(self, mock_find):
        mock_find.return_value = []
        explanations = explain(0, 1)
        assert len(explanations) == 0

    @patch("explainability.path_based.find_paths")
    def test_respects_max_hops(self, mock_find):
        mock_find.return_value = []
        explain(0, 1, 2)
        mock_find.assert_called_once_with(0, 1, 2)


class TestFormatExplanation:
    def test_formats_output(self, sample_explanation_paths):
        explanations = group_by_pattern(sample_explanation_paths)
        output = format_explanation(explanations, 0, 1)
        assert "=== Path-Based Explanation: Drug 0 -> Disease 1 ===" in output
        assert "Pattern 1 (2 supporting paths):" in output
        assert "Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease" in output
        assert "Lepirudin -> REN -> Diabetes" in output
        assert "Lepirudin -> AGT -> Diabetes" in output

    def test_empty_explanation(self):
        output = format_explanation([], 0, 1)
        assert "No paths found." in output


class TestFindPaths:
    @patch("explainability.path_based.GraphDatabase.driver")
    def test_builds_correct_cypher_query(self, mock_driver, mock_neo4j_paths):
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [{"p": p} for p in mock_neo4j_paths[:1]]
        mock_session.run.return_value = mock_result

        find_paths(0, 1, 2)
        
        call_args = mock_session.run.call_args
        query = call_args[0][0]
        assert "[*1..2]" in query
        assert call_args[1]["drug_id"] == 0
        assert call_args[1]["disease_id"] == 1

    @patch("explainability.path_based.GraphDatabase.driver")
    def test_parses_neo4j_paths(self, mock_driver, mock_neo4j_paths):
        mock_session = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [{"p": p} for p in mock_neo4j_paths]
        mock_session.run.return_value = mock_result

        paths = find_paths(0, 1, 3)
        assert len(paths) == 3
        
        # Verify first path parsed correctly
        assert len(paths[0].nodes) == 3
        assert paths[0].nodes[0].name == "Lepirudin"
        assert len(paths[0].edges) == 2
        assert paths[0].edges[0].type == "TARGETS"
        assert paths[0].meta_path_pattern == "Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease"
