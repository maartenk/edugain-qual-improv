# IdP Privacy Statement Tracking

## Feature Overview

Version 3.0 extends privacy statement tracking from Service Providers (SPs) to include Identity Providers (IdPs). Previously, the system ignored privacy statements published by IdPs, despite approximately 23.7% of eduGAIN IdPs declaring privacy URLs in their metadata.

This document provides technical context for federation operators and developers working with the updated system.

## Motivation

Privacy statements are not exclusive to SPs. Many IdPs publish comprehensive privacy policies covering data processing, retention, and user rights under GDPR. By tracking IdP privacy statements, federation operators gain:

- **Complete visibility** into privacy compliance across all entity types
- **Gap analysis** identifying IdPs with strong security (SIRTFI) but missing privacy documentation
- **Benchmarking** comparing SP vs IdP privacy adoption within federations
- **Trend tracking** monitoring IdP privacy statement adoption over time

## Technical Implementation

### Core Analysis Changes

**File:** `src/edugain_analysis/core/analysis.py`

Privacy statement extraction now applies to all entity types:

```python
# Statistics tracking for both SPs and IdPs
stats = {
    "sps_has_privacy": 0,
    "sps_missing_privacy": 0,
    "idps_has_privacy": 0,      # NEW in v3.0
    "idps_missing_privacy": 0,  # NEW in v3.0
    # ...
}

# Privacy counting logic
if is_sp:
    stats["total_sps"] += 1
    if record.has_privacy:
        stats["sps_has_privacy"] += 1
    else:
        stats["sps_missing_privacy"] += 1
elif is_idp:
    stats["total_idps"] += 1
    if record.has_privacy:
        stats["idps_has_privacy"] += 1
    else:
        stats["idps_missing_privacy"] += 1
```

### Display Formatting

**File:** `src/edugain_analysis/formatters/base.py`

Terminal output shows hierarchical privacy statistics:

```
📊 Privacy Statement URL Coverage: 🟡 3,720/8,234 (45.2%)
  ├─ SPs: 🟡 2,681/3,849 (69.7%)
  └─ IdPs: 🔴 1,039/4,385 (23.7%)
❌ Missing: 4,514/8,234 (54.8%)
```

Color-coded indicators:
- 🟢 Green: ≥80% coverage
- 🟡 Yellow: 50-79% coverage
- 🔴 Red: <50% coverage

### CSV Export Changes

**Entity CSV:**
- IdP rows now populate `HasPrivacyStatement` (`Yes`/`No`) instead of `N/A`
- IdP rows include `PrivacyStatementURL` when present

**Federation CSV:**
- New columns: `IdPsWithPrivacy`, `IdPsMissingPrivacy`
- Enables federation-level IdP privacy analysis

### URL Validation

**File:** `src/edugain_analysis/cli/broken_privacy.py`

The broken privacy links tool now validates URLs for both entity types:

```python
# URL collection includes both SPs and IdPs
for record in records:
    if record.has_privacy and record.privacy_url:
        urls_to_validate.append(record.privacy_url)
```

Output CSV includes `EntityType` column allowing filtering:

```bash
# All broken links (SPs and IdPs)
edugain-broken-privacy > all-broken.csv

# SP-only broken links
edugain-broken-privacy | grep ',SP,' > sp-broken.csv

# IdP-only broken links
edugain-broken-privacy | grep ',IdP,' > idp-broken.csv
```

### PDF Report Enhancements

**File:** `src/edugain_analysis/formatters/pdf.py`

Visual reports include:
- **IdP Privacy KPI Card**: Displays IdP privacy coverage percentage with color-coded status
- **Comparative Bar Chart**: Side-by-side visualization of SP vs IdP privacy compliance
- **Federation Breakdown**: Per-federation IdP privacy statistics in tabular format

## Data Model

Privacy statements are extracted from metadata using XPath:

```xml
<md:EntityDescriptor entityID="https://idp.example.edu">
  <md:IDPSSODescriptor>
    <!-- IdP role descriptor -->
  </md:IDPSSODescriptor>
  <md:Organization>
    <md:OrganizationName>Example University</md:OrganizationName>
  </md:Organization>
  <mdui:UIInfo>
    <mdui:PrivacyStatementURL xml:lang="en">
      https://example.edu/privacy
    </mdui:PrivacyStatementURL>
  </mdui:UIInfo>
</md:EntityDescriptor>
```

The system extracts `<mdui:PrivacyStatementURL>` regardless of entity type (SP or IdP).

## Statistics Dictionary

The `analyze_privacy_security()` function returns expanded statistics:

```python
from edugain_analysis.core import analyze_privacy_security

stats, entity_data, federation_stats = analyze_privacy_security(root)

# Access IdP privacy metrics
idp_privacy_count = stats['idps_has_privacy']
idp_missing_count = stats['idps_missing_privacy']
total_idps = stats['total_idps']

# Calculate IdP privacy coverage percentage
idp_privacy_pct = (idp_privacy_count / total_idps * 100) if total_idps > 0 else 0

# Combined privacy coverage (SPs + IdPs)
total_privacy = stats['sps_has_privacy'] + stats['idps_has_privacy']
total_entities = stats['total_sps'] + stats['total_idps']
combined_pct = (total_privacy / total_entities * 100) if total_entities > 0 else 0
```

## Use Cases

### 1. Federation Quality Dashboard

Display split privacy metrics:

```python
import csv

with open('federations.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        federation = row['Federation']
        sp_privacy_pct = int(row['SPsWithPrivacy']) / int(row['TotalSPs']) * 100
        idp_privacy_pct = int(row['IdPsWithPrivacy']) / int(row['TotalIdPs']) * 100

        print(f"{federation}:")
        print(f"  SP Privacy: {sp_privacy_pct:.1f}%")
        print(f"  IdP Privacy: {idp_privacy_pct:.1f}%")
```

### 2. Gap Analysis: SIRTFI Without Privacy

Identify IdPs with SIRTFI certification but no privacy statement:

```python
with open('entities.csv') as f:
    reader = csv.DictReader(f)
    gaps = [
        row for row in reader
        if row['EntityType'] == 'IdP'
        and row['HasSIRTFI'] == 'Yes'
        and row['HasPrivacyStatement'] == 'No'
    ]

print(f"Found {len(gaps)} IdPs with SIRTFI but no privacy statement")
```

### 3. Trend Monitoring

Track IdP privacy adoption over time by running analysis periodically:

```bash
# Monthly cron job
0 0 1 * * edugain-analyze --csv federations > /data/privacy-$(date +\%Y-\%m).csv
```

Analyze historical data to identify improving/declining federations.

### 4. Entity Comparison

Compare privacy compliance within an organization:

```bash
# Get all entities for a specific federation
edugain-analyze --csv entities | grep 'SWAMID' > swamid-entities.csv

# Filter to entities without privacy
cat swamid-entities.csv | grep ',No,' | wc -l
```

## Performance Considerations

**URL Validation:**
- IdP privacy URLs are validated in parallel alongside SP URLs
- No additional validation time penalty (both entity types validated concurrently)
- Caching applies to all URLs regardless of entity type (7-day cache expiry)

**Statistics Calculation:**
- Minimal overhead from IdP privacy tracking
- Single-pass iteration through metadata (no separate IdP processing loop)
- Statistics dictionary includes 2 additional integer keys

**CSV Export:**
- Federation CSV adds 2 columns (negligible file size increase)
- Entity CSV format unchanged (existing columns now populated for IdPs)

## Testing

The feature includes comprehensive test coverage:

- **Unit tests:** Entity privacy extraction for both SPs and IdPs
- **Statistics tests:** Verify IdP privacy counters aggregate correctly
- **CSV tests:** Validate new columns appear in federation export
- **Validation tests:** Confirm IdP URLs validated alongside SPs
- **Formatter tests:** Check tree-structured output renders correctly

Run tests:

```bash
pytest tests/unit/test_analysis.py -v -k privacy
pytest tests/unit/formatters/test_base.py -v -k privacy
```

## Known Limitations

1. **Historical Data:** Existing dashboards using v2.x CSV exports will not show IdP privacy in historical data (column did not exist).

2. **Filter Default Behavior:** Users expecting SP-only privacy filtering must explicitly filter by `EntityType` column.

3. **Backward Compatibility:** No compatibility mode available. Upgrading to v3.0 immediately changes CSV format and filter behavior.

## Future Enhancements

Potential improvements for future versions:

- **Privacy Quality Scoring:** Extend content quality analysis to IdP privacy pages
- **Policy Comparison:** Detect when SP and IdP from same organization share privacy URL
- **Language Coverage:** Track privacy statement translations for IdPs
- **Compliance Mapping:** Link IdP privacy statements to specific GDPR articles

## References

- **Migration Guide:** [docs/migration-guide-v3.md](migration-guide-v3.md)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)
- **User Documentation:** [README.md](../README.md)
- **Source Code:** `src/edugain_analysis/core/analysis.py`

## Support

For questions or issues related to IdP privacy tracking:

1. Check the [Migration Guide](migration-guide-v3.md) for upgrade instructions
2. Review [GitHub Issues](https://github.com/maartenk/edugain-qual-improv/issues) for known issues
3. Open a new issue with:
   - Expected behavior (e.g., "SP-only filtering")
   - Actual behavior (e.g., "Both SPs and IdPs returned")
   - Command used and relevant output
