"""Tests for core.entities module."""

import os
import sys
import xml.etree.ElementTree as ET

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.core.entities import EntityRecord, iter_entity_records


class TestIterEntityRecords:
    """Tests for iter_entity_records."""

    def test_iter_entity_records_basic(self):
        """SP with privacy, security, and SIRTFI attributes."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                               xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
                               xmlns:remd="http://refeds.org/metadata"
                               xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                               xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
                               xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <md:EntityDescriptor entityID="https://example.org/sp">
                <md:Extensions>
                    <mdrpi:RegistrationInfo registrationAuthority="https://incommon.org"/>
                    <mdattr:EntityAttributes>
                        <saml:Attribute Name="urn:oasis:names:tc:SAML:attribute:assurance-certification">
                            <saml:AttributeValue>https://refeds.org/sirtfi</saml:AttributeValue>
                        </saml:Attribute>
                    </mdattr:EntityAttributes>
                </md:Extensions>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:Extensions>
                        <mdui:UIInfo>
                            <mdui:PrivacyStatementURL xml:lang="en">https://example.org/privacy</mdui:PrivacyStatementURL>
                        </mdui:UIInfo>
                    </md:Extensions>
                </md:SPSSODescriptor>
                <md:ContactPerson remd:contactType="http://refeds.org/metadata/contactType/security">
                    <md:EmailAddress>security@example.org</md:EmailAddress>
                </md:ContactPerson>
                <md:Organization>
                    <md:OrganizationDisplayName xml:lang="en">Example SP</md:OrganizationDisplayName>
                </md:Organization>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        records = list(
            iter_entity_records(root, {"https://incommon.org": "InCommon Federation"})
        )

        assert len(records) == 1
        record = records[0]
        assert isinstance(record, EntityRecord)
        assert record.entity_id == "https://example.org/sp"
        assert record.entity_type == "SP"
        assert record.roles == ("SP",)
        assert record.is_sp is True
        assert record.is_idp is False
        assert record.org_name == "Example SP"
        assert record.registration_authority == "https://incommon.org"
        assert record.federation_name == "InCommon Federation"
        assert record.has_privacy is True
        assert record.privacy_url == "https://example.org/privacy"
        assert record.has_security is True
        assert record.has_sirtfi is True

    def test_iter_entity_records_nested_entities(self):
        """Ensure nested EntityDescriptor elements are discovered."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntitiesDescriptor>
                <md:EntityDescriptor entityID="https://nested.example.org/idp">
                    <md:Extensions>
                        <mdrpi:RegistrationInfo xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
                                                registrationAuthority="https://nested.org"/>
                    </md:Extensions>
                    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                </md:EntityDescriptor>
            </md:EntitiesDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        records = list(iter_entity_records(root))

        assert len(records) == 1
        record = records[0]
        assert record.entity_id == "https://nested.example.org/idp"
        assert record.entity_type == "IdP"
        assert record.roles == ("IdP",)
        assert record.is_sp is False
        assert record.is_idp is True
        assert record.registration_authority == "https://nested.org"

    def test_iter_entity_records_skips_missing_entity_id(self):
        """Entities without entityID should be skipped."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor>
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        records = list(iter_entity_records(root))

        assert records == []

    def test_iter_entity_records_sp_and_idp(self):
        """Entities acting as both SP and IdP should expose both roles."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <md:EntitiesDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata">
            <md:EntityDescriptor entityID="https://dual.example.org/metadata">
                <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol"/>
            </md:EntityDescriptor>
        </md:EntitiesDescriptor>"""

        root = ET.fromstring(xml_content)
        records = list(iter_entity_records(root))

        assert len(records) == 1
        record = records[0]
        assert record.entity_id == "https://dual.example.org/metadata"
        assert record.roles == ("SP", "IdP")
        assert record.entity_type == "SP+IdP"
        assert record.is_sp is True
        assert record.is_idp is True
