#!/usr/bin/env python3
"""
eduGAIN Privacy Statement and Security Contact Analysis Tool

This script downloads the current eduGAIN metadata aggregate XML and analyzes entities
to identify those missing privacy statement URLs and/or security contacts.

Default behavior: Shows summary statistics with coverage percentages

Usage:
    python privacy_security_analysis.py                      # Show summary statistics (default)
    python privacy_security_analysis.py --federation-summary # Markdown report with federation breakdown
    python privacy_security_analysis.py --list-missing-both  # CSV list of entities missing both
    python privacy_security_analysis.py --list-missing-privacy # CSV list without privacy statements
    python privacy_security_analysis.py --list-missing-security # CSV list without security contacts
    python privacy_security_analysis.py --list-all-entities  # Full CSV list of all entities
    python privacy_security_analysis.py --local-file file    # Use local XML file
    python privacy_security_analysis.py --help               # Show all available options
"""

import argparse
import csv
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

# Configuration
EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
EDUGAIN_FEDERATIONS_API = "https://technical.edugain.org/api.php?action=list_feds"
FEDERATION_CACHE_FILE = ".edugain_federations_cache.json"
METADATA_CACHE_FILE = ".edugain_metadata_cache.xml"
URL_VALIDATION_CACHE_FILE = ".edugain_url_validation_cache.json"
CACHE_EXPIRY_DAYS = 30
METADATA_EXPIRY_HOURS = 12
URL_VALIDATION_EXPIRY_DAYS = 7
REQUEST_TIMEOUT = 30
URL_VALIDATION_TIMEOUT = 10
URL_VALIDATION_DELAY = 0.5  # Seconds between URL checks (per thread)
MAX_CONTENT_SIZE = 50 * 1024  # 50KB limit for content analysis
URL_VALIDATION_THREADS = 8  # Number of parallel threads for URL validation
URL_VALIDATION_BATCH_SIZE = 50  # Process URLs in batches for progress reporting

# SAML metadata namespaces
NAMESPACES = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "mdui": "urn:oasis:names:tc:SAML:metadata:ui",
    "shibmd": "urn:mace:shibboleth:metadata:1.0",
    "remd": "http://refeds.org/metadata",
    "icmd": "http://id.incommon.org/metadata",
    "mdrpi": "urn:oasis:names:tc:SAML:metadata:rpi",
    "mdattr": "urn:oasis:names:tc:SAML:metadata:attribute",
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
}

# Privacy statement content validation patterns
PRIVACY_CONTENT_PATTERNS = [
    # Strong indicators
    r"\bprivacy\s+(statement|policy|notice)\b",
    r"\bdata\s+protection\b",
    r"\bpersonal\s+(information|data)\b",
    r"\bdata\s+processing\b",
    r"\bcookies?\s+(policy|statement)\b",
    r"\bGDPR\b",
    r"\bdata\s+controller\b",
    # Common privacy-related terms
    r"\bcollect.*\binformation\b",
    r"\buse.*\bdata\b",
    r"\bshare.*\binformation\b",
    r"\bthird.{1,10}part(y|ies)\b",
    r"\bopt.{1,5}out\b",
    r"\bwithdraw.*\bconsent\b",
]

# Compile regex patterns for performance
PRIVACY_REGEX = [
    re.compile(pattern, re.IGNORECASE) for pattern in PRIVACY_CONTENT_PATTERNS
]

# Global rate limiting semaphore for URL validation
_url_validation_semaphore = None


def _get_url_validation_semaphore(max_concurrent: int = URL_VALIDATION_THREADS):
    """Get or create the global URL validation semaphore."""
    global _url_validation_semaphore
    if _url_validation_semaphore is None:
        _url_validation_semaphore = threading.Semaphore(max_concurrent)
    return _url_validation_semaphore


def is_metadata_cache_valid() -> bool:
    """Check if metadata cache exists and is not expired."""
    if not os.path.exists(METADATA_CACHE_FILE):
        return False

    try:
        # Check if cache is expired (older than METADATA_EXPIRY_HOURS)
        cache_mtime = os.path.getmtime(METADATA_CACHE_FILE)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_mtime)

        if cache_age > timedelta(hours=METADATA_EXPIRY_HOURS):
            hours_old = cache_age.total_seconds() / 3600
            print(
                f"Metadata cache is {hours_old:.1f} hours old (>12h), refreshing...",
                file=sys.stderr,
            )
            return False

        hours_old = cache_age.total_seconds() / 3600
        print(f"Using cached metadata ({hours_old:.1f} hours old)", file=sys.stderr)
        return True

    except OSError as e:
        print(f"Warning: Could not check metadata cache: {e}", file=sys.stderr)
        return False


