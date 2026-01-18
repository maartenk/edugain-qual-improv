# AI Implementation Prompt: Metadata Completeness Scoring

**Feature ID**: 2.2 from ROADMAP.md
**Priority**: MEDIUM-HIGH
**Effort**: 3-4 weeks
**Type**: Check

## Objective

Implement comprehensive metadata quality scoring (0-100 points) based on completeness of organization information, branding, contacts, user-facing content, and multi-lingual support to provide a holistic quality assessment beyond binary compliance checks.

## Context

**Current State**:
- Tool checks binary presence/absence (has privacy statement: yes/no)
- No assessment of metadata richness or completeness
- No quality grading or scoring system
- Federation operators can't measure "metadata quality" holistically
- No way to identify "minimal" vs. "complete" entity metadata

**Current Output** (Binary Checks):
```
SP: https://sp.example.edu
  Has privacy statement: Yes
  Has security contact: Yes
  Has SIRTFI: No
```

**Improved Output** (With Completeness Scoring):
```
SP: https://sp.example.edu
  Completeness Score: 72/100 (C+)
  Grade: C+

  Score Breakdown:
    ✅ Organization Info: 18/20 (DisplayName ✓, URL ✓, multi-lang +3)
    ⚠️  Entity Branding: 5/15 (Logo missing)
    ✅ Contact Info: 20/20 (Technical ✓, Support ✓, Admin ✓)
    ⚠️  User-Facing Info: 10/20 (Description ✓, Info URL missing)
    ✅ Registration: 15/15 (RegistrationInfo ✓, Authority ✓)
    ⚠️  Multi-Lingual: 4/10 (Only 2 languages)

  Missing Elements:
    - Logo URL
    - Information URL (mdui:InformationURL)
    - Additional language support (recommend: de, fr)
```

**Problem**:
- **No holistic view**: Can't assess overall metadata quality
- **No ranking**: Can't compare entities or federations by quality
- **No improvement targets**: Operators don't know what to add
- **Hidden gaps**: Entities may pass compliance but lack important user-facing metadata

## Requirements

### Core Functionality

1. **Completeness Scoring System**:
   Calculate 0-100 score based on weighted components:

   ```python
   scoring_components = {
       "organization_info": 20,      # DisplayName, URL, languages
       "entity_branding": 15,         # Logo URL, accessibility, formats
       "contact_info": 20,            # Technical, support, admin contacts
       "user_facing_info": 20,        # Description, Information URL
       "registration_authority": 15,  # RegistrationInfo, recognized authority
       "multilingual_support": 10     # Number of languages
   }
   # Total: 100 points
   ```

2. **Detailed Scoring Rules**:

   **Organization Information (20 points)**:
   - OrganizationDisplayName present: 10 points
   - OrganizationDisplayName in multiple languages: +5 points (2+ langs)
   - OrganizationURL present: 3 points
   - OrganizationURL accessible (HTTP 200): +2 points

   **Entity Branding (15 points)**:
   - Logo URL present: 5 points
   - Logo URL accessible (HTTP 200): 5 points
   - Multiple logo sizes/formats available: +5 points

   **Contact Information (20 points)**:
   - Technical contact present: 10 points
   - Support contact present: 5 points
   - Administrative contact present: 5 points

   **User-Facing Information (20 points)**:
   - Entity description (`mdui:Description`): 10 points
   - Information URL (`mdui:InformationURL`): 8 points
   - Information URL accessible: +2 points

   **Registration & Authority (15 points)**:
   - RegistrationInfo present: 10 points
   - RegistrationAuthority recognized (matches federation): 5 points

   **Multi-Lingual Support (10 points)**:
   - 1 language (default): 0 points
   - 2 languages: 5 points
   - 3-4 languages: 8 points
   - 5+ languages: 10 points

3. **Grading System**:
   ```python
   grade_thresholds = {
       90-100: "A",
       80-89: "B",
       70-79: "C",
       60-69: "D",
       0-59: "F"
   }
   ```

4. **Statistics Tracking**:
   - Per-entity score and grade
   - Per-federation average score
   - Overall average score across eduGAIN
   - Score distribution (histogram)
   - Grade distribution (A/B/C/D/F counts)

5. **CSV Export**:
   - Add columns: `CompletenessScore`, `CompletenessGrade`
   - Add detailed breakdown columns (optional): `OrgInfoScore`, `BrandingScore`, etc.
   - New export mode: `--csv completeness` (sorted by score, lowest first)

