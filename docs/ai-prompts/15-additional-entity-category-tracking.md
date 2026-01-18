# AI Implementation Prompt: Additional Entity Category Tracking

**Feature ID**: 2.4 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 2-3 weeks
**Type**: Check

## Objective

Extend entity category tracking beyond SIRTFI to include Research & Scholarship (R&S), Code of Conduct (CoCo), Anonymous Access, and Pseudonymous Access categories, providing comprehensive visibility into compliance framework adoption across eduGAIN.

## Context

**Current State**:
- Tool only tracks SIRTFI compliance
- Other important REFEDS and GÉANT entity categories ignored
- No visibility into R&S adoption (most common category after SIRTFI)
- No tracking of data protection commitments (CoCo)
- Anonymous/Pseudonymous access patterns unknown

**Current Output** (SIRTFI Only):
```
📊 Summary Statistics:
  ...
  SIRTFI Compliance: 1,234 entities (23.1%)
```

**Improved Output** (All Categories):
```
📊 Entity Category Adoption:

  SIRTFI (Security Incident Response):
    Total: 1,234 entities (23.1%)
    SPs: 856 (69.4% of SIRTFI entities)
    IdPs: 378 (30.6% of SIRTFI entities)

  Research & Scholarship (R&S):
    Total: 3,456 entities (64.7%)
    SPs: 2,890 (83.6% of R&S entities)
    IdPs: 566 (16.4% of R&S entities)
    ⚠️  Most common category - indicates research/education use case

  Code of Conduct (CoCo):
    Total: 892 entities (16.7%)
    SPs: 734 (82.3% of CoCo entities)
    IdPs: 158 (17.7% of CoCo entities)
    ℹ️  GÉANT Data Protection commitment

  Anonymous Access:
    Total: 156 entities (2.9%)
    SPs only: 156 (100%)

  Pseudonymous Access:
    Total: 234 entities (4.4%)
    SPs: 228 (97.4%)
    IdPs: 6 (2.6%)

  Category Combinations:
    SIRTFI + R&S: 678 entities (12.7%)
    SIRTFI + CoCo: 234 entities (4.4%)
    R&S + CoCo: 456 entities (8.5%)
    All three: 123 entities (2.3%)
```

**Problem**:
- **Incomplete picture**: Only seeing SIRTFI, missing 60%+ of entities with R&S
- **No data protection visibility**: CoCo adoption unknown
- **Can't identify use cases**: R&S indicates research services vs. general IT
- **No correlation analysis**: Can't see which categories often appear together
- **Limited benchmarking**: Can't compare federation category adoption strategies

## Requirements

### Core Functionality

1. **New Entity Categories to Track**:

   ```python
   entity_categories = {
       # Existing
       "sirtfi": "http://refeds.org/sirtfi",

       # New - REFEDS Categories
       "research_and_scholarship": "http://refeds.org/category/research-and-scholarship",
       "anonymous": "http://refeds.org/category/anonymous",
       "pseudonymous": "http://refeds.org/category/pseudonymous",

       # New - GÉANT Categories
       "code_of_conduct": "http://www.geant.net/uri/dataprotection-code-of-conduct/v1",
   }
   ```

2. **Statistics Tracking**:
   - Total count per category
   - SP vs. IdP breakdown per category
   - Per-federation adoption rates
   - Category combination analysis (e.g., SIRTFI + R&S)
   - Percentage of entities in each category

3. **CSV Export**:
   - Add columns: `HasRS`, `HasCoCo`, `HasAnonymous`, `HasPseudonymous`
   - Keep existing `HasSIRTFI` column for backward compatibility
   - New export mode: `--csv categories` (show only entities with specific categories)

4. **Category Filtering**:
   ```bash
   # Show only R&S entities
   --csv entities --filter-category rs

   # Show entities with both SIRTFI and R&S
   --csv entities --filter-category sirtfi,rs

   # Show entities with any category
   --csv entities --has-any-category
   ```

