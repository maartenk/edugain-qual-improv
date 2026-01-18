# AI Implementation Prompt: Historical Snapshot Storage

**Feature ID**: 1.4 from ROADMAP.md
**Priority**: HIGH
**Effort**: 1 week
**Type**: Infrastructure

## Objective

Store daily snapshots of analysis results in a local SQLite database to enable future trend analysis and historical tracking of compliance metrics.

## Context

**Current State**:
- Each analysis run shows current state only
- No historical tracking of compliance trends
- Can't answer questions like "How has privacy coverage changed over time?"
- No way to track improvements or regressions

**Problem**:
- Federation operators can't demonstrate improvement over time
- Regressions not detected until too late
- No data for trend analysis or forecasting
- Manual snapshot tracking is error-prone

**Future Capabilities** (enabled by this foundation):
- Trend analysis reports (Phase 2)
- Automated regression detection
- Historical comparisons
- Compliance dashboards with time-series graphs

## Requirements

### Core Functionality

1. **Database Schema**:
   - SQLite database in XDG cache directory: `~/.cache/edugain-analysis/history.db`
   - Three tables: snapshots, federation_history, entity_history

2. **Automatic Snapshots**:
   - Create snapshot on every `edugain-analyze` run (after analysis completes)
   - Include overall stats, federation stats, and per-entity status
   - Store timestamp, metadata source, tool version

3. **Retention Policy**:
   - Keep all daily snapshots for 90 days
   - Aggregate to weekly snapshots after 90 days (keep for 1 year)
   - Aggregate to monthly snapshots after 1 year
   - Auto-cleanup on database size limit (max 100 MB)

4. **CLI Flags**:
   ```bash
   --skip-snapshot              # Disable automatic snapshot (for testing)
   --show-snapshot-stats        # Show database statistics (size, count, date range)
   ```

### Database Schema

**Table: snapshots**
```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,  -- ISO 8601 format
    tool_version TEXT NOT NULL,
    metadata_source TEXT NOT NULL,
    total_entities INTEGER NOT NULL,
    total_sps INTEGER NOT NULL,
    total_idps INTEGER NOT NULL,
    sps_with_privacy INTEGER NOT NULL,
    sps_missing_privacy INTEGER NOT NULL,
    entities_with_security INTEGER NOT NULL,
    entities_missing_security INTEGER NOT NULL,
    entities_with_sirtfi INTEGER NOT NULL,
    entities_missing_sirtfi INTEGER NOT NULL,
    privacy_coverage_percent REAL NOT NULL,
    security_coverage_percent REAL NOT NULL,
    sirtfi_coverage_percent REAL NOT NULL,
    UNIQUE(timestamp)  -- One snapshot per timestamp
);

CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp);
```

**Table: federation_history**
```sql
CREATE TABLE federation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    federation TEXT NOT NULL,
    total_entities INTEGER NOT NULL,
    total_sps INTEGER NOT NULL,
    total_idps INTEGER NOT NULL,
    sps_with_privacy INTEGER NOT NULL,
    entities_with_security INTEGER NOT NULL,
    entities_with_sirtfi INTEGER NOT NULL,
    privacy_coverage_percent REAL NOT NULL,
    security_coverage_percent REAL NOT NULL,
    sirtfi_coverage_percent REAL NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
    UNIQUE(snapshot_id, federation)
);

CREATE INDEX idx_federation_history_timestamp ON federation_history(timestamp);
CREATE INDEX idx_federation_history_federation ON federation_history(federation);
```

**Table: entity_history**
```sql
CREATE TABLE entity_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- 'SP' or 'IdP'
    federation TEXT NOT NULL,
    organization_name TEXT,
    has_privacy INTEGER NOT NULL,  -- 0 or 1 (boolean)
    has_security_contact INTEGER NOT NULL,
    has_sirtfi INTEGER NOT NULL,
    privacy_url TEXT,
    privacy_url_accessible INTEGER,  -- NULL if not validated
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
    UNIQUE(snapshot_id, entity_id)
);

CREATE INDEX idx_entity_history_timestamp ON entity_history(timestamp);
CREATE INDEX idx_entity_history_entity_id ON entity_history(entity_id);
CREATE INDEX idx_entity_history_federation ON entity_history(federation);
```

### Implementation Details

**Files to Create**:

