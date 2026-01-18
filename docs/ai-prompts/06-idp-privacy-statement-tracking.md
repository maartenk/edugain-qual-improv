# AI Implementation Prompt: IdP Privacy Statement Tracking

**Feature ID**: 1.1 from ROADMAP.md
**Priority**: HIGH
**Effort**: 1-2 weeks
**Type**: Check

## Objective

Extend privacy statement tracking to include Identity Providers (IdPs), not just Service Providers (SPs), providing a complete picture of federation privacy compliance.

## Context

**Current State**:
- Privacy statements tracked only for SPs (via `remd:PrivacyStatementURL`)
- IdP privacy statements marked as "N/A" in all outputs
- 23.58% of IdPs (~1,446 entities) have privacy statements that are ignored

**Problem**:
- Incomplete compliance picture: IdPs also process sensitive data
- GDPR requires privacy statements from data processors (IdPs)
- Federation operators lack visibility into IdP privacy compliance
- Misleading metrics (privacy coverage excludes half the entities)

**Rationale**:
- IdPs process credentials, attributes, and authentication logs
- Users should be informed about IdP data handling practices
- Complete federation quality assessment requires both SP and IdP tracking

## Requirements

### Core Functionality

1. **Track IdP Privacy Statements**:
   - Parse privacy statements for both SPs and IdPs
   - Store IdP privacy URLs separately from SP privacy URLs
   - Update statistics to include IdP privacy coverage

2. **Updated Statistics**:
   ```python
   stats = {
       # Existing SP stats
       "sps_has_privacy": 2681,
       "sps_missing_privacy": 1168,
       "sp_privacy_coverage_percent": 69.6,

       # New IdP stats
       "idps_has_privacy": 1446,
       "idps_missing_privacy": 4643,
       "idp_privacy_coverage_percent": 23.7,

       # Overall stats
       "total_entities_privacy": 4127,  # SPs + IdPs with privacy
       "total_privacy_coverage_percent": 40.3  # All entities
   }
   ```

3. **CSV Export Changes**:
   - Add `PrivacyStatementURL` column for IdPs (currently "N/A")
   - Keep `HasPrivacyStatement` for all entity types
   - Backward compatibility: Consider version flag

4. **Output Format Changes**:

   **Summary (Terminal)**:
   ```
   🔒 Privacy Statement Coverage:
     Service Providers (SPs):
       ✅ With privacy statements: 2,681 out of 3,849 (69.6%)
       ❌ Missing privacy statements: 1,168 out of 3,849 (30.4%)

     Identity Providers (IdPs):
       ✅ With privacy statements: 1,446 out of 6,089 (23.7%)
       ❌ Missing privacy statements: 4,643 out of 6,089 (76.3%)

     Overall Privacy Coverage: 4,127 out of 9,938 entities (41.5%)
   ```

   **Markdown Report**:
   ```markdown
   ### Privacy Statements

   | Entity Type | With Privacy | Missing Privacy | Coverage |
   |-------------|--------------|-----------------|----------|
   | SPs         | 2,681        | 1,168           | 69.6%    |
   | IdPs        | 1,446        | 4,643           | 23.7%    |
   | **Total**   | **4,127**    | **5,811**       | **41.5%**|
   ```

### Implementation Details

**Files to Modify**:

1. **`src/edugain_analysis/core/analysis.py`**:
   - Update `analyze_privacy_security()` to track IdP privacy statements
   - Add IdP privacy statistics to stats dictionary
   - Parse `remd:PrivacyStatementURL` for IdPs (same XPath as SPs)

2. **`src/edugain_analysis/formatters/base.py`**:
   - Update `print_summary()` to show IdP privacy stats
   - Update `print_summary_markdown()` for IdP privacy section
   - Update `export_federation_csv()` to include IdP privacy columns
   - Update CSV entity export to include IdP privacy URLs

3. **`src/edugain_analysis/cli/main.py`**:
   - Update CSV filtering to handle IdP privacy (`missing-privacy` includes both SPs and IdPs)
   - Optional: Add `--sp-privacy-only` flag for backward compatibility