6. **Summary Output**:
   ```
   📊 Metadata Completeness:
     Overall average: 72.3/100 (C+)

     Grade Distribution:
       A (90-100): 234 entities (8.5%)
       B (80-89):  521 entities (18.9%)
       C (70-79):  892 entities (32.4%)
       D (60-69):  645 entities (23.4%)
       F (0-59):   458 entities (16.6%)

     Per-Federation Averages:
       🥇 GÉANT: 78.5/100 (C+)
       🥈 InCommon: 76.2/100 (C+)
       🥉 DFN-AAI: 74.8/100 (C)
       ...

     Common Missing Elements:
       - Logo URLs: 1,234 entities (44.8%)
       - Information URLs: 987 entities (35.8%)
       - Multi-lingual support: 1,567 entities (56.9%)
   ```

7. **Actionable Insights**:
   - Identify "low-hanging fruit" (entities one element away from next grade)
   - "Add logo URLs to 15 entities → improve from D to C"
   - Top improvement opportunities per federation

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/completeness.py`** (NEW):
   - `calculate_completeness_score(entity_data)` function
   - Individual component scoring functions
   - Grade calculation
   - Score distribution analysis

2. **`src/edugain_analysis/core/analysis.py`**:
   - Call completeness scoring during entity parsing
   - Extract additional metadata elements (logo, description, info URL)
   - Store scores in entity data

3. **`src/edugain_analysis/formatters/base.py`**:
   - Add completeness summary section
   - Display grade distribution
   - Show federation average scores
   - Export completeness CSV

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--csv completeness` export mode
   - Optional: `--min-completeness-score N` threshold flag