5. **Summary Output Enhancement**:
   - Dedicated "Entity Category Adoption" section
   - Category rankings (most to least common)
   - Per-federation category adoption comparison
   - Category combination statistics

6. **Per-Federation Category Analysis**:
   ```
   Per-Federation Category Adoption:

   InCommon:
     SIRTFI: 234 (18.9%)
     R&S: 892 (72.3%)  ← Highest R&S adoption
     CoCo: 156 (12.6%)
     Anonymous: 12 (1.0%)
     Pseudonymous: 23 (1.9%)

   GÉANT:
     SIRTFI: 189 (21.2%)
     R&S: 567 (63.6%)
     CoCo: 234 (26.2%)  ← Highest CoCo adoption
     Anonymous: 34 (3.8%)
     Pseudonymous: 45 (5.0%)
   ```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/categories.py`** (NEW):
   - Category URI constants
   - Category detection functions
   - Category combination analysis

2. **`src/edugain_analysis/core/analysis.py`**:
   - Extend entity category detection (use same XPath as SIRTFI)
   - Track new category statistics
   - Calculate category combinations

3. **`src/edugain_analysis/formatters/base.py`**:
   - Add category adoption summary section
   - Display category combinations
   - Per-federation category breakdown

4. **`src/edugain_analysis/cli/main.py`**:
   - Add `--filter-category` flag
   - Add `--has-any-category` flag
   - Add `--csv categories` export mode

**XPath Pattern** (same as SIRTFI):
```python
# Entity categories are in Extensions/EntityAttributes
category_elements = entity_elem.findall(
    ".//md:Extensions/mdattr:EntityAttributes"
    "/saml:Attribute[@Name='http://macedir.org/entity-category']"
    "/saml:AttributeValue",
    namespaces=ns
)

# Check each category value
for category_elem in category_elements:
    category_uri = category_elem.text
    if category_uri == "http://refeds.org/category/research-and-scholarship":
        has_rs = True
    elif category_uri == "http://www.geant.net/uri/dataprotection-code-of-conduct/v1":
        has_coco = True
    # ... etc
```

**Edge Cases**:
- Multiple category values in same attribute: Count each separately
- Unknown/custom categories: Track but don't fail
- Empty AttributeValue elements: Ignore
- Categories in wrong location: Only check Extensions/EntityAttributes
- Deprecated category URIs: Handle old and new versions

## Acceptance Criteria

### Functional Requirements
- [ ] All 5 entity categories tracked (SIRTFI, R&S, CoCo, Anonymous, Pseudonymous)
- [ ] Per-category statistics calculated (total, SP/IdP breakdown)
- [ ] Per-federation adoption rates tracked
- [ ] Category combination analysis implemented
- [ ] CSV includes all category columns (HasRS, HasCoCo, etc.)
- [ ] `--filter-category` flag works correctly
- [ ] Summary shows category adoption section
- [ ] Backward compatible with existing SIRTFI tracking

### Quality Requirements
- [ ] Category detection is accurate (100% match with manual inspection)
- [ ] No false positives (non-existent categories detected)
- [ ] No false negatives (existing categories missed)
- [ ] Performance overhead < 3% (XPath is already fast)
- [ ] Clear documentation of category URIs
- [ ] Works with entities having multiple categories

### Testing Requirements
- [ ] Test category detection for each category type
- [ ] Test entities with multiple categories
- [ ] Test entities with no categories
- [ ] Test unknown/custom category URIs
- [ ] Test CSV export with category columns
- [ ] Test `--filter-category` flag
- [ ] Integration test with real metadata sample

## Testing Strategy

**Unit Tests**:
```python
def test_detect_research_and_scholarship():
    """Test R&S category detection."""
    metadata_xml = """
    <EntityDescriptor entityID="https://sp.example.edu">
        <Extensions>
            <mdattr:EntityAttributes>
                <saml:Attribute Name="http://macedir.org/entity-category">
                    <saml:AttributeValue>http://refeds.org/category/research-and-scholarship</saml:AttributeValue>
                </saml:Attribute>
            </mdattr:EntityAttributes>
        </Extensions>
        <SPSSODescriptor>...</SPSSODescriptor>
    </EntityDescriptor>
    """
    entity = ET.fromstring(metadata_xml)
    categories = detect_entity_categories(entity)

    assert categories["research_and_scholarship"] is True
    assert categories["sirtfi"] is False

