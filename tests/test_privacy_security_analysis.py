#!/usr/bin/env python3
"""
Test suite for privacy_security_analysis.py

Comprehensive tests for the eduGAIN Privacy Statement and Security Contact Analysis Tool.
"""

import argparse
import io
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import pytest
import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# Helper functions for mocking
def mock_open_read_json(data):
    """Helper to mock open() for reading JSON data."""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(data))


def mock_open_read_bytes(data):
    """Helper to mock open() for reading bytes data."""
    from unittest.mock import mock_open
    return mock_open(read_data=data)


def mock_open_write_bytes():
    """Helper to mock open() for writing bytes data."""
    from unittest.mock import mock_open
    return mock_open()


# Test classes
class TestFederationMapping:
    """Tests for federation mapping functionality."""

    @pytest.fixture
    def mock_federation_response(self):
        """Mock response from eduGAIN API."""
        return {
            "https://aaf.edu.au": "AAF",
            "https://incommon.org": "InCommon",
            "https://maren.ac.mw": "MAREN",
            "https://ukfederation.org.uk": "UK federation"
        }

    @patch("privacy_security_analysis.requests.get")
    def test_get_federation_mapping_api_success(self, mock_get, mock_federation_response):
        """Test successful federation mapping from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_federation_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock file operations to simulate no cache
        with patch("os.path.exists", return_value=False):
            result = privacy_security_analysis.get_federation_mapping()

        assert result == mock_federation_response
        mock_get.assert_called_once_with(privacy_security_analysis.EDUGAIN_API_URL, timeout=10)

    @patch("privacy_security_analysis.requests.get")
    def test_get_federation_mapping_api_failure(self, mock_get):
        """Test federation mapping fallback when API fails."""
        mock_get.side_effect = requests.exceptions.RequestException("API error")

        # Mock file operations to simulate no cache
        with patch("os.path.exists", return_value=False):
            with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                result = privacy_security_analysis.get_federation_mapping()

        assert result == {}
        assert "Warning: Could not fetch federation names" in mock_stderr.getvalue()

    def test_get_federation_mapping_cache_valid(self, mock_federation_response):
        """Test federation mapping from valid cache."""
        cache_data = {
            "federations": mock_federation_response,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_version": "1.0"
        }

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open_read_json(cache_data)):
                result = privacy_security_analysis.get_federation_mapping()

        assert result == mock_federation_response

    def test_get_federation_mapping_cache_expired(self, mock_federation_response):
        """Test federation mapping when cache is expired."""
        # Cache from 31 days ago (expired)
        old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
        cache_data = {
            "federations": {"old": "data"},
            "cached_at": old_date,
            "cache_version": "1.0"
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_federation_response
        mock_response.raise_for_status.return_value = None

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open_read_json(cache_data)):
                with patch("privacy_security_analysis.requests.get", return_value=mock_response):
                    with patch("sys.stderr", new_callable=io.StringIO):
                        result = privacy_security_analysis.get_federation_mapping()

        assert result == mock_federation_response

    def test_map_registration_authority_with_mapping(self, mock_federation_response):
        """Test mapping registration authority to federation name."""
        result = privacy_security_analysis.map_registration_authority(
            "https://incommon.org", mock_federation_response
        )
        assert result == "InCommon"

    def test_map_registration_authority_no_mapping(self, mock_federation_response):
        """Test mapping when no federation name exists."""
        result = privacy_security_analysis.map_registration_authority(
            "https://unknown.org", mock_federation_response
        )
        assert result == "https://unknown.org"

    @patch("privacy_security_analysis.get_federation_mapping")
    def test_analyze_with_federation_mapping(self, mock_get_federation, entities_descriptor, xml_builder):
        """Test that analyze_privacy_security uses federation mapping."""
        mock_federation_mapping = {
            "https://maren.ac.mw": "MAREN",
            "https://incommon.org": "InCommon"
        }
        mock_get_federation.return_value = mock_federation_mapping

        entity1 = xml_builder(
            entity_id="https://sp1.example.org",
            reg_authority="https://maren.ac.mw",
            org_name="Test SP"
        )
        entity2 = xml_builder(
            entity_id="https://sp2.example.org",
            reg_authority="https://incommon.org",
            org_name="Another SP"
        )
        entities_descriptor.extend([entity1, entity2])

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        # Check that federation names are used instead of URLs
        assert len(entities_list) == 2
        entity1_data = next(e for e in entities_list if e[3] == "https://sp1.example.org")
        entity2_data = next(e for e in entities_list if e[3] == "https://sp2.example.org")

        assert entity1_data[0] == "MAREN"  # Should be mapped name, not URL
        assert entity2_data[0] == "InCommon"  # Should be mapped name, not URL

        # Check federation stats use mapped names
        assert "MAREN" in federation_stats
        assert "InCommon" in federation_stats
        assert "https://maren.ac.mw" not in federation_stats
        assert "https://incommon.org" not in federation_stats


class TestMetadataCaching:
    """Tests for metadata caching functionality."""

    def test_get_metadata_cache_valid(self):
        """Test getting metadata from valid cache."""
        cache_file = ".edugain_metadata_cache.xml"
        xml_content = b"<EntitiesDescriptor>cached content</EntitiesDescriptor>"

        # Mock cache file exists and is recent (1 hour old)
        recent_time = datetime.utcnow() - timedelta(hours=1)

        with patch("os.path.exists", return_value=True):
            with patch("os.path.getmtime", return_value=recent_time.timestamp()):
                with patch("builtins.open", mock_open_read_bytes(xml_content)):
                    with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                        result = privacy_security_analysis.get_metadata()

        assert result == xml_content
        assert "Using cached metadata" in mock_stderr.getvalue()

    def test_get_metadata_cache_expired(self):
        """Test getting metadata when cache is expired."""
        cache_file = ".edugain_metadata_cache.xml"
        new_xml_content = b"<EntitiesDescriptor>fresh content</EntitiesDescriptor>"

        # Mock cache file exists but is old (13 hours)
        old_time = datetime.utcnow() - timedelta(hours=13)

        mock_response = MagicMock()
        mock_response.content = new_xml_content
        mock_response.raise_for_status.return_value = None

        with patch("os.path.exists", return_value=True):
            with patch("os.path.getmtime", return_value=old_time.timestamp()):
                with patch("privacy_security_analysis.requests.get", return_value=mock_response):
                    with patch("builtins.open", mock_open_write_bytes()) as mock_open:
                        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                            result = privacy_security_analysis.get_metadata()

        assert result == new_xml_content
        assert "Cache expired, downloading fresh metadata" in mock_stderr.getvalue()

    def test_get_metadata_no_cache(self):
        """Test getting metadata when no cache exists."""
        xml_content = b"<EntitiesDescriptor>new content</EntitiesDescriptor>"

        mock_response = MagicMock()
        mock_response.content = xml_content
        mock_response.raise_for_status.return_value = None

        with patch("os.path.exists", return_value=False):
            with patch("privacy_security_analysis.requests.get", return_value=mock_response):
                with patch("builtins.open", mock_open_write_bytes()) as mock_open:
                    with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                        result = privacy_security_analysis.get_metadata()

        assert result == xml_content
        assert "Downloading metadata" in mock_stderr.getvalue()


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

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
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
        assert stats["total_sps"] == 1
        assert stats["total_idps"] == 0
        assert stats["sps_has_privacy"] == 1
        assert stats["sps_has_security"] == 1
        assert stats["total_has_security"] == 1
        assert stats["sps_has_both"] == 1
        assert stats["sps_missing_both"] == 0

    def test_entity_missing_privacy_statement(self, entities_descriptor, xml_builder):
        """Test entity missing privacy statement."""
        entity = xml_builder(has_privacy_statement=False, has_security_contact=True)
        entities_descriptor.append(entity)

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "No"  # has privacy
        assert entity_data[5] == ""  # privacy URL (empty)
        assert entity_data[6] == "Yes"  # has security

        assert stats["sps_missing_privacy"] == 1
        assert stats["sps_has_security"] == 1
        assert stats["total_has_security"] == 1

    def test_entity_missing_security_contact(self, entities_descriptor, xml_builder):
        """Test entity missing security contact."""
        entity = xml_builder(has_privacy_statement=True, has_security_contact=False)
        entities_descriptor.append(entity)

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "Yes"  # has privacy
        assert entity_data[6] == "No"  # has security

        assert stats["sps_has_privacy"] == 1
        assert stats["sps_missing_security"] == 1
        assert stats["total_missing_security"] == 1

    def test_entity_missing_both(self, entities_descriptor, xml_builder):
        """Test entity missing both privacy statement and security contact."""
        entity = xml_builder(has_privacy_statement=False, has_security_contact=False)
        entities_descriptor.append(entity)

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 1
        entity_data = entities_list[0]
        assert entity_data[4] == "No"  # has privacy
        assert entity_data[5] == ""  # privacy URL (empty)
        assert entity_data[6] == "No"  # has security

        assert stats["sps_missing_privacy"] == 1
        assert stats["sps_missing_security"] == 1
        assert stats["total_missing_security"] == 1
        assert stats["sps_missing_both"] == 1
        assert stats["sps_has_both"] == 0

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

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
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

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
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

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 4
        assert stats["total_entities"] == 4
        assert stats["total_sps"] == 4  # All entities are SPs in this test
        assert stats["sps_has_privacy"] == 2
        assert stats["sps_missing_privacy"] == 2
        assert stats["total_has_security"] == 2
        assert stats["total_missing_security"] == 2
        assert stats["sps_has_security"] == 2
        assert stats["sps_missing_security"] == 2
        assert stats["sps_has_both"] == 1
        assert stats["sps_missing_both"] == 1

    def test_idp_vs_sp_privacy_handling(self, entities_descriptor, xml_builder):
        """Test that privacy statements are only analyzed for SPs, not IdPs."""
        # Create an IdP with a privacy statement element (should be ignored)
        idp_entity = xml_builder(
            entity_id="https://idp.example.org",
            entity_type="IdP",
            has_privacy_statement=True,  # This should be ignored for IdPs
            has_security_contact=True,
        )

        # Create an SP with a privacy statement
        sp_entity = xml_builder(
            entity_id="https://sp.example.org",
            entity_type="SP",
            has_privacy_statement=True,
            has_security_contact=True,
        )

        entities_descriptor.extend([idp_entity, sp_entity])

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 2
        assert stats["total_entities"] == 2
        assert stats["total_sps"] == 1
        assert stats["total_idps"] == 1

        # Privacy statistics should only count the SP
        assert stats["sps_has_privacy"] == 1
        assert stats["sps_missing_privacy"] == 0

        # Security statistics should count both
        assert stats["total_has_security"] == 2
        assert stats["sps_has_security"] == 1
        assert stats["idps_has_security"] == 1

        # Verify entity data
        idp_data = next(e for e in entities_list if e[1] == "IdP")
        sp_data = next(e for e in entities_list if e[1] == "SP")

        # IdP should show "No" for privacy (not analyzed)
        assert idp_data[4] == "No"  # HasPrivacyStatement
        assert idp_data[5] == ""  # PrivacyStatementURL
        assert idp_data[6] == "Yes"  # HasSecurityContact

        # SP should show "Yes" for privacy
        assert sp_data[4] == "Yes"  # HasPrivacyStatement
        assert sp_data[5] != ""  # PrivacyStatementURL
        assert sp_data[6] == "Yes"  # HasSecurityContact

    def test_security_contact_split_statistics(self, entities_descriptor, xml_builder):
        """Test security contact statistics are properly split between SPs and IdPs."""
        # Create 2 SPs: 1 with, 1 without security contact
        sp1 = xml_builder(
            entity_id="https://sp1.example.org",
            entity_type="SP",
            has_security_contact=True,
        )
        sp2 = xml_builder(
            entity_id="https://sp2.example.org",
            entity_type="SP",
            has_security_contact=False,
        )

        # Create 3 IdPs: 1 with, 2 without security contact
        idp1 = xml_builder(
            entity_id="https://idp1.example.org",
            entity_type="IdP",
            has_security_contact=True,
        )
        idp2 = xml_builder(
            entity_id="https://idp2.example.org",
            entity_type="IdP",
            has_security_contact=False,
        )
        idp3 = xml_builder(
            entity_id="https://idp3.example.org",
            entity_type="IdP",
            has_security_contact=False,
        )

        entities_descriptor.extend([sp1, sp2, idp1, idp2, idp3])

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 5
        assert stats["total_entities"] == 5
        assert stats["total_sps"] == 2
        assert stats["total_idps"] == 3

        # Overall security statistics
        assert stats["total_has_security"] == 2  # sp1 + idp1
        assert stats["total_missing_security"] == 3  # sp2 + idp2 + idp3

        # SP security statistics
        assert stats["sps_has_security"] == 1  # sp1
        assert stats["sps_missing_security"] == 1  # sp2

        # IdP security statistics
        assert stats["idps_has_security"] == 1  # idp1
        assert stats["idps_missing_security"] == 2  # idp2 + idp3

    def test_federation_statistics_tracking(self, entities_descriptor, xml_builder):
        """Test that federation-level statistics are tracked correctly."""
        # Create entities for two different federations
        fed1_sp = xml_builder(
            entity_id="https://fed1-sp.example.org",
            entity_type="SP",
            has_privacy_statement=True,
            has_security_contact=True,
            reg_authority="https://federation1.org",
        )
        fed1_idp = xml_builder(
            entity_id="https://fed1-idp.example.org",
            entity_type="IdP",
            has_security_contact=False,
            reg_authority="https://federation1.org",
        )
        fed2_sp = xml_builder(
            entity_id="https://fed2-sp.example.org",
            entity_type="SP",
            has_privacy_statement=False,
            has_security_contact=True,
            reg_authority="https://federation2.org",
        )

        entities_descriptor.extend([fed1_sp, fed1_idp, fed2_sp])

        entities_list, stats, federation_stats = privacy_security_analysis.analyze_privacy_security(
            entities_descriptor
        )

        assert len(entities_list) == 3
        assert len(federation_stats) == 2

        # Check federation 1 stats
        fed1_stats = federation_stats["https://federation1.org"]
        assert fed1_stats["total_entities"] == 2
        assert fed1_stats["total_sps"] == 1
        assert fed1_stats["total_idps"] == 1
        assert fed1_stats["sps_has_privacy"] == 1
        assert fed1_stats["sps_has_security"] == 1
        assert fed1_stats["idps_missing_security"] == 1
        assert fed1_stats["sps_has_both"] == 1

        # Check federation 2 stats
        fed2_stats = federation_stats["https://federation2.org"]
        assert fed2_stats["total_entities"] == 1
        assert fed2_stats["total_sps"] == 1
        assert fed2_stats["total_idps"] == 0
        assert fed2_stats["sps_missing_privacy"] == 1
        assert fed2_stats["sps_has_security"] == 1
        assert fed2_stats["sps_missing_both"] == 0  # Has security contact


class TestPrintFederationSummary:
    """Tests for the print_federation_summary function."""

    def test_print_federation_summary_with_data(self):
        """Test federation summary printing with sample data."""
        federation_stats = {
            "https://federation1.org": {
                "total_entities": 100,
                "total_sps": 60,
                "total_idps": 40,
                "sps_has_privacy": 50,
                "sps_has_security": 45,
                "idps_has_security": 20,
                "total_has_security": 65,
                "sps_has_both": 40,
            },
            "https://federation2.org": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_has_security": 20,
                "idps_has_security": 15,
                "total_has_security": 35,
                "sps_has_both": 18,
            },
        }

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.print_federation_summary(federation_stats)

        output = mock_stderr.getvalue()
        assert "## 🌍 Federation-Level Summary" in output
        assert "### 📍 **federation1.org**" in output
        assert "- **Total Entities:** 100 (60 SPs, 40 IdPs)" in output
        assert "- **SP Privacy Coverage:** 🟢 50/60 (83.3%)" in output
        assert "- **Security Contact Coverage:** 🟡 65/100 (65.0%)" in output
        assert "SPs: 45/60 (75.0%), IdPs: 20/40 (50.0%)" in output
        assert "- **SP Full Compliance:** 🟡 40/60 (66.7%)" in output

    def test_print_federation_summary_empty(self):
        """Test federation summary printing with no data."""
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.print_federation_summary({})

        output = mock_stderr.getvalue()
        assert "No federation data available." in output


class TestFederationCSVExport:
    """Tests for the export_federation_csv function."""

    def test_export_federation_csv_with_headers(self):
        """Test CSV export with headers."""
        federation_stats = {
            "https://federation1.org": {
                "total_entities": 100,
                "total_sps": 60,
                "total_idps": 40,
                "sps_has_privacy": 50,
                "sps_has_security": 45,
                "idps_has_security": 20,
                "total_has_security": 65,
                "sps_has_both": 40,
            },
            "https://federation2.org": {
                "total_entities": 30,
                "total_sps": 20,
                "total_idps": 10,
                "sps_has_privacy": 15,
                "sps_has_security": 12,
                "idps_has_security": 8,
                "total_has_security": 20,
                "sps_has_both": 10,
            },
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            privacy_security_analysis.export_federation_csv(federation_stats, True)

        output = mock_stdout.getvalue()
        lines = output.strip().split('\n')

        # Check header
        assert "RegistrationAuthority,TotalEntities,TotalSPs,TotalIdPs" in lines[0]
        assert "SPsWithPrivacy,SPsMissingPrivacy" in lines[0]
        assert "SPsWithBoth,SPsWithAtLeastOne,SPsMissingBoth" in lines[0]
        # Should not contain percentage columns
        assert "Percent" not in lines[0]

        # Check first federation (sorted by total entities desc)
        assert lines[1].startswith("https://federation1.org,100,60,40")
        assert "50,10" in lines[1]  # Privacy: 50 with, 10 missing
        assert "40,55,5" in lines[1]  # Both, at least one, missing both

        # Check second federation
        assert lines[2].startswith("https://federation2.org,30,20,10")
        assert "15,5" in lines[2]  # Privacy: 15 with, 5 missing

    def test_export_federation_csv_without_headers(self):
        """Test CSV export without headers."""
        federation_stats = {
            "https://test.org": {
                "total_entities": 50,
                "total_sps": 30,
                "total_idps": 20,
                "sps_has_privacy": 25,
                "sps_has_security": 20,
                "idps_has_security": 15,
                "total_has_security": 35,
                "sps_has_both": 18,
            }
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            privacy_security_analysis.export_federation_csv(federation_stats, False)

        output = mock_stdout.getvalue()
        lines = output.strip().split('\n')

        # Should have only 1 line (no header)
        assert len(lines) == 1
        assert lines[0].startswith("https://test.org,50,30,20")

    def test_export_federation_csv_zero_sps(self):
        """Test CSV export with federation having no SPs."""
        federation_stats = {
            "https://idp-only.org": {
                "total_entities": 20,
                "total_sps": 0,
                "total_idps": 20,
                "sps_has_privacy": 0,
                "sps_has_security": 0,
                "idps_has_security": 15,
                "total_has_security": 15,
                "sps_has_both": 0,
            }
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            privacy_security_analysis.export_federation_csv(federation_stats, True)

        output = mock_stdout.getvalue()
        lines = output.strip().split('\n')

        # Check that SP counts are 0 when no SPs exist
        assert "0,0" in lines[1]  # Privacy stats should be 0,0
        assert "0,0,0" in lines[1]  # SP both, at least one, missing both should be 0,0,0

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.export_federation_csv")
    def test_main_federation_csv(
        self, mock_export_csv, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with federation-csv option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        federation_stats = {"https://test.org": {"total_entities": 10}}
        mock_analyze.return_value = ([], {"total_entities": 10}, federation_stats)

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=False,
                federation_summary=False,
                federation_csv=True,
                missing_privacy=False,
                missing_security=False,
                missing_both=False,
            )
            privacy_security_analysis.main()

        # Should call export_federation_csv with correct parameters
        mock_export_csv.assert_called_once_with(federation_stats, True)

        # Should not call print_summary when federation_csv is True
        # (This is implied by the early return in main())


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
            "total_sps": 60,
            "total_idps": 40,
            "sps_has_privacy": 36,
            "sps_missing_privacy": 24,
            "total_has_security": 70,
            "total_missing_security": 30,
            "sps_has_security": 42,
            "sps_missing_security": 18,
            "idps_has_security": 28,
            "idps_missing_security": 12,
            "sps_has_both": 30,
            "sps_missing_both": 6,
        }

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            privacy_security_analysis.print_summary(stats)

        output = mock_stderr.getvalue()
        assert "Total entities analyzed: 100 (SPs: 60, IdPs: 40)" in output
        assert "Privacy Statement URL Coverage (SPs only):" in output
        assert "SPs with privacy statements: 36 out of 60 (60.0%)" in output
        assert "SPs missing privacy statements: 24 out of 60 (40.0%)" in output
        assert "Security Contact Coverage:" in output
        assert "Total entities with security contacts: 70 out of 100 (70.0%)" in output
        assert (
            "Total entities missing security contacts: 30 out of 100 (30.0%)" in output
        )
        assert "SPs: 42 with / 18 without (70.0% coverage)" in output
        assert "IdPs: 28 with / 12 without (70.0% coverage)" in output
        assert "Combined Coverage Summary (SPs only):" in output
        assert "SPs with BOTH (fully compliant): 30 out of 60 (50.0%)" in output
        assert "SPs with AT LEAST ONE: 54 out of 60 (90.0%)" in output
        assert "SPs missing both: 6 out of 60 (10.0%)" in output
        assert "Key Insights:" in output

    def test_print_summary_no_entities(self):
        """Test summary printing with no entities."""
        stats = {
            "total_entities": 0,
            "total_sps": 0,
            "total_idps": 0,
        }

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
            {
                "total_entities": 1,
                "total_sps": 1,
                "total_idps": 0,
                "sps_has_privacy": 1,
                "total_has_security": 1,
            },
            {},  # federation_stats
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
                federation_summary=False,
                federation_csv=False,
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
        mock_analyze.return_value = ([], {"total_entities": 0}, {})

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file="test.xml",
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=False,
                federation_summary=False,
                federation_csv=False,
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
        mock_analyze.return_value = ([], {"total_entities": 0}, {})

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=False,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                summary_only=True,
                federation_summary=False,
                federation_csv=False,
                missing_privacy=False,
                missing_security=False,
                missing_both=False,
            )
            privacy_security_analysis.main()

        mock_print_summary.assert_called_once()

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.filter_entities")
    @patch("privacy_security_analysis.print_entities_csv")
    def test_main_list_missing_both(
        self, mock_print_csv, mock_filter, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with --list-missing-both option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        entities_list = [["https://example.org", "SP", "Org", "entity", "No", "", "No"]]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=True,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                list_missing_both=True,
                list_missing_privacy=False,
                list_missing_security=False,
                list_all_entities=False,
                summary_only=False,
                federation_summary=False,
                federation_csv=False,
            )
            privacy_security_analysis.main()

        mock_filter.assert_called_once_with(entities_list, "missing_both")
        mock_print_csv.assert_called_once()

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.filter_entities")
    @patch("privacy_security_analysis.print_entities_csv")
    def test_main_list_missing_privacy(
        self, mock_print_csv, mock_filter, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with --list-missing-privacy option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        entities_list = [["https://example.org", "SP", "Org", "entity", "No", "", "Yes"]]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=True,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                list_missing_both=False,
                list_missing_privacy=True,
                list_missing_security=False,
                list_all_entities=False,
                summary_only=False,
                federation_summary=False,
                federation_csv=False,
            )
            privacy_security_analysis.main()

        mock_filter.assert_called_once_with(entities_list, "missing_privacy")
        mock_print_csv.assert_called_once()

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.filter_entities")
    @patch("privacy_security_analysis.print_entities_csv")
    def test_main_list_missing_security(
        self, mock_print_csv, mock_filter, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with --list-missing-security option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        entities_list = [["https://example.org", "SP", "Org", "entity", "Yes", "url", "No"]]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})
        mock_filter.return_value = entities_list

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=True,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                list_missing_both=False,
                list_missing_privacy=False,
                list_missing_security=True,
                list_all_entities=False,
                summary_only=False,
                federation_summary=False,
                federation_csv=False,
            )
            privacy_security_analysis.main()

        mock_filter.assert_called_once_with(entities_list, "missing_security")
        mock_print_csv.assert_called_once()

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.print_entities_csv")
    def test_main_list_all_entities(
        self, mock_print_csv, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with --list-all-entities option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        entities_list = [["https://example.org", "SP", "Org", "entity", "Yes", "url", "Yes"]]
        mock_analyze.return_value = (entities_list, {"total_entities": 1}, {})

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=True,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                list_missing_both=False,
                list_missing_privacy=False,
                list_missing_security=False,
                list_all_entities=True,
                summary_only=False,
                federation_summary=False,
                federation_csv=False,
            )
            privacy_security_analysis.main()

        # Should call print_entities_csv without filtering
        mock_print_csv.assert_called_once_with(entities_list, True)

    @patch("privacy_security_analysis.download_metadata")
    @patch("privacy_security_analysis.parse_metadata")
    @patch("privacy_security_analysis.analyze_privacy_security")
    @patch("privacy_security_analysis.print_federation_summary")
    def test_main_federation_summary(
        self, mock_print_federation, mock_analyze, mock_parse, mock_download
    ):
        """Test main function with --federation-summary option."""
        mock_download.return_value = b"<xml>content</xml>"
        mock_parse.return_value = MagicMock()
        federation_stats = {"MAREN": {"total_entities": 10}}
        mock_analyze.return_value = ([], {"total_entities": 10}, federation_stats)

        with patch.object(
            privacy_security_analysis.argparse.ArgumentParser, "parse_args"
        ) as mock_parse_args:
            mock_parse_args.return_value = argparse.Namespace(
                local_file=None,
                no_headers=True,
                url=privacy_security_analysis.EDUGAIN_METADATA_URL,
                list_missing_both=False,
                list_missing_privacy=False,
                list_missing_security=False,
                list_all_entities=False,
                summary_only=False,
                federation_summary=True,
                federation_csv=False,
            )
            privacy_security_analysis.main()

        # import sys is already available from the top of the file
        import sys
        mock_print_federation.assert_called_once_with(federation_stats, output_file=sys.stdout)


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
