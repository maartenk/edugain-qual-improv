# AI Implementation Prompt: Placeholder/Template URL Detection

**Feature ID**: 1.11 from ROADMAP.md
**Priority**: MEDIUM-HIGH
**Effort**: 2 days
**Type**: Check

## Objective

Detect privacy statement URLs that are placeholders or templates rather than real privacy statements, preventing artificially inflated compliance statistics.

## Context

**Current State**:
- Tool marks any privacy URL as "has privacy statement"
- Placeholder URLs like `https://example.org/privacy` counted as compliant
- Template URLs like `https://your-domain.org/privacy` not detected
- "TODO" URLs considered valid

**Problem**:
- **Inflated statistics**: Privacy coverage appears higher than reality
- **Hidden quality issues**: Federation operators unaware of placeholder URLs
- **User confusion**: Users expect real privacy statements, find placeholders
- **Compliance violations**: Placeholder URLs don't meet GDPR requirements

**Real-World Examples**:
```
Placeholder URLs that should be flagged:
- https://example.org/privacy
- https://example.com/privacy-policy
- https://changeme.org/privacy
- https://localhost/privacy
- https://your-domain.org/privacystatement
- https://domain.org/privacy
- https://fixme.edu/privacy
- https://todo.university.org/privacy
```

**Impact**:
```
Before detection: "Privacy coverage: 85% (2,340/2,750 SPs)"
After detection:  "Privacy coverage: 78% (2,145/2,750 SPs)"
                  "⚠️ 195 SPs have placeholder URLs"
```

## Requirements

### Core Functionality

1. **Placeholder Pattern Detection**:
   - Domain-based patterns: `example.*`, `localhost`, `changeme.*`
   - Template patterns: `your-domain.*`, `domain.*`, `fixme.*`
   - TODO indicators: `todo.*`, `tbd.*`, `pending.*`
   - Test domains: `test.*`, `testing.*`, `dev.*`

2. **URL Quality Classification**:
   ```python
   url_quality = {
       "valid": "Real privacy URL (not a placeholder)",
       "placeholder": "Template or example domain",
       "localhost": "Local/development URL",
       "malformed": "Invalid URL format"
   }
   ```

3. **Statistics Tracking**:
   - Separate counts for valid vs. placeholder privacy URLs
   - Update summary to show: "Valid privacy statements" vs. "Placeholder URLs"
   - Per-federation placeholder detection

4. **CSV Export**:
   - Add `PrivacyURLQuality` column: `valid|placeholder|localhost|malformed`
   - Keep existing `HasPrivacyStatement` for backward compatibility
   - New export mode: `--csv privacy-placeholders` (only placeholders)

5. **Summary Output**:
   ```
   🔒 Privacy Statement Coverage:
     SPs with privacy statements: 2,340 out of 2,750 (85.1%)
       ✅ Valid privacy URLs: 2,145 (78.0%)
       ⚠️  Placeholder URLs: 195 (7.1%)

     Common Placeholders Detected:
       - example.org: 85 entities
       - localhost: 45 entities
       - your-domain.org: 32 entities
       - changeme domains: 18 entities
   ```

### Placeholder Patterns

**Domain Patterns** (regex):
```python
PLACEHOLDER_DOMAINS = [
    r"example\.(org|com|edu|net|info)",  # Example domains
    r"localhost",                         # Local development
    r"127\.0\.0\.\d+",                   # Loopback IPs
    r"changeme\.",                       # Change-me domains
    r"your-domain\.",                    # Template domains
    r"domain\.(org|com|net)",            # Generic domain
    r"fix-?me\.",                        # Fix-me domains
    r"todo\.",                           # TODO domains
    r"tbd\.",                            # To-be-determined
    r"pending\.",                        # Pending domains
    r"test(ing)?\.",                     # Test domains (maybe)
]
```

