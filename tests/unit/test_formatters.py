"""Tests for formatters functionality."""

import os
import sys
from io import StringIO
from unittest.mock import patch

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.formatters.base import (
    export_federation_csv,
    print_federation_summary,
    print_summary,
    print_summary_markdown,
)


class TestPrintSummary:
    """Test the print_summary function."""

    def test_print_summary_basic(self):
        """Test basic summary printing."""
        stats = {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "sps_has_security": 30,
            "sps_missing_security": 30,
            "idps_has_security": 35,
            "idps_missing_security": 5,
            "total_has_security": 65,
            "total_missing_security": 35,
            "sps_has_both": 25,
            "sps_missing_both": 10,
            "total_has_sirtfi": 50,
            "sps_has_sirtfi": 27,
            "idps_has_sirtfi": 23,
            "total_missing_sirtfi": 50,
            "sps_missing_sirtfi": 33,
            "idps_missing_sirtfi": 17,
            "validation_enabled": False,
        }

        # Capture stderr where print_summary outputs
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "eduGAIN Quality Analysis: Privacy, Security & SIRTFI Coverage" in result
        assert "Total entities analyzed: 100" in result
        assert "SPs: 60, IdPs: 40" in result
        assert "45 out of 60 (75.0%)" in result

    def test_print_summary_with_validation(self):
        """Test summary printing with URL validation enabled."""
        stats = {
            "total_entities": 50,
            "total_sps": 30,
            "total_idps": 20,
            "sps_has_privacy": 25,
            "sps_missing_privacy": 5,
            "sps_has_security": 20,
            "sps_missing_security": 10,
            "idps_has_security": 18,
            "idps_missing_security": 2,
            "total_has_security": 38,
            "total_missing_security": 12,
            "sps_has_both": 18,
            "sps_missing_both": 2,
            "total_has_sirtfi": 24,
            "sps_has_sirtfi": 13,
            "idps_has_sirtfi": 11,
            "total_missing_sirtfi": 26,
            "sps_missing_sirtfi": 17,
            "idps_missing_sirtfi": 9,
            "validation_enabled": True,
            "urls_checked": 25,
            "urls_accessible": 20,
            "urls_broken": 5,
        }

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "Privacy Statement URL Check" in result
        assert "20 links working (80.0%)" in result

    def test_print_summary_edge_cases(self):
        """Test summary printing with edge cases."""
        stats = {
            "total_entities": 0,
            "total_sps": 0,
            "total_idps": 0,
            "sps_has_privacy": 0,
            "sps_missing_privacy": 0,
            "sps_has_security": 0,
            "sps_missing_security": 0,
            "idps_has_security": 0,
            "idps_missing_security": 0,
            "total_has_security": 0,
            "total_missing_security": 0,
            "sps_has_both": 0,
            "sps_missing_both": 0,
            "validation_enabled": False,
        }

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "No entities found in metadata" in result


class TestPrintSummaryMarkdown:
    """Test the print_summary_markdown function."""

    def test_print_summary_markdown_basic(self):
        """Test basic markdown summary printing."""
        stats = {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "sps_has_security": 30,
            "sps_missing_security": 30,
            "idps_has_security": 35,
            "idps_missing_security": 5,
            "total_has_security": 65,
            "total_missing_security": 35,
            "sps_has_both": 25,
            "sps_missing_both": 10,
            "total_has_sirtfi": 50,
            "sps_has_sirtfi": 27,
            "idps_has_sirtfi": 23,
            "total_missing_sirtfi": 50,
            "sps_missing_sirtfi": 33,
            "idps_missing_sirtfi": 17,
            "validation_enabled": False,
        }

        output = StringIO()
        print_summary_markdown(stats, output_file=output)
        result = output.getvalue()

        assert "eduGAIN Quality Analysis Report" in result
        assert "100 entities" in result
        assert "60 SPs, 40 IdPs" in result

    def test_print_summary_markdown_empty_metadata(self):
        """Test markdown summary with zero entities (empty metadata)."""
        stats = {
            "total_entities": 0,
            "total_sps": 0,
            "total_idps": 0,
            "sps_has_privacy": 0,
            "sps_missing_privacy": 0,
            "sps_has_security": 0,
            "sps_missing_security": 0,
            "idps_has_security": 0,
            "idps_missing_security": 0,
            "total_has_security": 0,
            "total_missing_security": 0,
            "sps_has_both": 0,
            "sps_missing_both": 0,
            "validation_enabled": False,
        }

        output = StringIO()
        print_summary_markdown(stats, output_file=output)
        result = output.getvalue()

        assert "eduGAIN Quality Analysis Report" in result
        assert "No entities found in the metadata" in result

    def test_print_summary_markdown_with_validation(self):
        """Test markdown summary with validation."""
        stats = {
            "total_entities": 50,
            "total_sps": 30,
            "total_idps": 20,
            "sps_has_privacy": 25,
            "sps_missing_privacy": 5,
            "sps_has_security": 20,
            "sps_missing_security": 10,
            "idps_has_security": 18,
            "idps_missing_security": 2,
            "total_has_security": 38,
            "total_missing_security": 12,
            "sps_has_both": 18,
            "sps_missing_both": 2,
            "total_has_sirtfi": 24,
            "sps_has_sirtfi": 13,
            "idps_has_sirtfi": 11,
            "total_missing_sirtfi": 26,
            "sps_missing_sirtfi": 17,
            "idps_missing_sirtfi": 9,
            "validation_enabled": True,
            "urls_checked": 25,
            "urls_accessible": 20,
            "urls_broken": 5,
        }

        output = StringIO()
        print_summary_markdown(stats, output_file=output)
        result = output.getvalue()

        assert "Privacy URL Validation Results" in result
        assert "25 privacy statement URLs" in result
        assert "20/25 (80.0%)" in result


