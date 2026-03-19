"""
Content quality analysis for privacy statement URLs.

Provides functions to analyse the actual content of privacy pages beyond
simple HTTP status checks — detecting soft-404s, thin content, missing
GDPR compliance keywords, and producing an actionable quality score.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from ..config import (
    CONTENT_QUALITY_EMPTY_THRESHOLD,
    CONTENT_QUALITY_MIN_LENGTH,
    CONTENT_QUALITY_SLOW_MS,
    CONTENT_QUALITY_VERY_SLOW_MS,
)

# ---------------------------------------------------------------------------
# Keyword / pattern data
# ---------------------------------------------------------------------------

GDPR_KEYWORDS: dict[str, list[str]] = {
    "en": [
        "privacy",
        "privacy notice",
        "privacy statement",
        "privacy policy",
        "data protection",
        "data privacy",
        "gdpr",
        "personal data",
        "cookie",
        "consent",
        "data controller",
        "right to erasure",
        "data subject",
        "your rights",
    ],
    "de": [
        "datenschutz",
        "datenschutzerklärung",
        "datenschutzhinweis",
        "personenbezogene daten",
        "dsgvo",
        "cookie",
        "einwilligung",
        "verantwortlicher",
        "betroffene",
        "widerrufsrecht",
    ],
    "fr": [
        "confidentialité",
        "politique de confidentialité",
        "données personnelles",
        "rgpd",
        "cookie",
        "consentement",
        "responsable du traitement",
        "droit d'accès",
        "vos droits",
    ],
    "es": [
        "privacidad",
        "política de privacidad",
        "aviso de privacidad",
        "datos personales",
        "rgpd",
        "cookie",
        "consentimiento",
        "responsable del tratamiento",
        "derecho al olvido",
        "sus derechos",
    ],
    "sv": [
        "integritet",
        "integritetspolicy",
        "dataskydd",
        "personuppgifter",
        "gdpr",
        "cookie",
        "samtycke",
        "personuppgiftsansvarig",
    ],
    "nl": [
        "privacybeleid",
        "persoonsgegevens",
        "gegevensbescherming",
        "avg",
        "cookie",
        "toestemming",
        "verwerkingsverantwoordelijke",
        "betrokkene",
        "uw rechten",
    ],
    "it": [
        "privacy",
        "informativa sulla privacy",
        "dati personali",
        "gdpr",
        "cookie",
        "consenso",
        "titolare del trattamento",
        "interessato",
        "i tuoi diritti",
    ],
    "pl": [
        "prywatność",
        "polityka prywatności",
        "dane osobowe",
        "rodo",
        "cookie",
        "zgoda",
        "administrator danych",
        "podmiot danych",
        "twoje prawa",
    ],
    "pt": [
        "privacidade",
        "política de privacidade",
        "dados pessoais",
        "rgpd",
        "cookie",
        "consentimento",
        "responsável pelo tratamento",
        "os seus direitos",
    ],
    "da": [
        "privatlivspolitik",
        "personoplysninger",
        "databeskyttelse",
        "gdpr",
        "cookie",
        "samtykke",
        "dataansvarlig",
        "registrerede",
        "dine rettigheder",
    ],
    "fi": [
        "tietosuoja",
        "tietosuojaseloste",
        "henkilötiedot",
        "gdpr",
        "cookie",
        "suostumus",
        "rekisterinpitäjä",
        "rekisteröidyn oikeudet",
    ],
    "no": [
        "personvern",
        "personvernerklæring",
        "personopplysninger",
        "gdpr",
        "cookie",
        "samtykke",
        "behandlingsansvarlig",
        "dine rettigheter",
    ],
}

SOFT_404_TITLES: list[str] = [
    "404",
    "not found",
    "page not found",
    "nicht gefunden",
    "seite nicht gefunden",
    "introuvable",
    "page introuvable",
    "no encontrada",
    "sidan hittades inte",
    "fejl",  # Danish: error
    "fout",  # Dutch: error
    "niet gevonden",  # Dutch: not found
    "non trovata",  # Italian: not found
    "nie znaleziono",  # Polish: not found
    "ikke funnet",  # Norwegian: not found
    "ei löydy",  # Finnish: not found
]

SOFT_404_BODY: list[str] = [
    "page not found",
    "404 error",
    "does not exist",
    "seite nicht gefunden",
    "page introuvable",
    "no se encontró la página",
    "sidan hittades inte",
    "this page could not be found",
    "the requested url was not found",
    "requested resource could not be found",
    "pagina niet gevonden",  # Dutch
    "pagina non trovata",  # Italian
    "strona nie została znaleziona",  # Polish
    "siden ble ikke funnet",  # Norwegian
    "sivua ei löydy",  # Finnish
]


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def detect_soft_404(html: str, url: str) -> bool:
    """Detect pages that return HTTP 200 but display error content.

    Args:
        html: Raw HTML content of the page.
        url: The URL that was fetched (unused in logic, kept for future use).

    Returns:
        True if the page appears to be a soft-404 error page.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Check page title
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title_lower = title_tag.string.lower().strip()
        for indicator in SOFT_404_TITLES:
            if indicator in title_lower:
                return True

    # Check body text (first 500 chars after stripping tags)
    body_text = soup.get_text(separator=" ", strip=True)[:500].lower()
    for indicator in SOFT_404_BODY:
        if indicator in body_text:
            return True

    return False


