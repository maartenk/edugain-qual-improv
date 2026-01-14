"""
URL validation module for privacy statement analysis.

Provides HTTP accessibility validation of privacy statement URLs.
"""

import os
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse

import certifi
import cloudscraper
import requests

from ..config import (
    CLOUDSCRAPER_RETRY_DELAY,
    CLOUDSCRAPER_TIMEOUT,
    ENABLE_CLOUDSCRAPER_RETRY,
    PROVIDER_RETRY_DELAYS,
    URL_VALIDATION_DELAY,
    URL_VALIDATION_THREADS,
    URL_VALIDATION_TIMEOUT,
)

GET_FALLBACK_STATUS_CODES = {301, 302, 303, 307, 308, 403, 405}

# Global rate limiting semaphore
_url_validation_semaphore = None

# Global CA bundle path (cached)
_ca_bundle_path = None


def _get_ca_bundle_path() -> str:
    """
    Get the best CA bundle path for SSL verification.

    Tries system certificate stores first (which may have more up-to-date
    certificates), then falls back to certifi bundle.

    Returns:
        Path to CA bundle file to use for SSL verification
    """
    global _ca_bundle_path

    if _ca_bundle_path is not None:
        return _ca_bundle_path

    # Try system certificate stores (often more up-to-date)
    system_cert_paths = [
        "/etc/ssl/cert.pem",  # macOS
        "/etc/ssl/certs/ca-certificates.crt",  # Debian/Ubuntu/Gentoo
        "/etc/pki/tls/certs/ca-bundle.crt",  # Fedora/RHEL
        "/etc/ssl/certs/ca-bundle.crt",  # OpenSUSE
        "/usr/local/etc/openssl/cert.pem",  # Homebrew OpenSSL
    ]

    for cert_path in system_cert_paths:
        if os.path.exists(cert_path):
            _ca_bundle_path = cert_path
            return _ca_bundle_path

    # Fall back to certifi bundle
    _ca_bundle_path = certifi.where()
    return _ca_bundle_path


def _get_url_validation_semaphore(
    max_concurrent: int = URL_VALIDATION_THREADS,
) -> threading.Semaphore:
    """Get or create the global semaphore for URL validation rate limiting."""
    global _url_validation_semaphore
    if _url_validation_semaphore is None:
        _url_validation_semaphore = threading.Semaphore(max_concurrent)
    return _url_validation_semaphore


