# AI Implementation Prompt: Privacy URL Content Quality Analysis

**Feature ID**: 1.5 from ROADMAP.md
**Priority**: MEDIUM-HIGH
**Effort**: 2-3 weeks
**Type**: Check

## Objective

Analyze privacy page content quality beyond HTTP accessibility, identifying "soft-404s", missing GDPR keywords, and other quality issues that indicate broken or inadequate privacy statements.

## Context

**Current State**:
- URL validation checks HTTP status codes only (200 = success)
- A privacy URL returning HTTP 200 may still be:
  - A 404 error page (soft-404)
  - An empty page
  - Wrong content (homepage, login page)
  - Non-HTTPS (security issue)

**Problem**:
- False positives: Pages marked "accessible" but unusable
- No detection of thin/inadequate privacy statements
- Can't identify GDPR compliance issues
- Missing language matching (e.g., German federation, English-only privacy page)

**Real-World Examples**:
```
URL: https://sp.example.edu/privacy
HTTP Status: 200 OK
Content: <h1>404 - Page Not Found</h1>  ← Soft-404!

URL: https://idp.university.org/privacy
HTTP Status: 200 OK
Content: <html><body></body></html>  ← Empty page!

URL: http://old.example.com/privacy  ← Non-HTTPS!
HTTP Status: 200 OK
```

## Requirements

### Core Functionality

1. **Content Quality Checks**:

   **A. Soft-404 Detection**:
   - Check page title for "404", "not found", "error"
   - Check body text for error indicators
   - Detect redirect to homepage (URL changed significantly)
   - Score based on confidence

   **B. HTTPS Enforcement**:
   - Flag non-HTTPS privacy URLs (security best practice)
   - Check for mixed content (HTTPS page loading HTTP resources)

   **C. Content Length Validation**:
   - Flag suspiciously short responses (< 500 bytes)
   - Flag empty pages (< 100 bytes after stripping HTML)
   - Compare against typical privacy statement length

   **D. GDPR Keyword Detection**:
   - Check for privacy-related terms:
     - English: "privacy", "data protection", "GDPR", "personal data", "cookie", "consent"
     - German: "datenschutz", "daten", "cookie", "einwilligung"
     - French: "confidentialité", "données personnelles", "RGPD"
     - Spanish: "privacidad", "datos personales", "GDPR"
   - Multilingual support for major European languages
   - Keyword density analysis

   **E. Language Matching** (optional):
   - Detect page language (HTML lang attribute + content analysis)
   - Compare with federation's expected language
   - Flag mismatches (German federation, English-only page)

   **F. Response Time Tracking**:
   - Flag extremely slow pages (> 10 seconds)
   - Indicator of server issues or bot protection

2. **Quality Scores**:
   ```python
   quality_scores = {
       "excellent": 90-100,  # HTTPS, keywords present, good length
       "good": 70-89,        # Minor issues (HTTP only, few keywords)
       "fair": 50-69,        # Several issues (thin content, slow)
       "poor": 30-49,        # Major issues (soft-404, very short)
       "broken": 0-29,       # Unusable (empty, wrong content)
       "inaccessible": -1    # HTTP error (existing check)
   }
   ```

3. **New CLI Flag**: `--validate-content`
   - More expensive than `--validate` (downloads and parses content)
   - Opt-in for detailed analysis
   - Can combine with `--validate` (status + content)

4. **Updated Cache Schema**:
   ```python
   cache_entry = {
       "url": "https://example.edu/privacy",
       "timestamp": "2026-01-18T12:00:00Z",
       "status_code": 200,
       "accessible": True,

       # New content analysis fields
       "content_quality_score": 85,
       "https_enabled": True,
       "content_length": 12500,
       "text_length": 3200,
       "has_gdpr_keywords": True,
       "keyword_count": 15,
       "is_soft_404": False,
       "detected_language": "en",
       "response_time_ms": 450,
       "quality_issues": ["non-https", "thin-content"],
   }
   ```

