# eduGAIN Quality Improvement - TODO

## Web Dashboard MVP Enhancements

### Priority 1: Data Layer & Infrastructure ✅

- [x] **Store entity-level data in database**
  - ✅ Added `Entity` model to `models.py` with columns: entity_id, snapshot_id, federation_id, entity_type (SP/IdP), organization_name, has_privacy_statement, privacy_statement_url, has_security_contact
  - ✅ Added indexes for efficient querying (snapshot_id, federation_id, entity_type, privacy/security status)
  - ✅ Updated `import_data.py` to populate entity table from analysis results
  - ✅ Added SQLAlchemy relationships between Snapshot, Federation, and Entity models
  - File: `src/edugain_analysis/web/models.py`

- [x] **Add URL validation tracking table**
  - ✅ Created `URLValidation` model with columns: entity_id, url, status_code, final_url, accessible, redirect_count, validation_error, validated_at
  - ✅ Added foreign key relationship to Entity table with cascade delete
  - ✅ Integrated with existing URL validation from `core/validation.py`
  - ✅ Added `--validate-urls` flag to import_data.py for optional URL validation
  - ✅ Tested with real eduGAIN metadata (10,047 entities imported successfully)
  - File: `src/edugain_analysis/web/models.py`

### Priority 2: Core Features ✅

- [x] **Add search functionality for entities and federations**
  - ✅ Implemented `/api/search` endpoint with query parameter returning JSON
  - ✅ Implemented `/partials/search` endpoint for HTMX live results
  - ✅ Added full-text search on entity names, entity IDs, federation names using SQL ILIKE
  - ✅ Created HTMX-powered search dropdown in navigation with live results (300ms debounce)
  - ✅ Search returns entities and federations with quick preview info
  - Files: `src/edugain_analysis/web/app.py`, `templates/base.html`, `templates/partials/search_results.html`

- [x] **Implement federation drill-down views**
  - ✅ Added `/federations/{federation_name}` route showing all entities in federation
  - ✅ Display entity table with privacy/security status per entity (visual indicators)
  - ✅ Include federation-specific statistics card with SP/IdP breakdown
  - ✅ Implemented pagination (100 entities per page limit)
  - ✅ Added "View Details" buttons linking to entity pages
  - Files: `src/edugain_analysis/web/app.py`, `templates/federation_detail.html`

- [x] **Add entity-level detail views (individual SPs/IdPs)**
  - ✅ Created `/entities/{entity_id:path}` route for individual entity details
  - ✅ Show full metadata: organization, entity type, federation, privacy statement URL, security contact status
  - ✅ Display URL validation results with HTTP status codes, redirects, and error messages
  - ✅ Added historical view showing entity status across multiple snapshots
  - ✅ Visual indicators for privacy/security status with color coding
  - Files: `src/edugain_analysis/web/app.py`, `templates/entity_detail.html`

### Priority 3: Enhanced Interactivity ✅

- [x] **Add interactive filtering/sorting for entity tables**
  - ✅ Added filter controls for entity type (SP/IdP), privacy status, security status
  - ✅ Implemented multi-column sorting with visual indicators (▲/▼)
  - ✅ Added "Show only missing privacy" and "Show only missing security" toggles
  - ✅ Created `/partials/entity_table` HTMX endpoint with filter/sort params
  - ✅ Added clear filters button and integrated with federation detail page
  - Files: `src/edugain_analysis/web/app.py`, `templates/partials/entity_table.html`

- [x] **Enhance visualizations with interactive charts/graphs**
  - ✅ Enhanced trend chart with multi-dataset support (privacy + security contacts for SPs/IdPs)
  - ✅ Added federation coverage comparison bar chart (top 20 federations by size)
  - ✅ Implemented interactive tooltips with detailed information
  - ✅ Added legend with dataset toggles
  - ✅ Improved chart aesthetics with color coding and labels
  - Files: `templates/partials/trend_chart.html`, `templates/partials/federation_comparison_chart.html`

- [x] **Add export functionality for filtered data (CSV/JSON)**
  - ✅ Implemented `/api/export/entities` endpoint with format parameter (csv/json)
  - ✅ Implemented `/api/export/federations` endpoint for federation statistics
  - ✅ Support all filter parameters matching table filters (type, privacy, security)
  - ✅ Added "Export to CSV" and "Export to JSON" buttons on entity tables and federation page
  - ✅ Generate downloadable files with proper Content-Disposition headers and timestamped filenames
  - File: `src/edugain_analysis/web/app.py`