def download_metadata(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    """Download eduGAIN metadata from the specified URL."""
    try:
        print(f"Downloading metadata from {url}...", file=sys.stderr)
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content: bytes = response.content
        print(f"Downloaded {len(content):,} bytes of metadata", file=sys.stderr)
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading metadata from {url}: {e}", file=sys.stderr)
        sys.exit(1)


def save_metadata_cache(content: bytes) -> None:
    """Save metadata content to cache file."""
    try:
        with open(METADATA_CACHE_FILE, "wb") as f:
            f.write(content)
        print(f"Metadata cached to {METADATA_CACHE_FILE}", file=sys.stderr)
    except OSError as e:
        print(f"Warning: Could not save metadata cache: {e}", file=sys.stderr)


def load_metadata_cache() -> Optional[bytes]:
    """Load metadata content from cache file if valid."""
    if not is_metadata_cache_valid():
        return None

    try:
        with open(METADATA_CACHE_FILE, "rb") as f:
            return f.read()
    except OSError as e:
        print(f"Warning: Could not read metadata cache: {e}", file=sys.stderr)
        return None


def get_metadata(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    """Get metadata from cache or download from URL, updating cache as needed."""
    # Try to load from cache first
    cached_content = load_metadata_cache()
    if cached_content is not None:
        return cached_content

    # Cache miss or expired, download from URL
    content = download_metadata(url, timeout)

    # Save to cache for future use
    save_metadata_cache(content)

    return content


def parse_metadata(
    xml_content: Optional[bytes], local_file: Optional[str] = None
) -> ET.Element:
    """Parse XML metadata content or local file."""
    try:
        if local_file:
            return ET.parse(local_file).getroot()
        else:
            return ET.fromstring(xml_content)  # type: ignore
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)


def load_federation_cache() -> Optional[Dict[str, str]]:
    """Load federation name mapping from cache file if it exists and is not expired."""
    if not os.path.exists(FEDERATION_CACHE_FILE):
        return None

    try:
        # Check if cache is expired (older than CACHE_EXPIRY_DAYS)
        cache_mtime = os.path.getmtime(FEDERATION_CACHE_FILE)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_mtime)

        if cache_age > timedelta(days=CACHE_EXPIRY_DAYS):
            print(
                f"Federation cache is {cache_age.days} days old, refreshing...",
                file=sys.stderr,
            )
            return None

        with open(FEDERATION_CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            return cache_data.get("federations", {})

    except (json.JSONDecodeError, OSError, KeyError) as e:
        print(f"Warning: Could not read federation cache: {e}", file=sys.stderr)
        return None


def save_federation_cache(federations: Dict[str, str]) -> None:
    """Save federation name mapping to cache file."""
    try:
        cache_data = {
            "federations": federations,
            "cached_at": datetime.now().isoformat(),
            "cache_version": "1.0",
        }

        with open(FEDERATION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    except OSError as e:
        print(f"Warning: Could not save federation cache: {e}", file=sys.stderr)


def fetch_federation_names() -> Dict[str, str]:
    """Fetch federation names from eduGAIN API and return mapping dict."""
    try:
        print("Fetching federation names from eduGAIN API...", file=sys.stderr)
        response = requests.get(EDUGAIN_FEDERATIONS_API, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        federations_data = response.json()

        # Create mapping from registration authority to federation name
        federation_mapping = {}

        for fed_id, fed_info in federations_data.items():
            if isinstance(fed_info, dict):
                reg_auth = fed_info.get("reg_auth")
                name = fed_info.get("name")

                if reg_auth and name:
                    federation_mapping[reg_auth] = name

        print(f"Loaded {len(federation_mapping)} federation names", file=sys.stderr)
        return federation_mapping

    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch federation names: {e}", file=sys.stderr)
        return {}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse federation API response: {e}", file=sys.stderr)
        return {}


def get_federation_mapping() -> Dict[str, str]:
    """Get federation name mapping, using cache if available or fetching from API."""
    # Try to load from cache first
    federation_mapping = load_federation_cache()

    if federation_mapping is not None:
        print(
            f"Using cached federation names ({len(federation_mapping)} federations)",
            file=sys.stderr,
        )
        return federation_mapping

    # Cache miss or expired, fetch from API
    federation_mapping = fetch_federation_names()

    # Save to cache for future use
    if federation_mapping:
        save_federation_cache(federation_mapping)

    return federation_mapping


def map_registration_authority(
    reg_auth: str, federation_mapping: Dict[str, str]
) -> str:
    """Map registration authority to federation name, fallback to reg_auth if not found."""
    if not reg_auth:
        return "Unknown"

    # Try to find federation name
    federation_name = federation_mapping.get(reg_auth)

    if federation_name:
        return federation_name
    else:
        # Fallback to registration authority, clean it up for display
        clean_reg_auth = reg_auth.replace("https://", "").replace("http://", "")
        if clean_reg_auth.endswith("/"):
            clean_reg_auth = clean_reg_auth[:-1]
        return clean_reg_auth


def load_url_validation_cache() -> Optional[Dict[str, Dict]]:
    """Load URL validation results from cache file if it exists and is not expired."""
    if not os.path.exists(URL_VALIDATION_CACHE_FILE):
        return None

    try:
        # Check if cache is expired (older than URL_VALIDATION_EXPIRY_DAYS)
        cache_mtime = os.path.getmtime(URL_VALIDATION_CACHE_FILE)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_mtime)

        if cache_age > timedelta(days=URL_VALIDATION_EXPIRY_DAYS):
            print(
                f"URL validation cache is {cache_age.days} days old, refreshing...",
                file=sys.stderr,
            )
            return None

        with open(URL_VALIDATION_CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            return cache_data.get("validations", {})

    except (json.JSONDecodeError, OSError, KeyError) as e:
        print(f"Warning: Could not read URL validation cache: {e}", file=sys.stderr)
        return None


def save_url_validation_cache(validations: Dict[str, Dict]) -> None:
    """Save URL validation results to cache file."""
    try:
        cache_data = {
            "validations": validations,
            "cached_at": datetime.now().isoformat(),
            "cache_version": "1.0",
        }

        with open(URL_VALIDATION_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

    except OSError as e:
        print(f"Warning: Could not save URL validation cache: {e}", file=sys.stderr)


def validate_privacy_url_content(content: str) -> Tuple[bool, int]:
    """
    Validate if content appears to be a genuine privacy statement.

    Returns:
        Tuple of (content_valid: bool, match_count: int)
    """
    if not content:
        return False, 0

    # Convert to lowercase for case-insensitive matching
    content_lower = content.lower()

    # Check for clear indicators this is NOT a privacy statement
    error_indicators = [
        "page not found",
        "404",
        "error",
        "not found",
        "under construction",
        "coming soon",
        "maintenance",
    ]

    for indicator in error_indicators:
        if indicator in content_lower:
            return False, 0

    # Count matches for privacy-related patterns
    match_count = 0
    for regex in PRIVACY_REGEX:
        if regex.search(content):
            match_count += 1

    # Content is considered valid if it has multiple privacy indicators
    content_valid = match_count >= 3

    return content_valid, match_count


def validate_privacy_url(
    url: str, validation_cache: Dict[str, Dict] = None, use_semaphore: bool = True
) -> Dict:
    """
    Validate a privacy statement URL for accessibility and content.

    Returns:
        Dict with validation results: {
            'status_code': int,
            'accessible': bool,
            'content_valid': bool,
            'match_count': int,
            'error': str or None,
            'checked_at': str
        }
    """
    if not url or not url.strip():
        return {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": "Empty URL",
            "checked_at": datetime.now().isoformat(),
        }

    url = url.strip()

    # Check cache first
    if validation_cache and url in validation_cache:
        cached_result = validation_cache[url].copy()
        cached_result["from_cache"] = True
        return cached_result

    # Get semaphore for rate limiting if needed
    semaphore = None
    if use_semaphore:
        semaphore = _get_url_validation_semaphore()
        semaphore.acquire()

    # Validate URL format
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            if semaphore is not None:
                semaphore.release()
            return {
                "status_code": 0,
                "accessible": False,
                "content_valid": False,
                "match_count": 0,
                "error": "Invalid URL format",
                "checked_at": datetime.now().isoformat(),
            }
    except Exception as e:
        if semaphore is not None:
            semaphore.release()
        return {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": f"URL parsing error: {str(e)}",
            "checked_at": datetime.now().isoformat(),
        }

    # Rate limiting
    time.sleep(URL_VALIDATION_DELAY)

    try:
        # Make HTTP request with restricted content size
        response = requests.get(
            url,
            timeout=URL_VALIDATION_TIMEOUT,
            headers={"User-Agent": "eduGAIN-Quality-Analysis/1.0 (URL validation bot)"},
            stream=True,
        )

        status_code = response.status_code

        # Check if URL is accessible (2xx or 3xx status codes)
        accessible = 200 <= status_code < 400

        # For content validation, we need successful responses
        content_valid = False
        match_count = 0

        if accessible and status_code < 300:  # Only analyze 2xx responses
            try:
                # Read limited content
                content_bytes = b""
                for chunk in response.iter_content(chunk_size=1024):
                    content_bytes += chunk
                    if len(content_bytes) >= MAX_CONTENT_SIZE:
                        break

                # Try to decode content
                content = content_bytes.decode("utf-8", errors="ignore")
                content_valid, match_count = validate_privacy_url_content(content)

            except Exception as content_error:
                print(
                    f"Warning: Content analysis failed for {url}: {content_error}",
                    file=sys.stderr,
                )

        result = {
            "status_code": status_code,
            "accessible": accessible,
            "content_valid": content_valid,
            "match_count": match_count,
            "error": None,
            "checked_at": datetime.now().isoformat(),
        }

        # Add result to cache
        if validation_cache is not None:
            validation_cache[url] = result

        return result

    except requests.exceptions.Timeout:
        result = {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": "Request timeout",
            "checked_at": datetime.now().isoformat(),
        }
        if validation_cache is not None:
            validation_cache[url] = result
        return result
    except requests.exceptions.SSLError:
        result = {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": "SSL certificate error",
            "checked_at": datetime.now().isoformat(),
        }
        if validation_cache is not None:
            validation_cache[url] = result
        return result
    except requests.exceptions.ConnectionError:
        result = {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": "Connection error",
            "checked_at": datetime.now().isoformat(),
        }
        if validation_cache is not None:
            validation_cache[url] = result
        return result
    except requests.exceptions.RequestException as e:
        result = {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": f"Request error: {str(e)}",
            "checked_at": datetime.now().isoformat(),
        }
        if validation_cache is not None:
            validation_cache[url] = result
        return result
    except Exception as e:
        result = {
            "status_code": 0,
            "accessible": False,
            "content_valid": False,
            "match_count": 0,
            "error": f"Unexpected error: {str(e)}",
            "checked_at": datetime.now().isoformat(),
        }
        if validation_cache is not None:
            validation_cache[url] = result
        return result
    finally:
        # Always release semaphore if acquired
        if semaphore is not None:
            semaphore.release()


def validate_urls_parallel(
    urls: List[str],
    validation_cache: Dict[str, Dict] = None,
    max_workers: int = URL_VALIDATION_THREADS,
) -> Dict[str, Dict]:
    """
    Validate multiple URLs in parallel using ThreadPoolExecutor.

    Args:
        urls: List of URLs to validate
        validation_cache: Shared cache for validation results
        max_workers: Maximum number of worker threads

    Returns:
        Dict mapping URLs to their validation results
    """
    if not urls:
        return {}

    results = {}

    # Filter out URLs that are already cached
    urls_to_check = []
    for url in urls:
        if validation_cache and url in validation_cache:
            results[url] = validation_cache[url]
        else:
            urls_to_check.append(url)

    if not urls_to_check:
        return results

    print(
        f"Validating {len(urls_to_check)} URLs in parallel (using {max_workers} threads)...",
        file=sys.stderr,
    )

    # Process URLs in batches for progress reporting
    total_batches = (
        len(urls_to_check) + URL_VALIDATION_BATCH_SIZE - 1
    ) // URL_VALIDATION_BATCH_SIZE

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for batch_num in range(total_batches):
            start_idx = batch_num * URL_VALIDATION_BATCH_SIZE
            end_idx = min(
                (batch_num + 1) * URL_VALIDATION_BATCH_SIZE, len(urls_to_check)
            )
            batch_urls = urls_to_check[start_idx:end_idx]

            print(
                f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_urls)} URLs)...",
                file=sys.stderr,
            )

            # Submit validation tasks for this batch
            future_to_url = {
                executor.submit(
                    validate_privacy_url, url, validation_cache, use_semaphore=True
                ): url
                for url in batch_urls
            }

            # Collect results as they complete
            batch_completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results[url] = result
                    batch_completed += 1

                    # Progress update every 10 URLs or at end of batch
                    if batch_completed % 10 == 0 or batch_completed == len(batch_urls):
                        print(
                            f"  Completed {batch_completed}/{len(batch_urls)} URLs in batch {batch_num + 1}",
                            file=sys.stderr,
                        )

                except Exception as exc:
                    print(f"URL validation failed for {url}: {exc}", file=sys.stderr)
                    # Create error result
                    results[url] = {
                        "status_code": 0,
                        "accessible": False,
                        "content_valid": False,
                        "match_count": 0,
                        "error": f"Validation failed: {str(exc)}",
                        "checked_at": datetime.now().isoformat(),
                    }
                    # Add to cache
                    if validation_cache is not None:
                        validation_cache[url] = results[url]

    print(f"Completed validation of {len(urls_to_check)} URLs", file=sys.stderr)
    return results


def analyze_privacy_security(
    root: ET.Element,
    federation_mapping: Dict[str, str] = None,
    validate_urls: bool = False,
    validation_cache: Dict[str, Dict] = None,
    max_workers: int = URL_VALIDATION_THREADS,
) -> Tuple[List[List[str]], dict, dict]:
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
        "urls_content_valid": 0,
        "urls_content_invalid": 0,
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

                    if url_validation_result["content_valid"]:
                        stats["urls_content_valid"] += 1
                    else:
                        stats["urls_content_invalid"] += 1

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
                    "urls_content_valid": 0,
                    "urls_content_invalid": 0,
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

                        if url_validation_result["content_valid"]:
                            fed_stats["urls_content_valid"] += 1
                        else:
                            fed_stats["urls_content_invalid"] += 1
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
            url_accessible = (
                "Yes" if url_validation_result.get("accessible", False) else "No"
            )
            content_valid = (
                "Yes" if url_validation_result.get("content_valid", False) else "No"
            )
            validation_error = url_validation_result.get("error", "")
        else:
            url_status = "" if not validate_urls else "Not Checked"
            url_accessible = "" if not validate_urls else "Not Checked"
            content_valid = "" if not validate_urls else "Not Checked"
            validation_error = "" if not validate_urls else "URL validation disabled"

        # Add entity data (use federation name for display, but keep using registration_authority for federation_stats)
        if validate_urls:
            # Extended format with validation results
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
                    url_accessible,
                    content_valid,
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
    entities_list: List[List[str]], filter_mode: str
) -> List[List[str]]:
    """Filter entities based on the specified mode."""
    if filter_mode == "missing_privacy":
        return [e for e in entities_list if e[4] == "No"]  # HasPrivacyStatement column
    elif filter_mode == "missing_security":
        return [e for e in entities_list if e[6] == "No"]  # HasSecurityContact column
    elif filter_mode == "missing_both":
        return [e for e in entities_list if e[4] == "No" and e[6] == "No"]
    else:
        return entities_list


