"""
eduGAIN Broken Privacy Links Analysis Tool

Self-contained script that downloads eduGAIN metadata and validates privacy statement URLs
for all Service Providers. Always performs live validation with 10 parallel workers.

Output: CSV format with columns: Federation, SP, EntityID, PrivacyLink, ErrorCode, ErrorType, CheckedAt

Usage:
    edugain-broken-privacy                    # Download and analyze current metadata
    edugain-broken-privacy --local-file file  # Analyze local XML file
    edugain-broken-privacy --no-headers       # Omit CSV headers
    edugain-broken-privacy --url URL          # Use custom metadata URL

Based on the code of https://gitlab.geant.org/edugain/edugain-contacts
"""

import argparse
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from xml.etree import ElementTree as ET

import requests

# Configuration
EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
FEDERATION_API_URL = "https://technical.edugain.org/api.php?action=list_feds"
REQUEST_TIMEOUT = 30
VALIDATION_WORKERS = 10

# SAML metadata namespaces
NAMESPACES = {
    "md": "urn:oasis:names:tc:SAML:2.0:metadata",
    "mdui": "urn:oasis:names:tc:SAML:metadata:ui",
    "mdrpi": "urn:oasis:names:tc:SAML:metadata:rpi",
}


def download_metadata(url: str) -> bytes:
    """Download eduGAIN metadata from the specified URL."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading metadata: {e}", file=sys.stderr)
        sys.exit(1)


def get_federation_mapping() -> dict[str, str]:
    """Fetch federation name mapping from eduGAIN API."""
    try:
        response = requests.get(
            FEDERATION_API_URL,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "eduGAIN-Privacy-Checker/1.0",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        federations_data = response.json()

        # API returns dict with federation keys, each value has "reg_auth" and "name"
        federation_mapping = {}
        for federation_data in federations_data.values():
            reg_auth = federation_data.get("reg_auth")
            name = federation_data.get("name")
            if reg_auth and name:
                federation_mapping[reg_auth] = name

        return federation_mapping
    except Exception as e:
        print(f"Warning: Could not fetch federation mapping: {e}", file=sys.stderr)
        return {}


def validate_url(url: str) -> dict:
    """
    Validate a single URL by making an HTTP request.

    Returns dict with: status_code, accessible, error, checked_at
    """
    result = {
        "status_code": 0,
        "accessible": False,
        "error": "",
        "checked_at": datetime.now(UTC).isoformat(),
    }

    try:
        response = requests.head(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "eduGAIN-Privacy-Checker/1.0"},
        )
        result["status_code"] = response.status_code
        result["accessible"] = 200 <= response.status_code < 400
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {str(e)}"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {str(e)}"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.TooManyRedirects:
        result["error"] = "Too many redirects"
    except Exception as e:
        result["error"] = str(e)

    return result


def categorize_error(status_code: int, error_msg: str) -> str:
    """Categorize error into actionable types."""
    if error_msg:
        error_lower = error_msg.lower()
        if "ssl" in error_lower or "certificate" in error_lower:
            return "SSL Certificate Error"
        if "connection" in error_lower or "dns" in error_lower:
            return "Connection Error"
        if "timeout" in error_lower:
            return "Timeout"
        if "redirect" in error_lower:
            return "Too Many Redirects"
        return f"Error: {error_msg}"

    if status_code == 0:
        return "Unknown Error"
    elif status_code == 404:
        return "Not Found (4xx)"
    elif status_code == 403:
        return "Forbidden (4xx)"
    elif status_code == 401:
        return "Unauthorized (4xx)"
    elif status_code == 410:
        return "Gone Permanently (4xx)"
    elif 400 <= status_code < 500:
        return f"Client Error {status_code} (4xx)"
    elif status_code >= 500:
        return f"Server Error {status_code} (5xx)"
    else:
        return f"Unexpected Status {status_code}"


def collect_sp_privacy_urls(root: ET.Element) -> list[tuple[str, str, str, str]]:
    """
    Collect all SPs with privacy statement URLs.

    Returns list of (registration_authority, org_name, entity_id, privacy_url)
    """
    sp_urls = []

    for entity in root.findall("./md:EntityDescriptor", NAMESPACES):
        entity_id = entity.attrib.get("entityID")
        if not entity_id:
            continue

        # Only SPs
        if entity.find("./md:SPSSODescriptor", NAMESPACES) is None:
            continue

        # Get privacy statement URL
        privacy_elem = entity.find(".//mdui:PrivacyStatementURL", NAMESPACES)
        if privacy_elem is None or not privacy_elem.text:
            continue

        privacy_url = privacy_elem.text.strip()
        if not privacy_url:
            continue

        # Get registration authority
        reg_info = entity.find("./md:Extensions/mdrpi:RegistrationInfo", NAMESPACES)
        if reg_info is None:
            continue

        reg_authority = reg_info.attrib.get("registrationAuthority", "").strip()
        if not reg_authority:
            continue

        # Get organization name
        org_elem = entity.find(
            "./md:Organization/md:OrganizationDisplayName", NAMESPACES
        )
        org_name = (
            org_elem.text.strip()
            if org_elem is not None and org_elem.text
            else "Unknown"
        )

        sp_urls.append((reg_authority, org_name, entity_id, privacy_url))

    return sp_urls


def validate_privacy_urls(
    sp_data: list[tuple[str, str, str, str]], max_workers: int
) -> dict[str, dict]:
    """
    Validate privacy URLs in parallel.

    Args:
        sp_data: List of (reg_authority, org_name, entity_id, privacy_url)
        max_workers: Number of parallel workers

    Returns:
        Dict mapping URL -> validation_result
    """
    # Extract unique URLs
    unique_urls = list({url for _, _, _, url in sp_data})

    print(
        f"Validating {len(unique_urls)} unique privacy URLs with {max_workers} workers...",
        file=sys.stderr,
    )

    validation_results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all validation tasks
        future_to_url = {executor.submit(validate_url, url): url for url in unique_urls}

        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                validation_results[url] = result
                completed += 1
                if completed % 50 == 0:
                    print(
                        f"  Progress: {completed}/{len(unique_urls)}", file=sys.stderr
                    )
            except Exception as e:
                print(f"  Error validating {url}: {e}", file=sys.stderr)
                validation_results[url] = {
                    "status_code": 0,
                    "accessible": False,
                    "error": str(e),
                    "checked_at": datetime.now(UTC).isoformat(),
                }

    print(
        f"Validation complete: {completed}/{len(unique_urls)} URLs checked",
        file=sys.stderr,
    )
    return validation_results


def analyze_broken_links(
    sp_data: list[tuple[str, str, str, str]],
    validation_results: dict[str, dict],
    federation_mapping: dict[str, str],
) -> list[list[str]]:
    """Identify SPs with broken privacy links."""
    broken_links = []

    for reg_authority, org_name, entity_id, privacy_url in sp_data:
        # Get validation result
        if privacy_url not in validation_results:
            continue

        result = validation_results[privacy_url]

        # Check if broken
        is_broken = not result.get("accessible", False)
        error_msg = result.get("error", "")

        if not is_broken and not error_msg:
            continue

        # Map to federation name
        federation_name = federation_mapping.get(reg_authority, reg_authority)

        # Format error code
        status_code = result.get("status_code", 0)
        error_code = str(status_code) if status_code else (error_msg or "Unknown error")

        # Categorize error
        error_type = categorize_error(status_code, error_msg)

        # Get timestamp
        checked_at = result.get("checked_at", "Unknown")

        broken_links.append(
            [
                federation_name,
                org_name,
                entity_id,
                privacy_url,
                error_code,
                error_type,
                checked_at,
            ]
        )

    return broken_links


def main() -> None:
    """Main function to orchestrate the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze eduGAIN metadata for SPs with broken privacy statement URLs (always runs live validation)"
    )
    parser.add_argument(
        "--local-file", help="Use local XML file instead of downloading metadata"
    )
    parser.add_argument(
        "--no-headers", action="store_true", help="Omit CSV headers from output"
    )
    parser.add_argument(
        "--url",
        default=EDUGAIN_METADATA_URL,
        help="Custom metadata URL (default: eduGAIN aggregate)",
    )
    args = parser.parse_args()

    # Get federation mapping
    print("Fetching federation name mapping...", file=sys.stderr)
    federation_mapping = get_federation_mapping()
    print(f"Loaded {len(federation_mapping)} federation names", file=sys.stderr)

    # Get metadata
    root: ET.Element | None = None
    if args.local_file:
        print(f"Parsing local metadata: {args.local_file}", file=sys.stderr)
        try:
            root = ET.parse(args.local_file).getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
            sys.exit(1)
            return
    else:
        print(f"Downloading metadata from {args.url}...", file=sys.stderr)
        xml_content = download_metadata(args.url)
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
            sys.exit(1)
            return

    if root is None:
        return

    # Collect SPs with privacy URLs
    print("Collecting SPs with privacy statement URLs...", file=sys.stderr)
    sp_data = collect_sp_privacy_urls(root)
    print(f"Found {len(sp_data)} SPs with privacy statement URLs", file=sys.stderr)

    if not sp_data:
        print("No SPs with privacy URLs found", file=sys.stderr)
        sys.exit(0)

    # Validate URLs in parallel
    validation_results = validate_privacy_urls(sp_data, VALIDATION_WORKERS)

    # Analyze for broken links
    print("Analyzing results for broken links...", file=sys.stderr)
    broken_links = analyze_broken_links(sp_data, validation_results, federation_mapping)
    print(f"Found {len(broken_links)} SPs with broken privacy links", file=sys.stderr)

    # Output CSV
    writer = csv.writer(sys.stdout)
    if not args.no_headers:
        writer.writerow(
            [
                "Federation",
                "SP",
                "EntityID",
                "PrivacyLink",
                "ErrorCode",
                "ErrorType",
                "CheckedAt",
            ]
        )
    writer.writerows(broken_links)


if __name__ == "__main__":
    main()
