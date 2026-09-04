"""
Cross-check DRKG against PrimeKG loaded in Neo4j.
"""

import argparse
import logging
import os
import shutil
import sys
import tarfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DRKG_URL = "https://dgl-data.s3-us-west-2.amazonaws.com/dataset/DRKG/drkg.tar.gz"

DRKG_ENTITY_TYPE_MAP = {
    "Compound": "Drug",
    "Disease": "Disease",
    "Gene": "Gene",
}

DRKG_RELATION_MAP = {
    "treats": "TREATS",
    "indication": "TREATS",
    "target": "TARGETS",
    "carrier": "TARGETS",
    "enzyme": "TARGETS",
    "transporter": "TARGETS",
    "associated with": "ASSOCIATED_WITH",
    "side effect": "CAUSES_SIDE_EFFECT",
    "ppi": "INTERACTS_WITH",
    "interacts with": "INTERACTS_WITH",
}


def download_drkg(output_dir: Path) -> Path:
    """Download and extract DRKG dataset to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "drkg.tsv"

    if filepath.exists():
        logger.info(f"DRKG dataset already exists at {filepath}")
        return filepath

    tar_path = output_dir / "drkg.tar.gz"
    logger.info(f"Downloading DRKG dataset from {DRKG_URL}...")
    response = requests.get(DRKG_URL, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024

    with open(tar_path, "wb") as f, tqdm(
        total=total_size, unit="iB", unit_scale=True, desc="drkg.tar.gz"
    ) as progress_bar:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            f.write(data)

    logger.info("Download complete. Extracting drkg.tsv...")

    # Extract only the drkg.tsv file from the archive
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("drkg.tsv"):
                extracted_file = tar.extractfile(member)
                if extracted_file is not None:
                    with open(filepath, "wb") as out_f:
                        # shutil.copyfileobj handles the chunking automatically and safely
                        shutil.copyfileobj(extracted_file, out_f)
                    logger.info(f"Successfully extracted DRKG dataset to {filepath}")
                    break
        else:
            logger.error("drkg.tsv not found inside the downloaded archive.")
            tar_path.unlink(missing_ok=True)
            sys.exit(1)

    # Clean up the compressed file to save disk space
    tar_path.unlink(missing_ok=True)
    return filepath


def parse_drkg(filepath: Path) -> dict:
    """
    Parse DRKG TSV file to count entity and relation types.

    Args:
        filepath: Path to the DRKG TSV file.

    Returns:
        dict: A dictionary containing entity counts, relation counts, and total triplets.
    """
    logger.info(f"Parsing DRKG dataset at {filepath}...")

    unique_entities = set()
    entity_type_counts = {}
    relation_type_counts = {}
    total_triplets = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 3:
                continue

            head, relation, tail = parts

            unique_entities.add(head)
            unique_entities.add(tail)

            # Extract relation type (e.g., DRUGBANK::target -> target)
            rel_type = (
                relation.split("::")[-1].lower()
                if "::" in relation
                else relation.lower()
            )
            relation_type_counts[rel_type] = relation_type_counts.get(rel_type, 0) + 1
            total_triplets += 1

    # Count unique entity types
    for entity in unique_entities:
        ent_type = entity.split("::")[0] if "::" in entity else entity
        entity_type_counts[ent_type] = entity_type_counts.get(ent_type, 0) + 1

    return {
        "entity_counts": entity_type_counts,
        "relation_counts": relation_type_counts,
        "total_triplets": total_triplets,
    }


def get_neo4j_config() -> dict[str, str]:
    """Get Neo4j configuration from environment variables."""
    load_dotenv()
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "curovex_neo4j_dev"),
    }


def get_primekg_counts_from_neo4j() -> dict:
    """
    Query Neo4j for node and edge counts.

    Returns:
        dict: Node counts by label, edge counts by type, and total edges.
    """
    config = get_neo4j_config()
    driver = GraphDatabase.driver(
        config["uri"], auth=(config["user"], config["password"])
    )

    counts = {
        "entity_counts": {},
        "relation_counts": {},
        "total_triplets": 0,
    }

    with driver.session() as session:
        # Node counts
        node_result = session.run(
            "MATCH (n) RETURN labels(n) AS labels, count(n) AS cnt"
        )
        for record in node_result:
            labels = record["labels"]
            cnt = record["cnt"]

            # Handle Gene/Protein dual-labeling in CuroVex
            if "Gene" in labels and "Protein" in labels:
                label_str = "Gene/Protein"
            else:
                label_str = "/".join(sorted(labels)) if labels else "Unknown"

            counts["entity_counts"][label_str] = (
                counts["entity_counts"].get(label_str, 0) + cnt
            )

        # Edge counts
        edge_result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt"
        )
        for record in edge_result:
            r_type = record["type"]
            cnt = record["cnt"]
            counts["relation_counts"][r_type] = (
                counts["relation_counts"].get(r_type, 0) + cnt
            )
            counts["total_triplets"] += cnt

    driver.close()
    return counts


def build_report(primekg_counts: dict, drkg_counts: dict) -> str:
    """
    Build a side-by-side discrepancy report.

    Args:
        primekg_counts: Counts from PrimeKG (Neo4j).
        drkg_counts: Counts from DRKG (parsed TSV).

    Returns:
        str: Formatted report string.
    """
    lines = []
    lines.append("=== CuroVex DRKG Cross-Check Report ===\n")

    # Map DRKG entity counts to CuroVex categories
    mapped_drkg_entities = {}
    for drkg_ent, cnt in drkg_counts["entity_counts"].items():
        curovex_cat = DRKG_ENTITY_TYPE_MAP.get(drkg_ent, drkg_ent)
        if curovex_cat == "Gene":
            curovex_cat = "Gene/Protein"
        mapped_drkg_entities[curovex_cat] = (
            mapped_drkg_entities.get(curovex_cat, 0) + cnt
        )

    # Map DRKG relation counts to CuroVex categories
    mapped_drkg_relations = {}
    for drkg_rel, cnt in drkg_counts["relation_counts"].items():
        curovex_rel = DRKG_RELATION_MAP.get(drkg_rel, drkg_rel.upper())
        mapped_drkg_relations[curovex_rel] = (
            mapped_drkg_relations.get(curovex_rel, 0) + cnt
        )

    lines.append("--- Entity/Node Counts ---")
    lines.append(f"{'Category':<18}{'PrimeKG':<11}{'DRKG':<11}{'Delta':<11}")

    all_ent_cats = sorted(
        set(primekg_counts["entity_counts"].keys()) | set(mapped_drkg_entities.keys())
    )
    for cat in all_ent_cats:
        p_cnt = primekg_counts["entity_counts"].get(cat, 0)
        d_cnt = mapped_drkg_entities.get(cat, 0)
        delta = d_cnt - p_cnt
        delta_str = f"+{delta:,}" if delta > 0 else f"{delta:,}"
        lines.append(f"{cat:<18}{p_cnt:<11,}{d_cnt:<11,}{delta_str:<11}")

    lines.append("\n--- Relationship/Edge Counts ---")
    lines.append(f"{'Category':<18}{'PrimeKG':<11}{'DRKG':<11}{'Delta':<11}")

    all_rel_cats = sorted(
        set(primekg_counts["relation_counts"].keys())
        | set(mapped_drkg_relations.keys())
    )
    for cat in all_rel_cats:
        p_cnt = primekg_counts["relation_counts"].get(cat, 0)
        d_cnt = mapped_drkg_relations.get(cat, 0)
        delta = d_cnt - p_cnt
        delta_str = f"+{delta:,}" if delta > 0 else f"{delta:,}"
        lines.append(f"{cat:<18}{p_cnt:<11,}{d_cnt:<11,}{delta_str:<11}")

    lines.append(
        f"\nTotal triplets:   PrimeKG: {primekg_counts['total_triplets']:,}   DRKG: {drkg_counts['total_triplets']:,}"
    )
    return "\n".join(lines)


def crosscheck(output_dir: str, skip_download: bool):
    """Run the cross-check pipeline."""
    out_path = Path(output_dir)

    if not skip_download:
        filepath = download_drkg(out_path)
    else:
        filepath = out_path / "drkg.tsv"
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            sys.exit(1)

    drkg_counts = parse_drkg(filepath)

    logger.info("Querying Neo4j for PrimeKG counts...")
    try:
        primekg_counts = get_primekg_counts_from_neo4j()
    except Exception as e:
        logger.error(f"Failed to get PrimeKG counts from Neo4j: {e}")
        sys.exit(1)

    report = build_report(primekg_counts, drkg_counts)
    print("\n" + report)


def main():
    parser = argparse.ArgumentParser(
        description="Cross-check DRKG dataset against Neo4j PrimeKG"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to store DRKG dataset",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading DRKG if already present",
    )
    args = parser.parse_args()

    crosscheck(args.output_dir, args.skip_download)


if __name__ == "__main__":
    main()