**Conservative Approach**:
- Only flag obvious placeholders (high confidence)
- Don't flag legitimate domains that happen to contain "example"
- Allow `test.example.edu` if `example.edu` is a real institution

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/validation.py`** (or new file):
   - Add `is_placeholder_url(url)` function
   - Pattern matching with compiled regexes
   - URL quality classification

2. **`src/edugain_analysis/core/analysis.py`**:
   - Call placeholder detection during entity parsing
   - Track placeholder statistics
   - Store quality classification in entity data

3. **`src/edugain_analysis/formatters/base.py`**:
   - Update summary to show valid vs. placeholder
   - Add placeholder breakdown
   - Export placeholder CSV

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--csv privacy-placeholders` export mode
   - Optional: `--strict-validation` flag (fail on placeholders)

**Edge Cases**:
- Case insensitivity: `Example.Org` should match pattern
- Subdomain handling: `privacy.example.org` vs. `example.org/privacy`
- Partial matches: Don't flag `examples.university.edu` (real domain)
- URL encoding: Normalize before matching
- IPv6 addresses: Handle `::1` loopback

## Acceptance Criteria

### Functional Requirements
- [ ] Placeholder URL detection with regex patterns
- [ ] URL quality classification (valid/placeholder/localhost/malformed)
- [ ] Statistics track valid vs. placeholder separately
- [ ] CSV includes `PrivacyURLQuality` column
- [ ] Summary shows placeholder breakdown
- [ ] `--csv privacy-placeholders` exports only placeholders
- [ ] False positive rate < 5% (real URLs flagged as placeholders)

### Quality Requirements
- [ ] High confidence placeholder detection (obvious cases only)
- [ ] No legitimate domains flagged incorrectly
- [ ] Clear documentation of placeholder patterns
- [ ] Performance overhead < 2% (regex matching is fast)
- [ ] Backward compatible statistics (still count total with privacy)

### Testing Requirements
- [ ] Test placeholder domain detection
- [ ] Test localhost and IP detection
- [ ] Test edge cases (subdomains, case sensitivity)
- [ ] Test false positive scenarios (real domains)
- [ ] Test CSV export with quality column
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_is_placeholder_url_example_domains():
    """Test detection of example domains."""
    assert is_placeholder_url("https://example.org/privacy") == "placeholder"
    assert is_placeholder_url("https://example.com/privacy-policy") == "placeholder"
    assert is_placeholder_url("https://www.example.edu/privacy") == "placeholder"

def test_is_placeholder_url_localhost():
    """Test detection of localhost URLs."""
    assert is_placeholder_url("https://localhost/privacy") == "localhost"
    assert is_placeholder_url("http://127.0.0.1/privacy") == "localhost"
    assert is_placeholder_url("https://[::1]/privacy") == "localhost"

def test_is_placeholder_url_changeme():
    """Test detection of changeme domains."""
    assert is_placeholder_url("https://changeme.org/privacy") == "placeholder"
    assert is_placeholder_url("https://your-domain.org/privacy") == "placeholder"
    assert is_placeholder_url("https://fixme.edu/privacy") == "placeholder"

def test_is_placeholder_url_valid():
    """Test that real URLs are not flagged."""
    assert is_placeholder_url("https://university.edu/privacy") == "valid"
    assert is_placeholder_url("https://sp.institution.org/privacy") == "valid"
    # Edge case: "examples" in domain name (plural, not placeholder)
    assert is_placeholder_url("https://examples.edu/privacy") == "valid"

def test_is_placeholder_url_case_insensitive():
    """Test case-insensitive matching."""
    assert is_placeholder_url("https://Example.Org/privacy") == "placeholder"
    assert is_placeholder_url("https://LOCALHOST/privacy") == "localhost"
```

## Implementation Guidance

### Step 1: Create Placeholder Detection Module

```python
# src/edugain_analysis/core/url_quality.py

import re
from urllib.parse import urlparse
from typing import Literal

