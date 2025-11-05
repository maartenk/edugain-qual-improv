# Future Enhancements and Considerations

This document tracks potential improvements and features for future versions of the eduGAIN quality improvement analysis tool.

**Status:** Planning / Discussion
**Last Updated:** 2025-10-12

---

## 1. IdP Privacy Statement Tracking

**Priority:** Medium
**Complexity:** Low
**Status:** Under Consideration

### Background

Current implementation only tracks privacy statements for Service Providers (SPs), marking IdP privacy statements as "N/A" in all outputs. However, analysis of eduGAIN metadata reveals that **approximately 23.58% of IdPs (1,446 out of 6,133) actually have privacy statements**.

### Rationale for IdPs Having Privacy Statements

IdPs have legitimate reasons to provide privacy statements:

1. **Data Processing & Storage**: IdPs store sensitive personal information (credentials, user attributes)
2. **Attribute Release**: Users should be informed about what attributes are shared with SPs
3. **GDPR & Privacy Law Compliance**: Privacy regulations require transparency from data processors
4. **User Trust & Transparency**: Users need to trust their IdP with authentication credentials
5. **Federation Requirements**: Some federations appear to require or encourage privacy statements from all participants

### Current Behavior

- **Code Location**: `src/edugain_analysis/core/analysis.py:146-176`
- **CSV Export**: IdP privacy statements marked as "N/A"
- **Summary Statistics**: Only SP privacy statements counted
- **Markdown Reports**: Only SP privacy statements included

### Proposed Changes

If implemented, the following would need to be updated:

#### Core Analysis Layer
- [ ] Modify privacy statement collection to include IdPs (currently restricted to SPs)
- [ ] Add IdP-specific privacy statement statistics to stats dict
  - `idps_has_privacy`: Number of IdPs with privacy statements
  - `idps_missing_privacy`: Number of IdPs without privacy statements
- [ ] Update federation-level statistics to track IdP privacy statements
- [ ] Consider adding a combined "entities with privacy" metric

#### CLI Output Formats
- [ ] Update `print_summary()` to show IdP privacy statistics separately
- [ ] Update markdown reports to include IdP privacy sections
- [ ] Modify CSV export format to include IdP privacy data
  - Option 1: Add separate columns (IdPHasPrivacy, IdPPrivacyURL)
  - Option 2: Use existing columns but remove "N/A" for IdPs
- [ ] Update federation CSV exports to include IdP privacy counts

#### Web Dashboard (if applicable)
- [ ] Add IdP privacy statistics to dashboard cards
- [ ] Update federation detail pages to show IdP privacy breakdown
- [ ] Add IdP privacy statement links to entity detail pages
- [ ] Update trend charts to include IdP privacy coverage over time

#### Database Models (if web dashboard exists)
- [ ] Consider whether current schema needs changes
- [ ] May need migration to support historical IdP privacy data

### Implementation Considerations

**Benefits:**
- More complete picture of federation privacy compliance
- Helps identify federations with comprehensive privacy policies
- Useful for privacy audits and compliance reporting
- Better data for researchers studying privacy practices

**Challenges:**
- Breaking change for CSV consumers (column structure changes)
- Need to decide on output format (separate columns vs. unified)
- Existing tools/scripts may rely on current "N/A" behavior
- May require database migration for web dashboard

**Backward Compatibility:**
- Could add a flag `--include-idp-privacy` to opt-in to new behavior
- Could version the CSV output format (v1 vs v2)
- Could add new CSV export modes (e.g., `--csv idp-privacy`)

### Research Questions

Before implementing, consider investigating:
1. What percentage of IdP privacy URLs are actually accessible? (Run validation)
2. Are there regional/federation patterns in IdP privacy statement adoption?
3. Do IdPs with privacy statements correlate with other quality metrics (security contacts, SIRTFI)?
4. Should IdP privacy statements be weighted differently than SP privacy statements in quality scores?

### Related Files to Modify

If implemented:
- `src/edugain_analysis/core/analysis.py` - Core detection logic
- `src/edugain_analysis/formatters/base.py` - Output formatters
- `src/edugain_analysis/cli/main.py` - CLI interface
- `src/edugain_analysis/web/models.py` - Database models (if applicable)
- `src/edugain_analysis/web/import_data.py` - Web data import (if applicable)
- `tests/unit/test_*.py` - All relevant test files
- `../README.md`, `./CLAUDE.md` - Documentation

### Discovery Information

**Analysis Date:** 2025-10-12
**Script Used:** `check_idp_privacy.py` (ad-hoc analysis script)
**Sample Findings:**
- LIAF (Sri Lanka): ~40 IdPs with privacy statements
- OMREN (Oman): ~100+ IdPs with privacy statements
- YETKİM (Turkey): Many IdPs with privacy statements
- RIF (Uganda): Many IdPs with privacy statements

---

## Future Enhancement Ideas

### 2. URL Validation Performance Improvements
**Priority:** TBD
**Status:** Idea

- Consider caching strategies for long-term URL validation
- Explore async HTTP requests for faster validation
- Add retry logic for transient failures

### 3. Additional Compliance Frameworks
**Priority:** TBD
**Status:** Idea

- Track additional frameworks beyond SIRTFI
- Support for REFEDS Research & Scholarship
- Support for GÉANT Data Protection Code of Conduct

### 4. Historical Trend Analysis
**Priority:** TBD
**Status:** Idea

- Compare snapshots over time to detect improvements/regressions
- Automated reports on federation quality changes
- Alerts for entities that drop compliance metrics

---

**Note:** Items in this document are considerations for future development and have not been committed to any release timeline. Community feedback and use case validation should inform prioritization.
