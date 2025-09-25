#!/usr/bin/env python3
"""
Test suite for seccon_nosirtfi.py

Comprehensive tests for the eduGAIN Security Contact Analysis Tool.
"""

import argparse
import io
import tempfile
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seccon_nosirtfi


# Test fixtures
@pytest.fixture
def mock_response():
    """Create a reusable mock HTTP response."""
    response = MagicMock()
    response.content = b"<xml>test content</xml>"
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "entity_id": "https://example.org/sp",
        "reg_authority": "https://example.org",
        "org_name": "Test Organization",
    }


@pytest.fixture
def xml_builder():
    """Factory function to build test XML entities."""

    def _build_entity(
        entity_id: str = "https://example.org/sp",
        has_security_contact: bool = True,
        has_sirtfi: bool = False,
        reg_authority: str = "https://example.org",
        org_name: str = "Test Org",
        entity_type: str = "SP",
        contact_type: str = "refeds",
    ):
        """Build a test entity XML element."""
        namespaces = {
            "md": "urn:oasis:names:tc:SAML:2.0:metadata",
            "remd": "http://refeds.org/metadata",
            "icmd": "http://id.incommon.org/metadata",
            "mdrpi": "urn:oasis:names:tc:SAML:metadata:rpi",
            "mdattr": "urn:oasis:names:tc:SAML:metadata:attribute",
            "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        }

        # Register namespaces for pretty XML generation
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        # Create root element
        entity = ET.Element(f"{{{namespaces['md']}}}EntityDescriptor")
        entity.set("entityID", entity_id)

        # Extensions
        extensions = ET.SubElement(entity, f"{{{namespaces['md']}}}Extensions")

        # Registration info
        reg_info = ET.SubElement(
            extensions, f"{{{namespaces['mdrpi']}}}RegistrationInfo"
        )
        reg_info.set("registrationAuthority", reg_authority)

        # SIRTFI certification if requested
        if has_sirtfi:
            entity_attrs = ET.SubElement(
                extensions, f"{{{namespaces['mdattr']}}}EntityAttributes"
            )
            attr = ET.SubElement(entity_attrs, f"{{{namespaces['saml']}}}Attribute")
            attr.set(
                "Name", "urn:oasis:names:tc:SAML:attribute:assurance-certification"
            )
            attr_value = ET.SubElement(attr, f"{{{namespaces['saml']}}}AttributeValue")
            attr_value.text = "https://refeds.org/sirtfi"

        # Security contact if requested
        if has_security_contact:
            contact = ET.SubElement(entity, f"{{{namespaces['md']}}}ContactPerson")
            if contact_type == "refeds":
                contact.set(
                    f"{{{namespaces['remd']}}}contactType",
                    "http://refeds.org/metadata/contactType/security",
                )
            else:  # incommon
                contact.set(
                    f"{{{namespaces['icmd']}}}contactType",
                    "http://id.incommon.org/metadata/contactType/security",
                )
            email = ET.SubElement(contact, f"{{{namespaces['md']}}}EmailAddress")
            email.text = "security@example.org"

        # Organization
        org = ET.SubElement(entity, f"{{{namespaces['md']}}}Organization")
        org_display = ET.SubElement(
            org, f"{{{namespaces['md']}}}OrganizationDisplayName"
        )
        org_display.text = org_name

        # Entity type descriptor
        if entity_type == "SP":
            ET.SubElement(entity, f"{{{namespaces['md']}}}SPSSODescriptor")
        elif entity_type == "IdP":
            ET.SubElement(entity, f"{{{namespaces['md']}}}IDPSSODescriptor")

        return entity

    return _build_entity


@pytest.fixture
def entities_descriptor():
    """Create an EntitiesDescriptor root element."""
    return ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")


# Test classes
class TestDownloadMetadata:
    """Tests for the download_metadata function."""

    @patch("seccon_nosirtfi.requests.get")
    def test_successful_download(self, mock_get, mock_response):
        """Test successful metadata download."""
        mock_get.return_value = mock_response

        result = seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=30)
        mock_response.raise_for_status.assert_called_once()
        assert result == b"<xml>test content</xml>"

    @patch("seccon_nosirtfi.requests.get")
    @patch("sys.exit")
    def test_request_exception(self, mock_exit, mock_get):
        """Test request exception handling."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_exit.assert_called_once_with(1)
        assert "Error downloading metadata" in mock_stderr.getvalue()

    @patch("seccon_nosirtfi.requests.get")
    @patch("sys.exit")
    def test_http_error(self, mock_exit, mock_get):
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_exit.assert_called_once_with(1)
        assert "Error downloading metadata" in mock_stderr.getvalue()

    @patch("seccon_nosirtfi.requests.get")
    def test_custom_timeout(self, mock_get, mock_response):
        """Test download with custom timeout."""
        mock_get.return_value = mock_response

        seccon_nosirtfi.download_metadata("http://example.com/metadata.xml", timeout=60)

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=60)


class TestParseMetadata:
    """Tests for the parse_metadata function."""

    def test_parse_xml_content(self):
        """Test parsing XML content from bytes."""
        xml_content = b"<root><child>test</child></root>"
        result = seccon_nosirtfi.parse_metadata(xml_content)

        assert result.tag == "root"
        child = result.find("child")
        assert child is not None
        assert child.text == "test"

    def test_parse_local_file(self):
        """Test parsing XML from local file."""
        xml_content = "<root><child>test</child></root>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            result = seccon_nosirtfi.parse_metadata(None, f.name)

        assert result.tag == "root"
        child = result.find("child")
        assert child is not None
        assert child.text == "test"

    @patch("sys.exit")
    def test_invalid_xml_content(self, mock_exit):
        """Test parsing invalid XML content."""
        xml_content = b"<invalid xml content"

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.parse_metadata(xml_content)

        mock_exit.assert_called_once_with(1)
        assert "Error parsing XML" in mock_stderr.getvalue()

    @patch("sys.exit")
    def test_invalid_local_file(self, mock_exit):
        """Test parsing invalid local XML file."""
        xml_content = "<invalid xml content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                seccon_nosirtfi.parse_metadata(None, f.name)

        mock_exit.assert_called_once_with(1)
        assert "Error parsing XML" in mock_stderr.getvalue()


class TestAnalyzeEntities:
    """Tests for the analyze_entities function."""

    def test_entity_with_security_contact_no_sirtfi(
        self, entities_descriptor, xml_builder, sample_entity_data
    ):
        """Test entity with security contact but no SIRTFI."""
        entity = xml_builder(
            entity_id=sample_entity_data["entity_id"],
            has_security_contact=True,
            has_sirtfi=False,
            reg_authority=sample_entity_data["reg_authority"],
            org_name=sample_entity_data["org_name"],
        )
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 1
        assert result[0][0] == sample_entity_data["reg_authority"]
        assert result[0][1] == "SP"
        assert result[0][2] == sample_entity_data["org_name"]
        assert result[0][3] == sample_entity_data["entity_id"]

    def test_entity_with_security_contact_and_sirtfi(
        self, entities_descriptor, xml_builder
    ):
        """Test entity with security contact and SIRTFI (should be excluded)."""
        entity = xml_builder(has_security_contact=True, has_sirtfi=True)
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 0

    def test_entity_without_security_contact(self, entities_descriptor, xml_builder):
        """Test entity without security contact (should be excluded)."""
        entity = xml_builder(has_security_contact=False, has_sirtfi=False)
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 0

    @pytest.mark.parametrize(
        "entity_type,expected_type",
        [
            ("SP", "SP"),
            ("IdP", "IdP"),
        ],
    )
    def test_entity_types(
        self, entities_descriptor, xml_builder, entity_type, expected_type
    ):
        """Test detection of SP and IdP entity types."""
        entity = xml_builder(entity_type=entity_type)
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 1
        assert result[0][1] == expected_type

    @pytest.mark.parametrize("contact_type", ["refeds", "incommon"])
    def test_security_contact_types(
        self, entities_descriptor, xml_builder, contact_type
    ):
        """Test both REFEDS and InCommon security contact types."""
        entity = xml_builder(contact_type=contact_type)
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 1

    def test_entity_without_registration_info(self, sample_entity_data):
        """Test entity without registration info (should be excluded)."""
        entity_xml = f"""
        <md:EntityDescriptor entityID="{sample_entity_data['entity_id']}"
                           xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                           xmlns:remd="http://refeds.org/metadata">
            <md:Extensions></md:Extensions>
            <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                <md:EmailAddress>security@example.org</md:EmailAddress>
            </md:ContactPerson>
            <md:Organization>
                <md:OrganizationDisplayName>{sample_entity_data['org_name']}</md:OrganizationDisplayName>
            </md:Organization>
            <md:SPSSODescriptor/>
        </md:EntityDescriptor>
        """

        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = ET.fromstring(entity_xml)
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        assert len(result) == 0

    def test_entity_with_missing_org_name(self, entities_descriptor, xml_builder):
        """Test entity with missing organization name."""
        entity = xml_builder(org_name="")
        # Manually remove the organization display name text
        org_display = entity.find(
            ".//{urn:oasis:names:tc:SAML:2.0:metadata}OrganizationDisplayName"
        )
        if org_display is not None:
            org_display.text = None
        entities_descriptor.append(entity)

        result = seccon_nosirtfi.analyze_entities(entities_descriptor)

        assert len(result) == 1
        assert result[0][2] == "Unknown"


class TestMainFunction:
    """Tests for the main function and CLI interface."""

    @patch("seccon_nosirtfi.download_metadata")
    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_default_behavior(
        self, mock_stdout, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with default arguments."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://example.org", "SP", "Test Org", "https://example.org/sp"]
        ]

        with patch("sys.argv", ["seccon_nosirtfi.py"]):
            seccon_nosirtfi.main()

        mock_download.assert_called_once_with(seccon_nosirtfi.EDUGAIN_METADATA_URL)
        mock_parse.assert_called_once()
        mock_analyze.assert_called_once()

        output = mock_stdout.getvalue()
        assert "RegistrationAuthority,EntityType,OrganizationName,EntityID" in output
        assert "https://example.org,SP,Test Org,https://example.org/sp" in output

    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_local_file(self, mock_stdout, mock_analyze, mock_parse):
        """Test main function with local file argument."""
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://example.org", "SP", "Test Org", "https://example.org/sp"]
        ]

        with patch("sys.argv", ["seccon_nosirtfi.py", "--local-file", "test.xml"]):
            seccon_nosirtfi.main()

        mock_parse.assert_called_once_with(None, "test.xml")

    @patch("seccon_nosirtfi.download_metadata")
    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_no_headers(
        self, mock_stdout, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with no headers argument."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://example.org", "SP", "Test Org", "https://example.org/sp"]
        ]

        with patch("sys.argv", ["seccon_nosirtfi.py", "--no-headers"]):
            seccon_nosirtfi.main()

        output = mock_stdout.getvalue()
        assert (
            "RegistrationAuthority,EntityType,OrganizationName,EntityID" not in output
        )
        assert "https://example.org,SP,Test Org,https://example.org/sp" in output

    @patch("seccon_nosirtfi.download_metadata")
    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    def test_main_custom_url(self, mock_analyze, mock_parse, mock_download):
        """Test main function with custom URL argument."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = []

        custom_url = "https://custom.example.com/metadata.xml"
        with patch("sys.argv", ["seccon_nosirtfi.py", "--url", custom_url]):
            seccon_nosirtfi.main()

        mock_download.assert_called_once_with(custom_url)