### Priority 4: User Experience

- [x] **Add URL validation results view with status codes**
  - ✅ Created `/validation` page showing all privacy statement URL validation results
  - ✅ Display table with columns: Entity, Federation, URL, Status Code, Final URL, Accessible, Last Checked
  - ✅ Added filtering by status (accessible, redirect, error, timeout)
  - ✅ Color-coded status indicators (green=2xx, orange=3xx, red=4xx/5xx)
  - ✅ Show validation error details with truncated preview in table
  - Files: `src/edugain_analysis/web/app.py`, `templates/validation.html`

- [ ] **Implement auto-refresh with cache status indicator**
  - Add cache metadata to Snapshot model: cache_age, metadata_source, last_refresh_attempt
  - Create `/api/cache/status` endpoint returning cache age and freshness
  - Add visual indicator showing data age with color coding (fresh/stale/expired)
  - Implement manual "Force Refresh" button triggering re-analysis
  - Show loading spinner during refresh operations
  - Files: `src/edugain_analysis/web/models.py`, `app.py`, `templates/base.html`

- [x] **Add data freshness indicator with last update time**
  - ✅ Display "Last updated: X hours ago" in dashboard header using time_ago filter
  - ✅ Added timestamp tooltip showing exact update time (YYYY-MM-DD HH:MM)
  - ✅ Show color-coded warnings: green (<12h), orange (12-24h), red (>24h stale)
  - ✅ Display "Data is stale" or "Data may be outdated" warnings based on age
  - File: `templates/base.html`

- [ ] **Add configuration page for analysis settings**
  - Create `/config` route with settings form
  - Add configurable options: auto-refresh interval, URL validation timeout, thread pool size, cache expiry
  - Store settings in database (new `Settings` table)
  - Add "Apply Settings" button with validation
  - Include "Reset to Defaults" option
  - Files: `src/edugain_analysis/web/app.py`, `templates/config.html`

### Priority 5: Historical Analysis

- [ ] **Add historical comparison views (trend analysis over time)**
  - Create `/history` page showing snapshot timeline
  - Add federation comparison across multiple snapshots
  - Show coverage trend per federation over time
  - Highlight entities that changed status (privacy/security added/removed)
  - Add date range selector for historical analysis
  - Files: `src/edugain_analysis/web/app.py`, `templates/history.html`

### Priority 6: Polish & Optimization

- [ ] **Improve responsive design for mobile devices**
  - Test all pages on mobile viewports (320px, 768px, 1024px)
  - Make tables horizontally scrollable on mobile
  - Optimize chart sizing for small screens
  - Convert multi-column layouts to stacked on mobile
  - Add mobile-friendly navigation menu (hamburger)
  - Test with PicoCSS responsive utilities
  - Files: `templates/*.html`, `static/css/custom.css`

## Architecture Notes

- **Database Schema**: SQLite with SQLAlchemy ORM (XDG-compliant cache location)
- **Frontend**: HTMX + PicoCSS + Chart.js (no build step, minimal JavaScript)
- **Backend**: FastAPI with Jinja2 templates
- **Data Flow**: CLI analysis → SQLite → FastAPI → HTMX partials
- **Caching Strategy**: XDG cache directory for metadata, federation mappings, URL validation

## Related Files

- **Web App**: `src/edugain_analysis/web/app.py` (FastAPI routes)
- **Models**: `src/edugain_analysis/web/models.py` (SQLAlchemy ORM)
- **Data Import**: `src/edugain_analysis/web/import_data.py` (CLI → DB sync)
- **Templates**: `src/edugain_analysis/web/templates/` (Jinja2 + HTMX)
- **Core Analysis**: `src/edugain_analysis/core/analysis.py` (Business logic)
- **URL Validation**: `src/edugain_analysis/core/validation.py` (Parallel HTTP checks)

## Testing Priorities

After implementing each feature:
1. Add unit tests in `tests/unit/test_web_*.py`
2. Test HTMX partial rendering with different parameters
3. Verify database queries are indexed and performant
4. Test with large datasets (1000+ entities)
5. Validate responsive design on mobile devices

## Future Considerations (Beyond MVP)

- [ ] Real-time notifications for data updates
- [ ] Email alerts for federation compliance changes
- [ ] Multi-user support with authentication
- [ ] API rate limiting and caching headers
- [ ] WebSocket support for live updates
- [ ] Advanced analytics dashboard with custom queries
- [ ] PDF report generation
- [ ] Integration with external monitoring systems
