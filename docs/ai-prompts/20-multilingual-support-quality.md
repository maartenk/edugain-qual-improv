# AI Implementation Prompt: Multi-Lingual Support Quality Assessment

**Feature ID**: 3.5 from ROADMAP.md
**Priority**: LOW
**Effort**: 4-5 weeks
**Type**: Check

## Objective

Assess quality of multi-lingual metadata to ensure accessibility and usability for international users, validate federation language alignment, check translation consistency, and detect encoding issues.

## Context

**Current State**:
- Tool ignores multi-lingual metadata elements
- No visibility into language support across entities
- Can't identify entities with poor internationalization
- No metrics for language diversity per federation
- Language mismatches go undetected (e.g., German federation with only English metadata)

**Problem Scenarios**:

**Accessibility**: "Our federation serves Spanish-speaking users, but how many entities actually provide Spanish metadata?"
- Current limitation: No language coverage metrics
- Need: Per-federation language statistics

**Quality Issues**: "Some entities have DisplayName in 3 languages but PrivacyURL only in English. How do we find these inconsistencies?"
- Current limitation: No consistency checking
- Need: Cross-element language validation

**Federation Alignment**: "We're a German federation. Why do 30% of our entities only have English metadata?"
- Current limitation: No language alignment checking
- Need: Federation vs. entity language matching

**Current Workflow** (Manual):
```
1. Open metadata XML in editor
2. Search for xml:lang attributes
3. Manually count languages per entity
4. Check if DisplayName, Description, PrivacyURL have same languages
5. Time-consuming and error-prone
```

**Improved Workflow** (Automated):
```
1. Run tool with language analysis:
   edugain-analyze --language-analysis

2. Get automated report:
   "Language Coverage:
    - Entities with 1 language: 1,234 (44.9%)
    - Entities with 2+ languages: 1,516 (55.1%)
    - Most common: en (98%), de (42%), fr (28%)

    Federation Language Alignment:
    - DFN-AAI (German): 78% have 'de' metadata ✅
    - RENATER (French): 65% have 'fr' metadata ⚠️
    - InCommon (English): 99% have 'en' metadata ✅

    Inconsistencies Found:
    - 234 entities: DisplayName in 3 langs, Description in 1
    - 89 entities: All elements in 'en' except PrivacyURL
    ..."

3. Export language quality CSV
4. Contact entity operators to improve translations
```

## Requirements

### Core Functionality

1. **Language Detection**:

   Parse `xml:lang` attributes from all metadata elements:
   ```xml
   <mdui:DisplayName xml:lang="en">Example University</mdui:DisplayName>
   <mdui:DisplayName xml:lang="de">Beispiel-Universität</mdui:DisplayName>
   <mdui:DisplayName xml:lang="fr">Université Exemple</mdui:DisplayName>

   <mdui:Description xml:lang="en">A research university...</mdui:Description>
   <mdui:Description xml:lang="de">Eine Forschungsuniversität...</mdui:Description>

   <mdui:PrivacyStatementURL xml:lang="en">https://example.edu/privacy</mdui:PrivacyStatementURL>
   ```

   Track languages per element type:
   - `mdui:DisplayName`
   - `mdui:Description`
   - `mdui:InformationURL`
   - `mdui:PrivacyStatementURL`
   - `mdui:Logo` (less common)
   - `Organization/OrganizationDisplayName`

2. **Language Coverage Metrics**:

   **Per-Entity**:
   ```python
   entity_language_info = {
       "supported_languages": ["en", "de", "fr"],  # All languages used
       "language_count": 3,
       "primary_language": "en",  # Most common language
       "element_languages": {
           "display_name": ["en", "de", "fr"],
           "description": ["en", "de"],
           "privacy_url": ["en"],
           "info_url": ["en", "de", "fr"],
       },
       "is_multilingual": True,  # 2+ languages
       "has_inconsistencies": True,  # Different langs per element
   }
   ```

   **Per-Federation**:
   ```python
   federation_language_stats = {
       "language_distribution": {
           "en": {"count": 1234, "percentage": 98.2},
           "de": {"count": 892, "percentage": 71.0},
           "fr": {"count": 456, "percentage": 36.3},
       },
       "monolingual_entities": 565,  # Only 1 language
       "multilingual_entities": 691,  # 2+ languages
       "average_languages_per_entity": 2.3,
       "expected_language": "de",  # Based on federation
       "language_alignment_rate": 78.5,  # % with expected language
   }
   ```

