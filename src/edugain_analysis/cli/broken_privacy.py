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
import sys
from xml.etree import ElementTree as ET

from ..core import (
    get_federation_mapping as core_get_federation_mapping,
)
from ..core import (
    get_metadata,
)
from ..core.entities import iter_entity_records
from ..core.validation import validate_privacy_url, validate_urls_parallel
from .utils import run_csv_cli

# Configuration
EDUGAIN_METADATA_URL = "https://mds.edugain.org/edugain-v2.xml"
REQUEST_TIMEOUT = 30
VALIDATION_WORKERS = 10
HEADERS = [
    "Federation",
    "SP",
    "EntityID",
    "PrivacyLink",
    "ErrorCode",
    "ErrorType",
    "CheckedAt",
]


def download_metadata(url: str) -> bytes:
    """Wrapper around core.get_metadata for backwards compatibility."""
    try:
        return get_metadata(url, REQUEST_TIMEOUT)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error downloading metadata: {exc}", file=sys.stderr)
        sys.exit(1)


def get_federation_mapping() -> dict[str, str]:
    """Wrapper that delegates to core.get_federation_mapping."""
    try:
        return core_get_federation_mapping()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Warning: Could not fetch federation mapping: {exc}", file=sys.stderr)
        return {}


def validate_url(url: str) -> dict:
    """
    Backwards-compatible wrapper around core.validate_privacy_url.
    """
    result = validate_privacy_url(url, None, use_semaphore=False)
    result["error"] = result.get("error") or ""
    return result


def categorize_error(
    status_code: int, error_msg: str, validation_result: dict = None
) -> str:
    """Categorize error into actionable types."""
    # Check for bot protection first (only if still blocked - status >= 400)
    if (
        validation_result
        and validation_result.get("protection_detected")
        and status_code >= 400
    ):
        provider = validation_result["protection_detected"]
        retry_method = validation_result.get("retry_method")
        if retry_method:
            # Retry attempted but still blocked
            return f"{provider} (bypassed failed)"
        return f"{provider} Protection"

    # Check error messages
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

    # Check status codes
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

    for record in iter_entity_records(root):
        if not record.is_sp:
            continue

        if not record.registration_authority or not record.has_privacy:
            continue

        privacy_url = record.privacy_url.strip()
        if not privacy_url:
            continue

        sp_urls.append(
            (
                record.registration_authority,
                record.org_name,
                record.entity_id,
                privacy_url,
            )
        )

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
    unique_urls = list({url for _, _, _, url in sp_data})
    if not unique_urls:
        return {}

    validation_cache: dict[str, dict] = {}
    results = validate_urls_parallel(unique_urls, validation_cache, max_workers)
    return results


def analyze_broken_links(
    sp_data: list[tuple[str, str, str, str]],
    validation_results: dict[str, dict],
    federation_mapping: dict[str, str],
) -> tuple[list[list[str]], dict[str, int]]:
    """
    Identify SPs with broken privacy links.

    Returns:
        Tuple of (broken_links, error_breakdown)
        - broken_links: List of broken link records
        - error_breakdown: Dictionary mapping error types to counts
    """
    broken_links = []
    error_breakdown = {}

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
        error_type = categorize_error(status_code, error_msg, result)

        # Count error types
        error_breakdown[error_type] = error_breakdown.get(error_type, 0) + 1

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

    return broken_links, error_breakdown


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

    # argparse normally exits on -h/--help, but tests may patch sys.exit;
    # short circuit to avoid continuing into network work when help is requested.
    if any(flag in sys.argv[1:] for flag in ("-h", "--help")):
        parser.print_help()
        sys.exit(0)
        return

    args = parser.parse_args()

    def rows_factory(root: ET.Element) -> list[list[str]]:
        print("Fetching federation name mapping...", file=sys.stderr)
        federation_mapping = get_federation_mapping()
        print(f"Loaded {len(federation_mapping)} federation names", file=sys.stderr)

        print("Collecting SPs with privacy statement URLs...", file=sys.stderr)
        sp_data = collect_sp_privacy_urls(root)
        print(f"Found {len(sp_data)} SPs with privacy statement URLs", file=sys.stderr)

        if not sp_data:
            print("No SPs with privacy URLs found", file=sys.stderr)
            return []

        validation_results = validate_privacy_urls(sp_data, VALIDATION_WORKERS)

        print("Analyzing results for broken links...", file=sys.stderr)
        broken_links, error_breakdown = analyze_broken_links(
            sp_data, validation_results, federation_mapping
        )
        print(
            f"Found {len(broken_links)} SPs with broken privacy links",
            file=sys.stderr,
        )

        # Print error breakdown summary
        if error_breakdown:
            print("\nError Breakdown:", file=sys.stderr)
            for error_type in sorted(
                error_breakdown.keys(), key=lambda x: error_breakdown[x], reverse=True
            ):
                count = error_breakdown[error_type]
                percentage = (count / len(broken_links) * 100) if broken_links else 0
                print(f"  {error_type}: {count} ({percentage:.1f}%)", file=sys.stderr)
            print(file=sys.stderr)

        return broken_links

    run_csv_cli(
        rows_factory,
        HEADERS,
        local_file=args.local_file,
        url=None if args.local_file else args.url,
        default_url=EDUGAIN_METADATA_URL,
        timeout=REQUEST_TIMEOUT,
        include_headers=not args.no_headers,
        error_label="broken privacy analysis",
    )


if __name__ == "__main__":
    main()