def print_summary(stats: dict) -> None:
    """Print summary statistics with positive framing."""
    total = stats["total_entities"]
    total_sps = stats["total_sps"]
    total_idps = stats["total_idps"]

    if total == 0:
        print("No entities found in metadata.", file=sys.stderr)
        return

    print(
        "\n=== eduGAIN Privacy Statement and Security Contact Coverage ===",
        file=sys.stderr,
    )
    print(
        f"Total entities analyzed: {total} (SPs: {total_sps}, IdPs: {total_idps})",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    # Privacy statement statistics - SP only
    if total_sps > 0:
        sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
        sp_missing_privacy_pct = (stats["sps_missing_privacy"] / total_sps) * 100
        print("📊 Privacy Statement URL Coverage (SPs only):", file=sys.stderr)
        print(
            f"  ✅ SPs with privacy statements: {stats['sps_has_privacy']} out of {total_sps} ({sp_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing privacy statements: {stats['sps_missing_privacy']} out of {total_sps} ({sp_missing_privacy_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Security contact statistics - split by entity type
    total_security_pct = (stats["total_has_security"] / total) * 100
    total_missing_security_pct = (stats["total_missing_security"] / total) * 100
    print("🔒 Security Contact Coverage:", file=sys.stderr)
    print(
        f"  ✅ Total entities with security contacts: {stats['total_has_security']} out of {total} ({total_security_pct:.1f}%)",
        file=sys.stderr,
    )
    print(
        f"  ❌ Total entities missing security contacts: {stats['total_missing_security']} out of {total} ({total_missing_security_pct:.1f}%)",
        file=sys.stderr,
    )

    # Split security stats by entity type
    if total_sps > 0:
        sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
        print(
            f"    📊 SPs: {stats['sps_has_security']} with / {stats['sps_missing_security']} without ({sp_security_pct:.1f}% coverage)",
            file=sys.stderr,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        print(
            f"    📊 IdPs: {stats['idps_has_security']} with / {stats['idps_missing_security']} without ({idp_security_pct:.1f}% coverage)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # Combined statistics - SP only (since privacy is SP-only)
    if total_sps > 0:
        sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
        sp_missing_both_pct = (stats["sps_missing_both"] / total_sps) * 100
        sp_has_at_least_one = total_sps - stats["sps_missing_both"]
        sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100

        print("📈 Combined Coverage Summary (SPs only):", file=sys.stderr)
        print(
            f"  🌟 SPs with BOTH (fully compliant): {stats['sps_has_both']} out of {total_sps} ({sp_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ⚡ SPs with AT LEAST ONE: {sp_has_at_least_one} out of {total_sps} ({sp_at_least_one_pct:.1f}%)",
            file=sys.stderr,
        )
        print(
            f"  ❌ SPs missing both: {stats['sps_missing_both']} out of {total_sps} ({sp_missing_both_pct:.1f}%)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Key insights for both entity types
    print("💡 Key Insights:", file=sys.stderr)

    # SP insights
    if total_sps > 0:
        print(
            f"  • {sp_at_least_one_pct:.1f}% of SPs provide at least basic compliance",
            file=sys.stderr,
        )
        print(
            f"  • {sp_both_pct:.1f}% of SPs achieve full compliance with both requirements",
            file=sys.stderr,
        )

    # IdP insights
    if total_idps > 0:
        print(
            f"  • {idp_security_pct:.1f}% of IdPs have security contacts (IdPs don't use privacy statements)",
            file=sys.stderr,
        )

    print("", file=sys.stderr)

    # URL Validation Statistics (if enabled)
    if stats.get("validation_enabled", False):
        urls_checked = stats["urls_checked"]
        if urls_checked > 0:
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100
            content_pct = (stats["urls_content_valid"] / urls_checked) * 100

            print("🔗 Privacy URL Validation Results:", file=sys.stderr)
            print(
                f"  📊 URLs checked: {urls_checked} privacy statement URLs",
                file=sys.stderr,
            )
            print(
                f"  ✅ Accessible URLs: {stats['urls_accessible']} out of {urls_checked} ({accessibility_pct:.1f}%)",
                file=sys.stderr,
            )
            print(
                f"  ❌ Broken/inaccessible URLs: {stats['urls_broken']} out of {urls_checked} ({100-accessibility_pct:.1f}%)",
                file=sys.stderr,
            )
            print(
                f"  📄 Valid privacy content: {stats['urls_content_valid']} out of {urls_checked} ({content_pct:.1f}%)",
                file=sys.stderr,
            )
            print(
                f"  ⚠️ Invalid/generic content: {stats['urls_content_invalid']} out of {urls_checked} ({100-content_pct:.1f}%)",
                file=sys.stderr,
            )
            print("", file=sys.stderr)

    print(
        "💡 For detailed entity lists, federation reports, or CSV exports, use --help to see all options.",
        file=sys.stderr,
    )


def print_summary_markdown(stats: dict, output_file=sys.stderr) -> None:
    """Print main summary statistics in markdown format."""
    total = stats["total_entities"]
    total_sps = stats["total_sps"]
    total_idps = stats["total_idps"]

    if total == 0:
        print("# 📊 eduGAIN Quality Analysis Report", file=output_file)
        print("", file=output_file)
        print("**No entities found in the metadata.**", file=output_file)
        return

    print("# 📊 eduGAIN Quality Analysis Report", file=output_file)
    print("", file=output_file)
    print(
        f"**Analysis Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        file=output_file,
    )
    print(
        f"**Total Entities Analyzed:** {total:,} ({total_sps:,} SPs, {total_idps:,} IdPs)",
        file=output_file,
    )
    print("", file=output_file)

    # Privacy Statement Coverage (SPs only)
    if total_sps > 0:
        sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
        sp_missing_privacy_pct = 100 - sp_privacy_pct
        privacy_status = (
            "🟢" if sp_privacy_pct >= 80 else "🟡" if sp_privacy_pct >= 50 else "🔴"
        )

        print("## 📋 Privacy Statement Coverage", file=output_file)
        print(
            "*Privacy statements are only required for Service Providers (SPs)*",
            file=output_file,
        )
        print("", file=output_file)
        print(
            f"- **{privacy_status} SPs with privacy statements:** {stats['sps_has_privacy']:,}/{total_sps:,} ({sp_privacy_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **❌ SPs missing privacy statements:** {stats['sps_missing_privacy']:,}/{total_sps:,} ({sp_missing_privacy_pct:.1f}%)",
            file=output_file,
        )
        print("", file=output_file)

    # Security Contact Coverage
    total_security_pct = (stats["total_has_security"] / total) * 100
    total_missing_security_pct = 100 - total_security_pct
    security_status = (
        "🟢" if total_security_pct >= 80 else "🟡" if total_security_pct >= 50 else "🔴"
    )

    print("## 🔒 Security Contact Coverage", file=output_file)
    print(
        "*Security contacts should be provided by both SPs and IdPs*", file=output_file
    )
    print("", file=output_file)
    print(
        f"- **{security_status} Total entities with security contacts:** {stats['total_has_security']:,}/{total:,} ({total_security_pct:.1f}%)",
        file=output_file,
    )
    print(
        f"- **❌ Total entities missing security contacts:** {stats['total_missing_security']:,}/{total:,} ({total_missing_security_pct:.1f}%)",
        file=output_file,
    )

    # Breakdown by entity type
    if total_sps > 0:
        sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
        sp_missing_security = total_sps - stats["sps_has_security"]
        print(
            f"  - **SPs:** {stats['sps_has_security']:,} with / {sp_missing_security:,} without ({sp_security_pct:.1f}% coverage)",
            file=output_file,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        idp_missing_security = total_idps - stats["idps_has_security"]
        print(
            f"  - **IdPs:** {stats['idps_has_security']:,} with / {idp_missing_security:,} without ({idp_security_pct:.1f}% coverage)",
            file=output_file,
        )

    print("", file=output_file)

    # Combined Coverage Summary (SPs only)
    if total_sps > 0:
        sp_has_at_least_one = (
            stats["sps_has_privacy"] + stats["sps_has_security"] - stats["sps_has_both"]
        )
        sp_missing_both = total_sps - sp_has_at_least_one

        sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
        sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100
        sp_missing_both_pct = (sp_missing_both / total_sps) * 100

        compliance_status = (
            "🟢" if sp_both_pct >= 80 else "🟡" if sp_both_pct >= 50 else "🔴"
        )

        print("## 📈 SP Compliance Summary", file=output_file)
        print(
            "*Combined privacy statement and security contact compliance for Service Providers*",
            file=output_file,
        )
        print("", file=output_file)
        print(
            f"- **{compliance_status} Full Compliance (Both):** {stats['sps_has_both']:,}/{total_sps:,} ({sp_both_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **⚡ Partial Compliance (At Least One):** {sp_has_at_least_one:,}/{total_sps:,} ({sp_at_least_one_pct:.1f}%)",
            file=output_file,
        )
        print(
            f"- **❌ No Compliance (Missing Both):** {sp_missing_both:,}/{total_sps:,} ({sp_missing_both_pct:.1f}%)",
            file=output_file,
        )
        print("", file=output_file)

    # Key Insights
    print("## 💡 Key Insights", file=output_file)

    if total_sps > 0:
        print(
            f"- {sp_at_least_one_pct:.1f}% of SPs provide at least basic compliance",
            file=output_file,
        )
        print(
            f"- {sp_both_pct:.1f}% of SPs achieve full compliance with both requirements",
            file=output_file,
        )

    if total_idps > 0:
        idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
        print(
            f"- {idp_security_pct:.1f}% of IdPs have security contacts (IdPs don't require privacy statements)",
            file=output_file,
        )

    print("", file=output_file)

    # URL Validation Results (if enabled)
    if stats.get("validation_enabled", False):
        urls_checked = stats["urls_checked"]
        if urls_checked > 0:
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100
            content_pct = (stats["urls_content_valid"] / urls_checked) * 100

            accessibility_status = (
                "🟢"
                if accessibility_pct >= 90
                else "🟡"
                if accessibility_pct >= 70
                else "🔴"
            )
            content_status = (
                "🟢" if content_pct >= 80 else "🟡" if content_pct >= 60 else "🔴"
            )

            print("## 🔗 Privacy URL Validation Results", file=output_file)
            print(
                "*Analysis of privacy statement URL accessibility and content quality*",
                file=output_file,
            )
            print("", file=output_file)
            print(
                f"- **📊 URLs Checked:** {urls_checked:,} privacy statement URLs",
                file=output_file,
            )
            print(
                f"- **{accessibility_status} URL Accessibility:** {stats['urls_accessible']:,}/{urls_checked:,} ({accessibility_pct:.1f}%)",
                file=output_file,
            )
            print(
                f"- **❌ Broken/Inaccessible URLs:** {stats['urls_broken']:,}/{urls_checked:,} ({100-accessibility_pct:.1f}%)",
                file=output_file,
            )
            print(
                f"- **{content_status} Valid Privacy Content:** {stats['urls_content_valid']:,}/{urls_checked:,} ({content_pct:.1f}%)",
                file=output_file,
            )
            print(
                f"- **⚠️ Invalid/Generic Content:** {stats['urls_content_invalid']:,}/{urls_checked:,} ({100-content_pct:.1f}%)",
                file=output_file,
            )
            print("", file=output_file)


def print_federation_summary(federation_stats: dict, output_file=sys.stderr) -> None:
    """Print user-friendly federation-level statistics in markdown format."""
    if not federation_stats:
        print("No federation data available.", file=output_file)
        return

    print("\n## 🌍 Federation-Level Summary", file=output_file)
    print("", file=output_file)

    # Sort federations by total entities (descending)
    sorted_federations = sorted(
        federation_stats.items(), key=lambda x: x[1]["total_entities"], reverse=True
    )

    for federation, stats in sorted_federations:
        total = stats["total_entities"]
        total_sps = stats["total_sps"]
        total_idps = stats["total_idps"]

        if total == 0:
            continue

        # Federation name is already mapped from registration authority
        federation_name = federation

        print(f"### 📍 **{federation_name}**", file=output_file)

        # Entity overview in compact format
        print(
            f"- **Total Entities:** {total:,} ({total_sps:,} SPs, {total_idps:,} IdPs)",
            file=output_file,
        )

        # Privacy and Security stats in one line each
        if total_sps > 0:
            sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
            privacy_status = (
                "🟢" if sp_privacy_pct >= 80 else "🟡" if sp_privacy_pct >= 50 else "🔴"
            )
            print(
                f"- **SP Privacy Coverage:** {privacy_status} {stats['sps_has_privacy']:,}/{total_sps:,} ({sp_privacy_pct:.1f}%)",
                file=output_file,
            )

        # Security coverage (overall)
        total_security_pct = (stats["total_has_security"] / total) * 100
        security_status = (
            "🟢"
            if total_security_pct >= 80
            else "🟡"
            if total_security_pct >= 50
            else "🔴"
        )
        print(
            f"- **Security Contact Coverage:** {security_status} {stats['total_has_security']:,}/{total:,} ({total_security_pct:.1f}%)",
            file=output_file,
        )

        # Entity type breakdown for security (compact)
        if total_sps > 0 and total_idps > 0:
            sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
            idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
            sp_security_status = (
                "🟢" if sp_security_pct >= 80 else "🟡" if sp_security_pct >= 50 else "🔴"
            )
            idp_security_status = (
                "🟢"
                if idp_security_pct >= 80
                else "🟡"
                if idp_security_pct >= 50
                else "🔴"
            )
            print(
                f"  - SPs: {sp_security_status} {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%), IdPs: {idp_security_status} {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
                file=output_file,
            )
        elif total_sps > 0:
            sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
            sp_security_status = (
                "🟢" if sp_security_pct >= 80 else "🟡" if sp_security_pct >= 50 else "🔴"
            )
            print(
                f"  - SPs: {sp_security_status} {stats['sps_has_security']:,}/{total_sps:,} ({sp_security_pct:.1f}%)",
                file=output_file,
            )
        elif total_idps > 0:
            idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
            idp_security_status = (
                "🟢"
                if idp_security_pct >= 80
                else "🟡"
                if idp_security_pct >= 50
                else "🔴"
            )
            print(
                f"  - IdPs: {idp_security_status} {stats['idps_has_security']:,}/{total_idps:,} ({idp_security_pct:.1f}%)",
                file=output_file,
            )

        # Combined compliance for SPs (if any)
        if total_sps > 0:
            sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
            compliance_status = (
                "🟢" if sp_both_pct >= 80 else "🟡" if sp_both_pct >= 50 else "🔴"
            )
            print(
                f"- **SP Full Compliance:** {compliance_status} {stats['sps_has_both']:,}/{total_sps:,} ({sp_both_pct:.1f}%)",
                file=output_file,
            )

        # URL Validation Statistics (if any URLs were checked)
        urls_checked = stats.get("urls_checked", 0)
        if urls_checked > 0:
            accessibility_pct = (stats["urls_accessible"] / urls_checked) * 100
            content_pct = (stats["urls_content_valid"] / urls_checked) * 100

            accessibility_status = (
                "🟢"
                if accessibility_pct >= 90
                else "🟡"
                if accessibility_pct >= 70
                else "🔴"
            )
            content_status = (
                "🟢" if content_pct >= 80 else "🟡" if content_pct >= 60 else "🔴"
            )

            print(
                f"- **Privacy URL Quality:** {accessibility_status} {stats['urls_accessible']:,}/{urls_checked:,} accessible ({accessibility_pct:.1f}%), {content_status} {stats['urls_content_valid']:,}/{urls_checked:,} valid content ({content_pct:.1f}%)",
                file=output_file,
            )

        print("", file=output_file)


def export_federation_csv(federation_stats: dict, include_headers: bool = True) -> None:
    """Export federation statistics to CSV format."""
    writer = csv.writer(sys.stdout)

    # CSV headers - check if validation was enabled for any federation
    validation_enabled = any(
        fed_stats.get("urls_checked", 0) > 0 for fed_stats in federation_stats.values()
    )

    if include_headers:
        headers = [
            "Federation",
            "TotalEntities",
            "TotalSPs",
            "TotalIdPs",
            "SPsWithPrivacy",
            "SPsMissingPrivacy",
            "EntitiesWithSecurity",
            "EntitiesMissingSecurity",
            "SPsWithSecurity",
            "SPsMissingSecurity",
            "IdPsWithSecurity",
            "IdPsMissingSecurity",
            "SPsWithBoth",
            "SPsWithAtLeastOne",
            "SPsMissingBoth",
        ]

        if validation_enabled:
            headers.extend(
                [
                    "URLsChecked",
                    "URLsAccessible",
                    "URLsBroken",
                    "URLsContentValid",
                    "URLsContentInvalid",
                    "AccessibilityPercentage",
                    "ContentValidityPercentage",
                ]
            )

        writer.writerow(headers)

    # Sort federations by total entities (descending)
    sorted_federations = sorted(
        federation_stats.items(), key=lambda x: x[1]["total_entities"], reverse=True
    )

    for federation, stats in sorted_federations:
        total = stats["total_entities"]
        total_sps = stats["total_sps"]
        total_idps = stats["total_idps"]

        if total == 0:
            continue

        # Calculate percentages and missing counts
        # Privacy (SPs only)
        if total_sps > 0:
            sp_privacy_pct = (stats["sps_has_privacy"] / total_sps) * 100
            sp_missing_privacy = total_sps - stats["sps_has_privacy"]
            sp_missing_privacy_pct = (sp_missing_privacy / total_sps) * 100
        else:
            sp_privacy_pct = 0
            sp_missing_privacy = 0
            sp_missing_privacy_pct = 0

        # Security (all entities)
        total_security_pct = (stats["total_has_security"] / total) * 100
        total_missing_security = total - stats["total_has_security"]
        total_missing_security_pct = (total_missing_security / total) * 100

        # Security (SPs)
        if total_sps > 0:
            sp_security_pct = (stats["sps_has_security"] / total_sps) * 100
            sp_missing_security = total_sps - stats["sps_has_security"]
        else:
            sp_security_pct = 0
            sp_missing_security = 0

        # Security (IdPs)
        if total_idps > 0:
            idp_security_pct = (stats["idps_has_security"] / total_idps) * 100
            idp_missing_security = total_idps - stats["idps_has_security"]
        else:
            idp_security_pct = 0
            idp_missing_security = 0

        # Combined (SPs only)
        if total_sps > 0:
            sp_has_at_least_one = (
                stats["sps_has_privacy"]
                + stats["sps_has_security"]
                - stats["sps_has_both"]
            )
            sp_missing_both = total_sps - sp_has_at_least_one
            sp_both_pct = (stats["sps_has_both"] / total_sps) * 100
            sp_at_least_one_pct = (sp_has_at_least_one / total_sps) * 100
            sp_missing_both_pct = (sp_missing_both / total_sps) * 100
        else:
            sp_has_at_least_one = 0
            sp_missing_both = 0
            sp_both_pct = 0
            sp_at_least_one_pct = 0
            sp_missing_both_pct = 0

        # Prepare base row data
        row_data = [
            federation,
            total,
            total_sps,
            total_idps,
            stats["sps_has_privacy"],
            sp_missing_privacy,
            stats["total_has_security"],
            total_missing_security,
            stats["sps_has_security"],
            sp_missing_security,
            stats["idps_has_security"],
            idp_missing_security,
            stats["sps_has_both"],
            sp_has_at_least_one,
            sp_missing_both,
        ]

        # Add URL validation data if enabled
        if validation_enabled:
            urls_checked = stats.get("urls_checked", 0)
            urls_accessible = stats.get("urls_accessible", 0)
            urls_broken = stats.get("urls_broken", 0)
            urls_content_valid = stats.get("urls_content_valid", 0)
            urls_content_invalid = stats.get("urls_content_invalid", 0)

            accessibility_pct = (
                (urls_accessible / urls_checked * 100) if urls_checked > 0 else 0
            )
            content_pct = (
                (urls_content_valid / urls_checked * 100) if urls_checked > 0 else 0
            )

            row_data.extend(
                [
                    urls_checked,
                    urls_accessible,
                    urls_broken,
                    urls_content_valid,
                    urls_content_invalid,
                    f"{accessibility_pct:.1f}%",
                    f"{content_pct:.1f}%",
                ]
            )

        # Write row
        writer.writerow(row_data)


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for privacy statements and security contacts. Default: shows summary statistics. Use --list-* options for CSV exports. Use --help to see all options."
    )
    parser.add_argument(
        "--local-file", help="Use local XML file instead of downloading"
    )
    parser.add_argument(
        "--no-headers", action="store_true", help="Omit CSV headers from output"
    )
    parser.add_argument(
        "--url", default=EDUGAIN_METADATA_URL, help="Custom metadata URL"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary statistics (default behavior)",
    )
    parser.add_argument(
        "--federation-summary",
        action="store_true",
        help="Show per-federation breakdown with statistics",
    )
    parser.add_argument(
        "--federation-csv",
        action="store_true",
        help="Export federation statistics to CSV format",
    )
    parser.add_argument(
        "--validate-urls",
        action="store_true",
        help="Validate privacy statement URLs for accessibility and content (slower)",
    )
    parser.add_argument(
        "--validation-threads",
        type=int,
        default=URL_VALIDATION_THREADS,
        help=f"Number of parallel threads for URL validation (default: {URL_VALIDATION_THREADS})",
    )

    # Entity list options (mutually exclusive with summary options)
    entity_group = parser.add_mutually_exclusive_group()
    entity_group.add_argument(
        "--list-all-entities",
        action="store_true",
        help="Export CSV list of all entities with their privacy/security status",
    )
    entity_group.add_argument(
        "--list-missing-privacy",
        action="store_true",
        help="Export CSV list of entities without privacy statement URLs",
    )
    entity_group.add_argument(
        "--list-missing-security",
        action="store_true",
        help="Export CSV list of entities without security contacts",
    )
    entity_group.add_argument(
        "--list-missing-both",
        action="store_true",
        help="Export CSV list of entities missing both privacy statements and security contacts",
    )

    args = parser.parse_args()

    # Get metadata
    if args.local_file:
        root = parse_metadata(None, args.local_file)
    else:
        xml_content = get_metadata(args.url)
        root = parse_metadata(xml_content)

    # Get federation name mapping
    federation_mapping = get_federation_mapping()

    # Load URL validation cache if URL validation is enabled
    validation_cache = None
    if args.validate_urls:
        validation_cache = load_url_validation_cache() or {}
        if validation_cache:
            print(
                f"Loaded {len(validation_cache)} cached URL validation results",
                file=sys.stderr,
            )

    # Analyze entities
    entities_list, stats, federation_stats = analyze_privacy_security(
        root,
        federation_mapping,
        args.validate_urls,
        validation_cache,
        args.validation_threads,
    )

    # Save updated URL validation cache if validation was performed
    if args.validate_urls and validation_cache is not None:
        # The validation_cache was updated during analysis, so save it
        urls_validated = stats.get("urls_checked", 0)
        if urls_validated > 0:
            print(
                f"Saving URL validation cache with {len(validation_cache)} entries",
                file=sys.stderr,
            )
            save_url_validation_cache(validation_cache)

    # Handle federation CSV export
    if args.federation_csv:
        export_federation_csv(federation_stats, not args.no_headers)
        return

    # Print summary statistics (markdown format for federation summary, regular for summary-only)
    if args.federation_summary:
        print_summary_markdown(stats, output_file=sys.stdout)
        print_federation_summary(federation_stats, output_file=sys.stdout)
    else:
        print_summary(stats)

    # Handle entity list requests
    if args.list_all_entities:
        # Show all entities
        pass  # entities_list already contains all entities
    elif args.list_missing_privacy:
        entities_list = filter_entities(entities_list, "missing_privacy")
    elif args.list_missing_security:
        entities_list = filter_entities(entities_list, "missing_security")
    elif args.list_missing_both:
        entities_list = filter_entities(entities_list, "missing_both")
    else:
        # Default behavior: show only summary, no entity list
        return

    # Output CSV results
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        headers = [
            "Federation",
            "EntityType",
            "OrganizationName",
            "EntityID",
            "HasPrivacyStatement",
            "PrivacyStatementURL",
            "HasSecurityContact",
        ]

        # Add URL validation headers if validation was enabled
        if stats.get("validation_enabled", False):
            headers.extend(
                [
                    "URLStatusCode",
                    "URLAccessible",
                    "ContentValid",
                    "ValidationError",
                ]
            )

        writer.writerow(headers)
    writer.writerows(entities_list)


if __name__ == "__main__":
    main()