def test_detect_code_of_conduct():
    """Test CoCo category detection."""
    metadata_xml = """
    <EntityDescriptor entityID="https://sp.example.edu">
        <Extensions>
            <mdattr:EntityAttributes>
                <saml:Attribute Name="http://macedir.org/entity-category">
                    <saml:AttributeValue>http://www.geant.net/uri/dataprotection-code-of-conduct/v1</saml:AttributeValue>
                </saml:Attribute>
            </mdattr:EntityAttributes>
        </Extensions>
        <SPSSODescriptor>...</SPSSODescriptor>
    </EntityDescriptor>
    """
    entity = ET.fromstring(metadata_xml)
    categories = detect_entity_categories(entity)

    assert categories["code_of_conduct"] is True

def test_detect_multiple_categories():
    """Test entity with multiple categories."""
    metadata_xml = """
    <EntityDescriptor entityID="https://sp.example.edu">
        <Extensions>
            <mdattr:EntityAttributes>
                <saml:Attribute Name="http://macedir.org/entity-category">
                    <saml:AttributeValue>http://refeds.org/sirtfi</saml:AttributeValue>
                    <saml:AttributeValue>http://refeds.org/category/research-and-scholarship</saml:AttributeValue>
                    <saml:AttributeValue>http://www.geant.net/uri/dataprotection-code-of-conduct/v1</saml:AttributeValue>
                </saml:Attribute>
            </mdattr:EntityAttributes>
        </Extensions>
        <SPSSODescriptor>...</SPSSODescriptor>
    </EntityDescriptor>
    """
    entity = ET.fromstring(metadata_xml)
    categories = detect_entity_categories(entity)

    assert categories["sirtfi"] is True
    assert categories["research_and_scholarship"] is True
    assert categories["code_of_conduct"] is True

def test_category_combination_analysis():
    """Test category combination statistics."""
    entities = [
        {"has_sirtfi": True, "has_rs": True, "has_coco": False},
        {"has_sirtfi": True, "has_rs": True, "has_coco": True},
        {"has_sirtfi": False, "has_rs": True, "has_coco": True},
    ]

    combos = analyze_category_combinations(entities)

    assert combos["sirtfi_rs"] == 2
    assert combos["sirtfi_coco"] == 1
    assert combos["rs_coco"] == 2
    assert combos["all_three"] == 1
```

## Implementation Guidance

### Step 1: Create Category Detection Module

```python
# src/edugain_analysis/core/categories.py

from typing import Dict
import xml.etree.ElementTree as ET

# Category URI constants
CATEGORY_URIS = {
    "sirtfi": "http://refeds.org/sirtfi",
    "research_and_scholarship": "http://refeds.org/category/research-and-scholarship",
    "anonymous": "http://refeds.org/category/anonymous",
    "pseudonymous": "http://refeds.org/category/pseudonymous",
    "code_of_conduct": "http://www.geant.net/uri/dataprotection-code-of-conduct/v1",
}

# Friendly display names
CATEGORY_NAMES = {
    "sirtfi": "SIRTFI (Security Incident Response)",
    "research_and_scholarship": "Research & Scholarship (R&S)",
    "anonymous": "Anonymous Access",
    "pseudonymous": "Pseudonymous Access",
    "code_of_conduct": "Code of Conduct (CoCo)",
}