def _detect_bot_protection(response) -> tuple[str | None, dict]:
    """
    Detect bot protection services from response headers.

    Args:
        response: requests.Response object

    Returns:
        Tuple of (provider_name, protection_headers)
        provider_name is None if no protection detected
    """
    headers = {k.lower(): v for k, v in response.headers.items()}
    protection_headers = {}

    # Cloudflare detection
    if "cf-ray" in headers or "cf-mitigated" in headers:
        if "cf-ray" in headers:
            protection_headers["cf-ray"] = headers["cf-ray"]
        if "cf-mitigated" in headers:
            protection_headers["cf-mitigated"] = headers["cf-mitigated"]
        if headers.get("server", "").lower() == "cloudflare":
            protection_headers["server"] = "cloudflare"

        # Only return Cloudflare if we have a 403 or challenge indicator
        if response.status_code == 403 or "cf-mitigated" in headers:
            return "Cloudflare", protection_headers

    # AWS Shield/WAF detection
    if any(k.startswith("x-amzn") for k in headers):
        for key in headers:
            if key.startswith("x-amzn"):
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "AWS WAF", protection_headers

    # Akamai Bot Manager detection
    server = headers.get("server", "")
    if server.lower() == "akamaighost" or any(
        k.startswith(("akamai", "x-akamai")) for k in headers
    ):
        if server.lower() == "akamaighost":
            protection_headers["server"] = server
        for key in headers:
            if "akamai" in key:
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "Akamai", protection_headers

    # Imperva/Incapsula detection
    if "x-cdn" in headers and "incapsula" in headers["x-cdn"].lower():
        protection_headers["x-cdn"] = headers["x-cdn"]
        if response.status_code == 403:
            return "Imperva", protection_headers

    if any(k.startswith("incap") for k in headers):
        for key in headers:
            if key.startswith("incap"):
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "Imperva", protection_headers

    # DataDome detection
    if any(k.startswith("x-datadome") for k in headers):
        for key in headers:
            if "datadome" in key:
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "DataDome", protection_headers

    # PerimeterX detection
    if any(k.startswith("x-px") for k in headers):
        for key in headers:
            if key.startswith("x-px"):
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "PerimeterX", protection_headers

    # Fastly detection
    if "x-served-by" in headers and "cache-" in headers["x-served-by"]:
        protection_headers["x-served-by"] = headers["x-served-by"]
        if response.status_code == 403:
            return "Fastly", protection_headers

    # Sucuri detection
    if any(k.startswith("x-sucuri") for k in headers):
        for key in headers:
            if "sucuri" in key:
                protection_headers[key] = headers[key]
        if response.status_code == 403:
            return "Sucuri", protection_headers

    # CloudFront detection
    server_lower = headers.get("server", "").lower()
    if "cloudfront" in server_lower:
        protection_headers["server"] = headers.get("server", "")
        if "x-cache" in headers:
            protection_headers["x-cache"] = headers["x-cache"]
        if "x-amz-cf-id" in headers:
            protection_headers["x-amz-cf-id"] = headers["x-amz-cf-id"]
        if response.status_code == 403:
            return "CloudFront", protection_headers

    # AWS ELB detection
    if "awselb" in server_lower:
        protection_headers["server"] = headers.get("server", "")
        if response.status_code == 403:
            return "AWS ELB", protection_headers

    # Generic WAF/CDN detection (403 with certain server headers)
    if response.status_code == 403:
        if any(
            keyword in server_lower
            for keyword in ["waf", "firewall", "protection", "security"]
        ):
            protection_headers["server"] = server_lower
            return "WAF/CDN", protection_headers

    return None, protection_headers


def _detect_bot_protection_from_body(body_snippet: str, status_code: int) -> str | None:
    """
    Detect bot protection from response body content.

    Only called for 403/429 responses without header-based detection.
    Analyzes first 2KB of response body for provider signatures.

    Args:
        body_snippet: First 2KB of response body
        status_code: HTTP status code

    Returns:
        Provider name if detected, None otherwise
    """
    if status_code not in [403, 429]:
        return None

    body_lower = body_snippet.lower()

    # CloudFront
    if "generated by cloudfront" in body_lower or "cloudfront.net" in body_lower:
        return "CloudFront"

    # Akamai
    if "errors.edgesuite.net" in body_lower or "akamai reference" in body_lower:
        return "Akamai"

    # Cloudflare
    if "cloudflare ray id" in body_lower or "cf-ray" in body_lower:
        return "Cloudflare"

    # Imperva/Incapsula
    if "incapsula incident" in body_lower or "impervawaf" in body_lower:
        return "Imperva"

    # AWS WAF
    if "aws waf" in body_lower or "awswaf" in body_lower:
        return "AWS WAF"

    return None


def _retry_with_cloudscraper(
    url: str, ca_bundle: str, provider: str | None = None
) -> tuple[int, str, int, str | None, dict]:
    """
    Retry URL validation using cloudscraper to bypass bot protection.

    Args:
        url: URL to validate
        ca_bundle: CA bundle path for SSL verification
        provider: Detected protection provider (for delay customization)

    Returns:
        Tuple of (status_code, final_url, redirect_count, protection_detected, protection_headers)
    """
    try:
        # Add delay before retry (provider-specific if available)
        delay = PROVIDER_RETRY_DELAYS.get(provider, CLOUDSCRAPER_RETRY_DELAY)
        time.sleep(delay)

        # Create cloudscraper session
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

        # Try GET request with cloudscraper
        response = scraper.get(
            url, timeout=CLOUDSCRAPER_TIMEOUT, allow_redirects=True, verify=ca_bundle
        )

        status_code = response.status_code
        final_url = response.url
        redirect_count = len(response.history)

        # Check if protection is still detected after cloudscraper
        protection_detected, protection_headers = _detect_bot_protection(response)

        response.close()
        return (
            status_code,
            final_url,
            redirect_count,
            protection_detected,
            protection_headers,
        )

    except Exception as e:
        # If cloudscraper fails, return error indicators
        return 0, url, 0, None, {}


