"""Tests for cli/broken_privacy.py functionality."""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from io import StringIO
from unittest.mock import MagicMock, patch

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.cli.broken_privacy import (
    analyze_broken_links,
    categorize_error,
    collect_sp_privacy_urls,
    download_metadata,
    get_federation_mapping,
    main,
    validate_privacy_urls,
    validate_url,
)


class TestDownloadMetadata:
    """Test the download_metadata function."""

    @patch("requests.get")
    def test_download_metadata_success(self, mock_get):
        """Test successful metadata download."""
        mock_response = MagicMock()
        mock_response.content = b"<xml>test content</xml>"
        mock_get.return_value = mock_response

        result = download_metadata("https://example.org/metadata")

        assert result == b"<xml>test content</xml>"
        mock_response.raise_for_status.assert_called_once()
        mock_get.assert_called_once_with("https://example.org/metadata", timeout=30)

    @patch("requests.get")
    @patch("sys.exit")
    def test_download_metadata_request_exception(self, mock_exit, mock_get):
        """Test download metadata with request exception."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            download_metadata("https://example.org/metadata")

        mock_exit.assert_called_once_with(1)
        assert "Error downloading metadata" in mock_stderr.getvalue()
        assert "Network error" in mock_stderr.getvalue()


class TestGetFederationMapping:
    """Test the get_federation_mapping function."""

    @patch("requests.get")
    def test_get_federation_mapping_success(self, mock_get):
        """Test successful federation mapping retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "fed1": {
                "reg_auth": "https://example.org",
                "name": "Example Federation",
            },
            "fed2": {
                "reg_auth": "https://test.org",
                "name": "Test Federation",
            },
        }
        mock_get.return_value = mock_response

        result = get_federation_mapping()

        assert result == {
            "https://example.org": "Example Federation",
            "https://test.org": "Test Federation",
        }
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.get")
    def test_get_federation_mapping_error(self, mock_get):
        """Test federation mapping with request error."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("API error")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = get_federation_mapping()

        assert result == {}
        assert "Warning: Could not fetch federation mapping" in mock_stderr.getvalue()

    @patch("requests.get")
    def test_get_federation_mapping_partial_data(self, mock_get):
        """Test federation mapping with missing fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "fed1": {"reg_auth": "https://example.org", "name": "Example Federation"},
            "fed2": {"reg_auth": "https://test.org"},  # Missing name
            "fed3": {"name": "Missing RegAuth"},  # Missing reg_auth
        }
        mock_get.return_value = mock_response

        result = get_federation_mapping()

        # Only fed1 should be included
        assert result == {"https://example.org": "Example Federation"}


class TestValidateURL:
    """Test the validate_url function."""

    @patch("requests.head")
    def test_validate_url_success(self, mock_head):
        """Test successful URL validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 200
        assert result["accessible"] is True
        assert result["error"] == ""
        assert "checked_at" in result

    @patch("requests.head")
    def test_validate_url_ssl_error(self, mock_head):
        """Test URL validation with SSL error."""
        import requests

        mock_head.side_effect = requests.exceptions.SSLError("Certificate error")

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert "SSL error" in result["error"]

    @patch("requests.head")
    def test_validate_url_connection_error(self, mock_head):
        """Test URL validation with connection error."""
        import requests

        mock_head.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert "Connection error" in result["error"]

    @patch("requests.head")
    def test_validate_url_timeout(self, mock_head):
        """Test URL validation with timeout."""
        import requests

        mock_head.side_effect = requests.exceptions.Timeout()

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Timeout"

    @patch("requests.head")
    def test_validate_url_too_many_redirects(self, mock_head):
        """Test URL validation with too many redirects."""
        import requests

        mock_head.side_effect = requests.exceptions.TooManyRedirects()

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Too many redirects"

    @patch("requests.head")
    def test_validate_url_client_error(self, mock_head):
        """Test URL validation with 404 error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 404
        assert result["accessible"] is False
        assert result["error"] == ""

    @patch("requests.head")
    def test_validate_url_server_error(self, mock_head):
        """Test URL validation with 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_head.return_value = mock_response

        result = validate_url("https://example.org/privacy")

        assert result["status_code"] == 500
        assert result["accessible"] is False
        assert result["error"] == ""


class TestCategorizeError:
    """Test the categorize_error function."""

    def test_categorize_ssl_error(self):
        """Test categorizing SSL errors."""
        result = categorize_error(0, "SSL certificate verification failed")
        assert result == "SSL Certificate Error"

    def test_categorize_connection_error(self):
        """Test categorizing connection errors."""
        result = categorize_error(0, "Connection refused")
        assert result == "Connection Error"

    def test_categorize_timeout(self):
        """Test categorizing timeout errors."""
        result = categorize_error(0, "Request timeout")
        assert result == "Timeout"

    def test_categorize_redirects(self):
        """Test categorizing redirect errors."""
        result = categorize_error(0, "Too many redirects")
        assert result == "Too Many Redirects"

    def test_categorize_404(self):
        """Test categorizing 404 errors."""
        result = categorize_error(404, "")
        assert result == "Not Found (4xx)"

    def test_categorize_403(self):
        """Test categorizing 403 errors."""
        result = categorize_error(403, "")
        assert result == "Forbidden (4xx)"

    def test_categorize_401(self):
        """Test categorizing 401 errors."""
        result = categorize_error(401, "")
        assert result == "Unauthorized (4xx)"

    def test_categorize_410(self):
        """Test categorizing 410 errors."""
        result = categorize_error(410, "")
        assert result == "Gone Permanently (4xx)"

    def test_categorize_other_4xx(self):
        """Test categorizing other 4xx errors."""
        result = categorize_error(418, "")
        assert result == "Client Error 418 (4xx)"

    def test_categorize_5xx(self):
        """Test categorizing 5xx errors."""
        result = categorize_error(503, "")
        assert result == "Server Error 503 (5xx)"

    def test_categorize_unknown(self):
        """Test categorizing unknown errors."""
        result = categorize_error(0, "")
        assert result == "Unknown Error"


class TestCollectSPPrivacyURLs:
    """Test the collect_sp_privacy_urls function."""

    def test_collect_sp_with_privacy_url(self):
        """Test collecting SPs with privacy URLs."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL>https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName>Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        result = collect_sp_privacy_urls(root)

        assert len(result) == 1
        assert result[0] == (
            "https://example.org",
            "Example SP",
            "https://example.org/sp",
            "https://example.org/privacy",
        )

    def test_collect_sp_without_privacy_url(self):
        """Test collecting SPs without privacy URLs."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName>Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        result = collect_sp_privacy_urls(root)

        assert len(result) == 0

    def test_collect_idp_ignored(self):
        """Test that IdPs are ignored."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/idp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL>https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        result = collect_sp_privacy_urls(root)

        assert len(result) == 0

    def test_collect_sp_missing_reg_authority(self):
        """Test collecting SPs without registration authority."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL>https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        result = collect_sp_privacy_urls(root)

        assert len(result) == 0

    def test_collect_sp_empty_privacy_url(self):
        """Test collecting SPs with empty privacy URL."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL></mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        result = collect_sp_privacy_urls(root)

        assert len(result) == 0