def detect_entity_categories(entity_elem: ET.Element, namespaces: Dict) -> Dict[str, bool]:
    """
    Detect all entity categories for an entity.

    Args:
        entity_elem: EntityDescriptor XML element
        namespaces: XML namespace dictionary

    Returns:
        Dictionary mapping category name to boolean (present/absent)
    """
    categories = {key: False for key in CATEGORY_URIS.keys()}

    # Find all entity category attribute values
    category_elements = entity_elem.findall(
        ".//md:Extensions/mdattr:EntityAttributes"
        "/saml:Attribute[@Name='http://macedir.org/entity-category']"
        "/saml:AttributeValue",
        namespaces=namespaces
    )

    # Check each category value
    for category_elem in category_elements:
        category_uri = category_elem.text
        if category_uri:
            category_uri = category_uri.strip()

            # Match against known categories
            for category_name, expected_uri in CATEGORY_URIS.items():
                if category_uri == expected_uri:
                    categories[category_name] = True

    return categories

def analyze_category_combinations(entities: list[Dict]) -> Dict[str, int]:
    """
    Analyze common category combinations.

    Args:
        entities: List of entity dictionaries with category flags

    Returns:
        Dictionary with combination counts
    """
    combinations = {
        "sirtfi_rs": 0,
        "sirtfi_coco": 0,
        "rs_coco": 0,
        "sirtfi_rs_coco": 0,
        "any_category": 0,
    }

    for entity in entities:
        has_sirtfi = entity.get("has_sirtfi", False)
        has_rs = entity.get("has_rs", False)
        has_coco = entity.get("has_coco", False)

        # SIRTFI + R&S
        if has_sirtfi and has_rs:
            combinations["sirtfi_rs"] += 1

        # SIRTFI + CoCo
        if has_sirtfi and has_coco:
            combinations["sirtfi_coco"] += 1

        # R&S + CoCo
        if has_rs and has_coco:
            combinations["rs_coco"] += 1

        # All three
        if has_sirtfi and has_rs and has_coco:
            combinations["sirtfi_rs_coco"] += 1

        # Any category
        if any([
            entity.get("has_sirtfi"),
            entity.get("has_rs"),
            entity.get("has_coco"),
            entity.get("has_anonymous"),
            entity.get("has_pseudonymous")
        ]):
            combinations["any_category"] += 1

    return combinations

def calculate_category_stats(entities: list[Dict]) -> Dict:
    """
    Calculate per-category statistics.

    Args:
        entities: List of entity dictionaries

    Returns:
        Statistics dictionary with per-category counts
    """
    stats = {}

    for category_key in CATEGORY_URIS.keys():
        has_key = f"has_{category_key}"

        # Count total
        total = sum(1 for e in entities if e.get(has_key, False))

        # Count SPs
        sps = sum(1 for e in entities
                  if e.get(has_key, False) and e.get("entity_type") == "SP")

        # Count IdPs
        idps = sum(1 for e in entities
                   if e.get(has_key, False) and e.get("entity_type") == "IdP")

        stats[category_key] = {
            "total": total,
            "sps": sps,
            "idps": idps,
            "percentage": (total / len(entities) * 100) if entities else 0
        }

    return stats
```

### Step 2: Integrate with Analysis

```python
# src/edugain_analysis/core/analysis.py

from .categories import detect_entity_categories, calculate_category_stats, analyze_category_combinations

