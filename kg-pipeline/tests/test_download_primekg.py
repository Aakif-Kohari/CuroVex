"""Tests for download_primekg.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from download_primekg import (
    EXPECTED_COLUMNS,
    PRIMEKG_URL,
    download_file,
    download_primekg,
    validate_columns,
)

# ---------------------------------------------------------------------------
# validate_columns
# ---------------------------------------------------------------------------


class TestValidateColumns:
    """Tests for the column-validation function."""

    def test_valid_columns(self, tmp_path: Path) -> None:
        """Passes when all expected columns are present."""
        csv_path = tmp_path / "kg.csv"
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        df.to_csv(csv_path, index=False)

        assert validate_columns(csv_path) is True

    def test_valid_columns_with_extras(self, tmp_path: Path) -> None:
        """Passes when expected columns exist alongside extra columns."""
        csv_path = tmp_path / "kg.csv"
        all_cols = EXPECTED_COLUMNS + ["extra_col_1", "extra_col_2"]
        df = pd.DataFrame(columns=all_cols)
        df.to_csv(csv_path, index=False)

        assert validate_columns(csv_path) is True

    def test_missing_columns(self, tmp_path: Path) -> None:
        """Fails when expected columns are missing."""
        csv_path = tmp_path / "kg.csv"
        partial_cols = EXPECTED_COLUMNS[:5]  # only first 5
        df = pd.DataFrame(columns=partial_cols)
        df.to_csv(csv_path, index=False)

        assert validate_columns(csv_path) is False

    def test_empty_csv(self, tmp_path: Path) -> None:
        """Fails when CSV has no columns at all."""
        csv_path = tmp_path / "kg.csv"
        csv_path.write_text("")

        # pandas will raise or return empty — validate should fail
        assert validate_columns(csv_path) is False


# ---------------------------------------------------------------------------
# download_file
# ---------------------------------------------------------------------------


class TestDownloadFile:
    """Tests for the HTTP download function."""

    @patch("download_primekg.requests.get")
    def test_downloads_content(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """Successfully downloads and writes file content."""
        content = b"col1,col2\nval1,val2\n"
        mock_response = MagicMock()
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        dest = tmp_path / "subdir" / "test.csv"
        download_file("https://example.com/test.csv", dest)

        assert dest.exists()
        assert dest.read_bytes() == content

    @patch("download_primekg.requests.get")
    def test_creates_parent_dirs(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        """Creates parent directories if they don't exist."""
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "0"}
        mock_response.iter_content.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        dest = tmp_path / "a" / "b" / "c" / "test.csv"
        download_file("https://example.com/test.csv", dest)

        assert dest.parent.exists()


# ---------------------------------------------------------------------------
# download_primekg (integration of download + validate)
# ---------------------------------------------------------------------------


class TestDownloadPrimekg:
    """Tests for the main download_primekg function."""

    def test_skips_existing_file(self, tmp_path: Path) -> None:
        """Does not download when file already exists and force=False."""
        csv_path = tmp_path / "kg.csv"
        csv_path.write_text("existing data")

        result = download_primekg(output_dir=tmp_path, force=False)

        assert result == csv_path
        assert csv_path.read_text() == "existing data"  # unchanged

    @patch("download_primekg.download_file")
    @patch("download_primekg.validate_columns", return_value=True)
    def test_downloads_when_forced(
        self,
        mock_validate: MagicMock,
        mock_download: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Downloads when file exists and force=True."""
        csv_path = tmp_path / "kg.csv"
        csv_path.write_text("old data")

        download_primekg(output_dir=tmp_path, force=True)

        mock_download.assert_called_once()
        mock_validate.assert_called_once()

    @patch("download_primekg.download_file")
    @patch("download_primekg.validate_columns", return_value=True)
    def test_downloads_when_missing(
        self,
        mock_validate: MagicMock,
        mock_download: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Downloads when file does not exist."""
        download_primekg(output_dir=tmp_path, force=False)

        mock_download.assert_called_once()
        call_args = mock_download.call_args
        assert call_args[0][0] == PRIMEKG_URL  # correct URL
        assert "kg.csv" in str(call_args[0][1])  # correct filename

    @patch("download_primekg.download_file")
    @patch("download_primekg.validate_columns", return_value=False)
    def test_exits_on_validation_failure(
        self,
        mock_validate: MagicMock,
        mock_download: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Exits with code 1 when column validation fails."""
        with pytest.raises(SystemExit) as exc_info:
            download_primekg(output_dir=tmp_path, force=False)

        assert exc_info.value.code == 1
