"""Tests for core validation functionality."""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.core.validation import (
    _create_error_result,
    _get_url_validation_semaphore,
    validate_privacy_url,
    validate_urls_parallel,
)


class TestValidatePrivacyURL:
    """Test the validate_privacy_url function."""

    def test_empty_url(self):
        """Test validation with empty URL."""
        result = validate_privacy_url("")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Empty URL"
        assert "checked_at" in result

    def test_whitespace_url(self):
        """Test validation with whitespace-only URL."""
        result = validate_privacy_url("   ")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Empty URL"

    def test_invalid_url_format(self):
        """Test validation with invalid URL format."""
        result = validate_privacy_url("not-a-url")

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Invalid URL format"

    def test_cache_hit(self):
        """Test validation with cache hit."""
        cache = {
            "https://example.org": {
                "status_code": 200,
                "accessible": True,
                "final_url": "https://example.org",
                "redirect_count": 0,
                "error": None,
                "checked_at": "2024-01-01T00:00:00",
            }
        }

        result = validate_privacy_url("https://example.org", validation_cache=cache)

        assert result["status_code"] == 200
        assert result["accessible"] is True
        assert result["from_cache"] is True

    @patch("requests.head")
    def test_successful_validation(self, mock_head):
        """Test successful URL validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.org/privacy"
        mock_response.history = []
        mock_head.return_value = mock_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 200
        assert result["accessible"] is True
        assert result["final_url"] == "https://example.org/privacy"
        assert result["redirect_count"] == 0
        assert result["error"] is None

    @patch("requests.head")
    def test_validation_with_redirects(self, mock_head):
        """Test URL validation with redirects."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.org/privacy-final"
        mock_response.history = [MagicMock(), MagicMock()]  # 2 redirects
        mock_head.return_value = mock_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 200
        assert result["accessible"] is True
        assert result["final_url"] == "https://example.org/privacy-final"
        assert result["redirect_count"] == 2

    @patch("requests.get")
    @patch("requests.head")
    def test_validation_head_fallback_to_get_success(self, mock_head, mock_get):
        """Test that validation falls back to GET when HEAD is rejected."""
        head_response = MagicMock()
        head_response.status_code = 405
        head_response.url = "https://example.org/privacy"
        head_response.history = []
        mock_head.return_value = head_response

        get_response = MagicMock()
        get_response.status_code = 200
        get_response.url = "https://example.org/privacy"
        get_response.history = [MagicMock()]
        mock_get.return_value = get_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 200
        assert result["accessible"] is True
        assert result["redirect_count"] == 1
        mock_head.assert_called_once()
        mock_get.assert_called_once()

    @patch("requests.get")
    @patch("requests.head")
    def test_validation_head_fallback_to_get_failure(self, mock_head, mock_get):
        """Test fallback when GET also fails."""
        head_response = MagicMock()
        head_response.status_code = 403
        head_response.url = "https://example.org/privacy"
        head_response.history = []
        mock_head.return_value = head_response

        get_response = MagicMock()
        get_response.status_code = 500
        get_response.url = "https://example.org/privacy"
        get_response.history = []
        mock_get.return_value = get_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 500
        assert result["accessible"] is False
        mock_head.assert_called_once()
        mock_get.assert_called_once()

    @patch("requests.head")
    def test_validation_client_error(self, mock_head):
        """Test URL validation with client error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://example.org/privacy"
        mock_response.history = []
        mock_head.return_value = mock_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 404
        assert result["accessible"] is False

    @patch("requests.head")
    def test_validation_server_error(self, mock_head):
        """Test URL validation with server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.url = "https://example.org/privacy"
        mock_response.history = []
        mock_head.return_value = mock_response

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 500
        assert result["accessible"] is False

    @patch("requests.head")
    def test_validation_timeout(self, mock_head):
        """Test URL validation timeout."""
        import requests

        mock_head.side_effect = requests.exceptions.Timeout()

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Request timeout"

    @patch("requests.head")
    def test_validation_connection_error(self, mock_head):
        """Test URL validation connection error."""
        import requests

        mock_head.side_effect = requests.exceptions.ConnectionError()

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Connection error"

    @patch("requests.head")
    def test_validation_ssl_error(self, mock_head):
        """Test URL validation SSL error."""
        import requests

        mock_head.side_effect = requests.exceptions.SSLError()

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "SSL certificate error"

    @patch("requests.head")
    def test_validation_too_many_redirects(self, mock_head):
        """Test URL validation with too many redirects."""
        import requests

        mock_head.side_effect = requests.exceptions.TooManyRedirects()

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Too many redirects"

    @patch("requests.head")
    def test_validation_request_exception(self, mock_head):
        """Test URL validation with general request exception."""
        import requests

        mock_head.side_effect = requests.exceptions.RequestException("Custom error")

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Request error: Custom error"

    @patch("requests.head")
    def test_validation_unexpected_exception(self, mock_head):
        """Test URL validation with unexpected exception."""
        mock_head.side_effect = ValueError("Unexpected error")

        result = validate_privacy_url(
            "https://example.org/privacy", use_semaphore=False
        )

        assert result["status_code"] == 0
        assert result["accessible"] is False
        assert result["error"] == "Unexpected error: Unexpected error"

    @patch("requests.head")
    def test_validation_adds_to_cache(self, mock_head):
        """Test that validation results are added to cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.org/privacy"
        mock_response.history = []
        mock_head.return_value = mock_response

        cache = {}
        validate_privacy_url(
            "https://example.org/privacy", validation_cache=cache, use_semaphore=False
        )

        assert "https://example.org/privacy" in cache
        assert cache["https://example.org/privacy"]["status_code"] == 200

    @patch("requests.head")
    def test_validation_cache_not_provided(self, mock_head):
        """Test validation when cache is not provided."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.org/privacy"
        mock_response.history = []
        mock_head.return_value = mock_response

        # Test with validation_cache=None
        result = validate_privacy_url(
            "https://example.org/privacy", validation_cache=None, use_semaphore=False
        )

        assert result["status_code"] == 200
        assert result["accessible"] is True

    def test_validation_with_semaphore(self):
        """Test validation with semaphore usage."""
        from edugain_analysis.core.validation import _get_url_validation_semaphore

        # Test semaphore creation and reuse
        semaphore1 = _get_url_validation_semaphore(5)
        semaphore2 = _get_url_validation_semaphore(10)  # Should return same instance

        assert semaphore1 is semaphore2

    def test_url_parsing_exception(self):
        """Test URL parsing exception handling."""
        # Create a URL that would cause urlparse to fail
        with patch("edugain_analysis.core.validation.urlparse") as mock_urlparse:
            mock_urlparse.side_effect = Exception("Parse error")

            result = validate_privacy_url("https://example.org")

            assert result["status_code"] == 0
            assert result["accessible"] is False
            assert "URL parsing error" in result["error"]