def analyze_privacy_security(root: ET.Element) -> tuple[dict, list]:
    """
    Analyze with entity category tracking.
    """
    stats = {
        # ... existing stats ...

        # Category statistics
        "entity_categories": {},  # Will be populated later
        "category_combinations": {},
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing entity parsing ...

        # Detect all entity categories
        categories = detect_entity_categories(entity_elem, ns)

        # Store in entity data
        entity_data = {
            # ... existing fields ...
            "has_sirtfi": categories["sirtfi"],
            "has_rs": categories["research_and_scholarship"],
            "has_coco": categories["code_of_conduct"],
            "has_anonymous": categories["anonymous"],
            "has_pseudonymous": categories["pseudonymous"],
        }

        entities_list.append(entity_data)

    # Calculate category statistics
    stats["entity_categories"] = calculate_category_stats(entities_list)
    stats["category_combinations"] = analyze_category_combinations(entities_list)

    return stats, entities_list
```

### Step 3: Update Summary Output

```python
# src/edugain_analysis/formatters/base.py

from ..core.categories import CATEGORY_NAMES

def print_category_summary(stats: dict):
    """
    Print entity category adoption summary.

    Args:
        stats: Statistics dictionary with category data
    """
    print("\n📊 Entity Category Adoption:")

    category_stats = stats.get("entity_categories", {})

    # Sort by total count (most common first)
    sorted_categories = sorted(
        category_stats.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )

    for category_key, data in sorted_categories:
        category_name = CATEGORY_NAMES.get(category_key, category_key)

        print(f"\n  {category_name}:")
        print(f"    Total: {data['total']:,} entities ({data['percentage']:.1f}%)")

        if data['total'] > 0:
            sp_pct = (data['sps'] / data['total'] * 100) if data['total'] > 0 else 0
            idp_pct = (data['idps'] / data['total'] * 100) if data['total'] > 0 else 0

            print(f"    SPs: {data['sps']:,} ({sp_pct:.1f}% of {category_key} entities)")
            print(f"    IdPs: {data['idps']:,} ({idp_pct:.1f}% of {category_key} entities)")

    # Category combinations
    combos = stats.get("category_combinations", {})
    if combos:
        print("\n  Category Combinations:")
        print(f"    SIRTFI + R&S: {combos.get('sirtfi_rs', 0):,} entities")
        print(f"    SIRTFI + CoCo: {combos.get('sirtfi_coco', 0):,} entities")
        print(f"    R&S + CoCo: {combos.get('rs_coco', 0):,} entities")
        print(f"    All three (SIRTFI + R&S + CoCo): {combos.get('sirtfi_rs_coco', 0):,} entities")
```

### Step 4: CSV Export

```python
# src/edugain_analysis/formatters/base.py

def export_entities_csv(entities: list[dict], include_headers: bool = True):
    """
    Export entities CSV with all category columns.
    """
    writer = csv.writer(sys.stdout)

    if include_headers:
        headers = [
            "Federation", "EntityType", "OrganizationName", "EntityID",
            "HasPrivacyStatement", "PrivacyStatementURL",
            "HasSecurityContact",
            "HasSIRTFI", "HasRS", "HasCoCo", "HasAnonymous", "HasPseudonymous"
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
            "Yes" if entity.get("has_security_contact") else "No",
            "Yes" if entity.get("has_sirtfi") else "No",
            "Yes" if entity.get("has_rs") else "No",
            "Yes" if entity.get("has_coco") else "No",
            "Yes" if entity.get("has_anonymous") else "No",
            "Yes" if entity.get("has_pseudonymous") else "No",
        ]
        writer.writerow(row)
```

## Success Metrics

- All 5 entity categories tracked accurately
- R&S identified as most common category (expected: 60-70% of entities)
- CoCo adoption visible per federation (GÉANT federations expected higher)
- Category combination analysis reveals patterns
- Zero false positives/negatives in category detection
- Performance overhead < 3%
- All tests pass with 100% coverage

## References

- REFEDS Entity Categories: https://refeds.org/category
- REFEDS Research & Scholarship: http://refeds.org/category/research-and-scholarship
- REFEDS SIRTFI: http://refeds.org/sirtfi
- GÉANT Data Protection Code of Conduct: https://wiki.geant.org/display/AARC/Data+Protection+Code+of+Conduct

## Dependencies

None - this is a standalone enhancement extending existing category detection.

**Future Enhancement**: Combine with Federation Benchmarking (Feature 1.13) to rank federations by category adoption rates.
