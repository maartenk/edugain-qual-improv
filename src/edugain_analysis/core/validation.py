"""
URL validation module for privacy statement analysis.

Provides HTTP accessibility validation of privacy statement URLs.
"""

import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse

import requests

from ..config import (
    URL_VALIDATION_DELAY,
    URL_VALIDATION_THREADS,
    URL_VALIDATION_TIMEOUT,
)

# Global rate limiting semaphore
_url_validation_semaphore = None


def _get_url_validation_semaphore(
    max_concurrent: int = URL_VALIDATION_THREADS,
) -> threading.Semaphore:
    """Get or create the global semaphore for URL validation rate limiting."""
    global _url_validation_semaphore
    if _url_validation_semaphore is None:
        _url_validation_semaphore = threading.Semaphore(max_concurrent)
    return _url_validation_semaphore


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
        }

    # Rate limiting
    time.sleep(URL_VALIDATION_DELAY)

    try:
        # Simple HTTP HEAD request to check accessibility
        response = requests.head(
            url,
            timeout=URL_VALIDATION_TIMEOUT,
            headers={
                "User-Agent": "eduGAIN-Quality-Analysis/2.0 (URL validation bot)",
            },
            allow_redirects=True,
        )

        status_code = response.status_code
        final_url = response.url
        redirect_count = len(response.history)

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
