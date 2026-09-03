"""Maps PrimeKG raw columns onto the CuroVex node/relationship schema.

Reads ``data/raw/kg.csv`` (PrimeKG) and outputs two normalized CSVs:
  - ``data/normalized/nodes.csv``  — deduplicated nodes with CuroVex labels
  - ``data/normalized/edges.csv``  — edges mapped to CuroVex relationship types

Only node types and relationship types defined in ``docs/DATABASE_SCHEMA.md``
are kept; everything else is dropped with a summary printed to stdout.

Usage:
    python normalize_schema.py
    python normalize_schema.py --input data/raw/kg.csv --output-dir data/normalized
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Node-type mapping: PrimeKG x_type/y_type → CuroVex Neo4j label(s)
#
# PrimeKG's "gene/protein" type is dual-labeled because the CuroVex schema
# defines Gene (entrez_id, symbol) and Protein (uniprot_id, name) as separate
# labels that participate in different relationships:
#   TARGETS:         Drug → Protein
#   ASSOCIATED_WITH: Gene → Disease
#   INTERACTS_WITH:  Protein → Protein
#   PART_OF_PATHWAY: Gene/Protein → Pathway
#
# PrimeKG doesn't distinguish them, so we assign BOTH labels to the same node.
#
# "effect/phenotype" maps to SideEffect — the closest match in the schema.
# ---------------------------------------------------------------------------
NODE_TYPE_MAP: dict[str, list[str]] = {
    "drug": ["Drug"],
    "disease": ["Disease"],
    "gene/protein": ["Gene", "Protein"],
    "pathway": ["Pathway"],
    "effect/phenotype": ["SideEffect"],
}

# Node types present in PrimeKG but NOT in the CuroVex schema — dropped.
SKIPPED_NODE_TYPES = {
    "anatomy",
    "biological_process",
    "cellular_component",
    "molecular_function",
    "exposure",
}

# ---------------------------------------------------------------------------
# Relationship mapping: PrimeKG display_relation → CuroVex relationship type
#
# Only the listed display_relation values are mapped.  Edges whose
# display_relation is not in this dict are dropped — they connect node types
# outside the CuroVex schema or represent semantics we don't model (e.g.
# "contraindication").
# ---------------------------------------------------------------------------
DISPLAY_RELATION_MAP: dict[str, str] = {
    # TREATS (Drug → Disease)
    "indication": "TREATS",
    "off-label use": "TREATS",
    "treats": "TREATS",
    "palliates": "TREATS",
    # TARGETS (Drug → Protein)
    "target": "TARGETS",
    "carrier": "TARGETS",
    "enzyme": "TARGETS",
    "transporter": "TARGETS",
    # ASSOCIATED_WITH (Gene → Disease)
    "associated with": "ASSOCIATED_WITH",
    # PART_OF_PATHWAY (Gene/Protein → Pathway)
    # PrimeKG uses "pathway" as the relation connecting gene/protein → pathway
    "pathway": "PART_OF_PATHWAY",
    # CAUSES_SIDE_EFFECT (Drug → SideEffect)
    "side effect": "CAUSES_SIDE_EFFECT",
    "phenotype present": "CAUSES_SIDE_EFFECT",
    # INTERACTS_WITH (Protein → Protein)
    "ppi": "INTERACTS_WITH",
    "interacts with": "INTERACTS_WITH",
}

# ---------------------------------------------------------------------------
# Direction validation: CuroVex relationship → (source_primekg_type, target_primekg_type)
#
# PrimeKG edges are directed (x → y).  If a valid mapped edge has its
# endpoints swapped relative to the CuroVex schema, we flip it.
# ---------------------------------------------------------------------------
EXPECTED_DIRECTIONS: dict[str, tuple[str, ...]] = {
    "TREATS": ("drug",),
    "TARGETS": ("drug",),
    "ASSOCIATED_WITH": ("gene/protein",),
    "PART_OF_PATHWAY": ("gene/protein",),
    "CAUSES_SIDE_EFFECT": ("drug",),
    "INTERACTS_WITH": ("gene/protein",),
}


def _get_default_input() -> Path:
    """Return the default input path based on DATA_DIR env var."""
    load_dotenv()
    data_dir = Path(os.getenv("DATA_DIR", "data/raw"))
    return data_dir / "kg.csv"


def extract_nodes(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and deduplicate nodes from both x and y columns.

    Returns a DataFrame with columns:
        node_index, source_id, name, labels, source, original_type
    """
    x_nodes = df[["x_index", "x_id", "x_type", "x_name", "x_source"]].rename(
        columns={
            "x_index": "node_index",
            "x_id": "source_id",
            "x_type": "original_type",
            "x_name": "name",
            "x_source": "source",
        }
    )
    y_nodes = df[["y_index", "y_id", "y_type", "y_name", "y_source"]].rename(
        columns={
            "y_index": "node_index",
            "y_id": "source_id",
            "y_type": "original_type",
            "y_name": "name",
            "y_source": "source",
        }
    )

    all_nodes = pd.concat([x_nodes, y_nodes], ignore_index=True)

    # Filter to supported types
    supported_mask = all_nodes["original_type"].isin(NODE_TYPE_MAP)
    dropped = all_nodes[~supported_mask]["original_type"].value_counts()
    all_nodes = all_nodes[supported_mask]

    if not dropped.empty:
        print("Dropped node types (not in CuroVex schema):")
        for ntype, count in dropped.items():
            print(f"  {ntype}: {count} occurrences")

    # Deduplicate by node_index (each unique entity appears in many rows)
    nodes = all_nodes.drop_duplicates(subset=["node_index"]).copy()

    # Map to CuroVex labels (pipe-separated for dual labels)
    nodes["labels"] = nodes["original_type"].map(
        lambda t: "|".join(NODE_TYPE_MAP[t])
    )

    # Ensure source_id is a string for consistent handling
    nodes["source_id"] = nodes["source_id"].astype(str)
    nodes["node_index"] = nodes["node_index"].astype(int)

    print(f"Extracted {len(nodes)} unique nodes:")
    for label_group, count in nodes["labels"].value_counts().items():
        print(f"  {label_group}: {count}")

    return nodes[["node_index", "source_id", "name", "labels", "source", "original_type"]]