class TestValidateURLsParallel:
    """Test the validate_urls_parallel function."""

    def test_empty_urls(self):
        """Test validation with empty URL list."""
        result = validate_urls_parallel([])
        assert result == {}

    @patch("edugain_analysis.core.validation.validate_privacy_url")
    def test_validation_with_cache_hits(self, mock_validate):
        """Test parallel validation with cache hits."""
        urls = ["https://example1.org", "https://example2.org"]
        cache = {
            "https://example1.org": {
                "status_code": 200,
                "accessible": True,
                "checked_at": "2024-01-01T00:00:00",
            }
        }

        # Only the uncached URL should be validated
        mock_validate.return_value = {
            "status_code": 404,
            "accessible": False,
            "checked_at": "2024-01-01T00:00:00",
        }

        result = validate_urls_parallel(urls, validation_cache=cache, max_workers=2)

        # Should have results for both URLs
        assert len(result) == 2
        assert "https://example1.org" in result
        assert "https://example2.org" in result

        # First URL should be from cache
        assert result["https://example1.org"]["from_cache"] is True

        # Second URL should be validated (mock was called once)
        mock_validate.assert_called_once()

    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("edugain_analysis.core.validation.validate_privacy_url")
    def test_validation_parallel_execution(self, mock_validate, mock_executor):
        """Test that parallel validation uses ThreadPoolExecutor correctly."""
        urls = ["https://example1.org", "https://example2.org"]

        # Mock ThreadPoolExecutor and futures
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        mock_future1 = MagicMock()
        mock_future2 = MagicMock()
        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]

        # Mock as_completed to return futures
        with patch("concurrent.futures.as_completed") as mock_as_completed:
            mock_as_completed.return_value = [mock_future1, mock_future2]

            # Mock future results
            mock_future1.result.return_value = {
                "status_code": 200,
                "accessible": True,
                "checked_at": "2024-01-01T00:00:00",
            }
            mock_future2.result.return_value = {
                "status_code": 404,
                "accessible": False,
                "checked_at": "2024-01-01T00:00:00",
            }

            # Future to URL mapping
            future_to_url = {mock_future1: urls[0], mock_future2: urls[1]}
            with patch.dict(
                "edugain_analysis.core.validation.validate_urls_parallel.__globals__",
                {"future_to_url": future_to_url},
            ):
                validate_urls_parallel(urls, max_workers=2)

        # Should create ThreadPoolExecutor with correct max_workers
        mock_executor.assert_called_once_with(max_workers=2)

    def test_validation_exception_handling(self):
        """Test exception handling during parallel validation."""
        urls = ["https://example.org"]

        # Mock the validate_privacy_url function to raise an exception
        with patch(
            "edugain_analysis.core.validation.validate_privacy_url"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Validation failed")

            result = validate_urls_parallel(urls, max_workers=1)

            # The function should handle the exception and return an error result
            assert urls[0] in result
            assert result[urls[0]]["accessible"] is False
            assert "Validation failed" in result[urls[0]]["error"]

    def test_parallel_validation_mixed_results(self):
        """Test parallel validation with mixed success and error results."""
        urls = ["https://example1.org", "https://example2.org"]

        # Mock validate_privacy_url to return different results
        def mock_validate_side_effect(url, validation_cache=None, use_semaphore=True):
            if "example1" in url:
                return {
                    "status_code": 200,
                    "accessible": True,
                    "final_url": url,
                    "redirect_count": 0,
                    "error": None,
                    "checked_at": "2024-01-01T00:00:00",
                }
            else:
                raise Exception("Network error")

        with patch(
            "edugain_analysis.core.validation.validate_privacy_url"
        ) as mock_validate:
            mock_validate.side_effect = mock_validate_side_effect

            result = validate_urls_parallel(urls, max_workers=2)

            # Should have results for both URLs
            assert len(result) == 2
            assert result["https://example1.org"]["accessible"] is True
            assert result["https://example2.org"]["accessible"] is False
            assert "Network error" in result["https://example2.org"]["error"]


class TestCreateErrorResult:
    """Test the _create_error_result function."""

    def test_create_error_result(self):
        """Test creating error result dictionary."""
        result = _create_error_result("https://example.org", "Test error")

        assert result["status_code"] == 0
        assert result["final_url"] == "https://example.org"
        assert result["accessible"] is False
        assert result["redirect_count"] == 0
        assert result["error"] == "Test error"
        assert "checked_at" in result


class TestSemaphore:
    """Test semaphore utility."""

    def test_get_url_validation_semaphore(self):
        """Test getting validation semaphore."""
        semaphore = _get_url_validation_semaphore(5)
        assert semaphore is not None

        # Should return same semaphore on subsequent calls
        semaphore2 = _get_url_validation_semaphore(10)
        assert semaphore is semaphore2
