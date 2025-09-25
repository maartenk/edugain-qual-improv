#!/usr/bin/env python3
"""
Test suite for privacy_security_analysis.py

Comprehensive tests for the eduGAIN Privacy Statement and Security Contact Analysis Tool.
"""

import argparse
import io
import tempfile
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
import requests

import privacy_security_analysis


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
        has_privacy_statement: bool = True,
        privacy_url: str = "https://example.org/privacy",
        has_security_contact: bool = True,
        reg_authority: str = "https://example.org",
        org_name: str = "Test Org",
        entity_type: str = "SP",
        contact_type: str = "refeds",
    ):
        """Build a test entity XML element."""
        namespaces = {
            "md": "urn:oasis:names:tc:SAML:2.0:metadata",
            "mdui": "urn:oasis:names:tc:SAML:metadata:ui",
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

        # UI Info with Privacy Statement URL if requested
        if has_privacy_statement:
            ui_info = ET.SubElement(extensions, f"{{{namespaces['mdui']}}}UIInfo")
            privacy_elem = ET.SubElement(
                ui_info, f"{{{namespaces['mdui']}}}PrivacyStatementURL"
            )
            privacy_elem.text = privacy_url

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

    @patch("privacy_security_analysis.requests.get")
    def test_successful_download(self, mock_get, mock_response):
        """Test successful metadata download."""
        mock_get.return_value = mock_response

        result = privacy_security_analysis.download_metadata(
            "http://example.com/metadata.xml"
        )

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=30)
        mock_response.raise_for_status.assert_called_once()
        assert result == b"<xml>test content</xml>"

    @patch("privacy_security_analysis.requests.get")
    @patch("sys.exit")
    def test_request_exception(self, mock_exit, mock_get):
        """Test request exception handling."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.download_metadata(
                "http://example.com/metadata.xml"
            )

        mock_exit.assert_called_once_with(1)
        assert "Error downloading metadata" in mock_stderr.getvalue()

    @patch("privacy_security_analysis.requests.get")
    def test_custom_timeout(self, mock_get, mock_response):
        """Test download with custom timeout."""
        mock_get.return_value = mock_response

        privacy_security_analysis.download_metadata(
            "http://example.com/metadata.xml", timeout=60
        )

        mock_get.assert_called_once_with("http://example.com/metadata.xml", timeout=60)


class TestParseMetadata:
    """Tests for the parse_metadata function."""

    def test_parse_xml_content(self):
        """Test parsing XML content from bytes."""
        xml_content = b"<root><child>test</child></root>"
        result = privacy_security_analysis.parse_metadata(xml_content)

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

            result = privacy_security_analysis.parse_metadata(None, f.name)

        assert result.tag == "root"
        child = result.find("child")
        assert child is not None
        assert child.text == "test"

    @patch("sys.exit")
    def test_invalid_xml_content(self, mock_exit):
        """Test parsing invalid XML content."""
        xml_content = b"<invalid xml content"

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.parse_metadata(xml_content)

        mock_exit.assert_called_once_with(1)
        assert "Error parsing XML" in mock_stderr.getvalue()


class TestAnalyzePrivacySecurity:
    """Tests for the analyze_privacy_security function."""

    def test_entity_with_both_privacy_and_security(
        self, entities_descriptor, xml_builder, sample_entity_data
    ):
        """Test entity with both privacy statement and security contact."""
        entity = xml_builder(
            entity_id=sample_entity_data["entity_id"],
            has_privacy_statement=True,
            has_security_contact=True,
            reg_authority=sample_entity_data["reg_authority"],
            org_name=sample_entity_data["org_name"],
        )
        entities_descriptor.append(entity)

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[0] == sample_entity_data["reg_authority"]  # reg authority
        assert entity_data[1] == "SP"  # entity type
        assert entity_data[2] == sample_entity_data["org_name"]  # org name
        assert entity_data[3] == sample_entity_data["entity_id"]  # entity ID
        assert entity_data[4] == "Yes"  # has privacy
        assert entity_data[5] == "https://example.org/privacy"  # privacy URL
        assert entity_data[6] == "Yes"  # has security

        # Check stats
        assert stats["total_entities"] == 1
        assert stats["has_privacy"] == 1
        assert stats["has_security"] == 1
        assert stats["has_both"] == 1
        assert stats["missing_both"] == 0

    def test_entity_missing_privacy_statement(self, entities_descriptor, xml_builder):
        """Test entity missing privacy statement."""
        entity = xml_builder(has_privacy_statement=False, has_security_contact=True)
        entities_descriptor.append(entity)

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "No"  # has privacy
        assert entity_data[5] == ""  # privacy URL (empty)
        assert entity_data[6] == "Yes"  # has security

        assert stats["missing_privacy"] == 1
        assert stats["has_security"] == 1

    def test_entity_missing_security_contact(self, entities_descriptor, xml_builder):
        """Test entity missing security contact."""
        entity = xml_builder(has_privacy_statement=True, has_security_contact=False)
        entities_descriptor.append(entity)

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "Yes"  # has privacy
        assert entity_data[6] == "No"  # has security

        assert stats["has_privacy"] == 1
        assert stats["missing_security"] == 1

    def test_entity_missing_both(self, entities_descriptor, xml_builder):
        """Test entity missing both privacy statement and security contact."""
        entity = xml_builder(has_privacy_statement=False, has_security_contact=False)
        entities_descriptor.append(entity)

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "No"  # has privacy
        assert entity_data[5] == ""  # privacy URL (empty)
        assert entity_data[6] == "No"  # has security

        assert stats["missing_privacy"] == 1
        assert stats["missing_security"] == 1
        assert stats["missing_both"] == 1
        assert stats["has_both"] == 0

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

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        assert entities_list[0][1] == expected_type

    @pytest.mark.parametrize("contact_type", ["refeds", "incommon"])
    def test_security_contact_types(
        self, entities_descriptor, xml_builder, contact_type
    ):
        """Test both REFEDS and InCommon security contact types."""
        entity = xml_builder(contact_type=contact_type)
        entities_descriptor.append(entity)

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        assert entities_list[0][6] == "Yes"  # has security contact

    def test_multiple_entities_statistics(self, entities_descriptor, xml_builder):
        """Test statistics calculation with multiple entities."""
        # Entity with both
        entity1 = xml_builder(
            entity_id="https://example1.org",
            has_privacy_statement=True,
            has_security_contact=True,
        )
        # Entity missing privacy
        entity2 = xml_builder(
            entity_id="https://example2.org",
            has_privacy_statement=False,
            has_security_contact=True,
        )
        # Entity missing security
        entity3 = xml_builder(
            entity_id="https://example3.org",
            has_privacy_statement=True,
            has_security_contact=False,
        )
        # Entity missing both
        entity4 = xml_builder(
            entity_id="https://example4.org",
            has_privacy_statement=False,
            has_security_contact=False,
        )

        entities_descriptor.extend([entity1, entity2, entity3, entity4])

        entities_list, stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 4
        assert stats["total_entities"] == 4
        assert stats["has_privacy"] == 2
        assert stats["missing_privacy"] == 2
        assert stats["has_security"] == 2
        assert stats["missing_security"] == 2
        assert stats["has_both"] == 1
        assert stats["missing_both"] == 1


class TestFilterEntities:
    """Tests for the filter_entities function."""

    @pytest.fixture
    def sample_entities_list(self):
        """Sample entities list for testing filters."""
        return [
            # Entity with both
            [
                "https://example1.org",
                "SP",
                "Org1",
                "https://example1.org/sp",
                "Yes",
                "https://example1.org/privacy",
                "Yes",
            ],
            # Entity missing privacy
            [
                "https://example2.org",
                "SP",
                "Org2",
                "https://example2.org/sp",
                "No",
                "",
                "Yes",
            ],
            # Entity missing security
            [
                "https://example3.org",
                "IdP",
                "Org3",
                "https://example3.org/idp",
                "Yes",
                "https://example3.org/privacy",
                "No",
            ],
            # Entity missing both
            [
                "https://example4.org",
                "SP",
                "Org4",
                "https://example4.org/sp",
                "No",
                "",
                "No",
            ],
        ]

    def test_filter_missing_privacy(self, sample_entities_list):
        """Test filtering entities missing privacy statements."""
        result = privacy_security_analysis.filter_entities(
            sample_entities_list, "missing_privacy"
        )

        assert len(result) == 2
        assert all(entity[4] == "No" for entity in result)  # HasPrivacyStatement

    def test_filter_missing_security(self, sample_entities_list):
        """Test filtering entities missing security contacts."""
        result = privacy_security_analysis.filter_entities(
            sample_entities_list, "missing_security"
        )

        assert len(result) == 2
        assert all(entity[6] == "No" for entity in result)  # HasSecurityContact

    def test_filter_missing_both(self, sample_entities_list):
        """Test filtering entities missing both privacy and security."""
        result = privacy_security_analysis.filter_entities(
            sample_entities_list, "missing_both"
        )

        assert len(result) == 1
        assert result[0][4] == "No" and result[0][6] == "No"

    def test_no_filter(self, sample_entities_list):
        """Test that no filter returns all entities."""
        result = privacy_security_analysis.filter_entities(sample_entities_list, "all")

        assert len(result) == 4
        assert result == sample_entities_list


class TestPrintSummary:
    """Tests for the print_summary function."""

    def test_print_summary_with_data(self):
        """Test summary printing with sample data."""
        stats = {
            "total_entities": 100,
            "has_privacy": 60,
            "missing_privacy": 40,
            "has_security": 70,
            "missing_security": 30,
            "has_both": 50,
            "missing_both": 10,
        }

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.print_summary(stats)

        output = mock_stderr.getvalue()
        assert "Total entities analyzed: 100" in output
        assert "Privacy Statement URL Coverage:" in output
        assert "HAVE privacy statements: 60 out of 100 (60.0%)" in output
        assert "Missing privacy statements: 40 out of 100 (40.0%)" in output
        assert "Security Contact Coverage:" in output
        assert "HAVE security contacts: 70 out of 100 (70.0%)" in output
        assert "Missing security contacts: 30 out of 100 (30.0%)" in output
        assert "HAVE BOTH (fully compliant): 50 out of 100 (50.0%)" in output
        assert "HAVE AT LEAST ONE: 90 out of 100 (90.0%)" in output
        assert "Missing both: 10 out of 100 (10.0%)" in output
        assert "Key Insights:" in output
        assert "Security Contacts are better covered (70.0% vs 60.0%)" in output

    def test_print_summary_no_entities(self):
        """Test summary printing with no entities."""
        stats = {"total_entities": 0}

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.print_summary(stats)

        output = mock_stderr.getvalue()
        assert "No entities found in metadata." in output


class TestMainFunction:
    """Tests for the main function and CLI interface."""

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.print_summary")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_default_behavior(
        self, mock_stdout, mock_print_summary, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with default arguments."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = (
            [
                [
                    "https://example.org",
                    "SP",
                    "Test Org",
                    "https://example.org/sp",
                    "Yes",
                    "https://example.org/privacy",
                    "Yes",
                ]
            ],
            {"total_entities": 1, "has_privacy": 1, "has_security": 1},
        )

        with (
            patch("sys.argv", ["privacy_security_analysis.py"]),
            patch.object(
                privacy_security_analysis.argparse.ArgumentParser, "parse_args"
            ) as mock_parse_args,
        ):
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=False,
                missing_privacy=False,
                missing_security=False,
                missing_both=False,
            )
            privacy_security_analysis.main()

        mock_download.assert_called_once_with(
            privacy_security_analysis.EDUGAIN_METADATA_URL
        )
        mock_parse.assert_called_once()
        mock_analyze.assert_called_once()
        mock_print_summary.assert_called_once()

        output = mock_stdout.getvalue()
        assert (
            "RegistrationAuthority,EntityType,OrganizationName,EntityID,HasPrivacyStatement,PrivacyStatementURL,HasSecurityContact"
            in output
        )

    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.print_summary")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_local_file(
        self, mock_stdout, mock_print_summary, mock_analyze, mock_parse
    ):
        """Test main function with local file argument."""
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 0})

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file="test.xml",
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=False,
                missing_privacy=False,
                missing_security=False,
                missing_both=False,
            )
            privacy_security_analysis.main()

        mock_parse.assert_called_once_with(None, "test.xml")

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.print_summary")
    def test_main_summary_only(
        self, mock_print_summary, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with summary-only option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        mock_analyze.return_value = ([], {"total_entities": 0})

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=True,
                missing_privacy=False,
                missing_security=False,
                missing_both=False,
            )
            privacy_security_analysis.main()

        mock_print_summary.assert_called_once()


class TestConstants:
    """Tests for constants and configuration."""

    def test_constants_defined(self):
        """Test that constants are properly defined."""
        assert (
            privacy_security_analysis.EDUGAIN_METADATA_URL
            == "https://mds.edugain.org/edugain-v2.xml"
        )
        assert privacy_security_analysis.REQUEST_TIMEOUT == 30
        assert isinstance(privacy_security_analysis.NAMESPACES, dict)
        assert "md" in privacy_security_analysis.NAMESPACES
        assert "mdui" in privacy_security_analysis.NAMESPACES
        assert "remd" in privacy_security_analysis.NAMESPACES


if __name__ == "__main__":
    pytest.main([__file__])