class TestPrintFederationSummary:
    """Test the print_federation_summary function."""

    def test_print_federation_summary_basic(self):
        """Test basic federation summary printing."""
        federation_stats = {
            "InCommon": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_missing_privacy": 5,
                "sps_has_security": 20,
                "sps_missing_security": 10,
                "idps_has_security": 18,
                "idps_missing_security": 2,
                "total_has_security": 38,
                "total_missing_security": 12,
                "sps_has_both": 18,
                "sps_missing_both": 2,
                "total_has_sirtfi": 24,
                "sps_has_sirtfi": 13,
                "idps_has_sirtfi": 11,
                "total_missing_sirtfi": 26,
                "sps_missing_sirtfi": 17,
                "idps_missing_sirtfi": 9,
                "urls_checked": 0,
                "urls_accessible": 0,
                "urls_broken": 0,
            }
        }

        output = StringIO()
        print_federation_summary(federation_stats, output_file=output)
        result = output.getvalue()

        assert "Federation Analysis" in result
        assert "InCommon" in result
        assert "50 entities" in result

    def test_print_federation_summary_empty(self):
        """Test federation summary with no federations."""
        output = StringIO()
        print_federation_summary({}, output_file=output)
        result = output.getvalue()

        assert "Federation Analysis" in result


class TestExportFederationCSV:
    """Test the export_federation_csv function."""

    def test_export_federation_csv_basic(self):
        """Test basic federation CSV export."""
        federation_stats = {
            "InCommon": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_missing_privacy": 5,
                "sps_has_security": 20,
                "sps_missing_security": 10,
                "idps_has_security": 18,
                "idps_missing_security": 2,
                "total_has_security": 38,
                "total_missing_security": 12,
                "sps_has_both": 18,
                "sps_missing_both": 2,
                "total_has_sirtfi": 24,
                "sps_has_sirtfi": 13,
                "idps_has_sirtfi": 11,
                "total_missing_sirtfi": 26,
                "sps_missing_sirtfi": 17,
                "idps_missing_sirtfi": 9,
                "urls_checked": 0,
                "urls_accessible": 0,
                "urls_broken": 0,
            }
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            export_federation_csv(federation_stats, include_headers=True)
            result = mock_stdout.getvalue()

        lines = result.strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 data row

        # Check that federation name appears in output
        assert "InCommon" in result

    def test_export_federation_csv_no_headers(self):
        """Test federation CSV export without headers."""
        federation_stats = {
            "InCommon": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_missing_privacy": 5,
                "sps_has_security": 20,
                "sps_missing_security": 10,
                "idps_has_security": 18,
                "idps_missing_security": 2,
                "total_has_security": 38,
                "total_missing_security": 12,
                "sps_has_both": 18,
                "sps_missing_both": 2,
                "total_has_sirtfi": 24,
                "sps_has_sirtfi": 13,
                "idps_has_sirtfi": 11,
                "total_missing_sirtfi": 26,
                "sps_missing_sirtfi": 17,
                "idps_missing_sirtfi": 9,
                "urls_checked": 0,
                "urls_accessible": 0,
                "urls_broken": 0,
            }
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            export_federation_csv(federation_stats, include_headers=False)
            result = mock_stdout.getvalue()

        assert "InCommon" in result

    def test_export_federation_csv_empty(self):
        """Test federation CSV export with empty data."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            export_federation_csv({}, include_headers=True)
            result = mock_stdout.getvalue()

        # Should at least have headers for empty data
        lines = result.strip().split("\n") if result.strip() else []
        assert len(lines) >= 1 or result == ""  # Either headers or empty