**Edge Cases**:
- Missing optional elements: Score 0 for that component (don't fail)
- Inaccessible URLs: Partial credit for presence, full credit requires accessibility
- Multi-lingual counting: Handle `xml:lang` attributes correctly
- Empty values: `<mdui:DisplayName xml:lang="en"></mdui:DisplayName>` counts as absent
- Duplicate elements: Count as one (don't give extra points)

## Acceptance Criteria

### Functional Requirements
- [ ] Completeness score (0-100) calculated for each entity
- [ ] Grade (A/B/C/D/F) assigned based on score
- [ ] All 6 scoring components implemented correctly
- [ ] Per-federation average scores calculated
- [ ] Grade distribution statistics tracked
- [ ] CSV includes `CompletenessScore` and `CompletenessGrade` columns
- [ ] `--csv completeness` exports entities sorted by score (lowest first)
- [ ] Summary shows grade distribution and federation rankings

### Quality Requirements
- [ ] Scoring is deterministic and reproducible
- [ ] Weights sum to 100 points exactly
- [ ] Edge cases handled gracefully (missing elements, empty values)
- [ ] Performance overhead < 5%
- [ ] Clear documentation of scoring methodology
- [ ] Actionable insights identify improvement opportunities

### Testing Requirements
- [ ] Test scoring with complete entity (should get ~90-100)
- [ ] Test scoring with minimal entity (should get ~20-40)
- [ ] Test each scoring component independently
- [ ] Test grade thresholds (boundary values: 90, 80, 70, 60)
- [ ] Test multi-lingual counting logic
- [ ] Test CSV export with scores
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_calculate_completeness_score_complete_entity():
    """Test scoring for fully complete entity."""
    entity_data = {
        "org_display_name": "Example University",
        "org_display_name_languages": ["en", "de", "fr"],  # 3 languages
        "org_url": "https://example.edu",
        "org_url_accessible": True,
        "logo_url": "https://example.edu/logo.png",
        "logo_url_accessible": True,
        "logo_formats": ["png", "svg"],  # Multiple formats
        "technical_contact": "tech@example.edu",
        "support_contact": "support@example.edu",
        "admin_contact": "admin@example.edu",
        "description": "Example University Service Provider",
        "info_url": "https://example.edu/info",
        "info_url_accessible": True,
        "registration_info": True,
        "registration_authority_valid": True,
        "supported_languages": 3,
    }

    score = calculate_completeness_score(entity_data)
    grade = calculate_grade(score)

    # Should score very high
    assert score >= 90
    assert grade == "A"

def test_calculate_completeness_score_minimal_entity():
    """Test scoring for minimal entity (only required elements)."""
    entity_data = {
        "org_display_name": "Minimal SP",
        "org_display_name_languages": ["en"],
        # Everything else missing
    }

    score = calculate_completeness_score(entity_data)
    grade = calculate_grade(score)

    # Should score low (only org name = 10 points)
    assert score <= 20
    assert grade == "F"

def test_organization_info_scoring():
    """Test organization information component scoring."""
    # Full score: 20 points
    full_data = {
        "org_display_name": "Test",
        "org_display_name_languages": ["en", "de"],
        "org_url": "https://test.edu",
        "org_url_accessible": True,
    }
    assert score_organization_info(full_data) == 20

    # Partial score: 10 points (name only)
    partial_data = {
        "org_display_name": "Test",
        "org_display_name_languages": ["en"],
    }
    assert score_organization_info(partial_data) == 10

def test_grade_calculation():
    """Test grade thresholds."""
    assert calculate_grade(95) == "A"
    assert calculate_grade(90) == "A"
    assert calculate_grade(89) == "B"
    assert calculate_grade(80) == "B"
    assert calculate_grade(79) == "C"
    assert calculate_grade(70) == "C"
    assert calculate_grade(69) == "D"
    assert calculate_grade(60) == "D"
    assert calculate_grade(59) == "F"
    assert calculate_grade(0) == "F"

def test_multilingual_scoring():
    """Test multi-lingual support scoring."""
    assert score_multilingual(1) == 0   # Single language
    assert score_multilingual(2) == 5   # Two languages
    assert score_multilingual(3) == 8   # Three languages
    assert score_multilingual(5) == 10  # Five or more languages
```

## Implementation Guidance

### Step 1: Create Completeness Scoring Module

```python
# src/edugain_analysis/core/completeness.py

from typing import Dict, Tuple

def calculate_completeness_score(entity_data: Dict) -> int:
    """
    Calculate metadata completeness score (0-100).

    Args:
        entity_data: Dictionary with entity metadata

    Returns:
        Completeness score (0-100)
    """
    score = 0

    # Organization Info (20 points)
    score += score_organization_info(entity_data)

    # Entity Branding (15 points)
    score += score_entity_branding(entity_data)

    # Contact Info (20 points)
    score += score_contact_info(entity_data)

    # User-Facing Info (20 points)
    score += score_user_facing_info(entity_data)

    # Registration & Authority (15 points)
    score += score_registration(entity_data)

    # Multi-Lingual Support (10 points)
    score += score_multilingual(entity_data.get("supported_languages", 1))

    return min(score, 100)  # Cap at 100

def score_organization_info(entity_data: Dict) -> int:
    """
    Score organization information (max 20 points).

    Scoring:
    - OrganizationDisplayName present: 10 points
    - Multiple languages (2+): +5 points
    - OrganizationURL present: 3 points
    - OrganizationURL accessible: +2 points
    """
    score = 0

    # Display name
    if entity_data.get("org_display_name"):
        score += 10

        # Multi-lingual bonus
        lang_count = len(entity_data.get("org_display_name_languages", []))
        if lang_count >= 2:
            score += 5

    # Organization URL
    if entity_data.get("org_url"):
        score += 3

        # Accessibility bonus
        if entity_data.get("org_url_accessible"):
            score += 2

    return score

def score_entity_branding(entity_data: Dict) -> int:
    """
    Score entity branding (max 15 points).

    Scoring:
    - Logo URL present: 5 points
    - Logo URL accessible: 5 points
    - Multiple formats: +5 points
    """
    score = 0

    if entity_data.get("logo_url"):
        score += 5

        # Accessibility
        if entity_data.get("logo_url_accessible"):
            score += 5

        # Multiple formats/sizes
        logo_formats = entity_data.get("logo_formats", [])
        if len(logo_formats) >= 2:
            score += 5

    return score

def score_contact_info(entity_data: Dict) -> int:
    """
    Score contact information (max 20 points).

    Scoring:
    - Technical contact: 10 points
    - Support contact: 5 points
    - Administrative contact: 5 points
    """
    score = 0

    if entity_data.get("technical_contact"):
        score += 10

    if entity_data.get("support_contact"):
        score += 5

    if entity_data.get("admin_contact"):
        score += 5

    return score

def score_user_facing_info(entity_data: Dict) -> int:
    """
    Score user-facing information (max 20 points).

    Scoring:
    - Description (mdui:Description): 10 points
    - Information URL: 8 points
    - Information URL accessible: +2 points
    """
    score = 0

    # Description
    if entity_data.get("description"):
        score += 10

    # Information URL
    if entity_data.get("info_url"):
        score += 8

        # Accessibility
        if entity_data.get("info_url_accessible"):
            score += 2

    return score

def score_registration(entity_data: Dict) -> int:
    """
    Score registration information (max 15 points).

    Scoring:
    - RegistrationInfo present: 10 points
    - RegistrationAuthority valid/recognized: 5 points
    """
    score = 0

    if entity_data.get("registration_info"):
        score += 10

        # Valid authority
        if entity_data.get("registration_authority_valid"):
            score += 5

    return score

def score_multilingual(language_count: int) -> int:
    """
    Score multi-lingual support (max 10 points).

    Scoring:
    - 1 language: 0 points
    - 2 languages: 5 points
    - 3-4 languages: 8 points
    - 5+ languages: 10 points
    """
    if language_count >= 5:
        return 10
    elif language_count >= 3:
        return 8
    elif language_count >= 2:
        return 5
    else:
        return 0

def calculate_grade(score: int) -> str:
    """
    Calculate letter grade from score.

    Args:
        score: Completeness score (0-100)

    Returns:
        Letter grade (A/B/C/D/F)
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def get_score_breakdown(entity_data: Dict) -> Dict[str, int]:
    """
    Get detailed score breakdown by component.

    Args:
        entity_data: Entity metadata dictionary

    Returns:
        Dictionary mapping component name to score
    """
    return {
        "organization_info": score_organization_info(entity_data),
        "entity_branding": score_entity_branding(entity_data),
        "contact_info": score_contact_info(entity_data),
        "user_facing_info": score_user_facing_info(entity_data),
        "registration": score_registration(entity_data),
        "multilingual": score_multilingual(entity_data.get("supported_languages", 1)),
    }

def identify_missing_elements(entity_data: Dict) -> list[str]:
    """
    Identify missing metadata elements for improvement.

    Args:
        entity_data: Entity metadata dictionary

    Returns:
        List of missing element descriptions
    """
    missing = []

    if not entity_data.get("logo_url"):
        missing.append("Logo URL")

    if not entity_data.get("info_url"):
        missing.append("Information URL (mdui:InformationURL)")

    if not entity_data.get("support_contact"):
        missing.append("Support contact")

    if not entity_data.get("admin_contact"):
        missing.append("Administrative contact")

    if not entity_data.get("description"):
        missing.append("Entity description (mdui:Description)")

    lang_count = entity_data.get("supported_languages", 1)
    if lang_count < 3:
        missing.append(f"Additional language support (currently {lang_count})")

    return missing
```

### Step 2: Integrate with Analysis

```python
# src/edugain_analysis/core/analysis.py

from .completeness import (
    calculate_completeness_score,
    calculate_grade,
    get_score_breakdown,
    identify_missing_elements
)

def analyze_privacy_security(root: ET.Element) -> tuple[dict, list]:
    """
    Analyze with completeness scoring.
    """
    stats = {
        # ... existing stats ...

        # Completeness statistics
        "completeness_scores": [],  # List of all scores
        "completeness_grades": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        "completeness_average": 0.0,
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing entity parsing ...

        # Extract additional completeness metadata
        entity_metadata = extract_completeness_metadata(entity_elem)

        # Calculate completeness score
        completeness_score = calculate_completeness_score(entity_metadata)
        completeness_grade = calculate_grade(completeness_score)

        # Update statistics
        stats["completeness_scores"].append(completeness_score)
        stats["completeness_grades"][completeness_grade] += 1

        # Store in entity data
        entity_data = {
            # ... existing fields ...
            "completeness_score": completeness_score,
            "completeness_grade": completeness_grade,
            "score_breakdown": get_score_breakdown(entity_metadata),
            "missing_elements": identify_missing_elements(entity_metadata),
        }

        entities_list.append(entity_data)

    # Calculate average
    if stats["completeness_scores"]:
        stats["completeness_average"] = sum(stats["completeness_scores"]) / len(stats["completeness_scores"])

    return stats, entities_list

def extract_completeness_metadata(entity_elem: ET.Element) -> Dict:
    """
    Extract all metadata needed for completeness scoring.

    Args:
        entity_elem: EntityDescriptor XML element

    Returns:
        Dictionary with all completeness-relevant fields
    """
    metadata = {}

    # Organization info
    org = entity_elem.find(".//md:Organization", ns)
    if org is not None:
        display_names = org.findall(".//md:OrganizationDisplayName", ns)
        if display_names:
            metadata["org_display_name"] = display_names[0].text
            metadata["org_display_name_languages"] = [
                dn.get("{http://www.w3.org/XML/1998/namespace}lang", "en")
                for dn in display_names
            ]

        org_url_elem = org.find(".//md:OrganizationURL", ns)
        if org_url_elem is not None and org_url_elem.text:
            metadata["org_url"] = org_url_elem.text
            # TODO: Check accessibility (requires HTTP request)

    # MDUI elements
    mdui_info = entity_elem.find(".//mdui:UIInfo", ns)
    if mdui_info is not None:
        # Logo
        logo_elem = mdui_info.find(".//mdui:Logo", ns)
        if logo_elem is not None and logo_elem.text:
            metadata["logo_url"] = logo_elem.text

        # Description
        desc_elem = mdui_info.find(".//mdui:Description", ns)
        if desc_elem is not None and desc_elem.text:
            metadata["description"] = desc_elem.text

        # Information URL
        info_url_elem = mdui_info.find(".//mdui:InformationURL", ns)
        if info_url_elem is not None and info_url_elem.text:
            metadata["info_url"] = info_url_elem.text

    # Contacts
    contacts = entity_elem.findall(".//md:ContactPerson", ns)
    for contact in contacts:
        contact_type = contact.get("contactType")
        email = contact.find(".//md:EmailAddress", ns)
        if email is not None:
            if contact_type == "technical":
                metadata["technical_contact"] = email.text
            elif contact_type == "support":
                metadata["support_contact"] = email.text
            elif contact_type == "administrative":
                metadata["admin_contact"] = email.text

    # Registration info
    reg_info = entity_elem.find(".//mdrpi:RegistrationInfo", ns)
    if reg_info is not None:
        metadata["registration_info"] = True
        reg_authority = reg_info.get("registrationAuthority")
        # TODO: Validate authority against known federations
        metadata["registration_authority_valid"] = reg_authority is not None

    # Count languages across all elements
    all_lang_elements = entity_elem.findall(".//*[@{http://www.w3.org/XML/1998/namespace}lang]")
    languages = set(
        elem.get("{http://www.w3.org/XML/1998/namespace}lang")
        for elem in all_lang_elements
    )
    metadata["supported_languages"] = len(languages)

    return metadata
```

### Step 3: Update Summary Output

```python
# src/edugain_analysis/formatters/base.py

def print_completeness_summary(stats: dict):
    """
    Print metadata completeness summary.

    Args:
        stats: Statistics dictionary with completeness data
    """
    print("\n📊 Metadata Completeness:")

    avg_score = stats.get("completeness_average", 0)
    avg_grade = calculate_grade(int(avg_score))
    print(f"  Overall average: {avg_score:.1f}/100 ({avg_grade})")

    # Grade distribution
    print("\n  Grade Distribution:")
    grades = stats.get("completeness_grades", {})
    total = sum(grades.values())

    for grade in ["A", "B", "C", "D", "F"]:
        count = grades.get(grade, 0)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"    {grade} (90-100 if A, etc.): {count:,} entities ({percentage:.1f}%)")

    # Per-federation averages (if available)
    # ... (calculate from federation_stats)

    # Common missing elements
    # ... (aggregate from all entities)
```

## Success Metrics

- Clear quality differentiation between "minimal" and "complete" metadata
- Federation operators can track completeness improvements over time
- Identify specific missing elements for each entity
- Federation rankings by average completeness score
- All scoring components tested and validated
- Performance overhead < 5%

## References

- SAML metadata specification for element names
- MDUI (Metadata UI) extension specification
- Similar scoring: Google PageSpeed score, SSL Labs rating

## Dependencies

**Optional Enhancement**: Combine with Historical Snapshot Storage (Feature 1.4) to track:
- Completeness score improvements over time
- Which federations improve metadata quality fastest
- Correlation between completeness and compliance

**Future Extension**:
- Accessibility checking for logo/info URLs
- Content quality analysis (description length, language quality)
- Registration authority validation against known federation list