def validate_privacy_url(
    url: str, validation_cache: dict[str, dict] = None, use_semaphore: bool = True
) -> dict:
    """
    Simple validation of privacy statement URL for basic accessibility.

    Args:
        url: Privacy statement URL to validate
        validation_cache: Cache of previous validation results
        use_semaphore: Whether to use rate limiting semaphore

    Returns:
        Dict with validation results including status code and accessibility
    """
    if not url or not url.strip():
        return {
            "status_code": 0,
            "final_url": "",
            "accessible": False,
            "redirect_count": 0,
            "error": "Empty URL",
            "checked_at": datetime.now().isoformat(),
            "protection_detected": None,
            "protection_headers": {},
            "retry_method": None,
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
                "final_url": url,
                "accessible": False,
                "redirect_count": 0,
                "error": "Invalid URL format",
                "checked_at": datetime.now().isoformat(),
                "protection_detected": None,
                "protection_headers": {},
                "retry_method": None,
            }
    except Exception as e:
        if semaphore is not None:
            semaphore.release()
        return {
            "status_code": 0,
            "final_url": url,
            "accessible": False,
            "redirect_count": 0,
            "error": f"URL parsing error: {str(e)}",
            "checked_at": datetime.now().isoformat(),
            "protection_detected": None,
            "protection_headers": {},
            "retry_method": None,
        }

    # Rate limiting
    time.sleep(URL_VALIDATION_DELAY)

    try:
        headers = {
            "User-Agent": "eduGAIN-Quality-Analysis/2.0 (URL validation bot)",
        }

        # Get the best CA bundle path for SSL verification
        ca_bundle = _get_ca_bundle_path()

        # Simple HTTP HEAD request to check accessibility
        response = requests.head(
            url,
            timeout=URL_VALIDATION_TIMEOUT,
            headers=headers,
            allow_redirects=True,
            verify=ca_bundle,
        )

        # Some sites block HEAD; fallback to lightweight GET in those cases
        if response.status_code in GET_FALLBACK_STATUS_CODES:
            response.close()
            response = requests.get(
                url,
                timeout=URL_VALIDATION_TIMEOUT,
                headers=headers,
                allow_redirects=True,
                stream=True,
                verify=ca_bundle,
            )

        status_code = response.status_code
        final_url = response.url
        redirect_count = len(response.history)

        # Detect bot protection services from headers
        protection_detected, protection_headers = _detect_bot_protection(response)

        # If no protection detected from headers, try body detection for 403/429
        if not protection_detected and status_code in [403, 429]:
            try:
                # Read first 2KB of response body for analysis
                body_snippet = ""
                if hasattr(response, "raw") and response.raw:
                    body_snippet = response.raw.read(2048).decode(
                        "utf-8", errors="ignore"
                    )
                elif hasattr(response, "content"):
                    body_snippet = response.content[:2048].decode(
                        "utf-8", errors="ignore"
                    )

                if body_snippet:
                    body_detected_provider = _detect_bot_protection_from_body(
                        body_snippet, status_code
                    )
                    if body_detected_provider:
                        protection_detected = body_detected_provider
                        protection_headers["detected_from"] = "response_body"
            except Exception:  # noqa: S110
                # Body detection is optional - if it fails (encoding issues, etc),
                # continue with header-based detection only
                pass

        response.close()

        # Retry with cloudscraper if bot protection detected or forbidden/rate-limited
        retry_method = None
        if ENABLE_CLOUDSCRAPER_RETRY and status_code in [403, 429]:
            retry_method = "cloudscraper"
            (
                status_code,
                final_url,
                redirect_count,
                protection_detected,
                protection_headers,
            ) = _retry_with_cloudscraper(url, ca_bundle, protection_detected)

        # Simple status code validation:
        # 200-299: Success (accessible)
        # 300-399: Redirects (accessible)
        # 400-499: Client errors (not accessible)
        # 500-599: Server errors (not accessible)
        accessible = 200 <= status_code < 400

        result = {
            "status_code": status_code,
            "final_url": final_url,
            "accessible": accessible,
            "redirect_count": redirect_count,
            "error": None,
            "checked_at": datetime.now().isoformat(),
            "protection_detected": protection_detected,
            "protection_headers": protection_headers if protection_detected else {},
            "retry_method": retry_method,
        }

        # Add result to cache
        if validation_cache is not None:
            validation_cache[url] = result

        return result

    except requests.exceptions.TooManyRedirects:
        result = _create_error_result(url, "Too many redirects")
    except requests.exceptions.Timeout:
        result = _create_error_result(url, "Request timeout")
    except requests.exceptions.SSLError:
        result = _create_error_result(url, "SSL certificate error")
    except requests.exceptions.ConnectionError:
        result = _create_error_result(url, "Connection error")
    except requests.exceptions.RequestException as e:
        result = _create_error_result(url, f"Request error: {str(e)}")
    except Exception as e:
        result = _create_error_result(url, f"Unexpected error: {str(e)}")
    finally:
        # Always release semaphore if acquired
        if semaphore is not None:
            semaphore.release()

    if validation_cache is not None:
        validation_cache[url] = result
    return result