5. **Output Examples**:

   **Summary (Terminal)**:
   ```
   🔍 Privacy URL Content Quality Analysis:
     Total URLs validated: 2,683
       ✅ Excellent quality: 1,850 (68.9%)
       🟢 Good quality: 520 (19.4%)
       🟡 Fair quality: 180 (6.7%)
       🟠 Poor quality: 95 (3.5%)
       🔴 Broken/unusable: 38 (1.4%)

     Common Quality Issues:
       - Non-HTTPS URLs: 215 (8.0%)
       - Soft-404 detected: 38 (1.4%)
       - Thin content (< 500 bytes): 125 (4.7%)
       - Missing GDPR keywords: 280 (10.4%)
       - Slow response (> 5s): 45 (1.7%)
   ```

   **CSV Export** (`--csv urls-content-analysis`):
   ```csv
   Federation,EntityID,PrivacyURL,StatusCode,ContentQualityScore,HTTPS,ContentLength,HasGDPRKeywords,IsSoft404,DetectedLanguage,QualityIssues
   InCommon,https://sp.example.edu,https://example.edu/privacy,200,95,Yes,12500,Yes,No,en,
   DFN-AAI,https://idp.test.de,http://test.de/privacy,200,65,No,8200,Yes,No,de,non-https
   SWAMID,https://sp.se.edu,https://se.edu/404,200,15,Yes,850,No,Yes,en,"soft-404,thin-content,missing-keywords"
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/content_analysis.py`**:
   - `analyze_content_quality(url, html_content)`: Main analysis function
   - `detect_soft_404(html, url)`: Soft-404 detection
   - `check_gdpr_keywords(text, language)`: Keyword analysis
   - `detect_language(html, text)`: Language detection
   - `calculate_quality_score(checks)`: Score calculation

2. **Files to Modify**:
   - `src/edugain_analysis/core/validation.py`: Extend to fetch and analyze content
   - `src/edugain_analysis/cli/main.py`: Add `--validate-content` flag
   - `src/edugain_analysis/formatters/base.py`: Format content quality results

**Dependencies** (New):
- `beautifulsoup4`: HTML parsing
- `langdetect`: Language detection (optional, or use simpler heuristics)
- `lxml`: Fast HTML parsing (optional, BeautifulSoup backend)

**Edge Cases**:
- Bot protection: Some pages block automated requests
- JavaScript-required pages: Can't analyze dynamic content
- Large pages: Limit download to first 100KB
- Timeout handling: Don't wait more than 15 seconds
- Encoding issues: Handle non-UTF-8 properly

## Acceptance Criteria

### Functional Requirements
- [ ] `--validate-content` flag performs content analysis
- [ ] Soft-404 detection with < 5% false positives
- [ ] GDPR keyword detection for major European languages
- [ ] Content length validation (min/max thresholds)
- [ ] HTTPS enforcement check
- [ ] Quality score calculation (0-100 scale)
- [ ] CSV export includes content quality columns
- [ ] Results cached to avoid repeated downloads
- [ ] Compatible with bot protection (graceful degradation)

### Quality Requirements
- [ ] False positive rate < 5% (good pages marked poor)
- [ ] Performance: < 1s per URL average
- [ ] Memory efficient: Stream large responses
- [ ] Respects robots.txt (optional)
- [ ] Rate limiting to avoid server overload
- [ ] Clear error messages for failures

### Testing Requirements
- [ ] Test soft-404 detection with real examples
- [ ] Test GDPR keyword detection (multi-language)
- [ ] Test content length validation
- [ ] Test HTTPS check
- [ ] Test language detection
- [ ] Test quality score calculation
- [ ] Test caching of content analysis results
- [ ] Test bot protection handling

## Testing Strategy

**Unit Tests**:
```python
def test_detect_soft_404_title():
    """Test soft-404 detection via page title."""
    html = """
    <html>
        <head><title>404 - Page Not Found</title></head>
        <body><h1>Error</h1></body>
    </html>
    """
    assert detect_soft_404(html, "https://example.org/privacy") == True

def test_check_gdpr_keywords_english():
    """Test GDPR keyword detection in English."""
    text = "This privacy policy explains how we collect personal data and comply with GDPR."
    result = check_gdpr_keywords(text, language="en")
    assert result["has_keywords"] == True
    assert result["keyword_count"] >= 3  # "privacy", "personal data", "GDPR"

def test_calculate_quality_score():
    """Test quality score calculation."""
    checks = {
        "https_enabled": True,
        "content_length": 5000,
        "has_gdpr_keywords": True,
        "keyword_count": 10,
        "is_soft_404": False,
        "response_time_ms": 500
    }
    score = calculate_quality_score(checks)
    assert 80 <= score <= 100  # Should be high quality

def test_analyze_thin_content():
    """Test detection of thin/empty content."""
    html = "<html><body><p>Privacy</p></body></html>"
    analysis = analyze_content_quality("https://example.org/privacy", html)
    assert "thin-content" in analysis["quality_issues"]
    assert analysis["content_quality_score"] < 50
```

## Implementation Guidance

### Step 1: Create Content Analysis Module