1. **`src/edugain_analysis/core/history.py`**:
   - `initialize_database()`: Create tables if not exist
   - `create_snapshot(stats, federation_stats, entities)`: Insert snapshot
   - `cleanup_old_snapshots(retention_days)`: Retention policy
   - `get_snapshot_stats()`: Database size, count, date range
   - `aggregate_to_weekly(cutoff_date)`: Convert daily to weekly
   - `aggregate_to_monthly(cutoff_date)`: Convert weekly to monthly

2. **Files to Modify**:
   - `src/edugain_analysis/cli/main.py`: Call snapshot creation after analysis
   - `src/edugain_analysis/__init__.py`: Add `__version__` if not present

**Edge Cases**:
- Database doesn't exist: Create automatically
- Database schema outdated: Migrate or recreate
- Disk space full: Log error, continue without snapshot
- Same timestamp (multiple runs): Update existing snapshot
- Entity IDs change: Track by entity_id string (historic record)

## Acceptance Criteria

### Functional Requirements
- [ ] Database created automatically on first run
- [ ] Snapshot stored on every `edugain-analyze` run
- [ ] `--skip-snapshot` prevents snapshot creation
- [ ] `--show-snapshot-stats` displays database info
- [ ] Retention policy executed automatically
- [ ] Database size stays under 100 MB for 1 year of daily data
- [ ] Foreign key constraints enforced (cascade deletes)

### Quality Requirements
- [ ] Snapshot creation doesn't impact CLI performance (< 100ms overhead)
- [ ] Database location follows XDG standards
- [ ] Schema migrations handled gracefully
- [ ] No data loss on errors (transactions)
- [ ] Thread-safe database access

### Testing Requirements
- [ ] Test database initialization
- [ ] Test snapshot creation with sample data
- [ ] Test retention policy (daily → weekly → monthly)
- [ ] Test `--skip-snapshot` flag
- [ ] Test `--show-snapshot-stats` output
- [ ] Test database size estimates
- [ ] Test concurrent access (if needed)

## Testing Strategy

**Unit Tests**:
```python
def test_initialize_database(tmp_path):
    """Test database initialization creates tables."""
    db_path = tmp_path / "history.db"
    initialize_database(db_path)
    assert db_path.exists()

    # Check tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "snapshots" in tables
    assert "federation_history" in tables
    assert "entity_history" in tables

def test_create_snapshot(tmp_path):
    """Test snapshot creation."""
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    stats = {
        "total_entities": 100,
        "total_sps": 60,
        "total_idps": 40,
        "sps_has_privacy": 45,
        # ...
    }
    federation_stats = {
        "InCommon": {"total_entities": 50, ...}
    }
    entities = [...]

    snapshot_id = create_snapshot(
        db_path, stats, federation_stats, entities,
        source="https://example.org", version="2.5.0"
    )
    assert snapshot_id > 0

    # Verify snapshot exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM snapshots")
    assert cursor.fetchone()[0] == 1

def test_retention_policy(tmp_path):
    """Test old snapshots are cleaned up."""
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    # Create old snapshots
    old_date = datetime.now(timezone.utc) - timedelta(days=100)
    # ... insert old snapshot ...

    cleanup_old_snapshots(db_path, retention_days=90)

    # Verify old snapshot removed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM snapshots WHERE timestamp < ?", (old_date,))
    assert cursor.fetchone()[0] == 0
```

## Implementation Guidance

### Step 1: Create History Module