def _create_error_result(url: str, error: str) -> dict:
    """Create a standardized error result dictionary."""
    return {
        "status_code": 0,
        "final_url": url,
        "accessible": False,
        "redirect_count": 0,
        "error": error,
        "checked_at": datetime.now().isoformat(),
        "protection_detected": None,
        "protection_headers": {},
        "retry_method": None,
    }


def validate_urls_parallel(
    urls: list[str],
    validation_cache: dict[str, dict] = None,
    max_workers: int = URL_VALIDATION_THREADS,
) -> dict[str, dict]:
    """
    Validate multiple URLs in parallel using thread pool.

    Args:
        urls: List of URLs to validate
        validation_cache: Cache of previous validation results
        max_workers: Maximum number of concurrent threads

    Returns:
        Dict mapping URLs to their validation results
    """
    if not urls:
        return {}

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Filter out URLs that are already cached
    urls_to_check = []
    results = {}

    if validation_cache:
        for url in urls:
            if url in validation_cache:
                cached_result = validation_cache[url].copy()
                cached_result["from_cache"] = True
                results[url] = cached_result
            else:
                urls_to_check.append(url)
    else:
        urls_to_check = urls.copy()

    if not urls_to_check:
        return results

    print(
        f"Validating {len(urls_to_check)} URLs using {max_workers} threads...",
        file=sys.stderr,
    )

    # Use ThreadPoolExecutor for parallel validation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all validation tasks
        future_to_url = {
            executor.submit(validate_privacy_url, url, None, True): url
            for url in urls_to_check
        }

        # Progress tracking
        completed_count = 0
        total_count = len(urls_to_check)

        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            completed_count += 1

            try:
                result = future.result()
                results[url] = result

                # Add to cache if provided
                if validation_cache is not None:
                    validation_cache[url] = result

                # Show progress
                accessible = "✓" if result.get("accessible", False) else "✗"
                status = result.get("status_code", 0)
                print(
                    f"[{completed_count:>{len(str(total_count))}}/{total_count}] {accessible} {status} {url[:60]}{'...' if len(url) > 60 else ''}",
                    file=sys.stderr,
                )

            except Exception as e:
                print(
                    f"[{completed_count:>{len(str(total_count))}}/{total_count}] ✗ ERROR {url}: {e}",
                    file=sys.stderr,
                )
                results[url] = _create_error_result(url, f"Validation failed: {str(e)}")

                # Add error result to cache
                if validation_cache is not None:
                    validation_cache[url] = results[url]

    print(f"Completed validation of {len(urls_to_check)} URLs", file=sys.stderr)
    return results
