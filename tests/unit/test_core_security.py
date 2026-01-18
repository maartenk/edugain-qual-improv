"""Tests for security utilities module."""

import pytest

from edugain_analysis.core.security import (
    SSRFError,
    sanitize_csv_value,
    sanitize_url_for_display,
    validate_url_for_ssrf,
)


class TestValidateUrlForSsrf:
    """Test SSRF validation function."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs pass validation."""
        validate_url_for_ssrf("https://example.org/privacy")
        validate_url_for_ssrf("https://sp.university.edu/privacy-statement")
        validate_url_for_ssrf("https://www.edugain.org/metadata")

    def test_http_scheme_rejected(self):
        """Test that HTTP scheme is rejected (only HTTPS allowed)."""
        with pytest.raises(SSRFError, match="Only HTTPS is allowed"):
            validate_url_for_ssrf("http://example.org/privacy")

    def test_file_scheme_rejected(self):
        """Test that file:// scheme is rejected."""
        with pytest.raises(SSRFError, match="Only HTTPS is allowed"):
            validate_url_for_ssrf("file:///etc/passwd")

    def test_ftp_scheme_rejected(self):
        """Test that ftp:// scheme is rejected."""
        with pytest.raises(SSRFError, match="Only HTTPS is allowed"):
            validate_url_for_ssrf("ftp://example.org/file")

    def test_localhost_rejected(self):
        """Test that localhost is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://localhost/api")

    def test_127_0_0_1_rejected(self):
        """Test that 127.0.0.1 (loopback) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://127.0.0.1/api")

    def test_10_0_0_0_network_rejected(self):
        """Test that 10.0.0.0/8 (private network) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://10.0.0.1/api")

        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://10.255.255.255/api")

    def test_172_16_0_0_network_rejected(self):
        """Test that 172.16.0.0/12 (private network) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://172.16.0.1/api")

        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://172.31.255.255/api")

    def test_192_168_0_0_network_rejected(self):
        """Test that 192.168.0.0/16 (private network) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://192.168.1.1/api")

        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://192.168.255.255/api")

    def test_169_254_0_0_network_rejected(self):
        """Test that 169.254.0.0/16 (link-local) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://169.254.1.1/api")

    def test_aws_metadata_endpoint_rejected(self):
        """Test that AWS metadata endpoint is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://169.254.169.254/latest/meta-data/")

    def test_gcp_metadata_endpoint_rejected(self):
        """Test that GCP metadata endpoint hostname is rejected."""
        # Note: GCP uses metadata.google.internal which requires DNS resolution
        # Testing with the common pattern
        with pytest.raises(SSRFError, match="cloud metadata"):
            validate_url_for_ssrf(
                "https://metadata.google.internal/computeMetadata/v1/"
            )

    def test_ipv6_loopback_rejected(self):
        """Test that IPv6 loopback (::1) is rejected."""
        with pytest.raises(SSRFError, match="private or reserved IP"):
            validate_url_for_ssrf("https://[::1]/api")

    def test_empty_url_rejected(self):
        """Test that empty URL is rejected."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_url_for_ssrf("")

    def test_none_url_rejected(self):
        """Test that None URL is rejected."""
        with pytest.raises(ValueError, match="non-empty string"):
            validate_url_for_ssrf(None)

    def test_malformed_url_rejected(self):
        """Test that malformed URLs are rejected."""
        with pytest.raises((ValueError, SSRFError)):
            validate_url_for_ssrf("not-a-url")

    def test_url_without_hostname_rejected(self):
        """Test that URLs without hostname are rejected."""
        with pytest.raises(ValueError, match="must have a hostname"):
            validate_url_for_ssrf("https:///path")


