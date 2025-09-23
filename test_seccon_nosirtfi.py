#!/usr/bin/env python3
"""
Test suite for seccon_nosirtfi.py

Comprehensive tests for the eduGAIN Security Contact Analysis Tool.
"""

import argparse
import io
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
import requests

import seccon_nosirtfi

# Test data constants for performance
SAMPLE_XML_CONTENT = b"<xml>test content</xml>"
MOCK_ENTITY_ID = "https://example.org/sp"
MOCK_REG_AUTHORITY = "https://example.org"
MOCK_ORG_NAME = "Example Organization"

# Reusable XML templates for efficient test data generation
XML_TEMPLATE_WITH_SIRTFI = """<?xml version="1.0" encoding="UTF-8"?>
<md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                       xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                       xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                       xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                       xmlns:remd="http://refeds.org/metadata"
                       xmlns:icmd="http://id.incommon.org/metadata">
    <md:EntityDescriptor entityID="{entity_id}">
        <md:Extensions>
            <mdrpi:RegistrationInfo registrationAuthority="{reg_authority}"/>
            <mdattr:EntityAttributes>
                <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                    <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                </saml:Attribute>
            </mdattr:EntityAttributes>
        </md:Extensions>
        <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
            <md:EmailAddress>security@example.org</md:EmailAddress>
        </md:ContactPerson>
        <md:Organization>
            <md:OrganizationDisplayName>{org_name}</md:OrganizationDisplayName>
        </md:Organization>
        <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
    </md:EntityDescriptor>
</md:EntitiesDescriptor>"""

XML_TEMPLATE_NO_SIRTFI = """<?xml version="1.0" encoding="UTF-8"?>
<md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                       xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                       xmlns:remd="http://refeds.org/metadata">
    <md:EntityDescriptor entityID="{entity_id}">
        <md:Extensions>
            <mdrpi:RegistrationInfo registrationAuthority="{reg_authority}"/>
        </md:Extensions>
        <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
            <md:EmailAddress>security@example.org</md:EmailAddress>
        </md:ContactPerson>
        <md:Organization>
            <md:OrganizationDisplayName>{org_name}</md:OrganizationDisplayName>
        </md:Organization>
        <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
    </md:EntityDescriptor>
</md:EntitiesDescriptor>"""


@pytest.fixture
def mock_response():
    """Create a reusable mock response."""
    response = MagicMock()
    response.content = SAMPLE_XML_CONTENT
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def sample_xml_with_sirtfi():
    """Generate sample XML with SIRTFI certification."""
    return XML_TEMPLATE_WITH_SIRTFI.format(
        entity_id=MOCK_ENTITY_ID,
        reg_authority=MOCK_REG_AUTHORITY,
        org_name=MOCK_ORG_NAME,
    )


@pytest.fixture
def sample_xml_no_sirtfi():
    """Generate sample XML without SIRTFI certification."""
    return XML_TEMPLATE_NO_SIRTFI.format(
        entity_id=MOCK_ENTITY_ID,
        reg_authority=MOCK_REG_AUTHORITY,
        org_name=MOCK_ORG_NAME,
    )


class TestDownloadMetadata(unittest.TestCase):
    """Test the download_metadata function."""

    @patch("seccon_nosirtfi.requests.get")
    def test_successful_download(self, mock_get: MagicMock) -> None:
        """Test successful metadata download."""
        mock_response = MagicMock()
        mock_response.content = SAMPLE_XML_CONTENT
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=30)
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, SAMPLE_XML_CONTENT)

    @patch("seccon_nosirtfi.requests.get")
    @patch("sys.exit")
    def test_download_request_exception(
        self, mock_exit: MagicMock, mock_get: MagicMock
    ) -> None:
        """Test request exception during download."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_exit.assert_called_once_with(1)
        self.assertIn("Error downloading metadata", mock_stderr.getvalue())

    @patch("seccon_nosirtfi.requests.get")
    @patch("sys.exit")
    def test_download_http_error(
        self, mock_exit: MagicMock, mock_get: MagicMock
    ) -> None:
        """Test HTTP error during download."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.download_metadata("http://example.com/metadata.xml")

        mock_exit.assert_called_once_with(1)
        self.assertIn("Error downloading metadata", mock_stderr.getvalue())

    @patch("seccon_nosirtfi.requests.get")
    def test_download_custom_timeout(self, mock_get: MagicMock) -> None:
        """Test download with custom timeout."""
        mock_response = MagicMock()
        mock_response.content = b"<xml>test</xml>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        seccon_nosirtfi.download_metadata("http://example.com/metadata.xml", timeout=60)

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=60)


