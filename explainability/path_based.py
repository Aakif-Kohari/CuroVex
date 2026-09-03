"""Path-based explanations for drug-disease predictions.

Given a (drug_id, disease_id) pair, queries Neo4j for meta-paths
connecting them (up to a configurable hop limit, default 3), extracts
meta-path patterns, ranks by support count, and returns structured
explanation data.

Usage:
    python path_based.py 0 1
    python path_based.py 0 1 --max-hops 3
"""

import argparse
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from neo4j import GraphDatabase


@dataclass
class PathNode:
    """A node in an explanation path."""
    id: int
    name: str
    labels: list[str]

@dataclass
class PathEdge:
    """An edge in an explanation path."""
    source_id: int
    target_id: int
    type: str

@dataclass
class ExplanationPath:
    """A single concrete path instance between drug and disease."""
    nodes: list[PathNode]
    edges: list[PathEdge]
    meta_path_pattern: str  # e.g. "Drug -[TARGETS]-> Protein -[ASSOCIATED_WITH]-> Disease"

@dataclass
class PathExplanation:
    """A grouped explanation: one meta-path pattern with all its instances."""
    meta_path_pattern: str
    support_count: int  # number of concrete path instances
    paths: list[ExplanationPath]


def get_neo4j_config() -> dict[str, str]:
    """Get Neo4j configuration from environment variables."""
    load_dotenv()
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "curovex_neo4j_dev"),
    }


def extract_meta_path_pattern(path: ExplanationPath) -> str:
    """Builds a human-readable pattern string from the path's node labels and edge types."""
    pattern_parts = []
    
    for i in range(len(path.edges)):
        source_node = path.nodes[i]
        target_node = path.nodes[i+1]
        edge = path.edges[i]
        
        if i == 0:
            source_label = source_node.labels[0] if source_node.labels else "Node"
            pattern_parts.append(source_label)
            
        target_label = target_node.labels[0] if target_node.labels else "Node"
        
        # Check edge direction relative to path traversal
        if edge.source_id == source_node.id and edge.target_id == target_node.id:
            pattern_parts.append(f"-[{edge.type}]->")
        else:
            pattern_parts.append(f"<-[{edge.type}]-")
            
        pattern_parts.append(target_label)
        
    return " ".join(pattern_parts)


def find_paths(drug_id: int, disease_id: int, max_hops: int = 3) -> list[ExplanationPath]:
    """Finds paths between a drug and a disease in Neo4j."""
    config = get_neo4j_config()
    driver = GraphDatabase.driver(config["uri"], auth=(config["user"], config["password"]))
    
    if max_hops not in [1, 2, 3]:
        raise ValueError("max_hops must be 1, 2, or 3")
        
    query = f"""
    MATCH p = (d {{id: $drug_id}})-[*1..{max_hops}]-(dis {{id: $disease_id}})
    WHERE d:Drug AND dis:Disease
    RETURN p
    LIMIT 100
    """
    
    explanation_paths = []
    
    with driver.session() as session:
        result = session.run(query, drug_id=drug_id, disease_id=disease_id)
        for record in result:
            path = record["p"]
            
            nodes_list = list(path.nodes)
            rels_list = list(path.relationships)
            
            path_nodes = []
            for n in nodes_list:
                name = n.get("name", str(n.get("id")))
                labels = list(n.labels)
                path_nodes.append(PathNode(id=n.get("id"), name=name, labels=labels))
                
            path_edges = []
            for r in rels_list:
                path_edges.append(PathEdge(
                    source_id=r.start_node.get("id"),
                    target_id=r.end_node.get("id"),
                    type=r.type
                ))
            
            ep = ExplanationPath(nodes=path_nodes, edges=path_edges, meta_path_pattern="")
            ep.meta_path_pattern = extract_meta_path_pattern(ep)
            explanation_paths.append(ep)
            
    driver.close()
    return explanation_paths


def group_by_pattern(paths: list[ExplanationPath]) -> list[PathExplanation]:
    """Groups paths by their meta-path pattern and sorts by support count."""
    groups = {}
    for p in paths:
        if p.meta_path_pattern not in groups:
            groups[p.meta_path_pattern] = []
        groups[p.meta_path_pattern].append(p)
        
    explanations = []
    for pattern, grouped_paths in groups.items():
        explanations.append(PathExplanation(
            meta_path_pattern=pattern,
            support_count=len(grouped_paths),
            paths=grouped_paths
        ))
        
    explanations.sort(key=lambda x: x.support_count, reverse=True)
    return explanations


def explain(drug_id: int, disease_id: int, max_hops: int = 3) -> list[PathExplanation]:
    """Main API to get grouped path-based explanations for a drug-disease pair."""
    paths = find_paths(drug_id, disease_id, max_hops)
    return group_by_pattern(paths)


def format_explanation(explanations: list[PathExplanation], drug_id: int, disease_id: int) -> str:
    """Formats the explanations for CLI output."""
    if not explanations:
        return f"=== Path-Based Explanation: Drug {drug_id} -> Disease {disease_id} ===\n\nNo paths found."
        
    lines = [f"=== Path-Based Explanation: Drug {drug_id} -> Disease {disease_id} ==="]
    
    for i, exp in enumerate(explanations, 1):
        lines.append("")
        path_word = "path" if exp.support_count == 1 else "paths"
        lines.append(f"Pattern {i} ({exp.support_count} supporting {path_word}):")
        lines.append(f"  {exp.meta_path_pattern}")
        lines.append("")
        
        for j, p in enumerate(exp.paths, 1):
            node_names = [n.name for n in p.nodes]
            path_str = " -> ".join(node_names)
            lines.append(f"  Path {j}: {path_str}")
            
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Path-based explanations for drug-disease predictions.")
    parser.add_argument("drug_id", type=int, help="ID of the drug node")
    parser.add_argument("disease_id", type=int, help="ID of the disease node")
    parser.add_argument("--max-hops", type=int, default=3, choices=[1, 2, 3], help="Maximum number of hops (default: 3)")
    
    args = parser.parse_args()
    
    explanations = explain(args.drug_id, args.disease_id, args.max_hops)
    output = format_explanation(explanations, args.drug_id, args.disease_id)
    print(output)


if __name__ == "__main__":
    main()
