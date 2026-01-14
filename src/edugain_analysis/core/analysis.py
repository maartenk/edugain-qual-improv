"""
Core analysis module for eduGAIN privacy and security assessment.

Provides the main analysis logic for processing eduGAIN metadata to identify
entities with privacy statements and security contacts.
"""

import sys
import xml.etree.ElementTree as ET

from ..config import NAMESPACES, URL_VALIDATION_THREADS
from .entities import iter_entity_records
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
        # SIRTFI statistics
        "total_has_sirtfi": 0,
        "sps_has_sirtfi": 0,
        "idps_has_sirtfi": 0,
        "total_missing_sirtfi": 0,
        "sps_missing_sirtfi": 0,
        "idps_missing_sirtfi": 0,
        # URL validation statistics
        "urls_checked": 0,
        "urls_accessible": 0,
        "urls_broken": 0,
        "validation_enabled": validate_urls,
        "provider_stats": {  # Bot protection provider statistics
            "total_detected": 0,
            "by_provider": {},  # Provider -> count
            "retry_attempted": 0,
            "retry_success": 0,
            "retry_failed": 0,
        },
    }

    # Federation-level statistics by registration authority
    federation_stats = {}

    records = list(iter_entity_records(root, federation_mapping or {}))
    stats["total_entities"] = len(root.findall(".//md:EntityDescriptor", NAMESPACES))

    # Collect all privacy URLs for parallel validation
    if validate_urls:
        print("Collecting privacy statement URLs for validation...", file=sys.stderr)
        urls_to_validate = []
        seen_urls = set()
        for record in records:
            if record.is_sp and record.has_privacy and record.privacy_url:
                if record.privacy_url not in seen_urls:
                    urls_to_validate.append(record.privacy_url)
                    seen_urls.add(record.privacy_url)

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

    for record in records:
        is_sp = record.is_sp
        is_idp = record.is_idp
        ent_type_display = record.entity_type

        if is_sp:
            stats["total_sps"] += 1
            if record.has_privacy:
                stats["sps_has_privacy"] += 1
            else:
                stats["sps_missing_privacy"] += 1
        elif is_idp:
            stats["total_idps"] += 1

        if record.has_security:
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

        # Update SIRTFI statistics by entity type
        if record.has_sirtfi:
            stats["total_has_sirtfi"] += 1
            if is_sp:
                stats["sps_has_sirtfi"] += 1
            elif is_idp:
                stats["idps_has_sirtfi"] += 1
        else:
            stats["total_missing_sirtfi"] += 1
            if is_sp:
                stats["sps_missing_sirtfi"] += 1
            elif is_idp:
                stats["idps_missing_sirtfi"] += 1

        # Update combined statistics (only for SPs since privacy is SP-only)
        if is_sp:
            if record.has_privacy and record.has_security:
                stats["sps_has_both"] += 1
            elif not record.has_privacy and not record.has_security:
                stats["sps_missing_both"] += 1

        has_privacy_display = (
            "Yes" if record.has_privacy else ("N/A" if not is_sp else "No")
        )
        privacy_url_display = (
            record.privacy_url if record.has_privacy else ("N/A" if not is_sp else "")
        )

        url_validation_result = None
        if (
            validate_urls
            and is_sp
            and record.has_privacy
            and record.privacy_url in url_validation_results
        ):
            url_validation_result = url_validation_results[record.privacy_url]
            stats["urls_checked"] += 1
            if url_validation_result["accessible"]:
                stats["urls_accessible"] += 1
            else:
                stats["urls_broken"] += 1

            # Track bot protection provider statistics
            protection_detected = url_validation_result.get("protection_detected")
            retry_method = url_validation_result.get("retry_method")
            status_code = url_validation_result.get("status_code", 0)

            if protection_detected:
                stats["provider_stats"]["total_detected"] += 1
                stats["provider_stats"]["by_provider"][protection_detected] = (
                    stats["provider_stats"]["by_provider"].get(protection_detected, 0)
                    + 1
                )

            if retry_method:
                stats["provider_stats"]["retry_attempted"] += 1
                if 200 <= status_code < 400:
                    stats["provider_stats"]["retry_success"] += 1
                else:
                    stats["provider_stats"]["retry_failed"] += 1

        # Update federation-level statistics (use federation name as key)
        if record.registration_authority:
            if record.federation_name not in federation_stats:
                federation_stats[record.federation_name] = {
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
                    # SIRTFI statistics
                    "total_has_sirtfi": 0,
                    "sps_has_sirtfi": 0,
                    "idps_has_sirtfi": 0,
                    "total_missing_sirtfi": 0,
                    "sps_missing_sirtfi": 0,
                    "idps_missing_sirtfi": 0,
                    # URL validation statistics
                    "urls_checked": 0,
                    "urls_accessible": 0,
                    "urls_broken": 0,
                    "provider_stats": {  # Bot protection provider statistics
                        "total_detected": 0,
                        "by_provider": {},
                        "retry_attempted": 0,
                        "retry_success": 0,
                        "retry_failed": 0,
                    },
                }

            fed_stats = federation_stats[record.federation_name]
            fed_stats["total_entities"] += 1

            if is_sp:
                fed_stats["total_sps"] += 1
                if record.has_privacy:
                    fed_stats["sps_has_privacy"] += 1

                    # Update federation URL validation stats
                    if validate_urls and url_validation_result is not None:
                        fed_stats["urls_checked"] += 1
                        if url_validation_result["accessible"]:
                            fed_stats["urls_accessible"] += 1
                        else:
                            fed_stats["urls_broken"] += 1

                        # Track federation provider statistics
                        protection_detected = url_validation_result.get(
                            "protection_detected"
                        )
                        retry_method = url_validation_result.get("retry_method")
                        status_code = url_validation_result.get("status_code", 0)

                        if protection_detected:
                            fed_stats["provider_stats"]["total_detected"] += 1
                            fed_stats["provider_stats"]["by_provider"][
                                protection_detected
                            ] = (
                                fed_stats["provider_stats"]["by_provider"].get(
                                    protection_detected, 0
                                )
                                + 1
                            )

                        if retry_method:
                            fed_stats["provider_stats"]["retry_attempted"] += 1
                            if 200 <= status_code < 400:
                                fed_stats["provider_stats"]["retry_success"] += 1
                            else:
                                fed_stats["provider_stats"]["retry_failed"] += 1

                else:
                    fed_stats["sps_missing_privacy"] += 1

                if record.has_security:
                    fed_stats["sps_has_security"] += 1
                else:
                    fed_stats["sps_missing_security"] += 1

                # SP SIRTFI stats
                if record.has_sirtfi:
                    fed_stats["sps_has_sirtfi"] += 1
                else:
                    fed_stats["sps_missing_sirtfi"] += 1

                if record.has_privacy and record.has_security:
                    fed_stats["sps_has_both"] += 1
                elif not record.has_privacy and not record.has_security:
                    fed_stats["sps_missing_both"] += 1

            elif is_idp:
                fed_stats["total_idps"] += 1
                if record.has_security:
                    fed_stats["idps_has_security"] += 1
                else:
                    fed_stats["idps_missing_security"] += 1

                # IdP SIRTFI stats
                if record.has_sirtfi:
                    fed_stats["idps_has_sirtfi"] += 1
                else:
                    fed_stats["idps_missing_sirtfi"] += 1

            # Overall federation security stats
            if record.has_security:
                fed_stats["total_has_security"] += 1
            else:
                fed_stats["total_missing_security"] += 1

            # Overall federation SIRTFI stats
            if record.has_sirtfi:
                fed_stats["total_has_sirtfi"] += 1
            else:
                fed_stats["total_missing_sirtfi"] += 1

        # Prepare validation data for entity list
        if validate_urls and url_validation_result is not None:
            url_status = url_validation_result.get("status_code", 0)
            final_url = url_validation_result.get("final_url", record.privacy_url)
            url_accessible = (
                "Yes" if url_validation_result.get("accessible", False) else "No"
            )
            redirect_count = url_validation_result.get("redirect_count", 0)
            validation_error = url_validation_result.get("error", "")
        else:
            url_status = "" if not validate_urls else "Not Checked"
            final_url = privacy_url_display
            url_accessible = "" if not validate_urls else "Not Checked"
            redirect_count = "" if not validate_urls else "Not Checked"
            validation_error = "" if not validate_urls else "URL validation disabled"

        # Add entity data (use federation name for display, but keep using registration_authority for federation_stats)
        if validate_urls:
            # Extended format with enhanced validation results
            entities_list.append(
                [
                    record.federation_name,
                    ent_type_display,
                    record.org_name,
                    record.entity_id,
                    has_privacy_display,
                    privacy_url_display,
                    "Yes" if record.has_security else "No",
                    "Yes" if record.has_sirtfi else "No",
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
                    record.federation_name,
                    ent_type_display,
                    record.org_name,
                    record.entity_id,
                    has_privacy_display,
                    privacy_url_display,
                    "Yes" if record.has_security else "No",
                    "Yes" if record.has_sirtfi else "No",
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
