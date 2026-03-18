# Privacy Page Content Quality Analysis

## Overview

A privacy statement URL that returns HTTP 200 is not necessarily a working privacy page. It might be a soft-404 served by the application framework, a placeholder with no real content, or a page that contains nothing resembling a GDPR privacy notice. The content quality analysis feature addresses this gap by downloading and inspecting the HTML of each privacy statement page registered in eduGAIN SP metadata.

Running `edugain-analyze --validate-content` performs HTTP validation (the same checks as `--validate`) and then fetches each accessible page to analyse its content. The result is a quality score per URL and a categorised list of issues, visible in the terminal summary and exportable as CSV.

## Why content quality matters

Federation operators and their members rely on privacy statement URLs to meet GDPR accountability obligations. A broken link or a "Page not found" page masquerading as a 200 response offers no protection. Thin pages — a sentence or two with no data-controller information — are similarly inadequate. Content quality analysis gives operators an evidence-based view of what is actually published, not just whether a URL resolves.

## Usage

```bash
# Terminal summary with quality tier breakdown
edugain-analyze --validate-content

# Per-URL CSV export
edugain-analyze --csv urls-content-analysis

# Pipe CSV to a file without headers
edugain-analyze --csv urls-content-analysis --no-headers > content-analysis.csv
```

`--validate-content` implies `--validate`. Passing both flags is harmless but redundant.

`--csv urls-content-analysis` also triggers content validation automatically; no separate flag is required.

## Quality score algorithm

Each privacy page starts with a score of 100. Deductions are applied as follows:

| Condition | Deduction |
| --- | --- |
| URL uses plain HTTP (not HTTPS) | −20 |
| HTML content under 100 bytes (empty) | −30 |
| HTML content under 500 bytes (thin) | −30 |
| HTML content 500–999 bytes (marginal) | −15 |
| Fewer than 2 GDPR keywords found | −25 |
| Exactly 2 GDPR keywords found (expected 3+) | −10 |
| Soft-404 detected | −50 |
| Response time over 5 000 ms | −10 |
| Response time over 10 000 ms | −20 (replaces the −10) |

Deductions stack. The final score is clamped to the range [0, 100].

Content length thresholds (bytes) are defined in `settings.py`:
- `CONTENT_QUALITY_EMPTY_THRESHOLD` = 100
- `CONTENT_QUALITY_MIN_LENGTH` = 500

Response time thresholds (milliseconds):
- `CONTENT_QUALITY_SLOW_MS` = 5 000
- `CONTENT_QUALITY_VERY_SLOW_MS` = 10 000

## Quality tiers

The terminal summary groups scores into five tiers:

| Tier | Score range | What it signals |
| --- | --- | --- |
| Excellent | 90–100 | Page passes all checks |
| Good | 70–89 | Minor issues — e.g. few GDPR keywords or a slow response |
| Fair | 50–69 | Notable problems worth addressing |
| Poor | 30–49 | Significant issues affecting GDPR compliance evidence |
| Broken | 0–29 | Soft-404, blank page, or severe combined issues |

## Quality issues glossary

The `QualityIssues` column in the CSV export and the terminal breakdown use these fixed strings:

| Issue | Trigger condition | Score impact |
| --- | --- | --- |
| `soft-404` | Page title or body text matches known error phrases | −50 |
| `empty-content` | HTML content under 100 bytes | −30 |
| `thin-content` | HTML content 100–499 bytes | −30 |
| `non-https` | URL scheme is `http://` | −20 |
| `no-gdpr-keywords` | Fewer than 2 GDPR keywords found | −25 |
| `few-gdpr-keywords` | Exactly 2 GDPR keywords found | −10 |
| `very-slow-response` | Response time over 10 000 ms | −20 |
| `slow-response` | Response time 5 000–10 000 ms | −10 |

Multiple issues on a single page are recorded as a pipe-separated string in the CSV, for example `thin-content|non-https`.

## GDPR keyword detection

The analyser checks for the presence of GDPR-related terms in the visible page text. A page must contain at least 2 matching keywords to be considered keyword-compliant (`has_gdpr_keywords = True`). Three or more is expected for a full score.