```python
# src/edugain_analysis/core/content_analysis.py

from bs4 import BeautifulSoup
import re
from typing import Optional
from urllib.parse import urlparse

# GDPR-related keywords by language
GDPR_KEYWORDS = {
    "en": [
        "privacy", "data protection", "gdpr", "personal data",
        "cookie", "consent", "processing", "controller", "processor"
    ],
    "de": [
        "datenschutz", "daten", "gdpr", "cookie", "einwilligung",
        "verarbeitung", "verantwortlicher", "auftragsverarbeiter"
    ],
    "fr": [
        "confidentialité", "protection des données", "rgpd",
        "données personnelles", "cookie", "consentement"
    ],
    "es": [
        "privacidad", "protección de datos", "gdpr",
        "datos personales", "cookie", "consentimiento"
    ],
    "sv": [
        "integritet", "dataskydd", "gdpr", "personuppgifter", "cookie"
    ]
}

# Soft-404 indicators
SOFT_404_INDICATORS = {
    "title": ["404", "not found", "error", "page not found", "seite nicht gefunden"],
    "body": ["404", "not found", "error occurred", "page doesn't exist"]
}

def detect_soft_404(html: str, url: str) -> bool:
    """
    Detect if page is a soft-404 (returns 200 but shows error).

    Args:
        html: Page HTML content
        url: Original URL

    Returns:
        True if soft-404 detected
    """
    soup = BeautifulSoup(html, "html.parser")

    # Check page title
    title = soup.find("title")
    if title and title.text:
        title_lower = title.text.lower()
        for indicator in SOFT_404_INDICATORS["title"]:
            if indicator in title_lower:
                return True

    # Check body text (first 500 chars)
    body_text = soup.get_text()[:500].lower()
    for indicator in SOFT_404_INDICATORS["body"]:
        if indicator in body_text:
            return True

    # Check if redirected to homepage (URL changed significantly)
    # This would require comparing final URL from redirect chain
    # For now, skip this check

    return False

def check_gdpr_keywords(text: str, language: str = "en") -> dict:
    """
    Check for GDPR-related keywords in text.

    Args:
        text: Page text content
        language: Expected language (en, de, fr, es, sv)

    Returns:
        Dictionary with keyword analysis
    """
    text_lower = text.lower()

    # Get keywords for language (default to English)
    keywords = GDPR_KEYWORDS.get(language, GDPR_KEYWORDS["en"])

    # Count keyword occurrences
    keyword_count = 0
    found_keywords = []

    for keyword in keywords:
        if keyword in text_lower:
            keyword_count += 1
            found_keywords.append(keyword)

    has_keywords = keyword_count >= 2  # At least 2 keywords

    return {
        "has_keywords": has_keywords,
        "keyword_count": keyword_count,
        "found_keywords": found_keywords,
        "density": keyword_count / len(keywords) * 100  # Percentage
    }

def detect_language(html: str, text: str) -> Optional[str]:
    """
    Detect page language from HTML lang attribute or content.

    Args:
        html: Page HTML
        text: Page text

    Returns:
        Language code (en, de, fr, es, sv) or None
    """
    soup = BeautifulSoup(html, "html.parser")

    # Check HTML lang attribute
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = html_tag.get("lang").lower()
        # Extract primary language code (e.g., "en-US" -> "en")
        return lang.split("-")[0]

    # Fallback: Simple keyword-based detection
    text_lower = text.lower()

    # Count keywords per language
    lang_scores = {}
    for lang, keywords in GDPR_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        lang_scores[lang] = score

    # Return language with highest score (if > 0)
    if max(lang_scores.values()) > 0:
        return max(lang_scores, key=lang_scores.get)

    return None

def calculate_quality_score(checks: dict) -> int:
    """
    Calculate content quality score (0-100).

    Args:
        checks: Dictionary with analysis results

    Returns:
        Quality score (0-100)
    """
    score = 100  # Start with perfect score

    # HTTPS check (-20 if HTTP)
    if not checks.get("https_enabled", True):
        score -= 20

    # Content length check
    content_length = checks.get("content_length", 0)
    if content_length < 500:
        score -= 30  # Very thin content
    elif content_length < 1000:
        score -= 15  # Thin content

    # GDPR keywords check
    if not checks.get("has_gdpr_keywords", False):
        score -= 25

    keyword_count = checks.get("keyword_count", 0)
    if keyword_count < 3:
        score -= 10  # Few keywords

    # Soft-404 check (-50 if detected)
    if checks.get("is_soft_404", False):
        score -= 50

    # Response time check
    response_time = checks.get("response_time_ms", 0)
    if response_time > 10000:  # > 10 seconds
        score -= 20
    elif response_time > 5000:  # > 5 seconds
        score -= 10

    # Ensure score stays in valid range
    return max(0, min(100, score))

def analyze_content_quality(
    url: str,
    html_content: str,
    response_time_ms: int,
    expected_language: Optional[str] = None
) -> dict:
    """
    Analyze privacy page content quality.

    Args:
        url: Privacy statement URL
        html_content: HTML content of the page
        response_time_ms: Response time in milliseconds
        expected_language: Expected language (based on federation)

    Returns:
        Dictionary with content quality analysis
    """
    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract text content
    text_content = soup.get_text()
    text_length = len(text_content.strip())

    # HTTPS check
    parsed_url = urlparse(url)
    https_enabled = parsed_url.scheme == "https"

    # Soft-404 detection
    is_soft_404 = detect_soft_404(html_content, url)

    # Language detection
    detected_language = detect_language(html_content, text_content)

    # GDPR keyword analysis
    keyword_analysis = check_gdpr_keywords(
        text_content,
        language=expected_language or detected_language or "en"
    )

    # Build quality checks
    checks = {
        "https_enabled": https_enabled,
        "content_length": len(html_content),
        "text_length": text_length,
        "has_gdpr_keywords": keyword_analysis["has_keywords"],
        "keyword_count": keyword_analysis["keyword_count"],
        "is_soft_404": is_soft_404,
        "response_time_ms": response_time_ms
    }

    # Calculate quality score
    quality_score = calculate_quality_score(checks)

    # Identify quality issues
    quality_issues = []
    if not https_enabled:
        quality_issues.append("non-https")
    if is_soft_404:
        quality_issues.append("soft-404")
    if text_length < 500:
        quality_issues.append("thin-content")
    if not keyword_analysis["has_keywords"]:
        quality_issues.append("missing-keywords")
    if response_time_ms > 5000:
        quality_issues.append("slow-response")

    return {
        "content_quality_score": quality_score,
        "https_enabled": https_enabled,
        "content_length": len(html_content),
        "text_length": text_length,
        "has_gdpr_keywords": keyword_analysis["has_keywords"],
        "keyword_count": keyword_analysis["keyword_count"],
        "is_soft_404": is_soft_404,
        "detected_language": detected_language,
        "response_time_ms": response_time_ms,
        "quality_issues": quality_issues
    }
```