class TestParseMetadata(unittest.TestCase):
    """Test the parse_metadata function."""

    def test_parse_xml_content(self) -> None:
        """Test parsing XML content from string."""
        xml_content = b"<root><child>test</child></root>"
        result = seccon_nosirtfi.parse_metadata(xml_content)

        self.assertEqual(result.tag, "root")
        child_elem = result.find("child")
        assert child_elem is not None
        self.assertEqual(child_elem.text, "test")

    def test_parse_local_file(self) -> None:
        """Test parsing XML from local file."""
        xml_content = "<root><child>test</child></root>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            result = seccon_nosirtfi.parse_metadata(None, f.name)

        self.assertEqual(result.tag, "root")
        child_elem = result.find("child")
        assert child_elem is not None
        self.assertEqual(child_elem.text, "test")

    @patch("sys.exit")
    def test_parse_invalid_xml_content(self, mock_exit: MagicMock) -> None:
        """Test parsing invalid XML content."""
        xml_content = b"<invalid xml content"

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            seccon_nosirtfi.parse_metadata(xml_content)

        mock_exit.assert_called_once_with(1)
        self.assertIn("Error parsing XML", mock_stderr.getvalue())

    @patch("sys.exit")
    def test_parse_invalid_local_file(self, mock_exit: MagicMock) -> None:
        """Test parsing invalid local XML file."""
        xml_content = "<invalid xml content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            f.flush()

            with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                seccon_nosirtfi.parse_metadata(None, f.name)

        mock_exit.assert_called_once_with(1)
        self.assertIn("Error parsing XML", mock_stderr.getvalue())


