"""Tests for CLI main functionality."""

import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.cli.main import main


class TestCLIMain:
    """Test the main CLI function."""

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary")
    def test_main_default_summary(
        self,
        mock_print_summary,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with default summary output."""
        # Mock return values
        mock_get_federation.return_value = {"https://incommon.org": "InCommon"}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 100}, {})

        # Test with default arguments (summary)
        with patch("sys.argv", ["analyze.py"]):
            main()

        # Verify function calls
        mock_get_federation.assert_called_once()
        mock_get_metadata.assert_called_once()
        mock_parse.assert_called_once()
        mock_analyze.assert_called_once()
        mock_print_summary.assert_called_once()

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary_markdown")
    @patch("edugain_analysis.cli.main.print_federation_summary")
    def test_main_report_option(
        self,
        mock_print_federation,
        mock_print_markdown,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --report option."""
        # Mock return values
        mock_get_federation.return_value = {"https://incommon.org": "InCommon"}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 100}, {"InCommon": {}})

        with patch("sys.argv", ["analyze.py", "--report"]):
            main()

        # Should call both markdown report functions
        mock_print_markdown.assert_called_once()
        mock_print_federation.assert_called_once()

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary")
    def test_main_validate_option(
        self,
        mock_print_summary,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --validate option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = (
            [],
            {"total_entities": 100, "validation_enabled": True},
            {},
        )

        with patch("sys.argv", ["analyze.py", "--validate"]):
            main()

        # Should call analyze with validation enabled
        args, kwargs = mock_analyze.call_args
        # Third positional argument should be validate_urls=True
        assert args[2] is True

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_entities(
        self,
        mock_stdout,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv entities option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        # Mock entity data
        entities_list = [
            [
                "InCommon",
                "SP",
                "Test Org",
                "https://test.org",
                "Yes",
                "https://test.org/privacy",
                "No",
            ]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})

        with patch("sys.argv", ["analyze.py", "--csv", "entities"]):
            main()

        output = mock_stdout.getvalue()
        # Should output CSV with headers
        assert "Federation,EntityType,OrganizationName" in output
        assert "InCommon,SP,Test Org" in output

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.export_federation_csv")
    def test_main_csv_federations(
        self,
        mock_export_csv,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv federations option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 1}, {"InCommon": {}})

        with patch("sys.argv", ["analyze.py", "--csv", "federations"]):
            main()

        # Should call export_federation_csv
        mock_export_csv.assert_called_once()

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.filter_entities")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_missing_privacy(
        self,
        mock_stdout,
        mock_filter,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv missing-privacy option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        entities_list = [
            ["InCommon", "SP", "Test Org", "https://test.org", "No", "", "Yes"]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch("sys.argv", ["analyze.py", "--csv", "missing-privacy"]):
            main()

        # Should call filter_entities with correct mode
        mock_filter.assert_called_once_with(entities_list, "missing_privacy")

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.filter_entities")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_missing_security(
        self,
        mock_stdout,
        mock_filter,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv missing-security option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        entities_list = [
            [
                "InCommon",
                "SP",
                "Test Org",
                "https://test.org",
                "Yes",
                "https://test.org/privacy",
                "No",
            ]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch("sys.argv", ["analyze.py", "--csv", "missing-security"]):
            main()

        # Should call filter_entities with correct mode
        mock_filter.assert_called_once_with(entities_list, "missing_security")

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.filter_entities")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_missing_both(
        self,
        mock_stdout,
        mock_filter,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv missing-both option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        entities_list = [
            ["InCommon", "SP", "Test Org", "https://test.org", "No", "", "No"]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch("sys.argv", ["analyze.py", "--csv", "missing-both"]):
            main()

        # Should call filter_entities with correct mode
        mock_filter.assert_called_once_with(entities_list, "missing_both")

    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary")
    def test_main_local_file(self, mock_print_summary, mock_analyze, mock_parse):
        """Test main function with local file source."""
        # Mock return values
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 100}, {})

        with patch("sys.argv", ["analyze.py", "--source", "/path/to/metadata.xml"]):
            main()

        # Should call parse_metadata with local file
        args, kwargs = mock_parse.call_args
        assert args[1] == "/path/to/metadata.xml"

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary")
    def test_main_custom_url(
        self,
        mock_print_summary,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with custom URL source."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 100}, {})

        with patch(
            "sys.argv", ["analyze.py", "--source", "https://custom.url/metadata.xml"]
        ):
            main()

        # Should call get_metadata with custom URL
        mock_get_metadata.assert_called_once_with("https://custom.url/metadata.xml")

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_no_headers(
        self,
        mock_stdout,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --no-headers option."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        entities_list = [
            [
                "InCommon",
                "SP",
                "Test Org",
                "https://test.org",
                "Yes",
                "https://test.org/privacy",
                "No",
            ]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})

        with patch("sys.argv", ["analyze.py", "--csv", "entities", "--no-headers"]):
            main()

        output = mock_stdout.getvalue()
        # Should not include CSV headers
        assert "Federation,EntityType,OrganizationName" not in output
        assert "InCommon,SP,Test Org" in output

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_urls_validated(
        self,
        mock_stdout,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv urls-validated option (auto-enables validation)."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        # Mock extended entity data with validation
        entities_list = [
            [
                "InCommon",
                "SP",
                "Test Org",
                "https://test.org",
                "Yes",
                "https://test.org/privacy",
                "No",
                "200",
                "https://test.org/privacy",
                "Yes",
                "0",
                "",
            ]
        ]
        mock_analyze.return_value = (
            entities_list,
            {"total_entities": 1, "validation_enabled": True},
            {},
        )

        with patch("sys.argv", ["analyze.py", "--csv", "urls-validated"]):
            main()

        # Should call analyze with validation enabled
        args, kwargs = mock_analyze.call_args
        # Third positional argument should be validate_urls=True
        assert args[2] is True

        # Should output extended CSV format
        output = mock_stdout.getvalue()
        assert (
            "URLStatusCode,FinalURL,URLAccessible,RedirectCount,ValidationError"
            in output
        )

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_csv_urls_basic(
        self,
        mock_stdout,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_get_federation,
    ):
        """Test main function with --csv urls option (basic URL list)."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()

        entities_list = [
            [
                "InCommon",
                "SP",
                "Test Org",
                "https://test.org",
                "Yes",
                "https://test.org/privacy",
                "No",
            ]
        ]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})

        with patch("sys.argv", ["analyze.py", "--csv", "urls"]):
            main()

        # Should not enable validation for basic URL list
        args, kwargs = mock_analyze.call_args
        # Third positional argument should be validate_urls=False
        assert args[2] is False

        # Should output basic URL list
        output = mock_stdout.getvalue()
        assert "Federation,EntityType,OrganizationName" in output
        assert (
            "StatusCode,FinalURL,URLAccessible" not in output
        )  # No validation columns

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.load_url_validation_cache")
    @patch("edugain_analysis.cli.main.save_url_validation_cache")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    @patch("edugain_analysis.cli.main.analyze_privacy_security")
    @patch("edugain_analysis.cli.main.print_summary")
    def test_main_validation_cache_handling(
        self,
        mock_print_summary,
        mock_analyze,
        mock_parse,
        mock_get_metadata,
        mock_save_cache,
        mock_load_cache,
        mock_get_federation,
    ):
        """Test main function handles validation cache correctly."""
        # Mock return values
        mock_get_federation.return_value = {}
        mock_load_cache.return_value = {"https://test.org": {"accessible": True}}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = (
            [],
            {"total_entities": 100, "validation_enabled": True, "urls_checked": 5},
            {},
        )

        with patch("sys.argv", ["analyze.py", "--validate"]):
            main()

        # Should load and save validation cache when validation is enabled
        mock_load_cache.assert_called_once()
        mock_save_cache.assert_called_once()

        # Should pass cache to analyze function
        args, kwargs = mock_analyze.call_args
        # Fourth positional argument should be validation_cache
        assert args[3] == {"https://test.org": {"accessible": True}}

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    def test_main_error_handling(
        self, mock_parse, mock_get_metadata, mock_get_federation
    ):
        """Test main function error handling."""
        # Mock an exception during parsing
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.side_effect = Exception("Parse error")

        with patch("sys.argv", ["analyze.py"]):
            with pytest.raises(SystemExit):
                main()

    @patch("edugain_analysis.cli.main.get_federation_mapping")
    @patch("edugain_analysis.cli.main.get_metadata")
    @patch("edugain_analysis.cli.main.parse_metadata")
    def test_main_keyboard_interrupt(
        self, mock_parse, mock_get_metadata, mock_get_federation
    ):
        """Test main function handles KeyboardInterrupt gracefully."""
        # Mock KeyboardInterrupt during parsing
        mock_get_federation.return_value = {}
        mock_get_metadata.return_value = b"<xml>metadata</xml>"
        mock_parse.side_effect = KeyboardInterrupt()

        with patch("sys.argv", ["analyze.py"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit with code 1
                assert exc_info.value.code == 1
                # Should print user-friendly message
                assert "interrupted by user" in mock_stderr.getvalue()

    def test_main_help(self):
        """Test main function with --help option."""
        with patch("sys.argv", ["analyze.py", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with code 0 for help
            assert exc_info.value.code == 0