3. **Federation Language Alignment**:

   Map federations to expected languages:
   ```python
   federation_languages = {
       "DFN-AAI": "de",           # German
       "RENATER": "fr",           # French
       "SWITCHaai": "de",         # Swiss German/French/Italian (multi)
       "UKAMF": "en",             # English
       "InCommon": "en",          # English
       "GÉANT": None,             # International (no single expected language)
       # ... etc
   }
   ```

   Check alignment:
   - Does entity have metadata in federation's expected language?
   - Calculate alignment percentage per federation
   - Flag entities missing expected language

4. **Translation Consistency Checking**:

   Detect inconsistencies:
   ```python
   consistency_issues = [
       {
           "entity_id": "sp.example.edu",
           "issue": "incomplete_translations",
           "details": "DisplayName in 3 languages (en, de, fr) but Description only in 1 (en)",
       },
       {
           "entity_id": "sp2.example.edu",
           "issue": "privacy_url_language_mismatch",
           "details": "All elements in en+de, but PrivacyURL only in en",
       },
       {
           "entity_id": "sp3.example.edu",
           "issue": "missing_primary_language",
           "details": "Has de, fr but missing expected en",
       }
   ]
   ```

5. **Character Encoding Detection** (Optional):

   Detect mojibake (character encoding issues):
   ```python
   # Common patterns indicating encoding problems
   mojibake_patterns = [
       "Ã©",  # é encoded as UTF-8, displayed as Latin-1
       "â€™", # ' (smart quote) encoding issue
       "Ã¼",  # ü encoding issue
   ]

   # Simple heuristic: unusual character combinations
   def detect_mojibake(text: str) -> bool:
       for pattern in mojibake_patterns:
           if pattern in text:
               return True
       return False
   ```

6. **Statistics Tracking**:

   **Overall**:
   - Total unique languages used
   - Language popularity ranking
   - Monolingual vs. multilingual distribution
   - Average languages per entity

   **Per-Federation**:
   - Top languages used
   - Alignment with expected language
   - Multilingual adoption rate

7. **CSV Export**:

   Add columns:
   - `SupportedLanguages` (comma-separated: "en,de,fr")
   - `LanguageCount` (integer)
   - `PrimaryLanguage` (most common)
   - `IsMultilingual` (Yes/No)
   - `HasLanguageInconsistencies` (Yes/No)
   - `InconsistencyDetails` (text description)
   - `HasExpectedLanguage` (Yes/No for federation alignment)

   New export mode:
   ```bash
   # Export entities with language inconsistencies
   --csv language-inconsistencies

   # Export monolingual entities
   --csv entities --filter monolingual

   # Export entities missing federation language
   --csv entities --missing-federation-language
   ```

8. **Summary Output**:

   ```
   🌍 Multi-Lingual Support Quality:

   Language Coverage:
     Total languages used: 23
     Top 5 languages:
       1. en (English): 2,689 entities (97.8%)
       2. de (German): 1,156 entities (42.0%)
       3. fr (French): 678 entities (24.7%)
       4. es (Spanish): 345 entities (12.5%)
       5. it (Italian): 234 entities (8.5%)

   Multi-Lingual Adoption:
     Monolingual (1 language): 1,234 entities (44.9%)
     Multi-lingual (2+ languages): 1,516 entities (55.1%)
     Highly multi-lingual (5+ languages): 89 entities (3.2%)

   Federation Language Alignment:
     DFN-AAI (expected: de):
       ✅ 892/1000 entities have 'de' (89.2%)
       ⚠️  108 entities missing 'de' metadata

     RENATER (expected: fr):
       ⚠️  567/800 entities have 'fr' (70.9%)
       ❌ 233 entities missing 'fr' metadata

   Translation Consistency Issues:
     234 entities: Incomplete translations (some elements missing languages)
     89 entities: PrivacyURL not translated (all other elements are)
     45 entities: DisplayName in >3 languages, Description in 1

   Character Encoding Issues:
     12 entities: Potential mojibake detected in DisplayName
   ```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/language.py`** (NEW):
   - Language attribute parsing
   - Language detection and counting
   - Consistency checking
   - Alignment validation
   - Encoding issue detection (optional)

2. **`src/edugain_analysis/core/analysis.py`**:
   - Call language analysis during entity parsing
   - Extract `xml:lang` from all relevant elements
   - Calculate and store language metrics

3. **`src/edugain_analysis/formatters/base.py`**:
   - Add language analysis summary section
   - Display language distribution
   - Show inconsistencies
   - Export language quality CSV

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--language-analysis` flag
   - Add `--csv language-inconsistencies`
   - Add filtering flags