Keywords are selected by language. Detection covers five languages:

| Code | Language | Example keywords |
| --- | --- | --- |
| `en` | English | privacy, data protection, gdpr, personal data, consent |
| `de` | German | datenschutz, dsgvo, einwilligung, verantwortlicher |
| `fr` | French | confidentialité, données personnelles, rgpd, consentement |
| `es` | Spanish | privacidad, datos personales, rgpd, consentimiento |
| `sv` | Swedish | integritet, dataskydd, personuppgifter, samtycke |

Language is determined in this order:
1. The `lang` attribute on the page's `<html>` element (region suffixes such as `en-US` are stripped).
2. If the `lang` attribute is absent or not in the supported list, keyword frequency across all five language sets is used as a heuristic.
3. If no language can be determined, English keywords are used as a fallback.

## Soft-404 detection

A soft-404 is a page that returns HTTP 200 but displays an error message. The detector checks:

1. The `<title>` element — if it contains phrases like "404", "not found", "seite nicht gefunden", "page introuvable", or equivalents in Dutch, Danish, and Swedish.
2. The first 500 characters of visible body text — checked against a similar list of error phrases.

If either check matches, `is_soft_404` is set to `True` and the `soft-404` issue is recorded, with a 50-point score deduction.

## Example output

### Terminal summary

```
📊 Privacy Page Content Quality Analysis:
  Analysed: 2,683 pages
  Average score: 74/100
  Excellent (90-100): 1,102 (41%)
  Good (70-89):         891 (33%)
  Fair (50-69):         412 (15%)
  Poor (30-49):         187 (7%)
  Broken (0-29):         91 (3%)
  Top quality issues:
    • no-gdpr-keywords: 523 (20%)
    • thin-content: 278 (10%)
    • non-https: 143 (5%)
    • soft-404: 91 (3%)
    • few-gdpr-keywords: 68 (3%)
```

### CSV excerpt (`--csv urls-content-analysis`)

```csv
Federation,EntityID,PrivacyURL,StatusCode,ContentQualityScore,HTTPS,ContentLength,HasGDPRKeywords,KeywordCount,IsSoft404,DetectedLanguage,ResponseTimeMs,QualityIssues
ExampleFed,https://sp.example.org,https://sp.example.org/privacy,200,92,True,8432,True,6,False,en,321,
ExampleFed,https://old.example.org,http://old.example.org/datenschutz,200,58,False,1204,True,4,False,de,887,non-https
ExampleFed,https://broken.example.org,https://broken.example.org/privacy,200,12,True,312,False,0,True,en,245,soft-404|thin-content|no-gdpr-keywords
```

## How to improve scores

The following actions target the most common issues, ordered by score impact:

**`soft-404` (−50)**
The privacy URL points to an error page. The SP operator must update the `mdui:PrivacyStatementURL` element in their metadata to a URL that returns a real privacy notice. Federation operators should contact the SP's technical contact.

**`no-gdpr-keywords` (−25)**
The page exists but contains no recognisable privacy or data-protection language. Possible causes: the page is behind a login wall, renders content via JavaScript (which this analyser does not execute), or genuinely lacks a GDPR notice. Operators should verify the page renders correctly in a browser and escalate to the SP if it is substantively empty.

**`non-https` (−20)**
The declared URL uses `http://`. The SP operator should update their privacy URL to the HTTPS equivalent and confirm the certificate is valid.

**`thin-content` or `empty-content` (−30)**
The page returns very little HTML. This often indicates a redirect target that itself requires JavaScript to load, or a page under construction. Operators should test the URL in a browser and request that the SP publish substantive content at that address.

**`few-gdpr-keywords` (−10)**
The page has some relevant language but not enough to be considered a full privacy notice. The SP operator should expand the privacy policy to cover data-controller identity, purpose of processing, data subject rights, and retention periods — all of which would naturally introduce additional matching terms.

**`slow-response` or `very-slow-response` (−10 / −20)**
These do not indicate a compliance problem, but slow pages degrade the user experience. The SP's hosting team should review server performance or CDN configuration.
