import pytest
from explainability.path_based import PathNode, PathEdge, ExplanationPath

@pytest.fixture
def mock_neo4j_paths():
    """Mock Neo4j path objects matching the specified patterns."""
    class MockNode:
        def __init__(self, node_id, name, labels):
            self.id_val = node_id
            self.name_val = name
            self.labels = labels
            
        def get(self, key, default=None):
            if key == "id":
                return self.id_val
            elif key == "name":
                return self.name_val
            return default

    class MockRel:
        def __init__(self, start_node, end_node, rel_type):
            self.start_node = start_node
            self.end_node = end_node
            self.type = rel_type
            
    class MockPath:
        def __init__(self, nodes, relationships):
            self.nodes = nodes
            self.relationships = relationships

    # Path 1: Drug(0) -> Protein(2) -> Disease(1)
    d0 = MockNode(0, "Lepirudin", ["Drug"])
    p2 = MockNode(2, "REN", ["Gene", "Protein"])
    dis1 = MockNode(1, "Diabetes", ["Disease"])
    r1 = MockRel(d0, p2, "TARGETS")
    r2 = MockRel(p2, dis1, "ASSOCIATED_WITH")
    path1 = MockPath([d0, p2, dis1], [r1, r2])

    # Path 2: Drug(0) -> Protein(5) -> Disease(1)
    p5 = MockNode(5, "AGT", ["Gene", "Protein"])
    r3 = MockRel(d0, p5, "TARGETS")
    r4 = MockRel(p5, dis1, "ASSOCIATED_WITH")
    path2 = MockPath([d0, p5, dis1], [r3, r4])

    # Path 3: Drug(0) -> Protein(2) -> Pathway(3) -> Disease(1)
    pathway3 = MockNode(3, "Metabolism", ["Pathway"])
    r5 = MockRel(p2, pathway3, "PART_OF_PATHWAY")
    r6 = MockRel(pathway3, dis1, "ASSOCIATED_WITH")
    path3 = MockPath([d0, p2, pathway3, dis1], [r1, r5, r6])

    return [path1, path2, path3]

@pytest.fixture
def sample_explanation_paths():
    """Pre-built ExplanationPath objects matching the mock paths."""
    d0 = PathNode(id=0, name="Lepirudin", labels=["Drug"])
    p2 = PathNode(id=2, name="REN", labels=["Gene", "Protein"])
    p5 = PathNode(id=5, name="AGT", labels=["Gene", "Protein"])
    dis1 = PathNode(id=1, name="Diabetes", labels=["Disease"])
    pathway3 = PathNode(id=3, name="Metabolism", labels=["Pathway"])

    ep1 = ExplanationPath(
        nodes=[d0, p2, dis1],
        edges=[PathEdge(0, 2, "TARGETS"), PathEdge(2, 1, "ASSOCIATED_WITH")],
        meta_path_pattern="Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease"
    )

    ep2 = ExplanationPath(
        nodes=[d0, p5, dis1],
        edges=[PathEdge(0, 5, "TARGETS"), PathEdge(5, 1, "ASSOCIATED_WITH")],
        meta_path_pattern="Drug -[TARGETS]-> Gene -[ASSOCIATED_WITH]-> Disease"
    )

    ep3 = ExplanationPath(
        nodes=[d0, p2, pathway3, dis1],
        edges=[PathEdge(0, 2, "TARGETS"), PathEdge(2, 3, "PART_OF_PATHWAY"), PathEdge(3, 1, "ASSOCIATED_WITH")],
        meta_path_pattern="Drug -[TARGETS]-> Gene -[PART_OF_PATHWAY]-> Pathway -[ASSOCIATED_WITH]-> Disease"
    )

    return [ep1, ep2, ep3]