# Placeholder domain patterns
PLACEHOLDER_PATTERNS = [
    # Example domains (IETF RFC 2606)
    re.compile(r'^(www\.)?example\.(org|com|net|edu|info)$', re.IGNORECASE),

    # Template/changeme domains
    re.compile(r'^changeme\.', re.IGNORECASE),
    re.compile(r'^change-me\.', re.IGNORECASE),
    re.compile(r'^your-domain\.', re.IGNORECASE),
    re.compile(r'^yourdomain\.', re.IGNORECASE),
    re.compile(r'^domain\.(org|com|net)$', re.IGNORECASE),

    # TODO/fixme domains
    re.compile(r'^(fix-?me|todo|tbd|pending)\.', re.IGNORECASE),

    # Test/dev domains (conservative - only root test domains)
    re.compile(r'^test\.(org|com|net)$', re.IGNORECASE),
    re.compile(r'^testing\.(org|com|net)$', re.IGNORECASE),
]

# Localhost patterns
LOCALHOST_PATTERNS = [
    re.compile(r'^localhost$', re.IGNORECASE),
    re.compile(r'^127\.0\.0\.\d+$'),  # IPv4 loopback
    re.compile(r'^\[::1\]$'),  # IPv6 loopback
    re.compile(r'^0\.0\.0\.0$'),  # Any interface
]

URLQuality = Literal["valid", "placeholder", "localhost", "malformed"]

def is_placeholder_url(url: str) -> URLQuality:
    """
    Detect if privacy URL is a placeholder/template.

    Args:
        url: Privacy statement URL

    Returns:
        URL quality: "valid", "placeholder", "localhost", or "malformed"
    """
    if not url or not isinstance(url, str):
        return "malformed"

    # Parse URL
    try:
        parsed = urlparse(url.strip())
        if not parsed.netloc:
            return "malformed"

        hostname = parsed.netloc.lower()

        # Remove port if present
        if ':' in hostname and not hostname.startswith('['):  # Not IPv6
            hostname = hostname.split(':')[0]

    except Exception:
        return "malformed"

    # Check for localhost patterns
    for pattern in LOCALHOST_PATTERNS:
        if pattern.match(hostname):
            return "localhost"

    # Check for placeholder patterns
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.match(hostname):
            return "placeholder"

    # Default: valid
    return "valid"

def classify_privacy_urls(entities: list[dict]) -> dict:
    """
    Classify all privacy URLs in entity list.

    Args:
        entities: List of entity dictionaries

    Returns:
        Statistics about URL quality
    """
    quality_counts = {
        "valid": 0,
        "placeholder": 0,
        "localhost": 0,
        "malformed": 0
    }

    # Track placeholder domains for summary
    placeholder_domains = {}

    for entity in entities:
        privacy_url = entity.get("privacy_url")
        if not privacy_url:
            continue

        quality = is_placeholder_url(privacy_url)
        entity["privacy_url_quality"] = quality
        quality_counts[quality] += 1

        # Track placeholder domain
        if quality == "placeholder":
            try:
                parsed = urlparse(privacy_url)
                domain = parsed.netloc.lower()
                placeholder_domains[domain] = placeholder_domains.get(domain, 0) + 1
            except:
                pass

    # Sort placeholder domains by count
    sorted_placeholders = sorted(
        placeholder_domains.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "quality_counts": quality_counts,
        "placeholder_domains": sorted_placeholders[:10]  # Top 10
    }
```

### Step 2: Integrate with Analysis

```python
# src/edugain_analysis/core/analysis.py

from .url_quality import is_placeholder_url, classify_privacy_urls

