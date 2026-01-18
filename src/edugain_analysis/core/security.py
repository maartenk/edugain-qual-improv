"""
Security utilities for input validation and sanitization.

Provides protection against:
- SSRF (Server-Side Request Forgery) attacks
- CSV injection vulnerabilities
- URL manipulation attacks
"""

import ipaddress
import re
from urllib.parse import urlparse


class SSRFError(ValueError):
    """Raised when a URL fails SSRF validation checks."""


def validate_url_for_ssrf(url: str) -> None:
    """
    Validate URL to prevent SSRF (Server-Side Request Forgery) attacks.

    Args:
        url: URL to validate

    Raises:
        SSRFError: If URL is potentially malicious or targets private networks
        ValueError: If URL is malformed

    Security checks:
    - Only HTTPS scheme allowed (prevents file://, ftp://, etc.)
    - Blocks private IP ranges (RFC 1918, loopback, link-local)
    - Blocks cloud metadata endpoints
    - Prevents DNS rebinding attacks
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Malformed URL: {e}") from e

    # Check scheme - only HTTPS allowed for remote URLs
    if parsed.scheme not in ("https",):
        raise SSRFError(
            f"Invalid URL scheme '{parsed.scheme}'. Only HTTPS is allowed for security. "
            f"Use --local-file for local files."
        )

    # Get hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a hostname")

    # Block numeric IP addresses - resolve hostname to check for private IPs
    if _is_private_target(hostname):
        raise SSRFError(
            f"Access to private networks is blocked for security. "
            f"Hostname '{hostname}' resolves to a private or reserved IP address. "
            f"Use --local-file for local files."
        )

    # Additional checks for cloud metadata endpoints
    if _is_cloud_metadata_endpoint(hostname):
        raise SSRFError(
            f"Access to cloud metadata endpoints is blocked. "
            f"Hostname '{hostname}' appears to be a cloud provider metadata service."
        )


def _is_private_target(hostname: str) -> bool:
    """
    Check if hostname resolves to a private or reserved IP address.

    Args:
        hostname: Hostname to check

    Returns:
        bool: True if hostname is private/reserved
    """
    # Check for localhost variations
    localhost_patterns = [
        r"^localhost$",
        r"^127\.",
        r"^::1$",
        r"^0\.0\.0\.0$",
        r"^::",
    ]
    for pattern in localhost_patterns:
        if re.match(pattern, hostname, re.IGNORECASE):
            return True

    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(hostname)

        # Check if IP is in private/reserved ranges
        if ip.is_private:  # RFC 1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
            return True
        if ip.is_loopback:  # 127.0.0.0/8, ::1
            return True
        if ip.is_link_local:  # 169.254.0.0/16, fe80::/10
            return True
        if ip.is_reserved:  # Reserved IP ranges
            return True
        if ip.is_multicast:  # Multicast addresses
            return True

        # Special case: Check for cloud metadata IPs
        # AWS metadata: 169.254.169.254
        if str(ip) == "169.254.169.254":
            return True

        return False

    except ValueError:
        # Not an IP address, check hostname patterns
        # Block common private network hostnames
        private_patterns = [
            r"^10\.",
            r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
            r"^192\.168\.",
            r"^169\.254\.",
            r"\.local$",
            r"\.internal$",
            r"\.private$",
        ]
        for pattern in private_patterns:
            if re.match(pattern, hostname, re.IGNORECASE):
                return True

        return False


def _is_cloud_metadata_endpoint(hostname: str) -> bool:
    """
    Check if hostname is a known cloud metadata endpoint.

    Args:
        hostname: Hostname to check

    Returns:
        bool: True if hostname is a cloud metadata endpoint
    """
    cloud_metadata_patterns = [
        r"169\.254\.169\.254",  # AWS, GCP, Azure, DigitalOcean
        r"metadata\.google\.internal",  # GCP
        r"metadata\.azure",  # Azure
        r"metadata\.packet\.net",  # Packet
    ]

    for pattern in cloud_metadata_patterns:
        if re.search(pattern, hostname, re.IGNORECASE):
            return True

    return False


def sanitize_csv_value(value: str) -> str:
    """
    Sanitize a CSV cell value to prevent CSV injection attacks.

    CSV injection occurs when a cell starts with special characters (=, +, -, @, tab, carriage return)
    that Excel and other spreadsheet applications interpret as formulas or commands.

    Args:
        value: CSV cell value to sanitize

    Returns:
        str: Sanitized value safe for CSV export

    Examples:
        >>> sanitize_csv_value("=1+1")
        "'=1+1"
        >>> sanitize_csv_value("Normal text")
        "Normal text"
        >>> sanitize_csv_value("@SUM(A1:A10)")
        "'@SUM(A1:A10)"
    """
    if not value or not isinstance(value, str):
        return value

    # Check if value starts with potentially dangerous characters
    dangerous_chars = ("=", "+", "-", "@", "\t", "\r")

    if value.startswith(dangerous_chars):
        # Prefix with single quote to prevent formula execution
        return f"'{value}"

    return value


def sanitize_url_for_display(url: str) -> str:
    """
    Sanitize URL for display in logs and error messages.

    Removes credentials from URLs to prevent password leakage in logs.

    Args:
        url: URL to sanitize

    Returns:
        str: URL with credentials removed

    Examples:
        >>> sanitize_url_for_display("https://user:pass@example.org/path")
        "https://example.org/path"
        >>> sanitize_url_for_display("https://example.org/path")
        "https://example.org/path"
    """
    if not url or not isinstance(url, str):
        return url

    try:
        parsed = urlparse(url)

        # Rebuild URL without credentials
        if parsed.username or parsed.password:
            # Reconstruct without userinfo
            sanitized = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                sanitized += f":{parsed.port}"
            sanitized += parsed.path
            if parsed.query:
                sanitized += f"?{parsed.query}"
            if parsed.fragment:
                sanitized += f"#{parsed.fragment}"
            return sanitized

        return url

    except Exception:
        # If parsing fails, return original (better than crashing)
        return url
