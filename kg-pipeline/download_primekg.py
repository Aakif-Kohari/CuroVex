"""Downloads PrimeKG source files from Harvard Dataverse.

Usage:
    python download_primekg.py            # downloads to DATA_DIR (default: data/raw)
    python download_primekg.py --force     # re-download even if file exists
    python download_primekg.py --output-dir /tmp/kg  # override output directory
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# PrimeKG kg.csv on Harvard Dataverse (DOI: 10.7910/DVN/IXA7BM)
PRIMEKG_URL = "https://dataverse.harvard.edu/api/access/datafile/6180620"
PRIMEKG_FILENAME = "kg.csv"

# The 12 expected columns in PrimeKG's kg.csv
EXPECTED_COLUMNS = [
    "relation",
    "display_relation",
    "x_index",
    "x_id",
    "x_type",
    "x_name",
    "x_source",
    "y_index",
    "y_id",
    "y_type",
    "y_name",
    "y_source",
]


def get_data_dir() -> Path:
    """Return the raw data directory from DATA_DIR env var or default."""
    load_dotenv()
    return Path(os.getenv("DATA_DIR", "data/raw"))


def download_file(
    url: str, dest: Path, chunk_size: int = 8192, timeout: int = 120
) -> None:
    """Download a file from *url* to *dest* with a tqdm progress bar.

    Creates parent directories if they don't exist.
    """
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    dest.parent.mkdir(parents=True, exist_ok=True)

    with (
        open(dest, "wb") as fh,
        tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=dest.name,
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=chunk_size):
            fh.write(chunk)
            pbar.update(len(chunk))


def validate_columns(filepath: Path) -> bool:
    """Check that *filepath* contains the expected PrimeKG columns.

    Only reads the header row — does not load the full file into memory.
    Returns True if all expected columns are present.
    """
    try:
        df_header = pd.read_csv(filepath, nrows=0)
    except pd.errors.EmptyDataError:
        print("ERROR: File is empty (no columns).", file=sys.stderr)
        return False

    actual_columns = list(df_header.columns)
    missing = [col for col in EXPECTED_COLUMNS if col not in actual_columns]

    if missing:
        print(f"ERROR: Missing expected columns: {missing}", file=sys.stderr)
        print(f"  Found columns: {actual_columns}", file=sys.stderr)
        return False

    print(f"Column validation passed ({len(actual_columns)} columns found).")
    return True


def download_primekg(output_dir: Path | None = None, force: bool = False) -> Path:
    """Download PrimeKG kg.csv and return the path to the saved file.

    Args:
        output_dir: Directory to save the file in.  Falls back to DATA_DIR
                    env var, then ``data/raw``.
        force:      If True, re-download even when the file already exists.

    Returns:
        Path to the downloaded (or already-existing) kg.csv.

    Raises:
        SystemExit: If column validation fails after download.
        requests.HTTPError: If the download request fails.
    """
    data_dir = output_dir if output_dir is not None else get_data_dir()
    dest = data_dir / PRIMEKG_FILENAME

    if dest.exists() and not force:
        print(f"File already exists: {dest}")
        print("Use --force to re-download.")
        return dest

    print(f"Downloading PrimeKG to {dest} ...")
    download_file(PRIMEKG_URL, dest)
    print("Download complete.")

    print("Validating columns ...")
    if not validate_columns(dest):
        sys.exit(1)

    print(f"PrimeKG saved to {dest}")
    return dest


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download PrimeKG dataset from Harvard Dataverse"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the file already exists",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override output directory (default: DATA_DIR env var or data/raw)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    download_primekg(output_dir=output_dir, force=args.force)


if __name__ == "__main__":
    main()