def check_gdpr_keywords(
    text: str, lang: str = "en"
) -> dict[str, bool | int | float | list[str]]:
    """Check for GDPR-related keywords in page text.

    Args:
        text: Plain text extracted from the privacy page.
        lang: ISO 639-1 language code to select the keyword list.
              Falls back to English if the language is not in GDPR_KEYWORDS.

    Returns:
        Dict with keys: has_keywords (bool), keyword_count (int),
        density (float 0-100), found_keywords (list[str]).
    """
    keyword_list = GDPR_KEYWORDS.get(lang, GDPR_KEYWORDS["en"])
    text_lower = text.lower()

    found: list[str] = []
    for kw in keyword_list:
        if kw in text_lower:
            found.append(kw)

    keyword_count = len(found)
    density = (keyword_count / len(keyword_list)) * 100 if keyword_list else 0.0

    return {
        "has_keywords": keyword_count >= 2,
        "keyword_count": keyword_count,
        "density": round(density, 1),
        "found_keywords": found,
    }


def detect_language(html: str) -> str | None:
    """Detect the primary language of a page.

    First checks the HTML ``lang`` attribute on the root ``<html>`` element.
    Falls back to a keyword-frequency heuristic across all supported languages.

    Args:
        html: Raw HTML content of the page.

    Returns:
        ISO 639-1 language code (e.g. "en", "de") or None if undetermined.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # 1. HTML lang attribute
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        raw_lang = str(html_tag["lang"]).lower().strip()
        # Strip region suffix: "en-US" → "en"
        lang_code = raw_lang.split("-")[0].split("_")[0]
        if lang_code in GDPR_KEYWORDS:
            return lang_code

    # 2. Keyword frequency fallback
    text = soup.get_text(separator=" ", strip=True).lower()
    scores: dict[str, int] = {}
    for lang, keywords in GDPR_KEYWORDS.items():
        scores[lang] = sum(1 for kw in keywords if kw in text)

    best_lang = max(scores, key=lambda la: scores[la])
    if scores[best_lang] > 0:
        return best_lang

    return None


def calculate_quality_score(checks: dict[str, object]) -> int:
    """Calculate a 0-100 content quality score from check results.

    Args:
        checks: Dict produced by ``analyze_content_quality``.  Expected keys:
            https_enabled (bool), content_length (int), text_length (int),
            has_gdpr_keywords (bool), keyword_count (int),
            is_soft_404 (bool), response_time_ms (int).

    Returns:
        Integer score in [0, 100].
    """
    score = 100

    if not checks.get("https_enabled", True):
        score -= 20

    content_length = checks.get("content_length", 0)
    if content_length < CONTENT_QUALITY_EMPTY_THRESHOLD:
        score -= 30  # effectively empty page
    elif content_length < CONTENT_QUALITY_MIN_LENGTH:
        score -= 15  # thin content (lighter penalty than empty)
    elif content_length < 1000:
        score -= 10  # borderline length

    if not checks.get("has_gdpr_keywords", True):
        score -= 25
    elif checks.get("keyword_count", 0) < 3:
        score -= 10

    if checks.get("is_soft_404", False):
        score -= 50

    response_time_ms = checks.get("response_time_ms", 0)
    if response_time_ms > CONTENT_QUALITY_VERY_SLOW_MS:
        score -= 20
    elif response_time_ms > CONTENT_QUALITY_SLOW_MS:
        score -= 10

    return max(0, min(100, score))


def analyze_content_quality(
    url: str,
    html: str,
    response_time_ms: int,
    expected_lang: str | None = None,
) -> dict[str, object]:
    """Orchestrate full content quality analysis for a privacy page.

    Args:
        url: The URL that was fetched.
        html: Raw HTML content.
        response_time_ms: Time taken to fetch the page in milliseconds.
        expected_lang: Optional hint for the expected language.

    Returns:
        Dict with all content quality fields.
    """
    https_enabled = url.lower().startswith("https://")

    # Parse HTML once for reuse
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    content_length = len(html.encode("utf-8", errors="replace"))
    text = soup.get_text(separator=" ", strip=True)
    text_length = len(text)

    is_soft_404 = detect_soft_404(html, url)

    detected_language = detect_language(html)
    lang_for_keywords = expected_lang or detected_language or "en"
    keyword_result = check_gdpr_keywords(text, lang_for_keywords)

    checks = {
        "https_enabled": https_enabled,
        "content_length": content_length,
        "text_length": text_length,
        "has_gdpr_keywords": keyword_result["has_keywords"],
        "keyword_count": keyword_result["keyword_count"],
        "is_soft_404": is_soft_404,
        "response_time_ms": response_time_ms,
    }
    score = calculate_quality_score(checks)

    # Build human-readable quality issues list
    quality_issues: list[str] = []
    if not https_enabled:
        quality_issues.append("non-https")
    if is_soft_404:
        quality_issues.append("soft-404")
    if content_length < CONTENT_QUALITY_EMPTY_THRESHOLD:
        quality_issues.append("empty-content")
    elif content_length < CONTENT_QUALITY_MIN_LENGTH:
        quality_issues.append("thin-content")
    if not keyword_result["has_keywords"]:
        quality_issues.append("no-gdpr-keywords")
    elif keyword_result["keyword_count"] < 3:
        quality_issues.append("few-gdpr-keywords")
    if response_time_ms > CONTENT_QUALITY_VERY_SLOW_MS:
        quality_issues.append("very-slow-response")
    elif response_time_ms > CONTENT_QUALITY_SLOW_MS:
        quality_issues.append("slow-response")

    return {
        "content_quality_score": score,
        "https_enabled": https_enabled,
        "content_length": content_length,
        "text_length": text_length,
        "has_gdpr_keywords": keyword_result["has_keywords"],
        "keyword_count": keyword_result["keyword_count"],
        "is_soft_404": is_soft_404,
        "detected_language": detected_language,
        "response_time_ms": response_time_ms,
        "quality_issues": quality_issues,
    }