**Federation Language Mapping**:
Create configuration file or hardcode mapping:
```python
# src/edugain_analysis/config/federation_languages.py

FEDERATION_LANGUAGES = {
    # German federations
    "DFN-AAI": ["de"],
    "AAI@EduHr": ["hr"],

    # French federations
    "RENATER": ["fr"],
    "eduID.cz": ["cs"],

    # Multi-lingual federations
    "SWITCHaai": ["de", "fr", "it"],  # Switzerland
    "IDEM": ["it"],

    # English federations
    "UKAMF": ["en"],
    "InCommon": ["en"],
    "AAF": ["en"],  # Australia

    # International (no specific expected language)
    "GÉANT": None,
    "eduGAIN": None,
}
```

**Edge Cases**:
- Missing `xml:lang` attribute: Assume default language (usually "en")
- Invalid language codes: Log warning, skip
- Mixed language codes (e.g., "en-US" vs "en"): Normalize to base language
- Empty element with `xml:lang`: Count as present
- Encoding issues: Heuristic detection only (not 100% accurate)

## Acceptance Criteria

### Functional Requirements
- [ ] Language detection from `xml:lang` attributes
- [ ] Per-entity language count and list
- [ ] Per-federation language statistics
- [ ] Federation language alignment checking
- [ ] Translation consistency validation
- [ ] Character encoding issue detection (optional)
- [ ] CSV export includes all language columns
- [ ] `--csv language-inconsistencies` exports problematic entities
- [ ] Summary shows language distribution and alignment

### Quality Requirements
- [ ] Language detection is accurate (no false negatives)
- [ ] Alignment checking is correct for all federations
- [ ] Consistency checking produces actionable results
- [ ] No false positives for encoding issues
- [ ] Performance overhead < 5%
- [ ] Works with all valid ISO 639-1 language codes

### Testing Requirements
- [ ] Test language detection from various elements
- [ ] Test multi-lingual entity handling
- [ ] Test consistency checking logic
- [ ] Test federation alignment validation
- [ ] Test encoding detection (with known mojibake examples)
- [ ] Test CSV export with language columns
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_extract_languages_from_entity():
    """Test language extraction."""
    metadata_xml = """
    <EntityDescriptor>
        <Extensions>
            <mdui:UIInfo>
                <mdui:DisplayName xml:lang="en">Example</mdui:DisplayName>
                <mdui:DisplayName xml:lang="de">Beispiel</mdui:DisplayName>
                <mdui:Description xml:lang="en">Description</mdui:Description>
            </mdui:UIInfo>
        </Extensions>
    </EntityDescriptor>
    """

    entity = ET.fromstring(metadata_xml)
    lang_info = extract_language_info(entity)

    assert set(lang_info["supported_languages"]) == {"en", "de"}
    assert lang_info["language_count"] == 2
    assert lang_info["element_languages"]["display_name"] == ["en", "de"]
    assert lang_info["element_languages"]["description"] == ["en"]

def test_detect_consistency_issues():
    """Test consistency checking."""
    lang_info = {
        "element_languages": {
            "display_name": ["en", "de", "fr"],
            "description": ["en"],
            "privacy_url": ["en"],
        }
    }

    issues = detect_language_inconsistencies(lang_info)

    assert len(issues) > 0
    assert any("incomplete_translations" in issue for issue in issues)

def test_federation_language_alignment():
    """Test federation alignment."""
    entity_languages = ["en", "fr"]
    federation = "RENATER"  # Expected: fr

    has_alignment = check_federation_alignment(entity_languages, federation)

    assert has_alignment is True  # Has 'fr'

    # Entity without expected language
    entity_languages_bad = ["en", "de"]
    has_alignment_bad = check_federation_alignment(entity_languages_bad, federation)

    assert has_alignment_bad is False  # Missing 'fr'

def test_mojibake_detection():
    """Test encoding issue detection."""
    # Common mojibake pattern
    text_with_mojibake = "CafÃ©"  # Should be "Café"
    assert detect_mojibake(text_with_mojibake) is True

    # Clean text
    text_clean = "Café"
    assert detect_mojibake(text_clean) is False
```

## Implementation Guidance

### Step 1: Create Language Analysis Module

```python
# src/edugain_analysis/core/language.py

import xml.etree.ElementTree as ET
from typing import Dict, List
from collections import Counter

# Federation expected languages
FEDERATION_LANGUAGES = {
    "DFN-AAI": ["de"],
    "RENATER": ["fr"],
    "SWITCHaai": ["de", "fr", "it"],
    "UKAMF": ["en"],
    "InCommon": ["en"],
    # ... etc
}

