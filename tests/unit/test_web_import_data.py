"""Unit tests for web data import functionality."""

from unittest.mock import MagicMock, patch

import pytest

try:
    from edugain_analysis_web.import_data import (
        generate_test_data,
        import_snapshot,
    )
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pytest.skip("Web dependencies not installed", allow_module_level=True)


class TestImportSnapshot:
    """Test snapshot import functionality."""

    @patch("edugain_analysis_web.import_data.SessionLocal")
    @patch("edugain_analysis_web.import_data.parse_metadata")
    @patch("edugain_analysis_web.import_data.get_metadata")
    @patch("edugain_analysis_web.import_data.get_federation_mapping")
    @patch("edugain_analysis_web.import_data.analyze_privacy_security")
    def test_import_snapshot_calls_dependencies(
        self,
        mock_analyze,
        mock_get_fed_mapping,
        mock_get_metadata,
        mock_parse_metadata,
        mock_session_local,
    ):
        """Test that import_snapshot calls all required dependencies."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_metadata.return_value = b"<xml>test</xml>"
        mock_parse_metadata.return_value = MagicMock()
        mock_get_fed_mapping.return_value = {}

        # Mock analysis results (with SIRTFI column)
        entities_list = [
            [
                "TestFed",
                "SP",
                "Test Org",
                "https://test.org/sp",
                True,
                "https://test.org/privacy",
                True,
                True,  # HasSIRTFI
            ]
        ]
        stats = {
            "total_entities": 1,
            "total_sps": 1,
            "total_idps": 0,
            "sps_has_privacy": 1,
            "sps_missing_privacy": 0,
            "sps_has_security": 1,
            "idps_has_security": 0,
            "sps_has_sirtfi": 1,
            "idps_has_sirtfi": 0,
            "total_has_sirtfi": 1,
        }
        fed_stats = {
            "TestFed": {
                "total_entities": 1,
                "total_sps": 1,
                "total_idps": 0,
                "sps_has_privacy": 1,
                "sps_missing_privacy": 0,
                "sps_has_security": 1,
                "idps_has_security": 0,
                "sps_has_sirtfi": 1,
                "idps_has_sirtfi": 0,
                "total_has_sirtfi": 1,
            }
        }
        mock_analyze.return_value = (entities_list, stats, fed_stats)

        # Execute
        import_snapshot(validate_urls=False)

        # Verify calls
        mock_get_metadata.assert_called_once()
        mock_parse_metadata.assert_called_once()
        mock_get_fed_mapping.assert_called_once()
        mock_analyze.assert_called_once()
        mock_db.commit.assert_called()

    @patch("edugain_analysis_web.import_data.SessionLocal")
    @patch("edugain_analysis.web.import_data.get_metadata")
    def test_import_snapshot_handles_errors(
        self,
        mock_get_metadata,
        mock_session_local,
    ):
        """Test snapshot import error handling."""
        mock_get_metadata.side_effect = Exception("Network error")

        # import_snapshot calls sys.exit(1) on error
        with pytest.raises(SystemExit) as exc_info:
            import_snapshot(validate_urls=False)
        assert exc_info.value.code == 1


class TestGenerateTestData:
    """Test test data generation."""

    @patch("edugain_analysis_web.import_data.SessionLocal")
    def test_generate_test_data_calls_database(self, mock_session_local):
        """Test that generate_test_data creates database records."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        generate_test_data(days=7)

        # Verify database operations were called
        mock_db.commit.assert_called()
        mock_db.close.assert_called()

    @patch("edugain_analysis_web.import_data.SessionLocal")
    def test_generate_test_data_custom_days(self, mock_session_local):
        """Test test data generation with custom days parameter."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        generate_test_data(days=14)

        # Verify database operations were called
        mock_db.commit.assert_called()
        mock_db.close.assert_called()