**Current Code Analysis** (analysis.py:146-176):
```python
# Current code only processes SPs for privacy
if entity_type == "SP":
    privacy_url = entity_elem.find("./md:Extensions/mdui:UIInfo/mdui:PrivacyStatementURL", ns)
    if privacy_url is not None and privacy_url.text:
        has_privacy = True
        privacy_url_text = privacy_url.text.strip()
    else:
        has_privacy = False
        stats["sps_missing_privacy"] += 1
```

**Proposed Change**:
```python
# Process privacy statements for both SPs and IdPs
privacy_url_elem = entity_elem.find(
    "./md:Extensions/mdui:UIInfo/mdui:PrivacyStatementURL", ns
)
if privacy_url_elem is not None and privacy_url_elem.text:
    has_privacy = True
    privacy_url_text = privacy_url_elem.text.strip()
else:
    has_privacy = False
    privacy_url_text = None

# Track statistics by entity type
if entity_type == "SP":
    if not has_privacy:
        stats["sps_missing_privacy"] += 1
    else:
        stats["sps_has_privacy"] += 1
elif entity_type == "IdP":
    if not has_privacy:
        stats["idps_missing_privacy"] += 1
    else:
        stats["idps_has_privacy"] += 1
```

### Backward Compatibility

**Option A: Immediate Change (Breaking)**:
- CSV exports now include IdP privacy URLs
- CSV filtering (`--csv missing-privacy`) includes both SPs and IdPs
- Update documentation and changelog

**Option B: Opt-In Flag (Recommended)**:
- Add `--include-idp-privacy` flag
- Default behavior unchanged (backward compatible)
- Deprecate old behavior in next major version
- Clear migration path for users

**Option C: Separate CSV Columns**:
- Keep existing `HasPrivacyStatement` for SPs only
- Add new `IdPPrivacyStatement` column
- Users can filter on either column
- Most compatible but verbose

**Recommendation**: Use Option B for gradual migration.

## Acceptance Criteria

### Functional Requirements
- [ ] Privacy statements tracked for both SPs and IdPs
- [ ] IdP privacy URLs extracted and stored
- [ ] Statistics include separate IdP privacy coverage
- [ ] Summary output shows SP vs. IdP privacy breakdown
- [ ] Markdown reports include IdP privacy statistics
- [ ] CSV exports include IdP privacy URLs (with opt-in flag)
- [ ] Federation statistics track IdP privacy per federation
- [ ] `--csv missing-privacy` includes IdPs (with opt-in)

### Quality Requirements
- [ ] No breaking changes to existing CSV consumers (with opt-in approach)
- [ ] Clear documentation of new metrics
- [ ] Migration guide for users
- [ ] Performance impact < 5% (minimal parsing overhead)

### Testing Requirements
- [ ] Test IdP privacy statement extraction from metadata
- [ ] Test statistics calculation (SP vs. IdP)
- [ ] Test CSV export with IdP privacy URLs
- [ ] Test backward compatibility (without opt-in flag)
- [ ] Test summary output formatting
- [ ] Test markdown report generation
- [ ] Test federation breakdown with IdP privacy

## Testing Strategy