class TestArgumentParser:
    """Tests for argument parser configuration."""

    def test_parser_defaults(self):
        """Test argument parser with default values."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--local-file", help="Use local XML file instead of downloading"
        )
        parser.add_argument(
            "--no-headers", action="store_true", help="Omit CSV headers from output"
        )
        parser.add_argument(
            "--url",
            default=seccon_nosirtfi.EDUGAIN_METADATA_URL,
            help="Custom metadata URL",
        )

        args = parser.parse_args([])

        assert args.local_file is None
        assert args.no_headers is False
        assert args.url == seccon_nosirtfi.EDUGAIN_METADATA_URL

    def test_parser_all_args(self):
        """Test argument parser with all arguments provided."""
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--local-file", help="Use local XML file instead of downloading"
        )
        parser.add_argument(
            "--no-headers", action="store_true", help="Omit CSV headers from output"
        )
        parser.add_argument(
            "--url",
            default=seccon_nosirtfi.EDUGAIN_METADATA_URL,
            help="Custom metadata URL",
        )

        args = parser.parse_args(
            ["--local-file", "test.xml", "--no-headers", "--url", "https://example.com"]
        )

        assert args.local_file == "test.xml"
        assert args.no_headers is True
        assert args.url == "https://example.com"


class TestConstants:
    """Tests for constants and configuration."""

    def test_constants_defined(self):
        """Test that constants are properly defined."""
        assert (
            seccon_nosirtfi.EDUGAIN_METADATA_URL
            == "https://mds.edugain.org/edugain-v2.xml"
        )
        assert seccon_nosirtfi.REQUEST_TIMEOUT == 30
        assert isinstance(seccon_nosirtfi.NAMESPACES, dict)
        assert "md" in seccon_nosirtfi.NAMESPACES
        assert "remd" in seccon_nosirtfi.NAMESPACES
        assert "icmd" in seccon_nosirtfi.NAMESPACES


if __name__ == "__main__":
    pytest.main([__file__])
