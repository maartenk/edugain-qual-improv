"""
Shared entity extraction utilities for eduGAIN metadata.

Provides a single source of truth for parsing entity metadata so that
all CLI entry points operate on consistent data.
"""

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass

from ..config import NAMESPACES
from .metadata import map_registration_authority

SIRTFI_VALUE = "https://refeds.org/sirtfi"


@dataclass(frozen=True)
class EntityRecord:
    """Normalized view of a single EntityDescriptor."""

    entity_id: str
    roles: tuple[str, ...]
    org_name: str
    registration_authority: str
    federation_name: str
    has_privacy: bool
    privacy_url: str
    has_security: bool
    has_sirtfi: bool

    @property
    def entity_type(self) -> str:
        """Return a display label for the entity roles."""
        if not self.roles:
            return "Unknown"
        if len(self.roles) == 1:
            return self.roles[0]
        return "+".join(self.roles)

    @property
    def is_sp(self) -> bool:
        """True if the entity functions as an SP."""
        return "SP" in self.roles

    @property
    def is_idp(self) -> bool:
        """True if the entity functions as an IdP."""
        return "IdP" in self.roles


def iter_entity_records(
    root: ET.Element, federation_mapping: dict[str, str] | None = None
) -> Iterable[EntityRecord]:
    """
    Yield normalized entity records from the provided metadata root.
    """
    federation_mapping = federation_mapping or {}

    privacy_xpath = ".//mdui:PrivacyStatementURL"
    sec_contact_refeds = './md:ContactPerson[@remd:contactType="http://refeds.org/metadata/contactType/security"]'
    sec_contact_incommon = './md:ContactPerson[@icmd:contactType="http://id.incommon.org/metadata/contactType/security"]'
    sirtfi_xpath = './md:Extensions/mdattr:EntityAttributes/saml:Attribute[@Name="urn:oasis:names:tc:SAML:attribute:assurance-certification"]/saml:AttributeValue'
    reg_info_xpath = "./md:Extensions/mdrpi:RegistrationInfo"
    org_name_xpath = "./md:Organization/md:OrganizationDisplayName"
    sp_descriptor_xpath = "./md:SPSSODescriptor"
    idp_descriptor_xpath = "./md:IDPSSODescriptor"

    for entity in root.findall(".//md:EntityDescriptor", NAMESPACES):
        entity_id = entity.attrib.get("entityID", "").strip()
        if not entity_id:
            continue

        orgname_elem = entity.find(org_name_xpath, NAMESPACES)
        org_name = (
            orgname_elem.text.strip()
            if orgname_elem is not None and orgname_elem.text
            else "Unknown"
        )

        is_sp = entity.find(sp_descriptor_xpath, NAMESPACES) is not None
        is_idp = entity.find(idp_descriptor_xpath, NAMESPACES) is not None

        roles: list[str] = []
        if is_sp:
            roles.append("SP")
        if is_idp:
            roles.append("IdP")

        privacy_elem = entity.find(privacy_xpath, NAMESPACES)
        has_privacy = bool(privacy_elem is not None and privacy_elem.text)
        privacy_url = privacy_elem.text.strip() if has_privacy else ""

        sec_contact_refeds_elem = entity.find(sec_contact_refeds, NAMESPACES)
        sec_contact_incommon_elem = entity.find(sec_contact_incommon, NAMESPACES)
        has_security = (sec_contact_refeds_elem is not None) or (
            sec_contact_incommon_elem is not None
        )

        has_sirtfi = any(
            ec.text == SIRTFI_VALUE
            for ec in entity.findall(sirtfi_xpath, NAMESPACES)
            if ec.text
        )

        registration_info = entity.find(reg_info_xpath, NAMESPACES)
        registration_authority = ""
        if registration_info is not None:
            registration_authority = registration_info.attrib.get(
                "registrationAuthority", ""
            ).strip()

        federation_name = map_registration_authority(
            registration_authority, federation_mapping
        )

        yield EntityRecord(
            entity_id=entity_id,
            roles=tuple(roles),
            org_name=org_name,
            registration_authority=registration_authority,
            federation_name=federation_name,
            has_privacy=has_privacy,
            privacy_url=privacy_url,
            has_security=has_security,
            has_sirtfi=has_sirtfi,
        )
