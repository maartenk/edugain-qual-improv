"""
Core analysis module for eduGAIN privacy and security assessment.

Provides the main analysis logic for processing eduGAIN metadata to identify
entities with privacy statements and security contacts.
"""

import sys
import xml.etree.ElementTree as ET

from ..config import NAMESPACES, URL_VALIDATION_THREADS
from .metadata import map_registration_authority
from .validation import validate_urls_parallel


def analyze_privacy_security(
    root: ET.Element,
    federation_mapping: dict[str, str] = None,
    validate_urls: bool = False,
    validation_cache: dict[str, dict] = None,
    max_workers: int = URL_VALIDATION_THREADS,
) -> tuple[list[list[str]], dict, dict]:
    """
    Analyze entities for privacy statement URLs and security contacts.
    Privacy statements are only analyzed for SPs (not IdPs).
    Security contacts are analyzed for both IdPs and SPs.

    Args:
        root: XML root element of eduGAIN metadata
        federation_mapping: Mapping of registration authorities to federation names
        validate_urls: Whether to perform URL validation (HTTP status + content check)
        validation_cache: Cache of previous URL validation results
        max_workers: Maximum number of threads for parallel URL validation

    Returns:
        Tuple of (entity_data_list, summary_stats, federation_stats)
    """
    entities_list = []
    stats = {
        "total_entities": 0,
        "total_sps": 0,
        "total_idps": 0,
        "sps_has_privacy": 0,
        "sps_missing_privacy": 0,
        "idps_has_security": 0,
        "sps_has_security": 0,
        "idps_missing_security": 0,
        "sps_missing_security": 0,
        "total_has_security": 0,
        "total_missing_security": 0,
        "sps_has_both": 0,
        "sps_missing_both": 0,
        # URL validation statistics
        "urls_checked": 0,
        "urls_accessible": 0,
        "urls_broken": 0,
        "validation_enabled": validate_urls,
    }

    # Federation-level statistics by registration authority
    federation_stats = {}

    entities = root.findall("./md:EntityDescriptor", NAMESPACES)

    # Pre-compile XPath expressions for performance
    privacy_xpath = ".//mdui:PrivacyStatementURL"
    sec_contact_refeds = './md:ContactPerson[@remd:contactType="http://refeds.org/metadata/contactType/security"]'
    sec_contact_incommon = './md:ContactPerson[@icmd:contactType="http://id.incommon.org/metadata/contactType/security"]'
    reg_info_xpath = "./md:Extensions/mdrpi:RegistrationInfo"
    org_name_xpath = "./md:Organization/md:OrganizationDisplayName"
    sp_descriptor_xpath = "./md:SPSSODescriptor"
    idp_descriptor_xpath = "./md:IDPSSODescriptor"

    # Collect all privacy URLs for parallel validation
    if validate_urls:
        print("Collecting privacy statement URLs for validation...", file=sys.stderr)
        urls_to_validate = []
        for entity in entities:
            ent_id = entity.attrib.get("entityID")
            if not ent_id:
                continue

            # Only collect URLs for SPs
            is_sp = entity.find(sp_descriptor_xpath, NAMESPACES) is not None
            if is_sp:
                privacy_elem = entity.find(privacy_xpath, NAMESPACES)
                if privacy_elem is not None and privacy_elem.text is not None:
                    privacy_url = privacy_elem.text.strip()
                    if privacy_url and privacy_url not in urls_to_validate:
                        urls_to_validate.append(privacy_url)

        # Validate all URLs in parallel
        if urls_to_validate:
            print(
                f"Found {len(urls_to_validate)} unique privacy URLs to validate",
                file=sys.stderr,
            )
            url_validation_results = validate_urls_parallel(
                urls_to_validate, validation_cache, max_workers
            )
        else:
            url_validation_results = {}
    else:
        url_validation_results = {}

    for entity in entities:
        stats["total_entities"] += 1

        # Early exit if no entityID
        ent_id = entity.attrib.get("entityID")
        if not ent_id:
            continue

        # Get organization name early for logging
        orgname_elem = entity.find(org_name_xpath, NAMESPACES)
        orgname = (
            orgname_elem.text.strip()
            if orgname_elem is not None and orgname_elem.text
            else "Unknown"
        )

        # Determine entity type first
        is_sp = entity.find(sp_descriptor_xpath, NAMESPACES) is not None
        is_idp = entity.find(idp_descriptor_xpath, NAMESPACES) is not None

        if is_sp:
            ent_type = "SP"
            stats["total_sps"] += 1
        elif is_idp:
            ent_type = "IdP"
            stats["total_idps"] += 1
        else:
            ent_type = "Unknown"

        # Check for privacy statement URL (only for SPs)
        has_privacy = False
        privacy_url = ""
        url_validation_result = None

        if is_sp:
            privacy_elem = entity.find(privacy_xpath, NAMESPACES)
            has_privacy = privacy_elem is not None and privacy_elem.text is not None
            privacy_url = privacy_elem.text.strip() if has_privacy else ""

            if has_privacy:
                stats["sps_has_privacy"] += 1

                # Get URL validation result if validation was enabled
                if (
                    validate_urls
                    and privacy_url
                    and privacy_url in url_validation_results
                ):
                    url_validation_result = url_validation_results[privacy_url]

                    # Update validation statistics
                    stats["urls_checked"] += 1
                    if url_validation_result["accessible"]:
                        stats["urls_accessible"] += 1
                    else:
                        stats["urls_broken"] += 1

            else:
                stats["sps_missing_privacy"] += 1

        # Check for security contact (both REFEDS and InCommon types)
        sec_contact_refeds_elem = entity.find(sec_contact_refeds, NAMESPACES)
        sec_contact_incommon_elem = entity.find(sec_contact_incommon, NAMESPACES)
        has_security = (
            sec_contact_refeds_elem is not None or sec_contact_incommon_elem is not None
        )

        # Update security contact statistics by entity type
        if has_security:
            stats["total_has_security"] += 1
            if is_sp:
                stats["sps_has_security"] += 1
            elif is_idp:
                stats["idps_has_security"] += 1
        else:
            stats["total_missing_security"] += 1
            if is_sp:
                stats["sps_missing_security"] += 1
            elif is_idp:
                stats["idps_missing_security"] += 1

        # Update combined statistics (only for SPs since privacy is SP-only)
        if is_sp:
            if has_privacy and has_security:
                stats["sps_has_both"] += 1
            elif not has_privacy and not has_security:
                stats["sps_missing_both"] += 1

        # Get registration authority and map to federation name
        registration_info = entity.find(reg_info_xpath, NAMESPACES)
        registration_authority = ""
        if registration_info is not None:
            registration_authority = registration_info.attrib.get(
                "registrationAuthority", ""
            ).strip()

        # Map registration authority to federation name for display
        federation_name = map_registration_authority(
            registration_authority, federation_mapping or {}
        )

        # Update federation-level statistics (use federation name as key)
        if registration_authority:
            if federation_name not in federation_stats:
                federation_stats[federation_name] = {
                    "total_entities": 0,
                    "total_sps": 0,
                    "total_idps": 0,
                    "sps_has_privacy": 0,
                    "sps_missing_privacy": 0,
                    "sps_has_security": 0,
                    "sps_missing_security": 0,
                    "idps_has_security": 0,
                    "idps_missing_security": 0,
                    "total_has_security": 0,
                    "total_missing_security": 0,
                    "sps_has_both": 0,
                    "sps_missing_both": 0,
                    # URL validation statistics
                    "urls_checked": 0,
                    "urls_accessible": 0,
                    "urls_broken": 0,
                }

            fed_stats = federation_stats[federation_name]
            fed_stats["total_entities"] += 1

            if is_sp:
                fed_stats["total_sps"] += 1
                if has_privacy:
                    fed_stats["sps_has_privacy"] += 1

                    # Update federation URL validation stats
                    if validate_urls and url_validation_result:
                        fed_stats["urls_checked"] += 1
                        if url_validation_result["accessible"]:
                            fed_stats["urls_accessible"] += 1
                        else:
                            fed_stats["urls_broken"] += 1

                else:
                    fed_stats["sps_missing_privacy"] += 1

                if has_security:
                    fed_stats["sps_has_security"] += 1
                else:
                    fed_stats["sps_missing_security"] += 1

                if has_privacy and has_security:
                    fed_stats["sps_has_both"] += 1
                elif not has_privacy and not has_security:
                    fed_stats["sps_missing_both"] += 1

            elif is_idp:
                fed_stats["total_idps"] += 1
                if has_security:
                    fed_stats["idps_has_security"] += 1
                else:
                    fed_stats["idps_missing_security"] += 1

            # Overall federation security stats
            if has_security:
                fed_stats["total_has_security"] += 1
            else:
                fed_stats["total_missing_security"] += 1

        # Prepare validation data for entity list
        if validate_urls and url_validation_result:
            url_status = url_validation_result.get("status_code", 0)
            final_url = url_validation_result.get("final_url", privacy_url)
            url_accessible = (
                "Yes" if url_validation_result.get("accessible", False) else "No"
            )
            redirect_count = url_validation_result.get("redirect_count", 0)
            validation_error = url_validation_result.get("error", "")
        else:
            url_status = "" if not validate_urls else "Not Checked"
            final_url = privacy_url if has_privacy else ""
            url_accessible = "" if not validate_urls else "Not Checked"
            redirect_count = "" if not validate_urls else "Not Checked"
            validation_error = "" if not validate_urls else "URL validation disabled"

        # Add entity data (use federation name for display, but keep using registration_authority for federation_stats)
        if validate_urls:
            # Extended format with enhanced validation results
            entities_list.append(
                [
                    federation_name,
                    ent_type,
                    orgname,
                    ent_id,
                    "Yes" if has_privacy else "No",
                    privacy_url if has_privacy else "",
                    "Yes" if has_security else "No",
                    str(url_status),
                    final_url,
                    url_accessible,
                    str(redirect_count),
                    validation_error,
                ]
            )
        else:
            # Original format without validation
            entities_list.append(
                [
                    federation_name,
                    ent_type,
                    orgname,
                    ent_id,
                    "Yes" if has_privacy else "No",
                    privacy_url if has_privacy else "",
                    "Yes" if has_security else "No",
                ]
            )

    return entities_list, stats, federation_stats


def filter_entities(
    entities_list: list[list[str]], filter_mode: str
) -> list[list[str]]:
    """
    Filter entities based on the specified mode.

    Args:
        entities_list: List of entity data rows
        filter_mode: Filter criteria (missing_privacy, missing_security, missing_both)

    Returns:
        List[List[str]]: Filtered entity data
    """
    if filter_mode == "missing_privacy":
        return [e for e in entities_list if e[4] == "No"]  # HasPrivacyStatement column
    elif filter_mode == "missing_security":
        return [e for e in entities_list if e[6] == "No"]  # HasSecurityContact column
    elif filter_mode == "missing_both":
        return [e for e in entities_list if e[4] == "No" and e[6] == "No"]
    else:
        return entities_list