def extract_language_info(entity_elem: ET.Element, namespaces: Dict) -> Dict:
    """
    Extract language information from entity metadata.

    Args:
        entity_elem: EntityDescriptor XML element
        namespaces: XML namespace dictionary

    Returns:
        Dictionary with language information
    """
    # Elements to check for language attributes
    language_elements = {
        "display_name": ".//mdui:DisplayName",
        "description": ".//mdui:Description",
        "info_url": ".//mdui:InformationURL",
        "privacy_url": ".//mdui:PrivacyStatementURL",
        "logo": ".//mdui:Logo",
        "org_display_name": ".//md:Organization/md:OrganizationDisplayName",
    }

    element_languages = {}
    all_languages = []

    for element_name, xpath in language_elements.items():
        elements = entity_elem.findall(xpath, namespaces)
        langs = []

        for elem in elements:
            lang = elem.get("{http://www.w3.org/XML/1998/namespace}lang")
            if lang:
                # Normalize language code (e.g., "en-US" -> "en")
                base_lang = lang.split("-")[0].lower()
                langs.append(base_lang)
                all_languages.append(base_lang)

        element_languages[element_name] = langs

    # Count occurrences to find primary language
    if all_languages:
        lang_counter = Counter(all_languages)
        primary_language = lang_counter.most_common(1)[0][0]
    else:
        primary_language = "unknown"

    # Unique languages
    supported_languages = sorted(set(all_languages))

    return {
        "supported_languages": supported_languages,
        "language_count": len(supported_languages),
        "primary_language": primary_language,
        "element_languages": element_languages,
        "is_multilingual": len(supported_languages) >= 2,
    }

def detect_language_inconsistencies(lang_info: Dict) -> List[str]:
    """
    Detect language consistency issues.

    Args:
        lang_info: Language information dictionary

    Returns:
        List of inconsistency descriptions
    """
    issues = []
    element_langs = lang_info["element_languages"]

    # Get all unique element types that have languages
    elements_with_langs = {
        elem: langs for elem, langs in element_langs.items()
        if langs
    }

    if not elements_with_langs:
        return issues

    # Find the element with most languages
    max_langs = max(len(langs) for langs in elements_with_langs.values())
    min_langs = min(len(langs) for langs in elements_with_langs.values())

    # Inconsistency: some elements have more languages than others
    if max_langs > min_langs:
        issues.append("incomplete_translations")

    # Check for specific common issues
    display_name_langs = set(element_langs.get("display_name", []))
    description_langs = set(element_langs.get("description", []))

    if display_name_langs and description_langs:
        if display_name_langs != description_langs:
            issues.append("display_name_description_mismatch")

    # Privacy URL often not translated
    privacy_langs = set(element_langs.get("privacy_url", []))
    if privacy_langs and display_name_langs:
        if privacy_langs < display_name_langs:
            issues.append("privacy_url_not_fully_translated")

    return issues

def check_federation_alignment(
    entity_languages: List[str],
    federation_name: str
) -> bool:
    """
    Check if entity has expected federation language(s).

    Args:
        entity_languages: List of languages entity supports
        federation_name: Federation name

    Returns:
        True if entity has expected language(s), False otherwise
    """
    expected_languages = FEDERATION_LANGUAGES.get(federation_name)

    # No expected language for this federation (international)
    if expected_languages is None:
        return True

    # Check if at least one expected language is present
    for expected_lang in expected_languages:
        if expected_lang in entity_languages:
            return True

    return False

def detect_mojibake(text: str) -> bool:
    """
    Detect potential character encoding issues (mojibake).

    Args:
        text: Text to check

    Returns:
        True if mojibake likely present, False otherwise
    """
    if not text:
        return False

    # Common mojibake patterns (UTF-8 displayed as Latin-1)
    mojibake_patterns = [
        "Ã©",  # é
        "Ã¨",  # è
        "Ã ",  # à
        "Ã¼",  # ü
        "Ã¶",  # ö
        "Ã¤",  # ä
        "â€™", # '
        "â€œ", # "
        "â€",  # "
    ]

    for pattern in mojibake_patterns:
        if pattern in text:
            return True

    return False

def calculate_language_statistics(entities: List[Dict]) -> Dict:
    """
    Calculate language statistics across all entities.

    Args:
        entities: List of entity dictionaries with language info

    Returns:
        Language statistics dictionary
    """
    lang_counter = Counter()
    monolingual_count = 0
    multilingual_count = 0
    total_language_count = 0

    for entity in entities:
        lang_info = entity.get("language_info", {})
        languages = lang_info.get("supported_languages", [])

        # Count language occurrences
        for lang in languages:
            lang_counter[lang] += 1

        # Count monolingual vs multilingual
        lang_count = len(languages)
        if lang_count == 1:
            monolingual_count += 1
        elif lang_count > 1:
            multilingual_count += 1

        total_language_count += lang_count

    total_entities = len(entities)
    avg_languages = total_language_count / total_entities if total_entities > 0 else 0

    return {
        "language_distribution": dict(lang_counter.most_common()),
        "monolingual_entities": monolingual_count,
        "multilingual_entities": multilingual_count,
        "average_languages_per_entity": avg_languages,
        "total_unique_languages": len(lang_counter),
    }