```python
# src/edugain_analysis/core/history.py

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from platformdirs import user_cache_dir
from typing import Optional

def get_history_db_path() -> Path:
    """Get path to history database following XDG standards."""
    cache_dir = Path(user_cache_dir("edugain-analysis", "edugain"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "history.db"

def initialize_database(db_path: Optional[Path] = None) -> Path:
    """
    Initialize history database with schema.

    Args:
        db_path: Optional custom database path (for testing)

    Returns:
        Path to database file
    """
    if db_path is None:
        db_path = get_history_db_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool_version TEXT NOT NULL,
            metadata_source TEXT NOT NULL,
            total_entities INTEGER NOT NULL,
            total_sps INTEGER NOT NULL,
            total_idps INTEGER NOT NULL,
            sps_with_privacy INTEGER NOT NULL,
            sps_missing_privacy INTEGER NOT NULL,
            entities_with_security INTEGER NOT NULL,
            entities_missing_security INTEGER NOT NULL,
            entities_with_sirtfi INTEGER NOT NULL,
            entities_missing_sirtfi INTEGER NOT NULL,
            privacy_coverage_percent REAL NOT NULL,
            security_coverage_percent REAL NOT NULL,
            sirtfi_coverage_percent REAL NOT NULL,
            UNIQUE(timestamp)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
        ON snapshots(timestamp)
    """)

    # Create federation_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS federation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            federation TEXT NOT NULL,
            total_entities INTEGER NOT NULL,
            total_sps INTEGER NOT NULL,
            total_idps INTEGER NOT NULL,
            sps_with_privacy INTEGER NOT NULL,
            entities_with_security INTEGER NOT NULL,
            entities_with_sirtfi INTEGER NOT NULL,
            privacy_coverage_percent REAL NOT NULL,
            security_coverage_percent REAL NOT NULL,
            sirtfi_coverage_percent REAL NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
            UNIQUE(snapshot_id, federation)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_federation_history_timestamp
        ON federation_history(timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_federation_history_federation
        ON federation_history(federation)
    """)

    # Create entity_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            federation TEXT NOT NULL,
            organization_name TEXT,
            has_privacy INTEGER NOT NULL,
            has_security_contact INTEGER NOT NULL,
            has_sirtfi INTEGER NOT NULL,
            privacy_url TEXT,
            privacy_url_accessible INTEGER,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
            UNIQUE(snapshot_id, entity_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_history_timestamp
        ON entity_history(timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_history_entity_id
        ON entity_history(entity_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_history_federation
        ON entity_history(federation)
    """)

    conn.commit()
    conn.close()

    return db_path

def create_snapshot(
    stats: dict,
    federation_stats: dict,
    entities: list[dict],
    metadata_source: str,
    tool_version: str,
    db_path: Optional[Path] = None
) -> int:
    """
    Create a new snapshot in the database.

    Args:
        stats: Overall statistics dictionary
        federation_stats: Per-federation statistics
        entities: List of entity dictionaries
        metadata_source: URL of metadata source
        tool_version: Tool version string
        db_path: Optional custom database path

    Returns:
        Snapshot ID

    Raises:
        sqlite3.Error: On database errors
    """
    if db_path is None:
        db_path = get_history_db_path()

    timestamp = datetime.now(timezone.utc).isoformat()

    # Calculate coverage percentages
    privacy_coverage = (
        (stats["sps_has_privacy"] / stats["total_sps"] * 100)
        if stats["total_sps"] > 0 else 0.0
    )
    security_coverage = (
        (stats["entities_with_security"] / stats["total_entities"] * 100)
        if stats["total_entities"] > 0 else 0.0
    )
    sirtfi_coverage = (
        (stats["entities_with_sirtfi"] / stats["total_entities"] * 100)
        if stats["total_entities"] > 0 else 0.0
    )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Insert snapshot (or update if same timestamp)
        cursor.execute("""
            INSERT OR REPLACE INTO snapshots (
                timestamp, tool_version, metadata_source,
                total_entities, total_sps, total_idps,
                sps_with_privacy, sps_missing_privacy,
                entities_with_security, entities_missing_security,
                entities_with_sirtfi, entities_missing_sirtfi,
                privacy_coverage_percent, security_coverage_percent,
                sirtfi_coverage_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, tool_version, metadata_source,
            stats["total_entities"], stats["total_sps"], stats["total_idps"],
            stats["sps_has_privacy"], stats["sps_missing_privacy"],
            stats["entities_with_security"], stats["entities_missing_security"],
            stats["entities_with_sirtfi"], stats["entities_missing_sirtfi"],
            round(privacy_coverage, 1),
            round(security_coverage, 1),
            round(sirtfi_coverage, 1)
        ))

        snapshot_id = cursor.lastrowid

        # Insert federation history
        for federation, fed_stats in federation_stats.items():
            # Calculate federation percentages
            # ... similar to overall stats ...

            cursor.execute("""
                INSERT OR REPLACE INTO federation_history (
                    snapshot_id, timestamp, federation,
                    total_entities, total_sps, total_idps,
                    sps_with_privacy, entities_with_security, entities_with_sirtfi,
                    privacy_coverage_percent, security_coverage_percent,
                    sirtfi_coverage_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, timestamp, federation, ...))

        # Insert entity history (batch insert for performance)
        entity_data = [
            (
                snapshot_id, timestamp, entity["entity_id"], entity["entity_type"],
                entity["federation"], entity.get("organization_name"),
                1 if entity.get("has_privacy") else 0,
                1 if entity.get("has_security_contact") else 0,
                1 if entity.get("has_sirtfi") else 0,
                entity.get("privacy_url"),
                1 if entity.get("privacy_url_accessible") else 0
            )
            for entity in entities
        ]

        cursor.executemany("""
            INSERT OR REPLACE INTO entity_history (
                snapshot_id, timestamp, entity_id, entity_type, federation,
                organization_name, has_privacy, has_security_contact, has_sirtfi,
                privacy_url, privacy_url_accessible
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, entity_data)

        conn.commit()
        return snapshot_id

    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

def cleanup_old_snapshots(retention_days: int = 90, db_path: Optional[Path] = None):
    """
    Clean up snapshots older than retention period.

    Args:
        retention_days: Number of days to keep daily snapshots
        db_path: Optional custom database path
    """
    if db_path is None:
        db_path = get_history_db_path()

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_iso = cutoff_date.isoformat()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Delete old snapshots (cascades to federation_history and entity_history)
        cursor.execute("""
            DELETE FROM snapshots WHERE timestamp < ?
        """, (cutoff_iso,))

        conn.commit()
    finally:
        conn.close()

def get_snapshot_stats(db_path: Optional[Path] = None) -> dict:
    """
    Get statistics about the snapshot database.

    Returns:
        Dictionary with count, date range, size
    """
    if db_path is None:
        db_path = get_history_db_path()

    if not db_path.exists():
        return {"count": 0, "size_mb": 0, "oldest": None, "newest": None}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM snapshots")
    count, oldest, newest = cursor.fetchone()

    conn.close()

    size_mb = db_path.stat().st_size / (1024 * 1024)

    return {
        "count": count or 0,
        "size_mb": round(size_mb, 2),
        "oldest": oldest,
        "newest": newest
    }
```