def extract_edges(df: pd.DataFrame, valid_indices: set[int]) -> pd.DataFrame:
    """Extract and map edges to CuroVex relationship types.

    Only keeps edges where:
    1. Both endpoints are in *valid_indices* (i.e. have supported node types)
    2. The display_relation maps to a CuroVex relationship type

    Returns a DataFrame with columns:
        source_index, target_index, type, display_relation
    """
    # Filter: both endpoints must be supported nodes
    endpoint_mask = df["x_index"].isin(valid_indices) & df["y_index"].isin(
        valid_indices
    )
    edges = df[endpoint_mask].copy()

    # Normalize display_relation (lowercase, strip whitespace)
    edges["display_relation_clean"] = (
        edges["display_relation"].str.lower().str.strip()
    )

    # Map to CuroVex relationship type
    edges["type"] = edges["display_relation_clean"].map(DISPLAY_RELATION_MAP)

    # Drop unmapped relations
    unmapped = edges[edges["type"].isna()]["display_relation_clean"].value_counts()
    edges = edges[edges["type"].notna()].copy()

    if not unmapped.empty:
        print("\nDropped display_relation values (no CuroVex mapping):")
        for rel, count in unmapped.head(20).items():
            print(f"  '{rel}': {count}")
        if len(unmapped) > 20:
            print(f"  ... and {len(unmapped) - 20} more")

    # Handle direction: if the source node type doesn't match the expected
    # direction for this relationship type, swap source and target
    edges["x_type_clean"] = edges["x_type"].str.lower().str.strip()

    # EXPECTED_DIRECTIONS entries are all single-element tuples, so flatten once:
    _EXPECTED_SOURCE = {k: v[0] for k, v in EXPECTED_DIRECTIONS.items() if v}

    # Vectorized flip logic (replaces slow .apply() row-by-row processing)
    edges["_expected_source"] = edges["type"].map(_EXPECTED_SOURCE)
    needs_flip = edges["x_type_clean"] != edges["_expected_source"]

    flipped_x = edges["x_index"].where(~needs_flip, edges["y_index"])
    flipped_y = edges["y_index"].where(~needs_flip, edges["x_index"])
    edges["x_index"], edges["y_index"] = flipped_x, flipped_y
    edges = edges.drop(columns=["_expected_source"])

    result = edges[["x_index", "y_index", "type", "display_relation"]].rename(
        columns={"x_index": "source_index", "y_index": "target_index"}
    )

    # Deduplicate edges (same source, target, type)
    before_dedup = len(result)
    result = result.drop_duplicates(
        subset=["source_index", "target_index", "type"]
    )
    if before_dedup > len(result):
        print(f"\nDeduplicated edges: {before_dedup} → {len(result)}")

    result["source_index"] = result["source_index"].astype(int)
    result["target_index"] = result["target_index"].astype(int)

    print(f"\nExtracted {len(result)} edges:")
    for rel_type, count in result["type"].value_counts().items():
        print(f"  {rel_type}: {count}")

    return result


def normalize(
    input_path: Path | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Run the full normalization pipeline.

    Args:
        input_path: Path to PrimeKG kg.csv.  Defaults to DATA_DIR/kg.csv.
        output_dir: Directory for output CSVs.  Defaults to data/normalized.

    Returns:
        Tuple of (nodes_path, edges_path).
    """
    if input_path is None:
        input_path = _get_default_input()
    if output_dir is None:
        output_dir = Path("data/normalized")

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        print("Run download_primekg.py first.", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading PrimeKG from {input_path} ...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows.")

    # --- Nodes ---
    print("\n--- Extracting nodes ---")
    nodes = extract_nodes(df)

    valid_indices = set(nodes["node_index"].values)

    # --- Edges ---
    print("\n--- Extracting edges ---")
    edges = extract_edges(df, valid_indices)

    # --- Write outputs ---
    nodes_path = output_dir / "nodes.csv"
    edges_path = output_dir / "edges.csv"

    nodes.to_csv(nodes_path, index=False)
    edges.to_csv(edges_path, index=False)

    print(f"\nNormalized nodes saved to {nodes_path}")
    print(f"Normalized edges saved to {edges_path}")

    return nodes_path, edges_path


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Normalize PrimeKG data to CuroVex schema"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to PrimeKG kg.csv (default: DATA_DIR/kg.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for normalized CSVs (default: data/normalized)",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    normalize(input_path=input_path, output_dir=output_dir)


if __name__ == "__main__":
    main()
