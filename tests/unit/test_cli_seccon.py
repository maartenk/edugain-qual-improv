"""Tests for cli/seccon.py functionality."""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.cli.seccon import (
    EDUGAIN_METADATA_URL,
    analyze_entities,
    download_metadata,
    main,
    parse_metadata,
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

    @patch("requests.get")
    def test_download_metadata_custom_timeout(self, mock_get):
        """Test download metadata with custom timeout."""
        mock_response = MagicMock()
        mock_response.content = b"<xml>test</xml>"
        mock_get.return_value = mock_response

        download_metadata("https://example.org/metadata", timeout=60)

        mock_get.assert_called_once_with("https://example.org/metadata", timeout=60)


class TestParseMetadata:
    """Test the parse_metadata function."""

    def test_parse_metadata_from_content(self):
        """Test parsing metadata from XML content."""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://example.org/sp"/>
        </md:EntitiesDescriptor>"""

        root = parse_metadata(xml_content)

        assert root.tag.endswith("EntitiesDescriptor")

    def test_parse_metadata_from_local_file(self):
        """Test parsing metadata from local file."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://example.org/sp"/>
        </md:EntitiesDescriptor>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_file = f.name

        try:
            root = parse_metadata(None, local_file=temp_file)
            assert root.tag.endswith("EntitiesDescriptor")
        finally:
            os.unlink(temp_file)

    @patch("sys.exit")
    def test_parse_metadata_invalid_xml(self, mock_exit):
        """Test parsing invalid XML content."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            parse_metadata(b"<invalid xml")

        mock_exit.assert_called_once_with(1)
        assert "Error parsing XML" in mock_stderr.getvalue()

    @patch("sys.exit")
    def test_parse_metadata_file_not_found(self, mock_exit):
        """Test parsing non-existent local file."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            # This will actually try to parse the file and fail with FileNotFoundError
            # which gets caught and converted to ParseError, then handled by sys.exit(1)
            with patch("xml.etree.ElementTree.parse") as mock_parse:
                mock_parse.side_effect = ET.ParseError("File not found")
                parse_metadata(None, local_file="/nonexistent/file.xml")

        mock_exit.assert_called_once_with(1)
        assert "Error parsing XML" in mock_stderr.getvalue()


class TestAnalyzeEntities:
    """Test the analyze_entities function."""

    def test_analyze_entities_with_security_no_sirtfi(self):
        """Test analysis of entities with security contacts but no SIRTFI."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 1
        assert entities[0][0] == "https://incommon.org"  # registration authority
        assert entities[0][1] == "SP"  # entity type
        assert entities[0][2] == "Example SP"  # organization name
        assert entities[0][3] == "https://sp.example.org"  # entity ID

    def test_analyze_entities_with_sirtfi_certification(self):
        """Test analysis of entities with SIRTFI certification (should be excluded)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example SP with SIRTFI</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded due to SIRTFI certification

    def test_analyze_entities_incommon_security_contact(self):
        """Test analysis with InCommon security contact format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:icmd="http://id.incommon.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://idp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                </md:Extensions>
                <md:ContactPerson icmd:contactType="http://id.incommon.org/metadata/contactType/security">
                    <md:EmailAddress>security@incommon.example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example IdP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 1
        assert entities[0][1] == "IdP"  # entity type

    def test_analyze_entities_no_security_contact(self):
        """Test analysis of entities without security contacts (should be excluded)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">SP without security contact</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - no security contact

    def test_analyze_entities_missing_fields(self):
        """Test analysis with missing optional fields but required registration authority."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://sp.minimal.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://minimal.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@minimal.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 1
        assert entities[0][0] == "https://minimal.org"  # registration authority
        assert entities[0][1] == "SP"  # entity type
        assert entities[0][2] == "Unknown"  # organization name (default when missing)
        assert entities[0][3] == "https://sp.minimal.org"  # entity ID

    def test_analyze_entities_empty_metadata(self):
        """Test analysis of empty metadata."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0

    def test_analyze_entities_missing_entity_id(self):
        """Test analysis of entities without entityID."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor>
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - no entityID

    def test_analyze_entities_missing_registration_info(self):
        """Test analysis of entities without registration info."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - no registration info

    def test_analyze_entities_empty_registration_authority(self):
        """Test analysis of entities with empty registration authority."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority=""/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - empty registration authority

    def test_analyze_entities_no_descriptor(self):
        """Test analysis of entities with neither SP nor IdP descriptor."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://unknown.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 1
        assert entities[0][1] is None  # entity type should be None


class TestCSVOutput:
    """Test CSV output functionality within main function."""

    @patch("edugain_analysis.cli.seccon.download_metadata")
    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_csv_output_with_headers(self, mock_analyze, mock_parse, mock_download):
        """Test CSV output with headers through main function."""
        mock_download.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://incommon.org", "SP", "Example SP", "https://sp.example.org"],
            ["https://ukfed.org.uk", "IdP", "Example IdP", "https://idp.example.org"],
        ]

        test_args = ["seccon"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        lines = result.strip().split("\n")
        assert "RegistrationAuthority,EntityType,OrganizationName,EntityID" in lines[0]
        assert "https://incommon.org,SP,Example SP,https://sp.example.org" in result

    @patch("edugain_analysis.cli.seccon.download_metadata")
    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_csv_output_without_headers(self, mock_analyze, mock_parse, mock_download):
        """Test CSV output without headers through main function."""
        mock_download.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://incommon.org", "SP", "Example SP", "https://sp.example.org"],
        ]

        test_args = ["seccon", "--no-headers"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        assert "RegistrationAuthority" not in result
        assert "https://incommon.org,SP,Example SP,https://sp.example.org" in result


class TestMain:
    """Test the main function."""

    @patch("edugain_analysis.cli.seccon.download_metadata")
    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_main_default_options(self, mock_analyze, mock_parse, mock_download):
        """Test main function with default options."""
        mock_download.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["seccon"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_download.assert_called_once_with(EDUGAIN_METADATA_URL)
        mock_parse.assert_called_once()
        mock_analyze.assert_called_once()

    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_main_local_file(self, mock_analyze, mock_parse):
        """Test main function with local file option."""
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["seccon", "--local-file", "metadata.xml"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_parse.assert_called_once_with(None, "metadata.xml")
        mock_analyze.assert_called_once()

    @patch("edugain_analysis.cli.seccon.download_metadata")
    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_main_no_headers(self, mock_analyze, mock_parse, mock_download):
        """Test main function with no headers option."""
        mock_download.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["seccon", "--no-headers"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        # Should not contain headers
        assert "RegistrationAuthority" not in result

    @patch("edugain_analysis.cli.seccon.download_metadata")
    @patch("edugain_analysis.cli.seccon.parse_metadata")
    @patch("edugain_analysis.cli.seccon.analyze_entities")
    def test_main_custom_url(self, mock_analyze, mock_parse, mock_download):
        """Test main function with custom URL option."""
        mock_download.return_value = b"<xml>metadata</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["seccon", "--url", "https://custom.example.org/metadata"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_download.assert_called_once_with("https://custom.example.org/metadata")

    def test_main_help_option(self):
        """Test main function with help option."""
        test_args = ["seccon", "--help"]
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0  # Help should exit with code 0