class TestValidatePrivacyURLs:
    """Test the validate_privacy_urls function."""

    @patch("edugain_analysis.cli.broken_privacy.validate_url")
    def test_validate_privacy_urls_success(self, mock_validate):
        """Test validating privacy URLs successfully."""
        sp_data = [
            (
                "https://example.org",
                "SP1",
                "https://example.org/sp1",
                "https://privacy1.org",
            ),
            (
                "https://example.org",
                "SP2",
                "https://example.org/sp2",
                "https://privacy2.org",
            ),
            (
                "https://example.org",
                "SP3",
                "https://example.org/sp3",
                "https://privacy1.org",
            ),  # Duplicate URL
        ]

        mock_validate.return_value = {
            "status_code": 200,
            "accessible": True,
            "error": "",
            "checked_at": "2025-01-01T00:00:00Z",
        }

        with patch("sys.stderr", new_callable=StringIO):
            result = validate_privacy_urls(sp_data, max_workers=2)

        # Should only validate 2 unique URLs
        assert len(result) == 2
        assert "https://privacy1.org" in result
        assert "https://privacy2.org" in result
        assert mock_validate.call_count == 2

    @patch("edugain_analysis.cli.broken_privacy.validate_url")
    def test_validate_privacy_urls_with_errors(self, mock_validate):
        """Test validating privacy URLs with some errors."""
        sp_data = [
            (
                "https://example.org",
                "SP1",
                "https://example.org/sp1",
                "https://privacy1.org",
            ),
        ]

        mock_validate.side_effect = Exception("Validation error")

        with patch("sys.stderr", new_callable=StringIO):
            result = validate_privacy_urls(sp_data, max_workers=1)

        # Should still return result with error
        assert len(result) == 1
        assert result["https://privacy1.org"]["accessible"] is False