### Step 2: Extend URL Validation

```python
# src/edugain_analysis/core/validation.py

from .content_analysis import analyze_content_quality

def validate_url_with_content(
    url: str,
    timeout: int = 15,
    max_size: int = 102400,  # 100 KB
    expected_language: Optional[str] = None
) -> dict:
    """
    Validate URL and analyze content quality.

    Args:
        url: URL to validate
        timeout: Request timeout in seconds
        max_size: Maximum response size to download
        expected_language: Expected page language

    Returns:
        Dictionary with validation and content analysis
    """
    import time
    import requests

    result = {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accessible": False,
        "status_code": None,
        "error": None,
    }

    try:
        start_time = time.time()

        # Make request with streaming to limit download size
        response = requests.get(
            url,
            timeout=timeout,
            stream=True,
            headers={"User-Agent": "eduGAIN-Analysis/2.5 (Privacy URL Validator)"}
        )

        # Read response content (up to max_size)
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size:
                break

        response_time_ms = int((time.time() - start_time) * 1000)

        result["status_code"] = response.status_code
        result["accessible"] = 200 <= response.status_code < 400
        result["response_time_ms"] = response_time_ms

        # Analyze content if accessible
        if result["accessible"]:
            html_content = content.decode("utf-8", errors="ignore")

            content_analysis = analyze_content_quality(
                url=url,
                html_content=html_content,
                response_time_ms=response_time_ms,
                expected_language=expected_language
            )

            # Merge content analysis into result
            result.update(content_analysis)

    except requests.Timeout:
        result["error"] = "Timeout"
    except requests.RequestException as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Analysis error: {str(e)}"

    return result
```

### Step 3: Update CLI

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--validate-content",
    action="store_true",
    help="Analyze privacy page content quality (requires --validate)"
)

def main():
    args = parser.parse_args()

    # Validate --validate-content requires --validate
    if args.validate_content and not args.validate:
        print("Error: --validate-content requires --validate", file=sys.stderr)
        sys.exit(2)

    # ... analysis ...

    if args.validate and args.validate_content:
        # Use content validation instead of basic validation
        from ..core.validation import validate_url_with_content

        # Determine expected language per federation (optional)
        # Map federations to expected languages...

        # Validate with content analysis
        validation_results = {}
        for url in privacy_urls:
            validation_results[url] = validate_url_with_content(
                url,
                expected_language=get_expected_language(entity_federation)
            )
```

## Success Metrics

- Soft-404 detection accuracy > 95%
- GDPR keyword detection covers 5+ languages
- False positive rate < 5% on quality scores
- Performance: < 1s per URL average
- Users report improved privacy page quality insights
- Integration with bot protection systems
- All tests pass with >85% coverage

## References

- Current validation: `src/edugain_analysis/core/validation.py`
- BeautifulSoup documentation: https://www.crummy.com/software/BeautifulSoup/
- GDPR requirements: Articles 13 & 14 (information to data subjects)
- Soft-404 detection patterns: Google Webmaster guidelines