class TestSanitizeCsvValue:
    """Test CSV sanitization function."""

    def test_normal_text_unchanged(self):
        """Test that normal text passes through unchanged."""
        assert sanitize_csv_value("Normal text") == "Normal text"
        assert sanitize_csv_value("Hello, World!") == "Hello, World!"
        assert sanitize_csv_value("123 Main Street") == "123 Main Street"

    def test_equals_sign_escaped(self):
        """Test that = at start is escaped."""
        assert sanitize_csv_value("=1+1") == "'=1+1"
        assert sanitize_csv_value("=SUM(A1:A10)") == "'=SUM(A1:A10)"

    def test_plus_sign_escaped(self):
        """Test that + at start is escaped."""
        assert sanitize_csv_value("+1234") == "'+1234"
        assert sanitize_csv_value("+A1+B1") == "'+A1+B1"

    def test_minus_sign_escaped(self):
        """Test that - at start is escaped."""
        assert sanitize_csv_value("-5678") == "'-5678"
        assert sanitize_csv_value("-A1") == "'-A1"

    def test_at_sign_escaped(self):
        """Test that @ at start is escaped."""
        assert sanitize_csv_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"

    def test_tab_character_escaped(self):
        """Test that tab at start is escaped."""
        assert sanitize_csv_value("\tvalue") == "'\tvalue"

    def test_carriage_return_escaped(self):
        """Test that carriage return at start is escaped."""
        assert sanitize_csv_value("\rvalue") == "'\rvalue"

    def test_empty_string_unchanged(self):
        """Test that empty string is handled."""
        assert sanitize_csv_value("") == ""

    def test_none_value_unchanged(self):
        """Test that None value is handled."""
        assert sanitize_csv_value(None) is None

    def test_non_string_unchanged(self):
        """Test that non-string values pass through."""
        assert sanitize_csv_value(123) == 123
        assert sanitize_csv_value(45.67) == 45.67

    def test_dangerous_formula_escaped(self):
        """Test that dangerous Excel formulas are escaped."""
        assert sanitize_csv_value("=cmd|'/c calc'!A1") == "'=cmd|'/c calc'!A1"
        assert (
            sanitize_csv_value("@SUM(1+1)*cmd|'/c calc'!A0")
            == "'@SUM(1+1)*cmd|'/c calc'!A0"
        )

    def test_mid_string_special_chars_unchanged(self):
        """Test that special chars in middle of string are not escaped."""
        assert sanitize_csv_value("A=B") == "A=B"
        assert sanitize_csv_value("1+2=3") == "1+2=3"
        assert sanitize_csv_value("email@example.org") == "email@example.org"


class TestSanitizeUrlForDisplay:
    """Test URL sanitization for display."""

    def test_normal_url_unchanged(self):
        """Test that normal URLs pass through unchanged."""
        assert (
            sanitize_url_for_display("https://example.org/privacy")
            == "https://example.org/privacy"
        )
        assert (
            sanitize_url_for_display("https://sp.edu/page?q=test")
            == "https://sp.edu/page?q=test"
        )

    def test_url_with_username_password_sanitized(self):
        """Test that URLs with username:password are sanitized."""
        result = sanitize_url_for_display("https://user:pass@example.org/api")
        assert "user" not in result
        assert "pass" not in result
        assert "example.org" in result
        assert "/api" in result

    def test_url_with_username_only_sanitized(self):
        """Test that URLs with username only are sanitized."""
        result = sanitize_url_for_display("https://admin@example.org/api")
        assert "admin" not in result
        assert "example.org" in result

    def test_url_with_port_preserved(self):
        """Test that port numbers are preserved."""
        result = sanitize_url_for_display("https://user:pass@example.org:8080/api")
        assert "user" not in result
        assert "pass" not in result
        assert ":8080" in result
        assert "example.org" in result

    def test_url_with_query_parameters_preserved(self):
        """Test that query parameters are preserved."""
        result = sanitize_url_for_display("https://user:pass@example.org/api?key=value")
        assert "user" not in result
        assert "pass" not in result
        assert "?key=value" in result

    def test_url_with_fragment_preserved(self):
        """Test that URL fragments are preserved."""
        result = sanitize_url_for_display("https://user:pass@example.org/page#section")
        assert "user" not in result
        assert "pass" not in result
        assert "#section" in result

    def test_empty_string_unchanged(self):
        """Test that empty string is handled."""
        assert sanitize_url_for_display("") == ""

    def test_none_value_unchanged(self):
        """Test that None value is handled."""
        assert sanitize_url_for_display(None) is None

    def test_non_string_unchanged(self):
        """Test that non-string values pass through."""
        assert sanitize_url_for_display(123) == 123

    def test_malformed_url_unchanged(self):
        """Test that malformed URLs pass through (better than crashing)."""
        malformed = "not-really-a-url"
        assert sanitize_url_for_display(malformed) == malformed
