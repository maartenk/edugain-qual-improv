"""Tests for cli/sirtfi.py functionality."""

import os
import sys
import xml.etree.ElementTree as ET
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.cli.sirtfi import (
    EDUGAIN_METADATA_URL,
    REQUEST_TIMEOUT,
    analyze_entities,
    main,
)


class TestAnalyzeEntities:
    """Test the analyze_entities function."""

    def test_analyze_entities_with_sirtfi_no_security(self):
        """Test analysis of entities with SIRTFI but no security contacts."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
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

    def test_analyze_entities_with_security_contact(self):
        """Test analysis of entities with security contact (should be excluded)."""
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
                    <md:OrganizationDisplayName xml:lang="en">SP with security contact</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - has security contact

    def test_analyze_entities_incommon_security_contact(self):
        """Test analysis with InCommon security contact format (should be excluded)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:icmd="http://id.incommon.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://idp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
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

        assert len(entities) == 0  # Should be excluded - has InCommon security contact

    def test_analyze_entities_no_sirtfi(self):
        """Test analysis of entities without SIRTFI certification (should be excluded)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">SP without SIRTFI</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 0  # Should be excluded - no SIRTFI

    def test_analyze_entities_missing_fields(self):
        """Test analysis with missing optional fields but required registration authority."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://sp.minimal.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://minimal.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
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
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor>
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
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
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
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
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://sp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority=""/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
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
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://unknown.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        entities = analyze_entities(root)

        assert len(entities) == 1
        assert entities[0][1] is None  # entity type should be None

    def test_analyze_entities_idp_with_sirtfi_no_security(self):
        """Test analysis of IdP with SIRTFI but no security contacts."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://idp.example.org">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://ukfed.org.uk"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
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


class TestCSVOutput:
    """Test CSV output functionality within main function."""

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_csv_output_with_headers(self, mock_analyze, mock_load):
        """Test CSV output with headers through main function."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://incommon.org", "SP", "Example SP", "https://sp.example.org"],
            ["https://ukfed.org.uk", "IdP", "Example IdP", "https://idp.example.org"],
        ]

        test_args = ["sirtfi"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        lines = result.strip().split("\n")
        assert "RegistrationAuthority,EntityType,OrganizationName,EntityID" in lines[0]
        assert "https://incommon.org,SP,Example SP,https://sp.example.org" in result
        mock_load.assert_called_once_with(
            None, EDUGAIN_METADATA_URL, EDUGAIN_METADATA_URL, REQUEST_TIMEOUT
        )

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_csv_output_without_headers(self, mock_analyze, mock_load):
        """Test CSV output without headers through main function."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [
            ["https://incommon.org", "SP", "Example SP", "https://sp.example.org"],
        ]

        test_args = ["sirtfi", "--no-headers"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        assert "RegistrationAuthority" not in result
        assert "https://incommon.org,SP,Example SP,https://sp.example.org" in result
        mock_load.assert_called_once_with(
            None, EDUGAIN_METADATA_URL, EDUGAIN_METADATA_URL, REQUEST_TIMEOUT
        )


class TestMain:
    """Test the main function."""

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_main_default_options(self, mock_analyze, mock_load):
        """Test main function with default options."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["sirtfi"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_load.assert_called_once_with(
            None, EDUGAIN_METADATA_URL, EDUGAIN_METADATA_URL, REQUEST_TIMEOUT
        )
        mock_analyze.assert_called_once_with(mock_load.return_value)

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_main_local_file(self, mock_analyze, mock_load):
        """Test main function with local file option."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["sirtfi", "--local-file", "metadata.xml"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_load.assert_called_once_with(
            "metadata.xml", None, EDUGAIN_METADATA_URL, REQUEST_TIMEOUT
        )
        mock_analyze.assert_called_once_with(mock_load.return_value)

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_main_no_headers(self, mock_analyze, mock_load):
        """Test main function with no headers option."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["sirtfi", "--no-headers"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                main()
                result = mock_stdout.getvalue()

        # Should not contain headers
        assert "RegistrationAuthority" not in result
        mock_load.assert_called_once_with(
            None, EDUGAIN_METADATA_URL, EDUGAIN_METADATA_URL, REQUEST_TIMEOUT
        )

    @patch("edugain_analysis.cli.utils.load_metadata_for_cli")
    @patch("edugain_analysis.cli.sirtfi.analyze_entities")
    def test_main_custom_url(self, mock_analyze, mock_load):
        """Test main function with custom URL option."""
        mock_load.return_value = MagicMock()
        mock_analyze.return_value = [["reg_auth", "SP", "Org", "entity_id"]]

        test_args = ["sirtfi", "--url", "https://custom.example.org/metadata"]
        with patch("sys.argv", test_args):
            with patch("sys.stdout", new_callable=StringIO):
                main()

        mock_load.assert_called_once_with(
            None,
            "https://custom.example.org/metadata",
            EDUGAIN_METADATA_URL,
            REQUEST_TIMEOUT,
        )

    def test_main_help_option(self):
        """Test main function with help option."""
        test_args = ["sirtfi", "--help"]
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0  # Help should exit with code 0