def analyze_privacy_security(root: ET.Element) -> tuple[dict, list]:
    """
    Analyze with placeholder URL detection.
    """
    stats = {
        # ... existing stats ...

        # New placeholder stats
        "sps_privacy_valid": 0,
        "sps_privacy_placeholder": 0,
        "sps_privacy_localhost": 0,
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing parsing ...

        # Extract privacy URL
        privacy_url = ...  # existing extraction

        # Classify URL quality
        if privacy_url and entity_type == "SP":
            url_quality = is_placeholder_url(privacy_url)

            # Update stats
            if url_quality == "valid":
                stats["sps_privacy_valid"] += 1
            elif url_quality == "placeholder":
                stats["sps_privacy_placeholder"] += 1
            elif url_quality == "localhost":
                stats["sps_privacy_localhost"] += 1
        else:
            url_quality = None

        entity_data = {
            # ... existing fields ...
            "privacy_url": privacy_url,
            "privacy_url_quality": url_quality,
        }
        entities_list.append(entity_data)

    # Classify all privacy URLs (for domain breakdown)
    url_quality_info = classify_privacy_urls(entities_list)

    return stats, entities_list, url_quality_info
```

### Step 3: Update Summary Output

```python
# src/edugain_analysis/formatters/base.py

def print_summary(stats: dict, url_quality_info: dict):
    """
    Print summary with placeholder URL breakdown.
    """
    # ... existing summary ...

    print("\n🔒 Privacy Statement Coverage:")
    print(f"  SPs with privacy statements: {stats['sps_has_privacy']:,} "
          f"out of {stats['total_sps']:,} ({coverage:.1f}%)")

    # Show quality breakdown
    valid_count = stats.get("sps_privacy_valid", 0)
    placeholder_count = stats.get("sps_privacy_placeholder", 0)
    localhost_count = stats.get("sps_privacy_localhost", 0)

    print(f"    ✅ Valid privacy URLs: {valid_count:,} "
          f"({valid_count/stats['total_sps']*100:.1f}%)")

    if placeholder_count > 0:
        print(f"    ⚠️  Placeholder URLs: {placeholder_count:,} "
              f"({placeholder_count/stats['total_sps']*100:.1f}%)")

    if localhost_count > 0:
        print(f"    🏠 Localhost URLs: {localhost_count:,}")

    # Show common placeholders
    if placeholder_count > 0:
        print("\n  Common Placeholders Detected:")
        for domain, count in url_quality_info["placeholder_domains"][:5]:
            print(f"    - {domain}: {count} entities")
```

### Step 4: CSV Export

```python
# src/edugain_analysis/formatters/base.py

def export_entities_csv(entities: list[dict], include_headers: bool = True):
    """
    Export entities CSV with PrivacyURLQuality column.
    """
    writer = csv.writer(sys.stdout)

    if include_headers:
        headers = [
            "Federation", "EntityType", "OrganizationName", "EntityID",
            "HasPrivacyStatement", "PrivacyStatementURL",
            "PrivacyURLQuality",  # NEW
            "HasSecurityContact", "HasSIRTFI"
        ]
        writer.writerow(headers)

    for entity in entities:
        row = [
            entity["federation"],
            entity["entity_type"],
            entity["organization"],
            entity["entity_id"],
            "Yes" if entity.get("has_privacy") else "No",
            entity.get("privacy_url", ""),
            entity.get("privacy_url_quality", ""),  # NEW
            "Yes" if entity.get("has_security_contact") else "No",
            "Yes" if entity.get("has_sirtfi") else "No",
        ]
        writer.writerow(row)

def export_privacy_placeholders_csv(entities: list[dict]):
    """
    Export only entities with placeholder privacy URLs.
    """
    placeholder_entities = [
        e for e in entities
        if e.get("privacy_url_quality") in ("placeholder", "localhost")
    ]

    # Export with standard format
    export_entities_csv(placeholder_entities)
```

### Step 5: CLI Integration

```python
# src/edugain_analysis/cli/main.py

# Add to CSV export modes
if args.csv == "privacy-placeholders":
    from ..formatters.base import export_privacy_placeholders_csv
    export_privacy_placeholders_csv(entities_list)
    return
```

## Success Metrics

- Placeholder detection accuracy > 95% (low false positives)
- All common placeholder patterns detected
- Privacy statistics more accurately reflect real compliance
- Federation operators can identify and fix placeholder URLs
- No legitimate domains incorrectly flagged
- All tests pass with 100% coverage

## References

- RFC 2606: Reserved Top Level DNS Names (example.com, example.org, etc.)
- IETF documentation domains: example.com, example.org, example.net
- Similar patterns in other tools: linters, validators, security scanners
