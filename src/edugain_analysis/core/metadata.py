"""
Metadata handling and caching module for eduGAIN analysis.

Provides functionality for:
- Downloading eduGAIN metadata with caching
- Parsing SAML metadata XML
- Managing federation name mappings
- URL validation cache management
- XDG-compliant cache utilities
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from ..config import (
    EDUGAIN_FEDERATIONS_API,
    EDUGAIN_METADATA_URL,
    FEDERATION_CACHE_DAYS,
    FEDERATION_CACHE_FILE,
    METADATA_CACHE_FILE,
    METADATA_CACHE_HOURS,
    REQUEST_TIMEOUT,
    URL_VALIDATION_CACHE_DAYS,
    URL_VALIDATION_CACHE_FILE,
)

# XDG-compliant cache management utilities (merged from utils/cache.py)
try:
    from platformdirs import user_cache_dir
except ImportError:
    # Fallback if platformdirs not available
    def user_cache_dir(app_name: str, app_author: str) -> str:
        """Fallback cache directory implementation."""
        home = Path.home()
        if os.name == "nt":  # Windows
            cache_dir = home / "AppData" / "Local" / app_author / app_name / "Cache"
        elif os.name == "posix":
            if "darwin" in os.uname().sysname.lower():  # macOS
                cache_dir = home / "Library" / "Caches" / app_name
            else:  # Linux
                cache_dir = home / ".cache" / app_name
        else:
            cache_dir = home / ".cache" / app_name
        return str(cache_dir)


def get_cache_dir() -> Path:
    """Get XDG-compliant cache directory for eduGAIN analysis."""
    cache_dir = Path(user_cache_dir("edugain-analysis", "edugain"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cache_file(filename: str) -> Path:
    """Get path to cache file in XDG-compliant directory."""
    return get_cache_dir() / filename


def load_json_cache(filename: str, max_age_hours: int = 24) -> dict[str, Any] | None:
    """Load JSON cache file if it exists and is not too old."""
    cache_file = get_cache_file(filename)

    if not cache_file.exists():
        return None

    # Check if cache is too old
    file_age = time.time() - cache_file.stat().st_mtime
    if file_age > max_age_hours * 3600:
        return None

    try:
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_json_cache(filename: str, data: dict[str, Any]) -> None:
    """Save data to JSON cache file."""
    cache_file = get_cache_file(filename)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # Silently fail if unable to write cache


def load_text_cache(filename: str, max_age_hours: int = 24) -> str | None:
    """Load text cache file if it exists and is not too old."""
    cache_file = get_cache_file(filename)

    if not cache_file.exists():
        return None

    # Check if cache is too old
    file_age = time.time() - cache_file.stat().st_mtime
    if file_age > max_age_hours * 3600:
        return None

    try:
        with open(cache_file, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def save_text_cache(filename: str, content: str) -> None:
    """Save text content to cache file."""
    cache_file = get_cache_file(filename)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError:
        pass  # Silently fail if unable to write cache


def is_metadata_cache_valid() -> bool:
    """
    Check if the metadata cache file exists and is still valid.

    Returns:
        bool: True if cache exists and is within expiry time
    """
    cache_file = get_cache_file(METADATA_CACHE_FILE)
    if not cache_file.exists():
        return False

    try:
        # Check file modification time
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(hours=METADATA_CACHE_HOURS)
        return file_time > expiry_time
    except (OSError, ValueError):
        return False


def download_metadata(url: str, timeout: int = REQUEST_TIMEOUT) -> bytes:
    """
    Download metadata from URL with proper error handling.

    Args:
        url: Metadata URL to download from
        timeout: Request timeout in seconds

    Returns:
        bytes: Raw metadata content

    Raises:
        requests.RequestException: If download fails
    """
    print(f"Downloading metadata from {url}...", file=sys.stderr)

    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "eduGAIN-Quality-Analysis/2.0 (Metadata fetcher)",
            "Accept": "application/xml, text/xml, */*",
        },
    )
    response.raise_for_status()

    print(f"Downloaded {len(response.content):,} bytes", file=sys.stderr)
    return response.content


def save_metadata_cache(content: bytes) -> None:
    """
    Save metadata content to cache file.

    Args:
        content: Raw metadata content to save
    """
    cache_file = get_cache_file(METADATA_CACHE_FILE)
    try:
        with open(cache_file, "wb") as f:
            f.write(content)
        print(f"Metadata cached to {cache_file}", file=sys.stderr)
    except OSError as e:
        print(f"Warning: Could not save metadata cache: {e}", file=sys.stderr)


def load_metadata_cache() -> bytes | None:
    """
    Load metadata from cache file if it exists and is valid.

    Returns:
        Optional[bytes]: Cached metadata content or None if not available
    """
    if not is_metadata_cache_valid():
        return None

    cache_file = get_cache_file(METADATA_CACHE_FILE)
    try:
        with open(cache_file, "rb") as f:
            content = f.read()
        print(f"Using cached metadata from {cache_file}", file=sys.stderr)
        return content
    except OSError as e:
        print(f"Warning: Could not load metadata cache: {e}", file=sys.stderr)
        return None


def get_metadata(
    url: str = EDUGAIN_METADATA_URL, timeout: int = REQUEST_TIMEOUT
) -> bytes:
    """
    Get eduGAIN metadata with intelligent caching.

    Args:
        url: Metadata URL (defaults to eduGAIN metadata endpoint)
        timeout: Request timeout in seconds

    Returns:
        bytes: Raw metadata content
    """
    # Try to load from cache first
    cached_content = load_metadata_cache()
    if cached_content:
        return cached_content

    # Download fresh metadata
    content = download_metadata(url, timeout)

    # Save to cache
    save_metadata_cache(content)

    return content


def parse_metadata(
    content: bytes | None = None, local_file: str | None = None
) -> ET.Element:
    """
    Parse eduGAIN metadata XML content or local file.

    Args:
        content: Raw XML content (optional)
        local_file: Path to local XML file (optional)

    Returns:
        ET.Element: Root element of parsed XML

    Raises:
        ET.ParseError: If XML parsing fails
        FileNotFoundError: If local file doesn't exist
    """
    if local_file:
        print(f"Parsing local metadata file: {local_file}", file=sys.stderr)
        try:
            tree = ET.parse(local_file)
            return tree.getroot()
        except FileNotFoundError:
            raise FileNotFoundError(f"Local metadata file not found: {local_file}")
        except ET.ParseError as e:
            raise ET.ParseError(f"Failed to parse local metadata file: {e}")

    elif content:
        print("Parsing metadata content...", file=sys.stderr)
        try:
            return ET.fromstring(content)
        except ET.ParseError as e:
            raise ET.ParseError(f"Failed to parse metadata content: {e}")

    else:
        raise ValueError("Either content or local_file must be provided")


def load_federation_cache() -> dict[str, str] | None:
    """
    Load federation name mappings from cache.

    Returns:
        Optional[Dict[str, str]]: Cached federation mappings or None
    """
    cache_file = get_cache_file(FEDERATION_CACHE_FILE)
    if not cache_file.exists():
        return None

    try:
        # Check if cache is still valid
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(days=FEDERATION_CACHE_DAYS)

        if file_time <= expiry_time:
            print("Federation cache expired, will refresh", file=sys.stderr)
            return None

        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)

        print(f"Loaded {len(data)} federation mappings from cache", file=sys.stderr)
        return data

    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Could not load federation cache: {e}", file=sys.stderr)
        return None


def save_federation_cache(federations: dict[str, str]) -> None:
    """
    Save federation name mappings to cache.

    Args:
        federations: Dictionary mapping registration authorities to federation names
    """
    cache_file = get_cache_file(FEDERATION_CACHE_FILE)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(federations, f, indent=2, ensure_ascii=False)
        print(f"Federation mappings cached to {cache_file}", file=sys.stderr)
    except OSError as e:
        print(f"Warning: Could not save federation cache: {e}", file=sys.stderr)


def fetch_federation_names() -> dict[str, str]:
    """
    Fetch federation names from eduGAIN API.

    Returns:
        Dict[str, str]: Mapping of registration authorities to federation names
    """
    print(
        f"Fetching federation names from {EDUGAIN_FEDERATIONS_API}...", file=sys.stderr
    )

    try:
        response = requests.get(
            EDUGAIN_FEDERATIONS_API,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "eduGAIN-Quality-Analysis/2.0 (Federation fetcher)",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        federations_data = response.json()
        federation_mapping = {}

        # API returns a dict with federation short names as keys
        for federation_key, federation_data in federations_data.items():
            reg_auth = federation_data.get("reg_auth")
            name = federation_data.get("name")
            if reg_auth and name:
                federation_mapping[reg_auth] = name

        print(f"Fetched {len(federation_mapping)} federation mappings", file=sys.stderr)
        return federation_mapping

    except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Failed to fetch federation names: {e}", file=sys.stderr)
        return {}


def get_federation_mapping() -> dict[str, str]:
    """
    Get federation name mappings with intelligent caching.

    Returns:
        Dict[str, str]: Mapping of registration authorities to federation names
    """
    # Try to load from cache first
    cached_federations = load_federation_cache()
    if cached_federations:
        return cached_federations

    # Fetch fresh federation data
    federations = fetch_federation_names()

    # Save to cache if we got data
    if federations:
        save_federation_cache(federations)

    return federations


def map_registration_authority(
    registration_authority: str, federation_mapping: dict[str, str]
) -> str:
    """
    Map registration authority URL to friendly federation name.

    Args:
        registration_authority: Registration authority URL
        federation_mapping: Mapping of authorities to names

    Returns:
        str: Federation name or original authority if not found
    """
    if not registration_authority:
        return "Unknown"

    # Try direct lookup first
    if registration_authority in federation_mapping:
        return federation_mapping[registration_authority]

    # If not found, return the registration authority as-is
    return registration_authority


def load_url_validation_cache() -> dict[str, dict] | None:
    """
    Load URL validation results from cache.

    Returns:
        Optional[Dict[str, Dict]]: Cached validation results or None
    """
    cache_file = get_cache_file(URL_VALIDATION_CACHE_FILE)
    if not cache_file.exists():
        return None

    try:
        # Check if cache is still valid
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        expiry_time = datetime.now() - timedelta(days=URL_VALIDATION_CACHE_DAYS)

        if file_time <= expiry_time:
            print("URL validation cache expired, will refresh", file=sys.stderr)
            return None

        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)

        return data

    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Could not load URL validation cache: {e}", file=sys.stderr)
        return None


def save_url_validation_cache(validations: dict[str, dict]) -> None:
    """
    Save URL validation results to cache.

    Args:
        validations: Dictionary mapping URLs to validation results
    """
    cache_file = get_cache_file(URL_VALIDATION_CACHE_FILE)
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(validations, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Warning: Could not save URL validation cache: {e}", file=sys.stderr)