**Unit Tests**:
```python
def test_analyze_privacy_idp_with_statement():
    """Test IdP privacy statement extraction."""
    metadata_xml = """
    <EntityDescriptor entityID="https://idp.example.edu">
        <IDPSSODescriptor>
            ...
        </IDPSSODescriptor>
        <Extensions>
            <mdui:UIInfo>
                <mdui:PrivacyStatementURL xml:lang="en">
                    https://idp.example.edu/privacy
                </mdui:PrivacyStatementURL>
            </mdui:UIInfo>
        </Extensions>
    </EntityDescriptor>
    """
    root = ET.fromstring(metadata_xml)
    stats, entities = analyze_privacy_security(root)

    assert stats["idps_has_privacy"] == 1
    assert stats["idps_missing_privacy"] == 0
    assert entities[0]["privacy_url"] == "https://idp.example.edu/privacy"

def test_idp_privacy_coverage_calculation():
    """Test IdP privacy coverage percentage."""
    stats = {
        "total_idps": 100,
        "idps_has_privacy": 25,
        "idps_missing_privacy": 75
    }
    coverage = (stats["idps_has_privacy"] / stats["total_idps"]) * 100
    assert coverage == 25.0

def test_csv_export_includes_idp_privacy():
    """Test CSV export includes IdP privacy URLs."""
    entities = [
        {
            "entity_type": "IdP",
            "entity_id": "https://idp.example.edu",
            "privacy_url": "https://idp.example.edu/privacy",
            "has_privacy": True
        }
    ]
    # ... generate CSV ...
    assert "https://idp.example.edu/privacy" in csv_output
```

**Integration Tests**:
```python
@patch("edugain_analysis.core.metadata.get_metadata")
def test_cli_idp_privacy_summary(mock_metadata, sample_metadata_with_idp_privacy):
    """Test summary output includes IdP privacy statistics."""
    mock_metadata.return_value = sample_metadata_with_idp_privacy

    result = subprocess.run(
        ["edugain-analyze", "--include-idp-privacy"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Identity Providers (IdPs):" in result.stdout
    assert "With privacy statements:" in result.stdout
    # Check percentages are calculated
    assert "23.7%" in result.stdout or "IdPs" in result.stdout

@patch("edugain_analysis.core.metadata.get_metadata")
def test_cli_csv_missing_privacy_includes_idps(mock_metadata, sample_metadata):
    """Test --csv missing-privacy includes IdPs when flag enabled."""
    mock_metadata.return_value = sample_metadata

    result = subprocess.run(
        ["edugain-analyze", "--csv", "missing-privacy", "--include-idp-privacy"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    # Should include IdPs in output
    assert ",IdP," in result.stdout
```

## Implementation Guidance

### Step 1: Update Analysis Logic

```python
# src/edugain_analysis/core/analysis.py

def analyze_privacy_security(root: ET.Element, include_idp_privacy: bool = False) -> tuple[dict, list]:
    """
    Analyze privacy statements, security contacts, and SIRTFI certification.

    Args:
        root: Parsed XML metadata root element
        include_idp_privacy: Whether to track IdP privacy statements

    Returns:
        Tuple of (statistics dict, entities list)
    """
    stats = {
        # Existing stats...
        "sps_has_privacy": 0,
        "sps_missing_privacy": 0,

        # New IdP privacy stats (if enabled)
        "idps_has_privacy": 0,
        "idps_missing_privacy": 0,
    }

    entities_list = []

    for entity_elem in root.findall(".//md:EntityDescriptor", ns):
        # ... existing entity parsing ...

        # Privacy statement extraction (both SPs and IdPs)
        privacy_url_elem = entity_elem.find(
            "./md:Extensions/mdui:UIInfo/mdui:PrivacyStatementURL", ns
        )
        has_privacy = False
        privacy_url_text = None

        if privacy_url_elem is not None and privacy_url_elem.text:
            has_privacy = True
            privacy_url_text = privacy_url_elem.text.strip()

        # Update statistics based on entity type
        if entity_type == "SP":
            if has_privacy:
                stats["sps_has_privacy"] += 1
            else:
                stats["sps_missing_privacy"] += 1

        elif entity_type == "IdP" and include_idp_privacy:
            if has_privacy:
                stats["idps_has_privacy"] += 1
            else:
                stats["idps_missing_privacy"] += 1

        # Store entity data
        entity_data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "organization": org_name,
            "federation": federation,
            "has_privacy": has_privacy if (entity_type == "SP" or include_idp_privacy) else None,
            "privacy_url": privacy_url_text if (entity_type == "SP" or include_idp_privacy) else None,
            # ... other fields ...
        }
        entities_list.append(entity_data)

    return stats, entities_list
```