class TestAnalyzeEntities(unittest.TestCase):
    """Test the analyze_entities function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.namespaces = seccon_nosirtfi.NAMESPACES

    def create_test_entity(
        self,
        entity_id: str,
        has_security_contact: bool = True,
        has_sirtfi: bool = False,
        registration_authority: str = "https://example.org",
        org_name: str = "Test Org",
        entity_type: str = "SP",
    ) -> ET.Element:
        """Helper to create test entity XML."""
        entity_xml = f"""
        <md:EntityDescriptor entityID="{entity_id}" xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                           xmlns:remd="http://refeds.org/metadata"
                           xmlns:icmd="http://id.incommon.org/metadata"
                           xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                           xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                           xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:Extensions>
                <mdrpi:RegistrationInfo registrationAuthority="{registration_authority}"/>
        """

        if has_sirtfi:
            entity_xml += """
                <mdattr:EntityAttributes>
                    <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                        <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                    </saml:Attribute>
                </mdattr:EntityAttributes>
            """

        entity_xml += "</md:Extensions>"

        if has_security_contact:
            entity_xml += """
            <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                <md:EmailAddress>security@example.org</md:EmailAddress>
            </md:ContactPerson>
            """

        entity_xml += f"""
            <md:Organization>
                <md:OrganizationDisplayName>{org_name}</md:OrganizationDisplayName>
            </md:Organization>
        """

        if entity_type == "SP":
            entity_xml += "<md:SPSSODescriptor/>"
        elif entity_type == "IdP":
            entity_xml += "<md:IDPSSODescriptor/>"

        entity_xml += "</md:EntityDescriptor>"

        return ET.fromstring(entity_xml)

    def test_entity_with_security_contact_no_sirtfi(self) -> None:
        """Test entity with security contact but no SIRTFI."""
        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = self.create_test_entity(
            "https://example.org/sp", has_security_contact=True, has_sirtfi=False
        )
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "https://example.org")  # registration authority
        self.assertEqual(result[0][1], "SP")  # entity type
        self.assertEqual(result[0][2], "Test Org")  # org name
        self.assertEqual(result[0][3], "https://example.org/sp")  # entity ID

    def test_entity_with_security_contact_and_sirtfi(self) -> None:
        """Test entity with security contact and SIRTFI (should be excluded)."""
        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = self.create_test_entity(
            "https://example.org/sp", has_security_contact=True, has_sirtfi=True
        )
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 0)

    def test_entity_without_security_contact(self) -> None:
        """Test entity without security contact (should be excluded)."""
        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = self.create_test_entity(
            "https://example.org/sp", has_security_contact=False, has_sirtfi=False
        )
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 0)

    def test_entity_types_sp_and_idp(self) -> None:
        """Test detection of SP and IdP entity types."""
        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")

        sp_entity = self.create_test_entity("https://example.org/sp", entity_type="SP")
        idp_entity = self.create_test_entity(
            "https://example.org/idp", entity_type="IdP"
        )

        root.append(sp_entity)
        root.append(idp_entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], "SP")
        self.assertEqual(result[1][1], "IdP")

    def test_incommon_security_contact(self) -> None:
        """Test InCommon security contact type."""
        entity_xml = """
        <md:EntityDescriptor entityID="https://example.org/sp" xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                           xmlns:icmd="http://id.incommon.org/metadata"
                           xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:Extensions>
                <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
            </md:Extensions>
            <md:ContactPerson icmd:contactType="http://id.incommon.org/metadata/contactType/security">
                <md:EmailAddress>security@example.org</md:EmailAddress>
            </md:ContactPerson>
            <md:Organization>
                <md:OrganizationDisplayName>Test Org</md:OrganizationDisplayName>
            </md:Organization>
            <md:SPSSODescriptor/>
        </md:EntityDescriptor>
        """

        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = ET.fromstring(entity_xml)
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 1)

    def test_entity_without_registration_info(self) -> None:
        """Test entity without registration info (should be excluded)."""
        entity_xml = """
        <md:EntityDescriptor entityID="https://example.org/sp" xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                           xmlns:remd="http://refeds.org/metadata">
            <md:Extensions>
            </md:Extensions>
            <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                <md:EmailAddress>security@example.org</md:EmailAddress>
            </md:ContactPerson>
            <md:Organization>
                <md:OrganizationDisplayName>Test Org</md:OrganizationDisplayName>
            </md:Organization>
            <md:SPSSODescriptor/>
        </md:EntityDescriptor>
        """

        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = ET.fromstring(entity_xml)
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 0)

    def test_entity_with_missing_org_name(self) -> None:
        """Test entity with missing organization name."""
        entity_xml = """
        <md:EntityDescriptor entityID="https://example.org/sp" xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                           xmlns:remd="http://refeds.org/metadata"
                           xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:Extensions>
                <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
            </md:Extensions>
            <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                <md:EmailAddress>security@example.org</md:EmailAddress>
            </md:ContactPerson>
            <md:Organization>
            </md:Organization>
            <md:SPSSODescriptor/>
        </md:EntityDescriptor>
        """

        root = ET.Element("{urn:oasis:names:tc:SAML:2.0:metadata}EntitiesDescriptor")
        entity = ET.fromstring(entity_xml)
        root.append(entity)

        result = seccon_nosirtfi.analyze_entities(root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][2], "Unknown")  # org name should be "Unknown"


class TestCommandLineInterface(unittest.TestCase):
    """Test command-line interface and main function."""

    @patch("seccon_nosirtfi.download_metadata")
    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_default_behavior(
        self,
        mock_stdout: io.StringIO,
        mock_analyze: MagicMock,
        mock_parse: MagicMock,
        mock_download: MagicMock,
    ) -> None:
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
        self.assertIn(
            "RegistrationAuthority,EntityType,OrganizationName,EntityID", output
        )
        self.assertIn("https://example.org,SP,Test Org,https://example.org/sp", output)

    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_local_file(
        self, mock_stdout: io.StringIO, mock_analyze: MagicMock, mock_parse: MagicMock
    ) -> None:
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
        self,
        mock_stdout: io.StringIO,
        mock_analyze: MagicMock,
        mock_parse: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        """Test main function with no headers argument."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://example.org", "SP", "Test Org", "https://example.org/sp"]
        ]

        with patch("sys.argv", ["seccon_nosirtfi.py", "--no-headers"]):
            seccon_nosirtfi.main()

        output = mock_stdout.getvalue()
        self.assertNotIn(
            "RegistrationAuthority,EntityType,OrganizationName,EntityID", output
        )
        self.assertIn("https://example.org,SP,Test Org,https://example.org/sp", output)

    @patch("seccon_nosirtfi.download_metadata")
    @patch("seccon_nosirtfi.parse_metadata")
    @patch("seccon_nosirtfi.analyze_entities")
    def test_main_custom_url(
        self, mock_analyze: MagicMock, mock_parse: MagicMock, mock_download: MagicMock
    ) -> None:
        """Test main function with custom URL argument."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = []

        with patch(
            "sys.argv",
            ["seccon_nosirtfi.py", "--url", "https://custom.example.com/metadata.xml"],
        ):
            seccon_nosirtfi.main()

        mock_download.assert_called_once_with("https://custom.example.com/metadata.xml")


class TestArgumentParser(unittest.TestCase):
    """Test argument parser configuration."""

    def test_argument_parser_defaults(self) -> None:
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

        self.assertIsNone(args.local_file)
        self.assertFalse(args.no_headers)
        self.assertEqual(args.url, seccon_nosirtfi.EDUGAIN_METADATA_URL)

    def test_argument_parser_all_args(self) -> None:
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

        self.assertEqual(args.local_file, "test.xml")
        self.assertTrue(args.no_headers)
        self.assertEqual(args.url, "https://example.com")


class TestConstants(unittest.TestCase):
    """Test constants and configuration."""

    def test_constants(self) -> None:
        """Test that constants are properly defined."""
        self.assertEqual(
            seccon_nosirtfi.EDUGAIN_METADATA_URL,
            "https://mds.edugain.org/edugain-v2.xml",
        )
        self.assertEqual(seccon_nosirtfi.REQUEST_TIMEOUT, 30)
        self.assertIsInstance(seccon_nosirtfi.NAMESPACES, dict)
        self.assertIn("md", seccon_nosirtfi.NAMESPACES)
        self.assertIn("remd", seccon_nosirtfi.NAMESPACES)
        self.assertIn("icmd", seccon_nosirtfi.NAMESPACES)


if __name__ == "__main__":
    unittest.main()
