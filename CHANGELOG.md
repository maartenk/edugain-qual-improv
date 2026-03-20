# Changelog

All notable changes to the eduGAIN Quality Analysis Package are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - Unreleased

### Breaking Changes

**Privacy Statement Tracking Extended to IdPs**

The system now tracks privacy statements for both Identity Providers (IdPs) and Service Providers (SPs). Previously, only SPs were tracked for privacy compliance. This introduces breaking changes across CSV exports, filter behavior, and statistics output.

**CSV Format Changes:**
- **Entity CSV (`--csv entities`)**: IdP rows now display `Yes`/`No` in the `HasPrivacyStatement` column instead of `N/A`. Consumers parsing this column must update logic to handle boolean values for both entity types.
- **Federation CSV (`--csv federations`)**: Two new columns added:
  - `IdPsWithPrivacy` - Count of IdPs with privacy statements
  - `IdPsMissingPrivacy` - Count of IdPs without privacy statements

  Scripts parsing federation CSV must handle additional columns or use column-name-based parsing.

**Filter Behavior:**
- **`--csv missing-privacy`**: Now returns both SPs **and** IdPs lacking privacy statements. Previously returned SP-only results. Dashboards or scripts expecting SP-only output must filter by `EntityType` column.

**Statistics Dictionary (API consumers):**
- New keys added to the statistics dict returned by `analyze_privacy_security()`:
  - `idps_has_privacy` (int)
  - `idps_missing_privacy` (int)

  Code accessing these keys should handle their presence gracefully.

**Validation Tool Updates:**
- **`edugain-broken-privacy`**: Now validates privacy URLs for **both** SPs and IdPs. Output CSV includes IdP rows. Filter by `EntityType` column if SP-only results are required.

### Added

- **IdP Privacy Statement Tracking**: Privacy URLs for IdPs are now extracted, displayed, validated, and reported alongside SPs
- **Combined Privacy Statistics**: Summary output shows aggregate privacy coverage across both entity types with split breakdowns
- **PDF Report Enhancements**:
  - New KPI card showing IdP privacy statement coverage
  - Comparative bar chart visualizing SP vs IdP privacy compliance side-by-side
- **Enhanced Validation**: `edugain-broken-privacy` validates IdP privacy URLs with same HTTP checks applied to SPs
- **Tree-structured Output**: Terminal summary displays hierarchical privacy statistics (total, then SP/IdP breakdown)

### Changed

- Privacy statement presence now tracked and reported for all entity types (not SP-only)
- CSV exports include IdP privacy data in all relevant formats
- Statistics calculations aggregate both SP and IdP privacy metrics
- Report generation includes IdP privacy coverage in all output modes (summary, CSV, markdown, PDF)

### Migration Guide

**For CSV Consumers:**

1. **Entity CSV parsing**: Update code expecting `N/A` for IdP `HasPrivacyStatement` values:
   ```python
   # Before (SP-only logic)
   if row['EntityType'] == 'SP' and row['HasPrivacyStatement'] == 'Yes':
       ...

   # After (handles both entity types)
   if row['HasPrivacyStatement'] == 'Yes':
       ...
   ```

2. **Federation CSV parsing**: Add support for new columns or use resilient column parsing:
   ```python
   # Resilient approach (recommended)
   reader = csv.DictReader(file)
   for row in reader:
       idps_privacy = int(row.get('IdPsWithPrivacy', 0))
       idps_missing = int(row.get('IdPsMissingPrivacy', 0))
   ```

3. **Missing-privacy filter**: Filter output by entity type if SP-only results required:
   ```bash
   # Get only SPs missing privacy
   edugain-analyze --csv missing-privacy | grep ',SP,' > sp-missing-privacy.csv
   ```

**For Dashboard/Reporting Tools:**

1. Update visualizations to display IdP privacy metrics alongside SP metrics
2. Add filters allowing users to toggle between combined/SP-only/IdP-only views
3. Update KPI cards to show both entity types or provide split views
4. Verify alert thresholds account for IdP privacy tracking

**For Python API Consumers:**

If your code directly calls `analyze_privacy_security()` and accesses the statistics dict:

```python
# Defensive access (recommended)
stats = analyze_privacy_security(root)
idps_privacy = stats.get('idps_has_privacy', 0)
idps_missing = stats.get('idps_missing_privacy', 0)

# Total privacy coverage now includes both SPs and IdPs
total_privacy = stats['sps_has_privacy'] + stats['idps_has_privacy']
total_entities = stats['total_sps'] + stats['total_idps']
privacy_pct = (total_privacy / total_entities * 100) if total_entities > 0 else 0
```

**Verification Steps:**

After upgrading, verify your integration:

1. Run `edugain-analyze --csv entities` and check IdP rows have `Yes`/`No` in `HasPrivacyStatement`
2. Run `edugain-analyze --csv federations` and verify new IdP privacy columns are present
3. Run `edugain-analyze --csv missing-privacy` and confirm output includes IdP rows
4. Check that dashboard displays IdP privacy metrics (if applicable)
5. Verify any scheduled scripts handle new CSV structure without errors

---

## [2.4.3] - 2026-01-15

### Changed
- Reorganized script structure: `scripts/app/` (CLI wrappers), `scripts/dev/` (development), `scripts/maintenance/` (cleanup)
- Enhanced `make help` with user-focused guidance separating everyday CLI usage from developer workflows

### Added
- Local CI script (`scripts/dev/local-ci.sh`) mirrors GitHub Actions workflow for offline quality checks
- Environment variable toggles for CI script: `SKIP_COVERAGE`, `SKIP_DOCKER`

---

## [2.4.0] - 2026-01-14

### Added
- Privacy page content quality analysis with `--validate-content` flag
- Quality scoring algorithm (0-100 scale) detecting soft-404s, thin content, missing GDPR keywords
- New CSV export: `--csv urls-content-analysis` with per-URL quality metrics
- Multi-language GDPR keyword detection (English, German, French, Spanish, Swedish)
- Visual PDF reports with charts and KPIs

### Security
- SSRF protection preventing access to private IPs and cloud metadata endpoints
- CSV injection prevention sanitizing formula characters in entity names
- URL credential stripping in error messages and logs

---

## [2.3.0] - 2026-01-10

### Added
- SIRTFI certification tracking across all output formats
- Specialized CLI tools: `edugain-seccon`, `edugain-sirtfi`
- `edugain-broken-privacy` tool for validating privacy statement URL accessibility

---

## Earlier Versions

See git history for changes prior to v2.3.0.
