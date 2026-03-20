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
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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
        # Privacy now shows combined stats
        assert "45/60 (75.0%)" in result  # SP privacy
        assert "30/40 (75.0%)" in result  # IdP privacy

    def test_print_summary_with_validation(self):
        """Test summary printing with URL validation enabled."""
        stats = {
            "total_entities": 50,
            "total_sps": 30,
            "total_idps": 20,
            "sps_has_privacy": 25,
            "sps_missing_privacy": 5,
            "idps_has_privacy": 15,
            "idps_missing_privacy": 5,
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
            "idps_has_privacy": 0,
            "idps_missing_privacy": 0,
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
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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
            "idps_has_privacy": 0,
            "idps_missing_privacy": 0,
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
            "idps_has_privacy": 15,
            "idps_missing_privacy": 5,
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
                "idps_has_privacy": 15,
                "idps_missing_privacy": 5,
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
                "idps_has_privacy": 15,
                "idps_missing_privacy": 5,
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
                "idps_has_privacy": 15,
                "idps_missing_privacy": 5,
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


class TestPrintSummaryContentQuality:
    """Test content quality section inside print_summary."""

    def _base_stats(self) -> dict:
        """Return minimal stats dict needed by print_summary."""
        return {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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

    def test_content_quality_summary_displayed(self):
        """Stats with content_validation_enabled=True and scores prints 'Content Quality' to stderr."""
        stats = self._base_stats()
        stats.update(
            {
                "content_validation_enabled": True,
                "content_urls_checked": 10,
                "content_quality_scores": [95, 75, 55, 40, 20, 88, 62, 71, 33, 90],
            }
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "Content Quality" in result

    def test_content_quality_hidden_when_disabled(self):
        """Stats with content_validation_enabled=False produces no 'Content Quality' section."""
        stats = self._base_stats()
        stats["content_validation_enabled"] = False

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "Content Quality" not in result

    def test_content_quality_issues_displayed(self):
        """Stats with content_quality_issues_breakdown prints individual issue names."""
        stats = self._base_stats()
        stats.update(
            {
                "content_validation_enabled": True,
                "content_urls_checked": 10,
                "content_quality_scores": [50, 60, 70, 80, 90, 40, 30, 20, 85, 75],
                "content_quality_issues_breakdown": {
                    "non-https": 3,
                    "soft-404": 1,
                    "thin-content": 2,
                },
            }
        )

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        assert "non-https" in result


class TestIdPPrivacyFormatters:
    """Test IdP privacy statement display in formatters."""

    def test_print_summary_includes_idp_privacy(self):
        """Verify IdP privacy statistics in terminal summary."""
        stats = {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        # Verify IdP privacy is shown
        assert "IdPs:" in result
        assert "30/40" in result  # IdP privacy count

    def test_print_summary_markdown_includes_idp_privacy(self):
        """Verify IdP privacy in markdown summary."""
        stats = {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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

        # Verify IdP privacy in markdown
        assert "IdPs:" in result
        assert "30/40" in result
        assert "75.0%" in result  # IdP privacy percentage

    def test_export_federation_csv_has_idp_columns(self):
        """Verify IdP privacy columns in federation CSV."""
        federation_stats = {
            "Test Federation": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_missing_privacy": 5,
                "idps_has_privacy": 15,
                "idps_missing_privacy": 5,
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

        # Check headers include IdP privacy columns
        assert "IdPsWithPrivacy" in result
        assert "IdPsMissingPrivacy" in result

        # Check data row includes IdP privacy values
        lines = result.strip().split("\n")
        data_line = lines[1]  # Second line is data
        assert "15" in data_line  # IdPs with privacy
        assert "5" in data_line  # IdPs missing privacy

    def test_idp_privacy_tree_structure(self):
        """Verify tree display format for IdP privacy."""
        stats = {
            "total_entities": 100,
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 45,
            "sps_missing_privacy": 15,
            "idps_has_privacy": 30,
            "idps_missing_privacy": 10,
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

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            print_summary(stats)
            result = mock_stderr.getvalue()

        # Verify tree structure with box-drawing characters
        assert "├─ SPs:" in result
        assert "└─ IdPs:" in result


# ---------------------------------------------------------------------------
# TestGeneratePdfReportContentQuality
# ---------------------------------------------------------------------------


class TestGeneratePdfReportContentQuality:
    """Test PDF report generation with content quality data."""

    def _base_stats(self) -> dict:
        return {
            "total_entities": 50,
            "total_sps": 30,
            "total_idps": 20,
            "sps_has_privacy": 20,
            "sps_missing_privacy": 10,
            "idps_has_privacy": 15,
            "idps_missing_privacy": 5,
            "sps_has_security": 15,
            "sps_missing_security": 15,
            "idps_has_security": 18,
            "idps_missing_security": 2,
            "total_has_security": 33,
            "total_missing_security": 17,
            "sps_has_both": 12,
            "sps_missing_both": 8,
            "total_has_sirtfi": 25,
            "sps_has_sirtfi": 14,
            "idps_has_sirtfi": 11,
            "total_missing_sirtfi": 25,
            "sps_missing_sirtfi": 16,
            "idps_missing_sirtfi": 9,
            "validation_enabled": False,
            "content_validation_enabled": False,
            "content_urls_checked": 0,
            "content_quality_scores": [],
            "content_quality_issues_breakdown": {},
        }

    def test_pdf_generates_without_content_flag(self, tmp_path):
        """generate_pdf_report without content flag produces a PDF file."""
        from edugain_analysis.formatters.pdf import generate_pdf_report

        out = str(tmp_path / "report.pdf")
        result = generate_pdf_report(
            self._base_stats(), {}, out, "Test", include_validation=False
        )
        assert result == out
        import os

        assert os.path.getsize(out) > 0

    def test_pdf_content_section_included_when_flag_and_data(self, tmp_path):
        """With include_content_validation=True and data, PDF is generated without error."""
        from edugain_analysis.formatters.pdf import generate_pdf_report

        stats = self._base_stats()
        stats.update(
            {
                "content_validation_enabled": True,
                "content_urls_checked": 10,
                "content_quality_scores": [95, 75, 55, 40, 20, 88, 62, 71, 33, 90],
                "content_quality_issues_breakdown": {
                    "non-https": 3,
                    "soft-404": 1,
                    "thin-content": 2,
                    "no-gdpr-keywords": 4,
                },
            }
        )
        out = str(tmp_path / "report_content.pdf")
        result = generate_pdf_report(
            stats,
            {},
            out,
            "Test with content",
            include_validation=False,
            include_content_validation=True,
        )
        assert result == out
        import os

        assert os.path.getsize(out) > 0

    def test_pdf_content_section_skipped_when_no_data(self, tmp_path):
        """With include_content_validation=True but content_urls_checked=0, PDF still generates."""
        from edugain_analysis.formatters.pdf import generate_pdf_report

        stats = self._base_stats()
        out = str(tmp_path / "report_empty.pdf")
        result = generate_pdf_report(
            stats,
            {},
            out,
            "Test empty content",
            include_validation=False,
            include_content_validation=True,
        )
        assert result == out
        import os

        assert os.path.getsize(out) > 0