### Step 2: Update Formatters

```python
# src/edugain_analysis/formatters/base.py

def print_summary(stats: dict, include_idp_privacy: bool = False):
    """
    Print summary statistics to terminal.

    Args:
        stats: Statistics dictionary
        include_idp_privacy: Whether IdP privacy stats are included
    """
    print("\n🔒 Privacy Statement Coverage:")

    # SP privacy (always shown)
    sp_coverage = (
        (stats["sps_has_privacy"] / stats["total_sps"] * 100)
        if stats["total_sps"] > 0 else 0
    )
    print(f"  Service Providers (SPs):")
    print(f"    ✅ With privacy statements: {stats['sps_has_privacy']:,} "
          f"out of {stats['total_sps']:,} ({sp_coverage:.1f}%)")
    print(f"    ❌ Missing privacy statements: {stats['sps_missing_privacy']:,} "
          f"out of {stats['total_sps']:,}")

    # IdP privacy (if enabled)
    if include_idp_privacy:
        idp_coverage = (
            (stats["idps_has_privacy"] / stats["total_idps"] * 100)
            if stats["total_idps"] > 0 else 0
        )
        print(f"\n  Identity Providers (IdPs):")
        print(f"    ✅ With privacy statements: {stats['idps_has_privacy']:,} "
              f"out of {stats['total_idps']:,} ({idp_coverage:.1f}%)")
        print(f"    ❌ Missing privacy statements: {stats['idps_missing_privacy']:,} "
              f"out of {stats['total_idps']:,}")

        # Overall coverage
        total_with_privacy = stats["sps_has_privacy"] + stats["idps_has_privacy"]
        total_entities = stats["total_sps"] + stats["total_idps"]
        overall_coverage = (
            (total_with_privacy / total_entities * 100)
            if total_entities > 0 else 0
        )
        print(f"\n  Overall Privacy Coverage: {total_with_privacy:,} "
              f"out of {total_entities:,} entities ({overall_coverage:.1f}%)")
```

### Step 3: Update CLI

```python
# src/edugain_analysis/cli/main.py

parser.add_argument(
    "--include-idp-privacy",
    action="store_true",
    help="Track privacy statements for IdPs in addition to SPs"
)

def main():
    args = parser.parse_args()

    # ... analysis ...
    stats, entities_list = analyze_privacy_security(
        root,
        include_idp_privacy=args.include_idp_privacy
    )

    # ... output ...
    if args.report:
        print_summary(stats, include_idp_privacy=args.include_idp_privacy)
```

## Migration Guide

### For Users

**Current Behavior**:
```bash
# Privacy tracking for SPs only
edugain-analyze --csv entities
# Output: IdP rows have "N/A" for privacy fields
```

**New Behavior** (opt-in):
```bash
# Privacy tracking for both SPs and IdPs
edugain-analyze --csv entities --include-idp-privacy
# Output: IdP rows have actual privacy URLs
```

### For Downstream Consumers

**CSV Schema Changes**:
- No changes to existing columns when flag not used
- With `--include-idp-privacy`:
  - IdP rows have `HasPrivacyStatement` = Yes/No (not N/A)
  - IdP rows have `PrivacyStatementURL` populated

**Migration Checklist**:
1. Test with `--include-idp-privacy` flag
2. Update CSV parsing logic to handle IdP privacy
3. Update dashboards to show IdP privacy metrics
4. Plan migration to new flag in next major version

## Success Metrics

- IdP privacy statements tracked for all federations
- No breaking changes to existing users
- Documentation clearly explains new flag
- Federation operators report more complete compliance picture
- All tests pass with >95% coverage
- Performance overhead < 5%

## References

- Current privacy parsing: `src/edugain_analysis/core/analysis.py:146-176`
- Privacy statement XPath: `./md:Extensions/mdui:UIInfo/mdui:PrivacyStatementURL`
- SAML metadata spec: MDUI extension
- GDPR requirements: Article 13 (information to be provided)