### Step 2: Update CLI

```python
# src/edugain_analysis/cli/main.py

from ..core.history import initialize_database, create_snapshot, get_snapshot_stats
from .. import __version__

parser.add_argument(
    "--skip-snapshot",
    action="store_true",
    help="Skip automatic snapshot creation (for testing)"
)
parser.add_argument(
    "--show-snapshot-stats",
    action="store_true",
    help="Show snapshot database statistics and exit"
)

def main():
    args = parser.parse_args()

    # Show snapshot stats if requested
    if args.show_snapshot_stats:
        stats = get_snapshot_stats()
        print(f"Snapshot Database Statistics:")
        print(f"  Total snapshots: {stats['count']}")
        print(f"  Database size: {stats['size_mb']} MB")
        print(f"  Oldest snapshot: {stats['oldest'] or 'N/A'}")
        print(f"  Newest snapshot: {stats['newest'] or 'N/A'}")
        return

    # ... existing analysis code ...

    # Create snapshot (unless disabled)
    if not args.skip_snapshot:
        try:
            initialize_database()
            create_snapshot(
                stats=stats,
                federation_stats=federation_stats,
                entities=entities_list,  # Need to collect this
                metadata_source=args.source or EDUGAIN_METADATA_URL,
                tool_version=__version__
            )
            # Cleanup old snapshots
            from ..core.history import cleanup_old_snapshots
            cleanup_old_snapshots(retention_days=90)
        except Exception as e:
            # Log error but don't fail the main analysis
            print(f"Warning: Failed to create snapshot: {e}", file=sys.stderr)
```

## Success Metrics

- Database created automatically on first run
- Snapshot creation completes in < 100ms for 10,000 entities
- Database size stays under 50 MB for 90 days of daily snapshots
- No errors reported during snapshot creation
- Tests achieve 100% coverage of history module
- Foundation ready for Phase 2 trend analysis features

## References

- XDG cache directory: `platformdirs.user_cache_dir()`
- SQLite best practices: Foreign keys, indexes, transactions
- Current analysis: `src/edugain_analysis/core/analysis.py`