```

### Step 2: Integrate with Analysis

```python
# src/edugain_analysis/core/analysis.py

from .language import (
    extract_language_info,
    detect_language_inconsistencies,
    check_federation_alignment,
    detect_mojibake
)

def analyze_privacy_security(root: ET.Element) -> tuple[dict, list]:
    """
    Analyze with language quality assessment.
    """
    stats = {
        # ... existing stats ...

        # Language statistics
        "language_stats": {},  # Will be calculated at end
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing entity parsing ...

        # Extract language information
        lang_info = extract_language_info(entity_elem, ns)

        # Check for inconsistencies
        inconsistencies = detect_language_inconsistencies(lang_info)

        # Check federation alignment
        federation = entity_data.get("federation", "")
        has_fed_alignment = check_federation_alignment(
            lang_info["supported_languages"],
            federation
        )

        # Check for encoding issues in DisplayName
        display_name = entity_data.get("organization", "")
        has_mojibake = detect_mojibake(display_name)

        # Store in entity data
        entity_data = {
            # ... existing fields ...
            "language_info": lang_info,
            "language_inconsistencies": inconsistencies,
            "has_federation_language_alignment": has_fed_alignment,
            "has_encoding_issues": has_mojibake,
        }

        entities_list.append(entity_data)

    # Calculate overall language statistics
    from .language import calculate_language_statistics
    stats["language_stats"] = calculate_language_statistics(entities_list)

    return stats, entities_list
```

### Step 3: Update Summary Output

```python
# src/edugain_analysis/formatters/base.py

def print_language_summary(stats: dict, entities: list[dict]):
    """
    Print multi-lingual support summary.

    Args:
        stats: Statistics dictionary with language data
        entities: Entity list for detailed analysis
    """
    lang_stats = stats.get("language_stats", {})

    print("\n🌍 Multi-Lingual Support Quality:")

    # Language coverage
    print("\n  Language Coverage:")
    print(f"    Total languages used: {lang_stats['total_unique_languages']}")

    print("\n    Top 5 languages:")
    for i, (lang, count) in enumerate(list(lang_stats["language_distribution"].items())[:5], start=1):
        pct = (count / len(entities) * 100) if entities else 0
        print(f"      {i}. {lang}: {count:,} entities ({pct:.1f}%)")

    # Multi-lingual adoption
    print("\n  Multi-Lingual Adoption:")
    mono = lang_stats["monolingual_entities"]
    multi = lang_stats["multilingual_entities"]
    total = mono + multi

    mono_pct = (mono / total * 100) if total > 0 else 0
    multi_pct = (multi / total * 100) if total > 0 else 0

    print(f"    Monolingual (1 language): {mono:,} entities ({mono_pct:.1f}%)")
    print(f"    Multi-lingual (2+ languages): {multi:,} entities ({multi_pct:.1f}%)")
    print(f"    Average languages per entity: {lang_stats['average_languages_per_entity']:.1f}")

    # Inconsistencies
    inconsistent_entities = [
        e for e in entities
        if e.get("language_inconsistencies", [])
    ]

    if inconsistent_entities:
        print(f"\n  Translation Consistency Issues:")
        print(f"    {len(inconsistent_entities):,} entities have language inconsistencies")

    # Encoding issues
    encoding_issues = [
        e for e in entities
        if e.get("has_encoding_issues", False)
    ]

    if encoding_issues:
        print(f"\n  Character Encoding Issues:")
        print(f"    {len(encoding_issues):,} entities: Potential mojibake detected")
```

## Success Metrics

- Language detection accuracy > 99%
- Inconsistency detection helps improve translation quality
- Federation alignment checking identifies gaps
- 50%+ increase in multi-lingual entity adoption (long-term)
- Character encoding issues resolved
- All tests pass with 100% coverage

## References

- ISO 639-1 language codes
- XML `xml:lang` attribute specification
- MDUI (Metadata UI) extension specification
- UTF-8 and character encoding best practices

## Dependencies

None - standalone feature

**Future Enhancement**:
- Machine translation quality detection (ML-based)
- Language-specific content validation
- Integration with Completeness Scoring (Feature 2.2) for multi-lingual bonus points