class TestAnalyzeBrokenLinks:
    """Test the analyze_broken_links function."""

    def test_analyze_broken_links_with_404(self):
        """Test analyzing broken links with 404 error."""
        sp_data = [
            (
                "https://example.org",
                "SP1",
                "https://example.org/sp1",
                "https://privacy1.org",
            ),
        ]

        validation_results = {
            "https://privacy1.org": {
                "status_code": 404,
                "accessible": False,
                "error": "",
                "checked_at": "2025-01-01T00:00:00Z",
            }
        }

        federation_mapping = {"https://example.org": "Example Federation"}

        result = analyze_broken_links(sp_data, validation_results, federation_mapping)

        assert len(result) == 1
        assert result[0][0] == "Example Federation"
        assert result[0][1] == "SP1"
        assert result[0][2] == "https://example.org/sp1"
        assert result[0][3] == "https://privacy1.org"
        assert result[0][4] == "404"
        assert result[0][5] == "Not Found (4xx)"
        assert result[0][6] == "2025-01-01T00:00:00Z"

    def test_analyze_broken_links_with_ssl_error(self):
        """Test analyzing broken links with SSL error."""
        sp_data = [
            (
                "https://example.org",
                "SP1",
                "https://example.org/sp1",
                "https://privacy1.org",
            ),
        ]

        validation_results = {
            "https://privacy1.org": {
                "status_code": 0,
                "accessible": False,
                "error": "SSL certificate error",
                "checked_at": "2025-01-01T00:00:00Z",
            }
        }

        federation_mapping = {}

        result = analyze_broken_links(sp_data, validation_results, federation_mapping)

        assert len(result) == 1
        assert result[0][0] == "https://example.org"  # No federation mapping
        assert result[0][4] == "SSL certificate error"
        assert result[0][5] == "SSL Certificate Error"

    def test_analyze_broken_links_accessible_urls_excluded(self):
        """Test that accessible URLs are not included in results."""
        sp_data = [
            (
                "https://example.org",
                "SP1",
                "https://example.org/sp1",
                "https://privacy1.org",
            ),
        ]

        validation_results = {
            "https://privacy1.org": {
                "status_code": 200,
                "accessible": True,
                "error": "",
                "checked_at": "2025-01-01T00:00:00Z",
            }
        }

        federation_mapping = {}

        result = analyze_broken_links(sp_data, validation_results, federation_mapping)

        assert len(result) == 0


class TestMain:
    """Test the main function."""

    @patch("edugain_analysis.cli.broken_privacy.download_metadata")
    @patch("edugain_analysis.cli.broken_privacy.get_federation_mapping")
    @patch("edugain_analysis.cli.broken_privacy.validate_privacy_urls")
    @patch("sys.argv", ["broken_privacy.py"])
    def test_main_default_options(
        self, mock_validate, mock_get_federation, mock_download
    ):
        """Test main with default options."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL>https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName>Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        mock_download.return_value = xml_content.encode()
        mock_get_federation.return_value = {"https://example.org": "Example Federation"}
        mock_validate.return_value = {
            "https://example.org/privacy": {
                "status_code": 404,
                "accessible": False,
                "error": "",
                "checked_at": "2025-01-01T00:00:00Z",
            }
        }

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO):
                main()

        output = mock_stdout.getvalue()
        assert "Federation" in output
        assert "Example Federation" in output

    @patch("sys.argv", ["broken_privacy.py", "--local-file", "test.xml"])
    @patch("edugain_analysis.cli.broken_privacy.get_federation_mapping")
    @patch("edugain_analysis.cli.broken_privacy.validate_privacy_urls")
    @patch("sys.exit")
    def test_main_local_file(self, mock_exit, mock_validate, mock_get_federation):
        """Test main with local file."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"/>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_file = f.name

        try:
            mock_get_federation.return_value = {}
            mock_validate.return_value = {}

            with patch("sys.argv", ["broken_privacy.py", "--local-file", temp_file]):
                with patch("sys.stdout", new_callable=StringIO):
                    with patch("sys.stderr", new_callable=StringIO):
                        main()
        finally:
            os.unlink(temp_file)

    @patch("edugain_analysis.cli.broken_privacy.download_metadata")
    @patch("edugain_analysis.cli.broken_privacy.get_federation_mapping")
    @patch("edugain_analysis.cli.broken_privacy.validate_privacy_urls")
    @patch("sys.exit")
    @patch("sys.argv", ["broken_privacy.py", "--no-headers"])
    def test_main_no_headers(
        self, mock_exit, mock_validate, mock_get_federation, mock_download
    ):
        """Test main with --no-headers option."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"/>"""

        mock_download.return_value = xml_content.encode()
        mock_get_federation.return_value = {}
        mock_validate.return_value = {}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.stderr", new_callable=StringIO):
                main()

        output = mock_stdout.getvalue()
        # Should not have headers
        assert "Federation" not in output or output.count("Federation") == 0

    @patch("edugain_analysis.cli.broken_privacy.download_metadata")
    @patch("edugain_analysis.cli.broken_privacy.get_federation_mapping")
    @patch("edugain_analysis.cli.broken_privacy.validate_privacy_urls")
    @patch("sys.exit")
    @patch("sys.argv", ["broken_privacy.py", "--url", "https://custom.url/metadata"])
    def test_main_custom_url(
        self, mock_exit, mock_validate, mock_get_federation, mock_download
    ):
        """Test main with custom URL."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"/>"""

        mock_download.return_value = xml_content.encode()
        mock_get_federation.return_value = {}
        mock_validate.return_value = {}

        with patch("sys.stdout", new_callable=StringIO):
            with patch("sys.stderr", new_callable=StringIO):
                main()

        mock_download.assert_called_once_with("https://custom.url/metadata")

    @patch("sys.argv", ["broken_privacy.py", "--help"])
    @patch("sys.exit")
    def test_main_help_option(self, mock_exit):
        """Test main with --help option."""
        with patch("sys.stdout", new_callable=StringIO):
            main()

        # argparse calls sys.exit(0) after printing help
        mock_exit.assert_called_once_with(0)
