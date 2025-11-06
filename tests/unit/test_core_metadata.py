"""Tests for core metadata functionality."""

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.core.metadata import (
    REQUEST_TIMEOUT,
    download_metadata,
    fetch_federation_names,
    get_cache_dir,
    get_cache_file,
    get_federation_mapping,
    get_metadata,
    is_metadata_cache_valid,
    load_federation_cache,
    load_json_cache,
    load_metadata_cache,
    load_text_cache,
    load_url_validation_cache,
    map_registration_authority,
    parse_metadata,
    save_federation_cache,
    save_json_cache,
    save_metadata_cache,
    save_text_cache,
    save_url_validation_cache,
)


class TestCacheUtilities:
    """Test cache utility functions."""

    def test_get_cache_dir(self):
        """Test cache directory creation."""
        cache_dir = get_cache_dir()
        assert isinstance(cache_dir, Path)
        assert "edugain" in str(cache_dir).lower()

    def test_get_cache_file(self):
        """Test cache file path generation."""
        cache_file = get_cache_file("test.json")
        assert isinstance(cache_file, Path)
        assert cache_file.name == "test.json"

    @patch("edugain_analysis.core.metadata.user_cache_dir")
    def test_get_cache_dir_fallback_import_error(self, mock_user_cache_dir):
        """Test cache directory creation with platformdirs import error fallback."""
        # This tests the fallback when platformdirs is not available
        # The fallback function should be used instead

        # Mock the fallback function behavior
        mock_user_cache_dir.return_value = "/tmp/fallback/cache"

        # Import and use the fallback implementation
        with patch.dict("sys.modules", {"platformdirs": None}):
            # Re-import the function to trigger fallback
            cache_dir = get_cache_dir()
            assert isinstance(cache_dir, Path)

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_load_json_cache_not_exists(self, mock_get_cache_file):
        """Test loading JSON cache when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_cache_file.return_value = mock_path

        result = load_json_cache("test.json")
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("builtins.open", new_callable=mock_open, read_data='{"test": "data"}')
    @patch("edugain_analysis.core.metadata.time")
    def test_load_json_cache_success(self, mock_time, mock_file, mock_get_cache_file):
        """Test successful JSON cache loading."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 2000  # 1000 seconds newer

        result = load_json_cache("test.json", max_age_hours=1)
        assert result == {"test": "data"}

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.time")
    def test_load_json_cache_expired(self, mock_time, mock_get_cache_file):
        """Test JSON cache loading when cache is expired."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 10000  # Much newer, cache expired

        result = load_json_cache("test.json", max_age_hours=1)
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("builtins.open", new_callable=mock_open, read_data='{"invalid": json}')
    @patch("edugain_analysis.core.metadata.time")
    def test_load_json_cache_json_decode_error(
        self, mock_time, mock_file, mock_get_cache_file
    ):
        """Test JSON cache loading with JSON decode error."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 2000

        # Mock json.load to raise JSONDecodeError
        with patch(
            "json.load", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
        ):
            result = load_json_cache("test.json", max_age_hours=1)
            assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.time")
    def test_load_json_cache_os_error(self, mock_time, mock_get_cache_file):
        """Test JSON cache loading with OS error."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 2000

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = load_json_cache("test.json", max_age_hours=1)
            assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_json_cache(self, mock_get_cache_file):
        """Test saving JSON cache."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        with patch("builtins.open", mock_open()) as mock_file:
            save_json_cache("test.json", {"test": "data"})
            mock_file.assert_called_once()

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_json_cache_os_error(self, mock_get_cache_file):
        """Test saving JSON cache with OS error."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        # Mock open to raise OSError during write
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception, just silently fail
            save_json_cache("test.json", {"test": "data"})

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    @patch("edugain_analysis.core.metadata.time")
    def test_load_text_cache_success(self, mock_time, mock_file, mock_get_cache_file):
        """Test successful text cache loading."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 2000  # 1000 seconds newer

        result = load_text_cache("test.txt", max_age_hours=1)
        assert result == "test content"

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_text_cache(self, mock_get_cache_file):
        """Test saving text cache."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        with patch("builtins.open", mock_open()) as mock_file:
            save_text_cache("test.txt", "test content")
            mock_file.assert_called_once()

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.time")
    def test_load_text_cache_expired(self, mock_time, mock_get_cache_file):
        """Test text cache loading when cache is expired."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 10000  # Much newer, cache expired

        result = load_text_cache("test.txt", max_age_hours=1)
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.time")
    def test_load_text_cache_os_error(self, mock_time, mock_get_cache_file):
        """Test text cache loading with OS error."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path
        mock_time.time.return_value = 2000

        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = load_text_cache("test.txt", max_age_hours=1)
            assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_text_cache_os_error(self, mock_get_cache_file):
        """Test saving text cache with OS error."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        # Mock open to raise OSError during write
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception, just silently fail
            save_text_cache("test.txt", "test content")


