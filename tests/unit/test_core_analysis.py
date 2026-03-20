"""Tests for core analysis functionality."""

import os
import sys
import xml.etree.ElementTree as ET
from unittest.mock import patch

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.core.analysis import analyze_privacy_security, filter_entities


class TestAnalyzePrivacySecurity:
    """Test the analyze_privacy_security function."""

    def test_empty_metadata(self):
        """Test analysis with empty metadata."""
        # Create minimal XML root
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert entities_list == []
        assert stats["total_entities"] == 0
        assert stats["total_sps"] == 0
        assert stats["total_idps"] == 0
        assert federation_stats == {}

    def test_single_sp_with_privacy(self):
        """Test analysis of single SP with privacy statement."""
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
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example Organization</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert len(entities_list) == 1
        assert stats["total_entities"] == 1
        assert stats["total_sps"] == 1
        assert stats["sps_has_privacy"] == 1
        assert stats["sps_missing_privacy"] == 0
        assert stats["sps_missing_security"] == 1  # No security contact

        # Check entity data
        entity = entities_list[0]
        assert entity[0] == "https://example.org"  # Federation name
        assert entity[1] == "SP"  # Entity type
        assert entity[2] == "Example Organization"  # Org name
        assert entity[3] == "https://example.org/sp"  # Entity ID
        assert entity[4] == "Yes"  # Has privacy
        assert entity[5] == "https://example.org/privacy"  # Privacy URL
        assert entity[6] == "No"  # Has security

    def test_single_idp_with_security_contact(self):
        """Test analysis of single IdP with security contact."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:remd="http://refeds.org/metadata"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/idp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example IdP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert len(entities_list) == 1
        assert stats["total_entities"] == 1
        assert stats["total_idps"] == 1
        assert stats["idps_has_security"] == 1
        assert stats["idps_missing_security"] == 0
        assert stats["total_has_security"] == 1

        # Check entity data
        entity = entities_list[0]
        assert entity[1] == "IdP"  # Entity type
        assert entity[6] == "Yes"  # Has security

    def test_sp_with_both_privacy_and_security(self):
        """Test SP with both privacy statement and security contact."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:remd="http://refeds.org/metadata"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert stats["sps_has_both"] == 1
        assert stats["sps_missing_both"] == 0
        assert stats["sps_has_privacy"] == 1
        assert stats["sps_has_security"] == 1

    def test_federation_statistics(self):
        """Test federation-level statistics are calculated correctly."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp1">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://fed1.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">SP 1</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <md:EntityDescriptor entityID="https://example.org/sp2">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://fed1.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">SP 2</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert "https://fed1.org" in federation_stats
        fed_stats = federation_stats["https://fed1.org"]
        assert fed_stats["total_entities"] == 2
        assert fed_stats["total_sps"] == 2
        assert fed_stats["total_idps"] == 0

    def test_with_federation_mapping(self):
        """Test analysis with federation name mapping."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Test SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        federation_mapping = {"https://incommon.org": "InCommon"}

        entities_list, stats, federation_stats = analyze_privacy_security(
            root, federation_mapping=federation_mapping
        )

        # Check that federation name is used instead of URL
        entity = entities_list[0]
        assert entity[0] == "InCommon"  # Federation name mapped

        # Check federation stats use the mapped name
        assert "InCommon" in federation_stats
        assert "https://incommon.org" not in federation_stats

    @patch("edugain_analysis.core.analysis.validate_urls_parallel")
    def test_with_url_validation(self, mock_validate):
        """Test analysis with URL validation enabled."""
        # Mock validation results
        mock_validate.return_value = {
            "https://example.org/privacy": {
                "accessible": True,
                "status_code": 200,
                "final_url": "https://example.org/privacy",
                "redirect_count": 0,
                "error": None,
            }
        }

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
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(
            root, validate_urls=True
        )

        # Check validation statistics
        assert stats["validation_enabled"] is True
        assert stats["urls_checked"] == 1
        assert stats["urls_accessible"] == 1
        assert stats["urls_broken"] == 0

        # Check extended entity data format (now includes HasSIRTFI column)
        entity = entities_list[0]
        assert len(entity) == 13  # Extended format with validation data + SIRTFI
        assert entity[7] == "No"  # HasSIRTFI
        assert entity[8] == "200"  # Status code
        assert entity[10] == "Yes"  # URL accessible

    def test_entity_without_entityid(self):
        """Test handling of entity without entityID attribute."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        # Entity should be counted but not included in output
        assert stats["total_entities"] == 1
        assert len(entities_list) == 0  # No entityID, so not included


class TestFilterEntities:
    """Test the filter_entities function."""

    def setup_method(self):
        """Set up test entities list."""
        self.entities = [
            ["Fed1", "SP", "Org1", "entity1", "Yes", "https://url1", "Yes"],  # Has both
            ["Fed1", "SP", "Org2", "entity2", "No", "", "Yes"],  # Missing privacy
            [
                "Fed1",
                "SP",
                "Org3",
                "entity3",
                "Yes",
                "https://url3",
                "No",
            ],  # Missing security
            ["Fed1", "SP", "Org4", "entity4", "No", "", "No"],  # Missing both
            ["Fed1", "IdP", "Org5", "entity5", "No", "", "Yes"],  # IdP with security
        ]

    def test_filter_missing_privacy(self):
        """Test filtering entities missing privacy statements."""
        result = filter_entities(self.entities, "missing_privacy")

        assert len(result) == 3  # Entities 2, 4, and 5 (IdP also has "No" for privacy)
        entity_ids = [entity[3] for entity in result]
        assert "entity2" in entity_ids
        assert "entity4" in entity_ids
        assert "entity5" in entity_ids  # IdP also filtered as expected

    def test_filter_missing_security(self):
        """Test filtering entities missing security contacts."""
        result = filter_entities(self.entities, "missing_security")

        assert len(result) == 2  # Entities 3 and 4
        assert result[0][3] == "entity3"
        assert result[1][3] == "entity4"

    def test_filter_missing_both(self):
        """Test filtering entities missing both privacy and security."""
        result = filter_entities(self.entities, "missing_both")

        assert len(result) == 1  # Only entity 4
        assert result[0][3] == "entity4"

    def test_filter_no_filter(self):
        """Test with no filter applied."""
        result = filter_entities(self.entities, "none")

        assert len(result) == 5  # All entities
        assert result == self.entities

    def test_filter_empty_list(self):
        """Test filtering empty entities list."""
        result = filter_entities([], "missing_privacy")

        assert result == []


class TestIdPPrivacyStatements:
    """Test IdP privacy statement tracking functionality."""

    def test_single_idp_with_privacy(self):
        """Test analysis of single IdP with privacy statement."""
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
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/idp-privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example IdP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert len(entities_list) == 1
        assert stats["total_entities"] == 1
        assert stats["total_idps"] == 1
        assert stats["idps_has_privacy"] == 1
        assert stats["idps_missing_privacy"] == 0

        # Check entity data
        entity = entities_list[0]
        assert entity[1] == "IdP"  # Entity type
        assert entity[4] == "Yes"  # Has privacy (not "N/A")
        assert entity[5] == "https://example.org/idp-privacy"  # Privacy URL

    def test_idp_privacy_statistics(self):
        """Test IdP privacy statistics counts."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <!-- IdP with privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp1">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy1</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 1</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <!-- IdP without privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp2">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 2</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <!-- Another IdP with privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp3">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy3</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 3</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert stats["total_idps"] == 3
        assert stats["idps_has_privacy"] == 2
        assert stats["idps_missing_privacy"] == 1

    def test_mixed_entities_privacy(self):
        """Test mix of SPs and IdPs with and without privacy."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <!-- SP with privacy -->
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/sp-privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">SP 1</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <!-- IdP with privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/idp-privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 1</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert stats["total_sps"] == 1
        assert stats["total_idps"] == 1
        assert stats["sps_has_privacy"] == 1
        assert stats["idps_has_privacy"] == 1
        assert stats["sps_missing_privacy"] == 0
        assert stats["idps_missing_privacy"] == 0

        # Verify both entities show "Yes" for privacy
        sp_entity = [e for e in entities_list if e[1] == "SP"][0]
        idp_entity = [e for e in entities_list if e[1] == "IdP"][0]

        assert sp_entity[4] == "Yes"  # SP has privacy
        assert idp_entity[4] == "Yes"  # IdP has privacy

    def test_idp_privacy_in_federation_stats(self):
        """Test federation-level IdP privacy tracking."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <md:EntityDescriptor entityID="https://example.org/idp1">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://fed1.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 1</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <md:EntityDescriptor entityID="https://example.org/idp2">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://fed1.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP 2</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        assert "https://fed1.org" in federation_stats
        fed_stats = federation_stats["https://fed1.org"]
        assert fed_stats["total_idps"] == 2
        assert fed_stats["idps_has_privacy"] == 1
        assert fed_stats["idps_missing_privacy"] == 1

    @patch("edugain_analysis.core.analysis.validate_urls_parallel")
    def test_idp_privacy_url_validation_collection(self, mock_validate):
        """Test IdP privacy URLs are collected for validation."""
        mock_validate.return_value = {
            "https://example.org/idp-privacy": {
                "accessible": True,
                "status_code": 200,
                "final_url": "https://example.org/idp-privacy",
                "redirect_count": 0,
                "error": None,
            }
        }

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
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/idp-privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example IdP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(
            root, validate_urls=True
        )

        # Verify validation was called with IdP privacy URL
        mock_validate.assert_called_once()
        args, _ = mock_validate.call_args
        urls = args[0]
        assert "https://example.org/idp-privacy" in urls

        # Verify validation stats
        assert stats["urls_checked"] == 1
        assert stats["urls_accessible"] == 1

    def test_idp_privacy_display_not_na(self):
        """Verify IdPs show Yes/No for privacy, not N/A."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                              xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                              xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi">
            <!-- IdP with privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp1">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:IDPSSODescriptor>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP With Privacy</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
            <!-- IdP without privacy -->
            <md:EntityDescriptor entityID="https://example.org/idp2">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://example.org"/>
                </md:Extensions>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">IdP Without Privacy</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""
        root = ET.fromstring(xml_content)

        entities_list, stats, federation_stats = analyze_privacy_security(root)

        # Find both IdPs
        idp_with_privacy = [e for e in entities_list if "With Privacy" in e[2]][0]
        idp_without_privacy = [e for e in entities_list if "Without Privacy" in e[2]][0]

        # Both should show Yes/No, not N/A
        assert idp_with_privacy[4] == "Yes"
        assert idp_without_privacy[4] == "No"
        assert idp_with_privacy[4] != "N/A"
        assert idp_without_privacy[4] != "N/A"
