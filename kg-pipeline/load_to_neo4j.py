"""Loads normalized CuroVex data into Neo4j via the Python driver.

Reads ``data/normalized/nodes.csv`` and ``data/normalized/edges.csv`` (output
of ``normalize_schema.py``) and loads them into Neo4j using MERGE — fully
idempotent, safe to re-run.

Usage:
    python load_to_neo4j.py
    python load_to_neo4j.py --input-dir data/normalized --batch-size 500
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Property mapping:  CuroVex label → how PrimeKG's source_id maps to the
# schema-defined property name (from docs/DATABASE_SCHEMA.md).
#
# For dual-labeled Gene|Protein nodes we set both entrez_id and symbol, and
# leave uniprot_id null (PrimeKG doesn't provide it — enrichable from DRKG
# or UniProt ID mapping files later).
# ---------------------------------------------------------------------------
LABEL_PROPERTY_MAP: dict[str, dict[str, str]] = {
    "Drug": {
        "id_property": "drugbank_id",
        "name_property": "name",
    },
    "Disease": {
        "id_property": "mondo_id",
        "name_property": "name",
    },
    "Gene|Protein": {
        "id_property": "entrez_id",
        "name_property": "symbol",
    },
    "Pathway": {
        "id_property": "reactome_id",
        "name_property": "name",
    },
    "SideEffect": {
        "id_property": "meddra_id",
        "name_property": "name",
    },
}

# Default batch size for UNWIND operations
DEFAULT_BATCH_SIZE = 1000

# ---------------------------------------------------------------------------
# Relationship endpoint labels for indexed MATCH queries.
# Since all Gene|Protein nodes are given the :Gene label during node load,
# we use :Gene here to leverage the uniqueness constraint index.
# ---------------------------------------------------------------------------
REL_TYPE_ENDPOINT_LABELS: dict[str, tuple[str, str]] = {
    "TREATS": ("Drug", "Disease"),
    "TARGETS": ("Drug", "Gene"),
    "ASSOCIATED_WITH": ("Gene", "Disease"),
    "PART_OF_PATHWAY": ("Gene", "Pathway"),
    "CAUSES_SIDE_EFFECT": ("Drug", "SideEffect"),
    "INTERACTS_WITH": ("Gene", "Gene"),
}


def get_neo4j_config() -> dict[str, str]:
    """Read Neo4j connection details from environment / .env file."""
    load_dotenv()
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "curovex_neo4j_dev"),
    }


def batched(iterable: list[Any], size: int) -> list[list[Any]]:
    """Split *iterable* into chunks of at most *size*."""
    return [iterable[i : i + size] for i in range(0, len(iterable), size)]


# ---------------------------------------------------------------------------
# Cypher query builders
# ---------------------------------------------------------------------------


def build_constraint_queries() -> list[str]:
    """Return Cypher statements to create uniqueness constraints (idempotent).

    Uses ``CREATE CONSTRAINT IF NOT EXISTS`` so re-runs are safe.
    """
    return [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Drug) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Gene) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Protein) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Pathway) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SideEffect) REQUIRE n.id IS UNIQUE",
    ]


def build_index_queries() -> list[str]:
    """Return Cypher statements to create lookup indexes (idempotent)."""
    return [
        "CREATE INDEX IF NOT EXISTS FOR (n:Drug) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Drug) ON (n.drugbank_id)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON (n.mondo_id)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Gene) ON (n.symbol)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Gene) ON (n.entrez_id)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Protein) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Pathway) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Pathway) ON (n.reactome_id)",
        "CREATE INDEX IF NOT EXISTS FOR (n:SideEffect) ON (n.name)",
        "CREATE INDEX IF NOT EXISTS FOR (n:SideEffect) ON (n.meddra_id)",
    ]


def build_node_merge_query(labels: str) -> str:
    """Return a Cypher UNWIND/MERGE query for nodes with *labels*.

    The query MERGEs on ``id`` and sets label-specific properties based on
    the LABEL_PROPERTY_MAP.

    For dual-labeled Gene|Protein nodes the primary MERGE uses :Gene (which
    has a uniqueness constraint) and then adds the :Protein label via SET.
    """
    props = LABEL_PROPERTY_MAP[labels]
    id_prop = props["id_property"]
    name_prop = props["name_property"]

    if labels == "Gene|Protein":
        # MERGE on Gene (indexed), then add Protein label
        return (
            "UNWIND $batch AS row "
            "MERGE (n:Gene {id: row.node_index}) "
            "SET n:Protein, "
            f"n.{id_prop} = row.source_id, "
            f"n.{name_prop} = row.name, "
            "n.name = row.name, "
            "n.source = row.source"
        )
    else:
        primary_label = labels  # single label
        return (
            "UNWIND $batch AS row "
            f"MERGE (n:{primary_label} {{id: row.node_index}}) "
            f"SET n.{id_prop} = row.source_id, "
            f"n.{name_prop} = row.name, "
            "n.name = row.name, "
            "n.source = row.source"
        )


def build_edge_merge_query(rel_type: str) -> str:
    """Return a Cypher UNWIND/MERGE query for relationships of *rel_type*.

    Matches source and target nodes by ``id`` (node_index) using their
    specific labels so Neo4j can use the uniqueness constraint indexes
    instead of doing full node scans.
    """
    src_label, tgt_label = REL_TYPE_ENDPOINT_LABELS[rel_type]
    return (
        "UNWIND $batch AS row "
        f"MATCH (src:{src_label} {{id: row.source_index}}) "
        f"MATCH (tgt:{tgt_label} {{id: row.target_index}}) "
        f"MERGE (src)-[r:{rel_type}]->(tgt) "
        "SET r.source = 'PrimeKG'"
    )


# ---------------------------------------------------------------------------
# Loading logic
# ---------------------------------------------------------------------------


def create_constraints_and_indexes(session: Any) -> None:
    """Create uniqueness constraints and indexes in Neo4j."""
    print("Creating constraints ...")
    for query in build_constraint_queries():
        session.run(query)
    print("Creating indexes ...")
    for query in build_index_queries():
        session.run(query)
    print("Constraints and indexes created.")


def load_nodes(
    session: Any, nodes_df: pd.DataFrame, batch_size: int = DEFAULT_BATCH_SIZE
) -> dict[str, int]:
    """Load nodes into Neo4j, grouped by label.  Returns counts per label."""
    counts: dict[str, int] = {}

    for labels, group in nodes_df.groupby("labels"):
        query = build_node_merge_query(labels)
        records = group.to_dict("records")
        total = len(records)
        loaded = 0

        for chunk in batched(records, batch_size):
            session.run(query, batch=chunk)
            loaded += len(chunk)
            print(f"  {labels}: {loaded}/{total}", end="\r")

        print(f"  {labels}: {total} nodes merged")
        counts[labels] = total

    return counts


def load_edges(
    session: Any, edges_df: pd.DataFrame, batch_size: int = DEFAULT_BATCH_SIZE
) -> dict[str, int]:
    """Load edges into Neo4j, grouped by relationship type.  Returns counts."""
    counts: dict[str, int] = {}

    for rel_type, group in edges_df.groupby("type"):
        query = build_edge_merge_query(rel_type)
        records = group.to_dict("records")
        total = len(records)
        loaded = 0

        for chunk in batched(records, batch_size):
            session.run(query, batch=chunk)
            loaded += len(chunk)
            print(f"  {rel_type}: {loaded}/{total}", end="\r")

        print(f"  {rel_type}: {total} edges merged")
        counts[rel_type] = total

    return counts


def load_to_neo4j(
    input_dir: Path | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    exclude_rel_types: list[str] | None = None,
) -> None:
    """Run the full load pipeline.

    Args:
        input_dir:  Directory containing nodes.csv and edges.csv.
                    Defaults to ``data/normalized``.
        batch_size: Number of rows per UNWIND batch.
        exclude_rel_types: List of relationship types to skip loading.
    """
    if input_dir is None:
        input_dir = Path("data/normalized")

    nodes_path = input_dir / "nodes.csv"
    edges_path = input_dir / "edges.csv"

    for path in (nodes_path, edges_path):
        if not path.exists():
            print(f"ERROR: {path} not found.", file=sys.stderr)
            print("Run normalize_schema.py first.", file=sys.stderr)
            sys.exit(1)

    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)

    if exclude_rel_types:
        before = len(edges_df)
        edges_df = edges_df[~edges_df["type"].isin(exclude_rel_types)]
        print(
            f"Excluded {before - len(edges_df)} edges of type(s): {', '.join(exclude_rel_types)}"
        )

    print(f"Read {len(nodes_df)} nodes and {len(edges_df)} edges.")

    config = get_neo4j_config()
    print(f"Connecting to Neo4j at {config['uri']} ...")

    driver = GraphDatabase.driver(
        config["uri"], auth=(config["user"], config["password"])
    )

    # Verify connectivity
    driver.verify_connectivity()
    print("Connected.")

    start = time.time()

    with driver.session() as session:
        create_constraints_and_indexes(session)

        print("\n--- Loading nodes ---")
        node_counts = load_nodes(session, nodes_df, batch_size)

        print("\n--- Loading edges ---")
        edge_counts = load_edges(session, edges_df, batch_size)

    driver.close()
    elapsed = time.time() - start

    print(f"\nLoad complete in {elapsed:.1f}s.")
    print(f"  Nodes: {sum(node_counts.values())} total")
    for label, count in node_counts.items():
        print(f"    {label}: {count}")
    print(f"  Edges: {sum(edge_counts.values())} total")
    for rel_type, count in edge_counts.items():
        print(f"    {rel_type}: {count}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Load normalized CuroVex data into Neo4j"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Directory with nodes.csv and edges.csv (default: data/normalized)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Rows per UNWIND batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--exclude-rel-types",
        type=str,
        default="",
        help="Comma-separated relationship types to skip (e.g. INTERACTS_WITH,CAUSES_SIDE_EFFECT)",
    )
    args = parser.parse_args()

    exclude = [t.strip() for t in args.exclude_rel_types.split(",") if t.strip()]
    input_dir = Path(args.input_dir) if args.input_dir else None
    load_to_neo4j(
        input_dir=input_dir,
        batch_size=args.batch_size,
        exclude_rel_types=exclude or None,
    )


if __name__ == "__main__":
    main()
