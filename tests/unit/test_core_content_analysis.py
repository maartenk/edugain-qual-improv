"""Tests for core content_analysis functionality."""

import os
import sys

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)

from edugain_analysis.core.content_analysis import (
    analyze_content_quality,
    calculate_quality_score,
    check_gdpr_keywords,
    detect_language,
    detect_soft_404,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GOOD_PRIVACY_HTML = """
<html lang="en">
<head><title>Privacy Policy</title></head>
<body>
<h1>Privacy Policy</h1>
<p>
We are committed to protecting your privacy and personal data.
This policy explains how we handle your data under the GDPR and data protection law.
We collect personal data to provide our services. You have the right to consent to
data processing, request erasure (right to erasure), or contact our data controller.
We use cookies to improve your experience. As a data subject, you have full rights.
</p>
</body>
</html>
"""

SOFT_404_TITLE_HTML = """
<html>
<head><title>404 Not Found</title></head>
<body><p>The page you are looking for does not exist.</p></body>
</html>
"""

SOFT_404_BODY_HTML = """
<html>
<head><title>My Website</title></head>
<body><p>Page not found. Please return to the home page.</p></body>
</html>
"""

GERMAN_404_HTML = """
<html lang="de">
<head><title>Seite nicht gefunden</title></head>
<body><p>Die gesuchte Seite wurde nicht gefunden.</p></body>
</html>
"""

GERMAN_PRIVACY_HTML = """
<html lang="de">
<head><title>Datenschutzerklärung</title></head>
<body>
<h1>Datenschutz</h1>
<p>
Diese Seite erklärt den Umgang mit personenbezogene daten gemaess dsgvo.
Wir verwenden cookie-Technologien und holen Einwilligung ein.
Der Verantwortlicher ist die Universität. Betroffene Personen haben das
Widerrufsrecht.
</p>
</body>
</html>
"""

FRENCH_PRIVACY_HTML = """
<html lang="fr">
<head><title>Politique de confidentialité</title></head>
<body>
<h1>Confidentialité</h1>
<p>
Nous traitons vos données personnelles conformément au rgpd.
Nous utilisons des cookie pour améliorer votre expérience.
Vous avez le droit de donner votre consentement.
Le responsable du traitement est notre organisation.
Vous bénéficiez d'un droit d'accès à vos données.
</p>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# TestDetectSoft404
# ---------------------------------------------------------------------------


class TestDetectSoft404:
    """Test the detect_soft_404 function."""

    def test_title_match(self):
        """HTML with '404 Not Found' in title returns True."""
        result = detect_soft_404(SOFT_404_TITLE_HTML, "https://example.org/privacy")
        assert result is True

    def test_body_match(self):
        """HTML with 'page not found' in body text returns True."""
        result = detect_soft_404(SOFT_404_BODY_HTML, "https://example.org/privacy")
        assert result is True

    def test_negative_case(self):
        """Valid English privacy page HTML returns False."""
        result = detect_soft_404(GOOD_PRIVACY_HTML, "https://example.org/privacy")
        assert result is False

    def test_multilingual_german(self):
        """HTML with 'Seite nicht gefunden' in title returns True."""
        result = detect_soft_404(GERMAN_404_HTML, "https://example.org/privacy")
        assert result is True

    def test_empty_html(self):
        """Empty string returns False without crashing."""
        result = detect_soft_404("", "https://example.org/privacy")
        assert result is False

    def test_error_in_title_not_soft_404(self):
        """Title containing 'Error' as a template artifact must NOT be flagged as soft-404."""
        html = (
            "<html><head><title>Error | Privacy Policy</title></head>"
            "<body><p>We protect your personal data under GDPR.</p></body></html>"
        )
        result = detect_soft_404(html, "https://example.org/privacy")
        assert result is False


# ---------------------------------------------------------------------------
# TestCheckGDPRKeywords
# ---------------------------------------------------------------------------


class TestCheckGDPRKeywords:
    """Test the check_gdpr_keywords function."""

    def test_english_keywords_found(self):
        """Text containing 'privacy', 'gdpr', 'cookie' returns has_keywords=True with count>=3."""
        text = (
            "This privacy policy covers gdpr compliance. We use cookie technology, "
            "collect personal data, require consent, and respect data subject rights."
        )
        result = check_gdpr_keywords(text, "en")
        assert result["has_keywords"] is True
        assert result["keyword_count"] >= 3

    def test_german_keywords(self):
        """German text with 'datenschutz' and 'cookie' returns has_keywords=True."""
        text = "Unsere datenschutz policy verwendet cookie-Technologie und verarbeitet personenbezogene daten gemaess dsgvo."
        result = check_gdpr_keywords(text, "de")
        assert result["has_keywords"] is True

    def test_french_keywords(self):
        """French text with 'confidentialité' and 'rgpd' returns has_keywords=True."""
        text = "Notre politique de confidentialité explique le traitement rgpd. Nous utilisons des cookie."
        result = check_gdpr_keywords(text, "fr")
        assert result["has_keywords"] is True

    def test_missing_keywords(self):
        """Text with no GDPR keywords returns has_keywords=False and count=0."""
        text = "Hello world. This is a completely unrelated page about sports."
        result = check_gdpr_keywords(text, "en")
        assert result["has_keywords"] is False
        assert result["keyword_count"] == 0

    def test_density_calculation(self):
        """Density is computed as (found / total) * 100 using the actual list size."""
        from edugain_analysis.core.content_analysis import GDPR_KEYWORDS

        text = "privacy gdpr cookie nothing else here at all whatsoever"
        result = check_gdpr_keywords(text, "en")
        total = len(GDPR_KEYWORDS["en"])
        expected_density = (result["keyword_count"] / total) * 100
        assert abs(result["density"] - round(expected_density, 1)) < 0.01


# ---------------------------------------------------------------------------
# TestCalculateQualityScore
# ---------------------------------------------------------------------------


class TestCalculateQualityScore:
    """Test the calculate_quality_score function."""

    def _good_checks(self) -> dict:
        """Return a baseline set of checks that yields 100."""
        return {
            "https_enabled": True,
            "content_length": 5000,
            "text_length": 2000,
            "has_gdpr_keywords": True,
            "keyword_count": 5,
            "is_soft_404": False,
            "response_time_ms": 500,
        }

    def test_excellent_score(self):
        """All checks passing returns a score of 100."""
        score = calculate_quality_score(self._good_checks())
        assert score == 100

    def test_non_https_deduction(self):
        """https_enabled=False reduces score by 20 points."""
        checks = self._good_checks()
        checks["https_enabled"] = False
        score = calculate_quality_score(checks)
        assert score <= 80

    def test_thin_content_deduction(self):
        """content_length below min threshold deducts 15 points (thin, not empty)."""
        checks = self._good_checks()
        checks["content_length"] = 400  # below CONTENT_QUALITY_MIN_LENGTH (500)
        score = calculate_quality_score(checks)
        assert score <= 85  # -15 for thin content (lighter than empty page penalty)

    def test_soft_404_deduction(self):
        """is_soft_404=True reduces score by 50 points."""
        checks = self._good_checks()
        checks["is_soft_404"] = True
        score = calculate_quality_score(checks)
        assert score <= 50

    def test_combined_penalties(self):
        """Non-https combined with no GDPR keywords causes a significant deduction."""
        checks = self._good_checks()
        checks["https_enabled"] = False
        checks["has_gdpr_keywords"] = False
        checks["keyword_count"] = 0
        score = calculate_quality_score(checks)
        # -20 (non-https) -25 (no keywords) = 55 at most
        assert score <= 55

    def test_score_clamped_zero(self):
        """All bad checks result in score clamped at 0, never negative."""
        checks = {
            "https_enabled": False,
            "content_length": 0,
            "text_length": 0,
            "has_gdpr_keywords": False,
            "keyword_count": 0,
            "is_soft_404": True,
            "response_time_ms": 15000,  # very slow
        }
        score = calculate_quality_score(checks)
        assert score >= 0
        assert score <= 100


# ---------------------------------------------------------------------------
# TestDetectLanguage
# ---------------------------------------------------------------------------


class TestDetectLanguage:
    """Test the detect_language function."""

    def test_html_lang_attribute(self):
        """HTML with lang='de' attribute returns 'de'."""
        html = "<html lang='de'><head></head><body>Datenschutz personenbezogene daten dsgvo cookie einwilligung</body></html>"
        result = detect_language(html)
        assert result == "de"

    def test_html_lang_with_region(self):
        """HTML with lang='fr-FR' returns base code 'fr'."""
        html = "<html lang='fr-FR'><head></head><body>confidentialité données personnelles rgpd cookie consentement</body></html>"
        result = detect_language(html)
        assert result == "fr"

    def test_keyword_fallback(self):
        """No lang attr but German text with datenschutz/cookie/dsgvo falls back to 'de'."""
        html = (
            "<html><head></head><body>"
            "datenschutz personenbezogene daten dsgvo cookie einwilligung verantwortlicher betroffene"
            "</body></html>"
        )
        result = detect_language(html)
        assert result == "de"

    def test_no_language_detected(self):
        """Completely empty HTML returns None."""
        result = detect_language("")
        assert result is None


# ---------------------------------------------------------------------------
# TestAnalyzeContentQuality
# ---------------------------------------------------------------------------


class TestAnalyzeContentQuality:
    """Test the analyze_content_quality orchestration function."""

    def test_full_analysis_good_page(self):
        """Good English privacy page yields score>=60, https_enabled=True, has_gdpr_keywords=True."""
        result = analyze_content_quality(
            "https://example.org/privacy",
            GOOD_PRIVACY_HTML,
            300,
        )
        assert result["content_quality_score"] >= 60
        assert result["https_enabled"] is True
        assert result["has_gdpr_keywords"] is True
        assert "content_quality_score" in result
        assert "quality_issues" in result

    def test_soft_404_page(self):
        """HTML with 'Page Not Found' in title causes is_soft_404=True and low score."""
        html = """
        <html lang="en">
        <head><title>Page Not Found</title></head>
        <body><p>The requested page could not be found.</p></body>
        </html>
        """
        result = analyze_content_quality(
            "https://example.org/privacy",
            html,
            400,
        )
        assert result["is_soft_404"] is True
        assert result["content_quality_score"] < 60
        assert "soft-404" in result["quality_issues"]

    def test_non_https_url_flagged(self):
        """HTTP URL is flagged as non-https in result and quality_issues list."""
        result = analyze_content_quality(
            "http://example.org/privacy",
            GOOD_PRIVACY_HTML,
            300,
        )
        assert result["https_enabled"] is False
        assert "non-https" in result["quality_issues"]

    def test_detected_language_returned(self):
        """German HTML sets detected_language to 'de' in the result."""
        result = analyze_content_quality(
            "https://example.org/datenschutz",
            GERMAN_PRIVACY_HTML,
            200,
        )
        assert result["detected_language"] == "de"

    def test_response_time_returned(self):
        """response_time_ms value passed in is echoed in the result."""
        result = analyze_content_quality(
            "https://example.org/privacy",
            GOOD_PRIVACY_HTML,
            1234,
        )
        assert result["response_time_ms"] == 1234

    def test_empty_html_no_crash(self):
        """Empty HTML string does not crash and returns a valid result dict."""
        result = analyze_content_quality(
            "https://example.org/privacy",
            "",
            100,
        )
        assert "content_quality_score" in result
        assert isinstance(result["content_quality_score"], int)

    def test_expected_lang_overrides_detection(self):
        """expected_lang hint is used for keyword analysis even if HTML has no lang attr."""
        # German text without lang attribute on <html>
        html = (
            "<html><head><title>Datenschutz</title></head>"
            "<body>datenschutz cookie dsgvo personenbezogene daten einwilligung verantwortlicher</body></html>"
        )
        result = analyze_content_quality(
            "https://example.org/datenschutz",
            html,
            100,
            expected_lang="de",
        )
        # keyword check was done against German list
        assert result["has_gdpr_keywords"] is True