class TestMetadataCache:
    """Test metadata caching functions."""

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_is_metadata_cache_valid_not_exists(
        self, mock_datetime, mock_get_cache_file
    ):
        """Test cache validity when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_cache_file.return_value = mock_path

        result = is_metadata_cache_valid()
        assert result is False

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_is_metadata_cache_valid_expired(self, mock_datetime, mock_get_cache_file):
        """Test cache validity when file is expired."""
        from datetime import datetime, timedelta

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path

        # Mock datetime to simulate expired cache
        # file_time should be older than expiry_time for cache to be expired
        file_time = datetime.fromtimestamp(1000)
        current_time = datetime.fromtimestamp(1000) + timedelta(
            hours=25
        )  # Current time + 25 hours
        expiry_time = current_time - timedelta(
            hours=12
        )  # 12 hours ago (METADATA_CACHE_HOURS)

        mock_datetime.fromtimestamp.return_value = file_time
        mock_datetime.now.return_value = current_time

        # Since file_time (1000) < expiry_time (1000 + 13 hours), cache should be expired
        result = is_metadata_cache_valid()
        assert result is False

    @patch("requests.get")
    def test_download_metadata_success(self, mock_get):
        """Test successful metadata download."""
        mock_response = MagicMock()
        mock_response.content = b"<xml>test</xml>"
        mock_get.return_value = mock_response

        result = download_metadata("https://example.org/metadata")
        assert result == b"<xml>test</xml>"
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.get")
    def test_download_metadata_http_error(self, mock_get):
        """Test metadata download with HTTP error."""
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            download_metadata("https://example.org/metadata")

    @patch("requests.get")
    def test_download_metadata_connection_error(self, mock_get):
        """Test metadata download with connection error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            download_metadata("https://example.org/metadata")

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_metadata_cache(self, mock_get_cache_file):
        """Test saving metadata to cache."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        with patch("builtins.open", mock_open()) as mock_file:
            save_metadata_cache(b"<xml>test</xml>")
            mock_file.assert_called_once_with(mock_path, "wb")

    @patch("edugain_analysis.core.metadata.is_metadata_cache_valid")
    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_load_metadata_cache_invalid(self, mock_get_cache_file, mock_is_valid):
        """Test loading metadata cache when invalid."""
        mock_is_valid.return_value = False

        result = load_metadata_cache()
        assert result is None

    @patch("edugain_analysis.core.metadata.is_metadata_cache_valid")
    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_load_metadata_cache_success(self, mock_get_cache_file, mock_is_valid):
        """Test successful metadata cache loading."""
        mock_is_valid.return_value = True
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        with patch(
            "builtins.open", mock_open(read_data=b"<xml>cached</xml>")
        ) as mock_file:
            result = load_metadata_cache()
            assert result == b"<xml>cached</xml>"

    @patch("edugain_analysis.core.metadata.load_metadata_cache")
    @patch("edugain_analysis.core.metadata.download_metadata")
    @patch("edugain_analysis.core.metadata.save_metadata_cache")
    def test_get_metadata_from_cache(self, mock_save, mock_download, mock_load):
        """Test getting metadata from cache."""
        mock_load.return_value = b"<xml>cached</xml>"

        result = get_metadata()
        assert result == b"<xml>cached</xml>"
        mock_download.assert_not_called()
        mock_save.assert_not_called()

    @patch("edugain_analysis.core.metadata.load_metadata_cache")
    @patch("edugain_analysis.core.metadata.download_metadata")
    @patch("edugain_analysis.core.metadata.save_metadata_cache")
    def test_get_metadata_download_fresh(self, mock_save, mock_download, mock_load):
        """Test downloading fresh metadata."""
        mock_load.return_value = None
        mock_download.return_value = b"<xml>fresh</xml>"

        result = get_metadata()
        assert result == b"<xml>fresh</xml>"
        mock_download.assert_called_once()
        mock_save.assert_called_once_with(b"<xml>fresh</xml>")

    @patch("edugain_analysis.core.metadata.load_metadata_cache")
    @patch("edugain_analysis.core.metadata.download_metadata")
    @patch("edugain_analysis.core.metadata.save_metadata_cache")
    def test_get_metadata_custom_url_skips_cache(
        self, mock_save, mock_download, mock_load
    ):
        """Custom metadata sources should bypass cache read/write."""
        mock_load.return_value = b"<xml>cached</xml>"
        mock_download.return_value = b"<xml>custom</xml>"

        custom_url = "https://custom.example.org/metadata.xml"
        result = get_metadata(custom_url)

        assert result == b"<xml>custom</xml>"
        mock_load.assert_not_called()
        mock_save.assert_not_called()
        mock_download.assert_called_once_with(custom_url, REQUEST_TIMEOUT)


class TestMetadataParsing:
    """Test metadata parsing functions."""

    def test_parse_metadata_content(self):
        """Test parsing metadata from content."""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = parse_metadata(content=xml_content)
        assert root.tag.endswith("EntitiesDescriptor")

    def test_parse_metadata_local_file(self):
        """Test parsing metadata from local file."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_file = f.name

        try:
            root = parse_metadata(local_file=temp_file)
            assert root.tag.endswith("EntitiesDescriptor")
        finally:
            os.unlink(temp_file)

    def test_parse_metadata_file_not_found(self):
        """Test parsing metadata from non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_metadata(local_file="/nonexistent/file.xml")

    def test_parse_metadata_invalid_xml(self):
        """Test parsing invalid XML content."""
        with pytest.raises(ET.ParseError):
            parse_metadata(content=b"<invalid xml")

    def test_parse_metadata_no_input(self):
        """Test parsing metadata with no input."""
        with pytest.raises(ValueError):
            parse_metadata()


class TestFederationMapping:
    """Test federation mapping functions."""

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_federation_cache_not_exists(self, mock_datetime, mock_get_cache_file):
        """Test loading federation cache when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_cache_file.return_value = mock_path

        result = load_federation_cache()
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_federation_cache(self, mock_get_cache_file):
        """Test saving federation cache."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        with patch("builtins.open", mock_open()) as mock_file:
            save_federation_cache({"https://incommon.org": "InCommon"})
            mock_file.assert_called_once()

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_federation_cache_error(self, mock_get_cache_file):
        """Test saving federation cache with error."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        # Mock open to raise OSError during write
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception, just silently fail
            save_federation_cache({"https://incommon.org": "InCommon"})

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_federation_cache_expired(self, mock_datetime, mock_get_cache_file):
        """Test loading federation cache when expired."""
        from datetime import datetime

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path

        # Mock datetime to simulate expired cache
        old_time = datetime.fromtimestamp(1000)
        current_time = datetime.fromtimestamp(10000)  # Much later
        mock_datetime.fromtimestamp.side_effect = [old_time, current_time]
        mock_datetime.now.return_value = current_time

        result = load_federation_cache()
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_federation_cache_json_error(self, mock_datetime, mock_get_cache_file):
        """Test loading federation cache with JSON error."""
        from datetime import datetime

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path

        # Mock datetime to simulate fresh cache
        current_time = datetime.fromtimestamp(2000)
        mock_datetime.fromtimestamp.return_value = current_time
        mock_datetime.now.return_value = current_time

        # Mock json.load to raise JSONDecodeError
        with patch("builtins.open", mock_open(read_data='{"invalid": json}')):
            with patch(
                "json.load", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
            ):
                result = load_federation_cache()
                assert result is None

    @patch("requests.get")
    def test_fetch_federation_names_success(self, mock_get):
        """Test successful federation names fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "incommon": {"reg_auth": "https://incommon.org", "name": "InCommon"},
            "ukfed": {"reg_auth": "https://ukfed.org.uk", "name": "UK federation"},
        }
        mock_get.return_value = mock_response

        result = fetch_federation_names()
        assert result == {
            "https://incommon.org": "InCommon",
            "https://ukfed.org.uk": "UK federation",
        }

    @patch("requests.get")
    def test_fetch_federation_names_error(self, mock_get):
        """Test federation names fetch with error."""
        import requests

        mock_get.side_effect = requests.RequestException("Network error")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = fetch_federation_names()

        assert result == {}
        stderr_output = mock_stderr.getvalue()
        assert "Fetching federation names" in stderr_output
        assert "Failed to fetch federation names" in stderr_output

    @patch("edugain_analysis.core.metadata.load_federation_cache")
    @patch("edugain_analysis.core.metadata.fetch_federation_names")
    @patch("edugain_analysis.core.metadata.save_federation_cache")
    def test_get_federation_mapping_from_cache(self, mock_save, mock_fetch, mock_load):
        """Test getting federation mapping from cache."""
        mock_load.return_value = {"https://incommon.org": "InCommon"}

        result = get_federation_mapping()
        assert result == {"https://incommon.org": "InCommon"}
        mock_fetch.assert_not_called()
        mock_save.assert_not_called()

    @patch("edugain_analysis.core.metadata.load_federation_cache")
    @patch("edugain_analysis.core.metadata.fetch_federation_names")
    @patch("edugain_analysis.core.metadata.save_federation_cache")
    def test_get_federation_mapping_fetch_fresh(self, mock_save, mock_fetch, mock_load):
        """Test fetching fresh federation mapping."""
        mock_load.return_value = None
        mock_fetch.return_value = {"https://incommon.org": "InCommon"}

        result = get_federation_mapping()
        assert result == {"https://incommon.org": "InCommon"}
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()

    def test_map_registration_authority_found(self):
        """Test mapping registration authority when found."""
        federation_mapping = {"https://incommon.org": "InCommon"}

        result = map_registration_authority("https://incommon.org", federation_mapping)
        assert result == "InCommon"

    def test_map_registration_authority_not_found(self):
        """Test mapping registration authority when not found."""
        federation_mapping = {"https://incommon.org": "InCommon"}

        result = map_registration_authority("https://unknown.org", federation_mapping)
        assert result == "https://unknown.org"

    def test_map_registration_authority_empty(self):
        """Test mapping empty registration authority."""
        federation_mapping = {"https://incommon.org": "InCommon"}

        result = map_registration_authority("", federation_mapping)
        assert result == "Unknown"


class TestURLValidationCache:
    """Test URL validation cache functions."""

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_url_validation_cache_not_exists(
        self, mock_datetime, mock_get_cache_file
    ):
        """Test loading URL validation cache when file doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_cache_file.return_value = mock_path

        result = load_url_validation_cache()
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_url_validation_cache(self, mock_get_cache_file):
        """Test saving URL validation cache."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        validation_data = {
            "https://example.org": {"accessible": True, "status_code": 200}
        }

        with patch("builtins.open", mock_open()) as mock_file:
            save_url_validation_cache(validation_data)
            mock_file.assert_called_once()

    @patch("edugain_analysis.core.metadata.get_cache_file")
    def test_save_url_validation_cache_error(self, mock_get_cache_file):
        """Test saving URL validation cache with error."""
        mock_path = MagicMock()
        mock_get_cache_file.return_value = mock_path

        validation_data = {
            "https://example.org": {"accessible": True, "status_code": 200}
        }

        # Mock open to raise OSError during write
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Should not raise exception, just silently fail
            save_url_validation_cache(validation_data)

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_url_validation_cache_expired(
        self, mock_datetime, mock_get_cache_file
    ):
        """Test loading URL validation cache when expired."""
        from datetime import datetime

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path

        # Mock datetime to simulate expired cache
        old_time = datetime.fromtimestamp(1000)
        current_time = datetime.fromtimestamp(1000000)  # Much later
        mock_datetime.fromtimestamp.side_effect = [old_time, current_time]
        mock_datetime.now.return_value = current_time

        result = load_url_validation_cache()
        assert result is None

    @patch("edugain_analysis.core.metadata.get_cache_file")
    @patch("edugain_analysis.core.metadata.datetime")
    def test_load_url_validation_cache_json_error(
        self, mock_datetime, mock_get_cache_file
    ):
        """Test loading URL validation cache with JSON error."""
        from datetime import datetime

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value.st_mtime = 1000
        mock_get_cache_file.return_value = mock_path

        # Mock datetime to simulate fresh cache
        current_time = datetime.fromtimestamp(2000)
        mock_datetime.fromtimestamp.return_value = current_time
        mock_datetime.now.return_value = current_time

        # Mock json.load to raise JSONDecodeError
        with patch("builtins.open", mock_open(read_data='{"invalid": json}')):
            with patch(
                "json.load", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
            ):
                result = load_url_validation_cache()
                assert result is None
