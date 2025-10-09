"""FastAPI web application for eduGAIN analysis dashboard."""

# ruff: noqa: B008 - Depends in defaults is standard FastAPI pattern

import csv
import json
import threading
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .models import (
    Entity,
    Federation,
    SessionLocal,
    Settings,
    Snapshot,
    URLValidation,
    get_db,
)

# Initialize FastAPI app with enhanced API documentation
app = FastAPI(
    title="eduGAIN Quality Dashboard API",
    description="""
# eduGAIN Quality Dashboard API

The eduGAIN Quality Dashboard provides comprehensive analysis and monitoring of privacy statement coverage
and security contact information across all eduGAIN federation entities (Service Providers and Identity Providers).

## Features

- **Real-time Statistics**: Get up-to-date metrics on privacy coverage and security contacts
- **Federation Analytics**: Detailed breakdowns by federation
- **Entity Management**: Search, filter, and export entity data
- **Historical Tracking**: Monitor trends and changes over time
- **URL Validation**: Track accessibility of privacy statement URLs
- **Export Capabilities**: CSV and JSON export for all data
- **Database Backup/Restore**: Full database export and import

## Data Model

- **Snapshot**: Point-in-time analysis results with aggregate statistics
- **Federation**: Per-federation metrics linked to snapshots
- **Entity**: Individual SP/IdP entities with privacy and security status
- **URLValidation**: Privacy statement URL validation results

## Usage

All API endpoints are available at `/api/*`. Interactive documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Rate Limits

Some endpoints may have rate limits to prevent abuse:
- `/api/database/export`: 10 requests/hour
- `/api/database/import`: 5 requests/hour
- `/api/refresh`: 2 requests/hour
""",
    version="1.0.0",
    contact={
        "name": "eduGAIN Quality Improvement Project",
        "url": "https://github.com/your-org/edugain-qual-improv",
    },
    license_info={
        "name": "License",
        "url": "https://github.com/your-org/edugain-qual-improv/blob/main/LICENSE",
    },
    openapi_tags=[
        {
            "name": "Pages",
            "description": "Full HTML page routes for the web dashboard",
        },
        {
            "name": "Partials",
            "description": "HTMX partial routes for dynamic content updates",
        },
        {
            "name": "API - Data",
            "description": "JSON API endpoints for retrieving snapshot and federation data",
        },
        {
            "name": "API - Export",
            "description": "Export entities and federations as CSV or JSON",
        },
        {
            "name": "API - Settings",
            "description": "Configuration and cache management endpoints",
        },
        {
            "name": "API - Refresh",
            "description": "Trigger data refresh and check import status",
        },
        {
            "name": "API - Database",
            "description": "Database backup and restore operations",
        },
        {
            "name": "Health",
            "description": "System health check endpoints",
        },
    ],
)

# Get templates directory
TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize templates
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# Template filters
def time_ago(dt: datetime) -> str:
    """Convert datetime to relative time string."""
    if not dt:
        return "Never"

    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        return (
            f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
        )
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
    else:
        return "Just now"


templates.env.filters["time_ago"] = time_ago


# ========================================
# Full Page Routes
# ========================================


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    # Get latest snapshot
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        # No data yet - show empty state
        return templates.TemplateResponse(
            request, "empty.html", {"title": "eduGAIN Quality Dashboard"}
        )

    # Get top 10 federations by coverage
    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.coverage_pct.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "snapshot": snapshot,
            "federations": federations,
            "title": "Dashboard",
            "now": datetime.now(),
        },
    )


@app.get("/federations", response_class=HTMLResponse)
async def federations_page(request: Request, db: Session = Depends(get_db)):
    """Federations page with full list."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {"title": "Federations"},
        )

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.name)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "federations.html",
        {
            "federations": federations,
            "snapshot": snapshot,
            "title": "Federations",
            "now": datetime.now(),
        },
    )


@app.get("/federations/{federation_name}", response_class=HTMLResponse)
async def federation_detail(
    request: Request, federation_name: str, db: Session = Depends(get_db)
):
    """Federation detail page showing all entities."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return templates.TemplateResponse(
            request, "empty.html", {"title": "Federation Detail"}
        )

    # Get federation
    federation = (
        db.query(Federation)
        .filter(
            Federation.snapshot_id == snapshot.id, Federation.name == federation_name
        )
        .first()
    )

    if not federation:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {
                "title": "Federation Not Found",
                "message": f"Federation '{federation_name}' not found.",
            },
        )

    # Get entities for this federation (with pagination)
    entities = (
        db.query(Entity)
        .filter(Entity.federation_id == federation.id)
        .order_by(Entity.organization_name)
        .limit(100)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "federation_detail.html",
        {
            "federation": federation,
            "entities": entities,
            "snapshot": snapshot,
            "title": f"Federation: {federation_name}",
            "now": datetime.now(),
        },
    )


@app.get("/entities/{entity_id:path}", response_class=HTMLResponse)
async def entity_detail(
    request: Request, entity_id: str, db: Session = Depends(get_db)
):
    """Entity detail page showing full information."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return templates.TemplateResponse(
            request, "empty.html", {"title": "Entity Detail"}
        )

    # Get entity from latest snapshot
    entity = (
        db.query(Entity)
        .filter(Entity.snapshot_id == snapshot.id, Entity.entity_id == entity_id)
        .first()
    )

    if not entity:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {
                "title": "Entity Not Found",
                "message": "Entity not found.",
            },
        )

    # Get URL validation results if available
    url_validation = None
    if entity.privacy_statement_url:
        url_validation = (
            db.query(URLValidation).filter(URLValidation.entity_id == entity.id).first()
        )

    # Get historical data (other snapshots with this entity)
    historical_entities = (
        db.query(Entity)
        .filter(Entity.entity_id == entity_id, Entity.snapshot_id != snapshot.id)
        .order_by(Entity.snapshot_id.desc())
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "entity_detail.html",
        {
            "entity": entity,
            "url_validation": url_validation,
            "historical_entities": historical_entities,
            "snapshot": snapshot,
            "title": entity.organization_name or "Entity Detail",
            "now": datetime.now(),
        },
    )


@app.get("/validation", response_class=HTMLResponse)
async def validation_page(
    request: Request,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
):
    """URL validation results page."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {"title": "URL Validation"},
        )

    # Get all URL validations for the latest snapshot (only SPs have privacy statements)
    query = (
        db.query(URLValidation, Entity)
        .join(Entity, URLValidation.entity_id == Entity.id)
        .filter(Entity.snapshot_id == snapshot.id, Entity.entity_type == "SP")
    )

    # Apply status filter
    if status_filter == "accessible":
        query = query.filter(URLValidation.accessible.is_(True))
    elif status_filter == "error":
        query = query.filter(URLValidation.status_code >= 400)
    elif status_filter == "timeout":
        query = query.filter(URLValidation.validation_error.isnot(None))

    validations = query.order_by(URLValidation.validated_at.desc()).limit(500).all()

    # Get validation stats (only for SPs)
    total_validations = (
        db.query(URLValidation)
        .join(Entity)
        .filter(Entity.snapshot_id == snapshot.id, Entity.entity_type == "SP")
        .count()
    )
    accessible_count = (
        db.query(URLValidation)
        .join(Entity)
        .filter(
            Entity.snapshot_id == snapshot.id,
            Entity.entity_type == "SP",
            URLValidation.accessible.is_(True),
        )
        .count()
    )
    error_count = (
        db.query(URLValidation)
        .join(Entity)
        .filter(
            Entity.snapshot_id == snapshot.id,
            Entity.entity_type == "SP",
            URLValidation.status_code >= 400,
        )
        .count()
    )

    return templates.TemplateResponse(
        request,
        "validation.html",
        {
            "snapshot": snapshot,
            "validations": validations,
            "status_filter": status_filter,
            "total_validations": total_validations,
            "accessible_count": accessible_count,
            "error_count": error_count,
            "title": "URL Validation Results",
            "now": datetime.now(),
        },
    )


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, db: Session = Depends(get_db)):
    """Configuration page for analysis settings."""
    # Get or create settings
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    return templates.TemplateResponse(
        request,
        "config.html",
        {
            "settings": settings,
            "snapshot": snapshot,
            "title": "Configuration",
            "now": datetime.now(),
        },
    )


@app.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    days: int = 30,
    federation_name: str | None = None,
    db: Session = Depends(get_db),
):
    """Historical analysis page showing trends over time."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {"title": "Historical Analysis"},
        )

    # Get date range
    cutoff = datetime.now() - timedelta(days=days)
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.timestamp >= cutoff)
        .order_by(Snapshot.timestamp.desc())
        .all()
    )

    # Get all federations for dropdown
    federations = (
        db.query(Federation.name)
        .filter(Federation.snapshot_id == snapshot.id)
        .distinct()
        .order_by(Federation.name)
        .all()
    )
    federation_names = [f.name for f in federations]

    # If federation selected, get historical data for that federation
    federation_history = []
    if federation_name:
        for snap in snapshots:
            fed = (
                db.query(Federation)
                .filter(
                    Federation.snapshot_id == snap.id,
                    Federation.name == federation_name,
                )
                .first()
            )
            if fed:
                federation_history.append({"snapshot": snap, "federation": fed})

    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "snapshot": snapshot,
            "snapshots": snapshots,
            "federation_names": federation_names,
            "selected_federation": federation_name,
            "federation_history": federation_history,
            "days": days,
            "title": "Historical Analysis",
            "now": datetime.now(),
        },
    )


# ========================================
# HTMX Partial Routes
# ========================================


@app.get("/partials/stats", response_class=HTMLResponse)
async def stats_partial(request: Request, db: Session = Depends(get_db)):
    """Return stats cards as HTML fragment."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return "<p>No data available</p>"

    return templates.TemplateResponse(
        request,
        "partials/stats_cards.html",
        {"snapshot": snapshot, "now": datetime.now()},
    )


@app.get("/partials/federations", response_class=HTMLResponse)
async def federations_partial(
    request: Request,
    sort: str = "coverage",
    order: str = "desc",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Return federation table as HTML fragment."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return "<p>No data available</p>"

    # Build query
    query = db.query(Federation).filter(Federation.snapshot_id == snapshot.id)

    # Apply sorting
    if sort == "name":
        query = query.order_by(
            Federation.name.desc() if order == "desc" else Federation.name
        )
    elif sort == "entities":
        query = query.order_by(
            Federation.total_entities.desc()
            if order == "desc"
            else Federation.total_entities
        )
    else:  # coverage
        query = query.order_by(
            Federation.coverage_pct.desc()
            if order == "desc"
            else Federation.coverage_pct
        )

    if limit > 0:
        query = query.limit(limit)

    federations = query.all()

    return templates.TemplateResponse(
        request,
        "partials/federation_table.html",
        {
            "federations": federations,
            "sort": sort,
            "order": order,
        },
    )


@app.get("/partials/trends", response_class=HTMLResponse)
async def trends_partial(
    request: Request, days: int = 30, db: Session = Depends(get_db)
):
    """Return trend chart data as HTML with Chart.js."""
    cutoff = datetime.now() - timedelta(days=days)
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.timestamp >= cutoff)
        .order_by(Snapshot.timestamp)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "partials/trend_chart.html",
        {"snapshots": snapshots, "days": days},
    )


@app.get("/partials/search", response_class=HTMLResponse)
async def search_partial(request: Request, q: str = "", db: Session = Depends(get_db)):
    """Return search results as HTML fragment."""
    if not q or len(q) < 2:
        return "<div><p>Enter at least 2 characters to search...</p></div>"

    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return "<div><p>No data available</p></div>"

    # Search entities and federations
    search_pattern = f"%{q}%"
    entities = (
        db.query(Entity)
        .filter(Entity.snapshot_id == snapshot.id)
        .filter(
            (Entity.organization_name.ilike(search_pattern))
            | (Entity.entity_id.ilike(search_pattern))
        )
        .limit(10)
        .all()
    )

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .filter(Federation.name.ilike(search_pattern))
        .limit(5)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "partials/search_results.html",
        {
            "entities": entities,
            "federations": federations,
            "query": q,
        },
    )


@app.get("/partials/federation_comparison", response_class=HTMLResponse)
async def federation_comparison_partial(
    request: Request, limit: int = 20, db: Session = Depends(get_db)
):
    """Return federation comparison chart as HTML fragment."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return "<p>No data available</p>"

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.total_entities.desc())
        .limit(limit)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "partials/federation_comparison_chart.html",
        {"federations": federations},
    )


@app.get("/partials/entity_changes", response_class=HTMLResponse)
async def entity_changes_partial(
    request: Request,
    snapshot1_id: int,
    snapshot2_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return entity changes between two snapshots as HTML fragment.

    Shows entities that changed privacy or security status.
    If snapshot2_id is None, compares snapshot1_id with the previous snapshot.
    """
    snapshot1 = db.query(Snapshot).filter(Snapshot.id == snapshot1_id).first()
    if not snapshot1:
        return "<p>Snapshot not found</p>"

    # Get snapshot2 (previous snapshot if not specified)
    if snapshot2_id:
        snapshot2 = db.query(Snapshot).filter(Snapshot.id == snapshot2_id).first()
    else:
        snapshot2 = (
            db.query(Snapshot)
            .filter(Snapshot.timestamp < snapshot1.timestamp)
            .order_by(Snapshot.timestamp.desc())
            .first()
        )

    if not snapshot2:
        return "<p>No previous snapshot available for comparison</p>"

    # Get entities from both snapshots
    entities1 = {
        e.entity_id: e
        for e in db.query(Entity).filter(Entity.snapshot_id == snapshot1.id).all()
    }
    entities2 = {
        e.entity_id: e
        for e in db.query(Entity).filter(Entity.snapshot_id == snapshot2.id).all()
    }

    # Find entities that changed status
    changes = []
    for entity_id, entity1 in entities1.items():
        entity2 = entities2.get(entity_id)
        if not entity2:
            # New entity
            changes.append(
                {
                    "entity": entity1,
                    "change_type": "new",
                    "privacy_changed": False,
                    "security_changed": False,
                    "old_privacy": None,
                    "new_privacy": entity1.has_privacy_statement,
                    "old_security": None,
                    "new_security": entity1.has_security_contact,
                }
            )
        else:
            # Check for status changes
            privacy_changed = (
                entity1.has_privacy_statement != entity2.has_privacy_statement
            )
            security_changed = (
                entity1.has_security_contact != entity2.has_security_contact
            )

            if privacy_changed or security_changed:
                changes.append(
                    {
                        "entity": entity1,
                        "change_type": "modified",
                        "privacy_changed": privacy_changed,
                        "security_changed": security_changed,
                        "old_privacy": entity2.has_privacy_statement,
                        "new_privacy": entity1.has_privacy_statement,
                        "old_security": entity2.has_security_contact,
                        "new_security": entity1.has_security_contact,
                    }
                )

    # Check for removed entities
    for entity_id, entity2 in entities2.items():
        if entity_id not in entities1:
            changes.append(
                {
                    "entity": entity2,
                    "change_type": "removed",
                    "privacy_changed": False,
                    "security_changed": False,
                    "old_privacy": entity2.has_privacy_statement,
                    "new_privacy": None,
                    "old_security": entity2.has_security_contact,
                    "new_security": None,
                }
            )

    # Limit results
    changes = changes[:limit]

    return templates.TemplateResponse(
        request,
        "partials/entity_changes.html",
        {
            "changes": changes,
            "snapshot1": snapshot1,
            "snapshot2": snapshot2,
        },
    )


# ========================================
# Helper Functions for Query Building
# ========================================


def _apply_entity_filters(
    query, federation_id, entity_type, privacy_filter, security_filter
):
    """Apply filters to entity query.

    Args:
        query: SQLAlchemy query object
        federation_id: Filter by federation ID
        entity_type: Filter by SP or IdP
        privacy_filter: 'yes', 'no', 'na', or None
        security_filter: 'yes', 'no', or None

    Returns:
        Filtered query object
    """
    if federation_id:
        query = query.filter(Entity.federation_id == federation_id)

    if entity_type and entity_type in ["SP", "IdP"]:
        query = query.filter(Entity.entity_type == entity_type)

    if privacy_filter == "yes":
        query = query.filter(Entity.has_privacy_statement.is_(True))
    elif privacy_filter == "no":
        query = query.filter(
            Entity.has_privacy_statement.is_(False),
            Entity.entity_type == "SP",
        )
    elif privacy_filter == "na":
        query = query.filter(Entity.entity_type == "IdP")

    if security_filter == "yes":
        query = query.filter(Entity.has_security_contact.is_(True))
    elif security_filter == "no":
        query = query.filter(Entity.has_security_contact.is_(False))

    return query


def _get_sort_column(sort_by: str):
    """Get SQLAlchemy column for sorting.

    Args:
        sort_by: Column name to sort by

    Returns:
        SQLAlchemy column object
    """
    sort_columns = {
        "organization": Entity.organization_name,
        "type": Entity.entity_type,
        "privacy": Entity.has_privacy_statement,
        "security": Entity.has_security_contact,
        "sirtfi": Entity.has_sirtfi,
    }
    return sort_columns.get(sort_by, Entity.organization_name)


@app.get("/partials/entity_table", response_class=HTMLResponse)
async def entity_table_partial(
    request: Request,
    federation_id: int | None = None,
    entity_type: str | None = None,
    privacy_filter: str | None = None,
    security_filter: str | None = None,
    sort_by: str = "organization",
    sort_order: str = "asc",
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return filtered and sorted entity table as HTML fragment.

    Args:
        federation_id: Filter by federation ID
        entity_type: Filter by SP or IdP
        privacy_filter: 'yes', 'no', 'na', or None (all)
        security_filter: 'yes', 'no', or None (all)
        sort_by: Column to sort by (organization, type, privacy, security)
        sort_order: 'asc' or 'desc'
        page: Page number (1-indexed)
        limit: Max entities per page
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return "<p>No data available</p>"

    # Build query
    query = db.query(Entity).filter(Entity.snapshot_id == snapshot.id)

    # Apply filters
    query = _apply_entity_filters(
        query, federation_id, entity_type, privacy_filter, security_filter
    )

    # Apply sorting
    sort_col = _get_sort_column(sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Get total count for pagination
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit  # Ceiling division

    # Apply pagination
    offset = (page - 1) * limit
    entities = query.limit(limit).offset(offset).all()

    # Get federation info if filtering by federation
    federation = None
    if federation_id:
        federation = db.query(Federation).filter(Federation.id == federation_id).first()

    return templates.TemplateResponse(
        request,
        "partials/entity_table.html",
        {
            "entities": entities,
            "federation": federation,
            "snapshot": snapshot,
            "entity_type": entity_type,
            "privacy_filter": privacy_filter,
            "security_filter": security_filter,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": total_pages,
            "now": datetime.now(),
        },
    )


# ========================================
# API Endpoints (JSON)
# ========================================


@app.get(
    "/api/search",
    tags=["API - Data"],
    summary="Search entities and federations",
    description="""
    Perform a full-text search across entities and federations.

    Search is performed on:
    - Entity organization names
    - Entity IDs
    - Federation names

    Returns matching entities and federations with their key metrics.
    """,
    response_description="Search results containing matching entities and federations",
)
async def search(
    q: str = "",
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search for entities and federations.

    Full-text search on:
    - Entity names (organization_name)
    - Entity IDs
    - Federation names

    **Example Response:**
    ```json
    {
      "query": "incommon",
      "entities": [
        {
          "id": "https://example.edu/shibboleth",
          "organization_name": "Example University",
          "entity_type": "SP",
          "federation": "InCommon",
          "has_privacy": true,
          "has_security": true
        }
      ],
      "federations": [
        {
          "name": "InCommon",
          "total_entities": 5234,
          "coverage_pct": 78.5
        }
      ]
    }
    ```
    """
    if not q or len(q) < 2:
        return {"entities": [], "federations": [], "query": q}

    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return {"entities": [], "federations": [], "query": q}

    # Search entities
    search_pattern = f"%{q}%"
    entities = (
        db.query(Entity)
        .filter(Entity.snapshot_id == snapshot.id)
        .filter(
            (Entity.organization_name.ilike(search_pattern))
            | (Entity.entity_id.ilike(search_pattern))
        )
        .limit(limit)
        .all()
    )

    # Search federations
    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .filter(Federation.name.ilike(search_pattern))
        .limit(limit)
        .all()
    )

    return {
        "query": q,
        "entities": [
            {
                "id": e.entity_id,
                "organization_name": e.organization_name,
                "entity_type": e.entity_type,
                "federation": e.federation.name if e.federation else "Unknown",
                "has_privacy": e.has_privacy_statement,
                "has_security": e.has_security_contact,
            }
            for e in entities
        ],
        "federations": [
            {
                "name": f.name,
                "total_entities": f.total_entities,
                "coverage_pct": round(f.coverage_pct, 2),
            }
            for f in federations
        ],
    }


@app.get(
    "/api/snapshot/latest",
    tags=["API - Data"],
    summary="Get latest analysis snapshot",
    description="""
    Retrieve the most recent analysis snapshot with aggregate statistics.

    Returns key metrics including total entities, coverage percentages, and timestamp.
    """,
    response_description="Latest snapshot data with aggregate statistics",
)
async def get_latest_snapshot(db: Session = Depends(get_db)):
    """Get latest snapshot as JSON.

    **Example Response:**
    ```json
    {
      "timestamp": "2025-10-02T14:30:00",
      "total_entities": 10523,
      "total_sps": 8234,
      "total_idps": 2289,
      "coverage_pct": 76.8
    }
    ```
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return {"error": "No data available"}

    return {
        "timestamp": snapshot.timestamp.isoformat(),
        "total_entities": snapshot.total_entities,
        "total_sps": snapshot.total_sps,
        "total_idps": snapshot.total_idps,
        "coverage_pct": round(snapshot.coverage_pct, 2),
    }


@app.get(
    "/api/federations",
    tags=["API - Data"],
    summary="Get all federations",
    description="""
    Retrieve a list of all federations with their statistics from the latest snapshot.

    Returns federation names, entity counts, and privacy coverage percentages.
    """,
    response_description="List of all federations with statistics",
)
async def get_federations_json(db: Session = Depends(get_db)):
    """Get all federations as JSON.

    **Example Response:**
    ```json
    [
      {
        "name": "InCommon",
        "total_entities": 5234,
        "coverage_pct": 78.5
      },
      {
        "name": "UKAMF",
        "total_entities": 1523,
        "coverage_pct": 92.3
      }
    ]
    ```
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return []

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.name)
        .all()
    )

    return [
        {
            "name": f.name,
            "total_entities": f.total_entities,
            "coverage_pct": round(f.coverage_pct, 2),
        }
        for f in federations
    ]


# ========================================
# Export Endpoints
# ========================================


def _format_entity_csv(entities, snapshot):
    """Format entities as CSV.

    Args:
        entities: List of Entity objects
        snapshot: Snapshot object for timestamp

    Returns:
        CSV content string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Federation",
            "EntityType",
            "OrganizationName",
            "EntityID",
            "HasPrivacyStatement",
            "PrivacyStatementURL",
            "HasSecurityContact",
        ]
    )

    # Write data
    for entity in entities:
        privacy_status = (
            "N/A"
            if entity.entity_type == "IdP"
            else ("Yes" if entity.has_privacy_statement else "No")
        )
        privacy_url = (
            "N/A"
            if entity.entity_type == "IdP"
            else (entity.privacy_statement_url or "")
        )

        writer.writerow(
            [
                entity.federation.name if entity.federation else "Unknown",
                entity.entity_type,
                entity.organization_name or "",
                entity.entity_id,
                privacy_status,
                privacy_url,
                "Yes" if entity.has_security_contact else "No",
            ]
        )

    return output.getvalue()


def _format_entity_json(entities, snapshot):
    """Format entities as JSON.

    Args:
        entities: List of Entity objects
        snapshot: Snapshot object for timestamp

    Returns:
        JSON content string
    """
    data = {
        "snapshot_timestamp": snapshot.timestamp.isoformat(),
        "total_entities": len(entities),
        "entities": [
            {
                "federation": e.federation.name if e.federation else "Unknown",
                "entity_type": e.entity_type,
                "organization_name": e.organization_name,
                "entity_id": e.entity_id,
                "has_privacy_statement": (
                    "N/A" if e.entity_type == "IdP" else e.has_privacy_statement
                ),
                "privacy_statement_url": (
                    "N/A" if e.entity_type == "IdP" else e.privacy_statement_url
                ),
                "has_security_contact": e.has_security_contact,
            }
            for e in entities
        ],
    }
    return json.dumps(data, indent=2)


@app.get(
    "/api/export/entities",
    tags=["API - Export"],
    summary="Export entity data",
    description="""
    Export entity data as CSV or JSON with optional filtering.

    **Filters:**
    - `federation_id`: Filter by specific federation
    - `entity_type`: Filter by 'SP' or 'IdP'
    - `privacy_filter`: 'yes', 'no', or 'na' (not applicable for IdPs)
    - `security_filter`: 'yes' or 'no'

    **Formats:**
    - `csv`: Comma-separated values (default)
    - `json`: JSON format with metadata

    Returns a downloadable file with filtered entity data.
    """,
    response_description="CSV or JSON file containing entity data",
)
async def export_entities(
    export_format: str = "csv",
    federation_id: int | None = None,
    entity_type: str | None = None,
    privacy_filter: str | None = None,
    security_filter: str | None = None,
    db: Session = Depends(get_db),
):
    """Export entities as CSV or JSON.

    Args:
        export_format: 'csv' or 'json'
        federation_id: Filter by federation ID
        entity_type: Filter by SP or IdP
        privacy_filter: 'yes', 'no', 'na', or None
        security_filter: 'yes', 'no', or None
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return {"error": "No data available"}

    # Build query with filters
    query = db.query(Entity).filter(Entity.snapshot_id == snapshot.id)
    query = _apply_entity_filters(
        query, federation_id, entity_type, privacy_filter, security_filter
    )
    entities = query.order_by(Entity.organization_name).all()

    # Format output
    timestamp = snapshot.timestamp.strftime("%Y%m%d")
    if export_format == "csv":
        content = _format_entity_csv(entities, snapshot)
        filename = f"edugain_entities_{timestamp}.csv"
        media_type = "text/csv"
    else:
        content = _format_entity_json(entities, snapshot)
        filename = f"edugain_entities_{timestamp}.json"
        media_type = "application/json"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get(
    "/api/export/federations",
    tags=["API - Export"],
    summary="Export federation statistics",
    description="""
    Export federation-level statistics as CSV or JSON.

    Includes total entities, privacy coverage, and security contact metrics for all federations.
    """,
    response_description="CSV or JSON file containing federation statistics",
)
async def export_federations(export_format: str = "csv", db: Session = Depends(get_db)):
    """Export federation statistics as CSV or JSON."""
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return {"error": "No data available"}

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.name)
        .all()
    )

    # CSV export
    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Federation",
                "TotalEntities",
                "TotalSPs",
                "TotalIdPs",
                "SPsWithPrivacy",
                "SPsHasSecurity",
                "IdPsHasSecurity",
                "CoveragePct",
            ]
        )

        # Write data
        for fed in federations:
            writer.writerow(
                [
                    fed.name,
                    fed.total_entities,
                    fed.total_sps,
                    fed.total_idps,
                    fed.sps_with_privacy,
                    fed.sps_has_security,
                    fed.idps_has_security,
                    round(fed.coverage_pct, 2),
                ]
            )

        csv_content = output.getvalue()
        timestamp = snapshot.timestamp.strftime("%Y%m%d")
        filename = f"edugain_federations_{timestamp}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # JSON export
    else:
        data = {
            "snapshot_timestamp": snapshot.timestamp.isoformat(),
            "total_federations": len(federations),
            "federations": [
                {
                    "name": f.name,
                    "total_entities": f.total_entities,
                    "total_sps": f.total_sps,
                    "total_idps": f.total_idps,
                    "sps_with_privacy": f.sps_with_privacy,
                    "sps_has_security": f.sps_has_security,
                    "idps_has_security": f.idps_has_security,
                    "coverage_pct": round(f.coverage_pct, 2),
                }
                for f in federations
            ],
        }

        timestamp = snapshot.timestamp.strftime("%Y%m%d")
        filename = f"edugain_federations_{timestamp}.json"

        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


# ========================================
# Settings and Cache Status API
# ========================================


@app.get(
    "/api/cache/status",
    tags=["API - Settings"],
    summary="Get cache status",
    description="""
    Retrieve information about the current data cache status.

    Returns the age of the current snapshot, freshness status, and metadata source information.

    **Status Values:**
    - `fresh`: Data is up to date (< 12 hours old)
    - `stale`: Data may be outdated (12-24 hours old)
    - `expired`: Data is stale and should be refreshed (> 24 hours old)
    """,
    response_description="Cache status information",
)
async def cache_status(db: Session = Depends(get_db)):
    """Get cache status information.

    **Example Response:**
    ```json
    {
      "status": "fresh",
      "message": "Data is up to date",
      "timestamp": "2025-10-02T14:30:00",
      "age_hours": 2.5,
      "metadata_source": "eduGAIN Production",
      "cache_age_hours": 2.5
    }
    ```
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    if not snapshot:
        return {
            "status": "no_data",
            "message": "No data available. Run data import first.",
        }

    # Calculate age of snapshot
    now = datetime.now()
    age_hours = (now - snapshot.timestamp).total_seconds() / 3600

    # Determine freshness status
    if age_hours < 12:
        status = "fresh"
        message = "Data is up to date"
    elif age_hours < 24:
        status = "stale"
        message = "Data may be outdated"
    else:
        status = "expired"
        message = "Data is stale and should be refreshed"

    return {
        "status": status,
        "message": message,
        "timestamp": snapshot.timestamp.isoformat(),
        "age_hours": round(age_hours, 2),
        "metadata_source": snapshot.metadata_source or "eduGAIN Production",
        "cache_age_hours": snapshot.cache_age_hours,
    }


@app.get(
    "/api/settings",
    tags=["API - Settings"],
    summary="Get current settings",
    description="""
    Retrieve the current configuration settings for the dashboard.

    Includes cache expiry times, validation timeouts, and thread pool settings.
    """,
    response_description="Current settings configuration",
)
async def get_settings(db: Session = Depends(get_db)):
    """Get current settings.

    **Example Response:**
    ```json
    {
      "auto_refresh_interval": 12,
      "url_validation_timeout": 10,
      "url_validation_threads": 10,
      "metadata_cache_expiry": 12,
      "federation_cache_expiry": 720,
      "updated_at": "2025-10-02T14:30:00"
    }
    ```
    """
    settings = db.query(Settings).first()
    if not settings:
        # Return defaults
        return {
            "auto_refresh_interval": 12,
            "url_validation_timeout": 10,
            "url_validation_threads": 10,
            "metadata_cache_expiry": 12,
            "federation_cache_expiry": 720,
        }

    return {
        "auto_refresh_interval": settings.auto_refresh_interval,
        "url_validation_timeout": settings.url_validation_timeout,
        "url_validation_threads": settings.url_validation_threads,
        "metadata_cache_expiry": settings.metadata_cache_expiry,
        "federation_cache_expiry": settings.federation_cache_expiry,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


@app.post(
    "/api/settings",
    tags=["API - Settings"],
    summary="Update settings",
    description="""
    Update configuration settings for the dashboard.

    **Validation Ranges:**
    - `auto_refresh_interval`: 1-168 hours (max 1 week)
    - `url_validation_timeout`: 1-60 seconds
    - `url_validation_threads`: 1-50 threads
    - `metadata_cache_expiry`: 1-168 hours
    - `federation_cache_expiry`: 1-8760 hours (max 1 year)
    """,
    response_description="Updated settings configuration",
)
async def update_settings(
    auto_refresh_interval: int = 12,
    url_validation_timeout: int = 10,
    url_validation_threads: int = 10,
    metadata_cache_expiry: int = 12,
    federation_cache_expiry: int = 720,
    db: Session = Depends(get_db),
):
    """Update settings."""
    # Validate inputs
    if auto_refresh_interval < 1 or auto_refresh_interval > 168:  # Max 1 week
        return {"error": "auto_refresh_interval must be between 1 and 168 hours"}
    if url_validation_timeout < 1 or url_validation_timeout > 60:
        return {"error": "url_validation_timeout must be between 1 and 60 seconds"}
    if url_validation_threads < 1 or url_validation_threads > 50:
        return {"error": "url_validation_threads must be between 1 and 50"}
    if metadata_cache_expiry < 1 or metadata_cache_expiry > 168:
        return {"error": "metadata_cache_expiry must be between 1 and 168 hours"}
    if federation_cache_expiry < 1 or federation_cache_expiry > 8760:  # Max 1 year
        return {"error": "federation_cache_expiry must be between 1 and 8760 hours"}

    # Get or create settings
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)

    # Update values
    settings.auto_refresh_interval = auto_refresh_interval
    settings.url_validation_timeout = url_validation_timeout
    settings.url_validation_threads = url_validation_threads
    settings.metadata_cache_expiry = metadata_cache_expiry
    settings.federation_cache_expiry = federation_cache_expiry
    settings.updated_at = datetime.now()

    db.commit()
    db.refresh(settings)

    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": {
            "auto_refresh_interval": settings.auto_refresh_interval,
            "url_validation_timeout": settings.url_validation_timeout,
            "url_validation_threads": settings.url_validation_threads,
            "metadata_cache_expiry": settings.metadata_cache_expiry,
            "federation_cache_expiry": settings.federation_cache_expiry,
        },
    }


@app.post(
    "/api/settings/reset",
    tags=["API - Settings"],
    summary="Reset settings to defaults",
    description="""
    Reset all configuration settings to their default values.

    **Default Values:**
    - `auto_refresh_interval`: 12 hours
    - `url_validation_timeout`: 10 seconds
    - `url_validation_threads`: 10 threads
    - `metadata_cache_expiry`: 12 hours
    - `federation_cache_expiry`: 720 hours (30 days)
    """,
    response_description="Confirmation of settings reset",
)
async def reset_settings(db: Session = Depends(get_db)):
    """Reset settings to defaults."""
    settings = db.query(Settings).first()
    if settings:
        settings.auto_refresh_interval = 12
        settings.url_validation_timeout = 10
        settings.url_validation_threads = 10
        settings.metadata_cache_expiry = 12
        settings.federation_cache_expiry = 720
        settings.updated_at = datetime.now()
        db.commit()

    return {"success": True, "message": "Settings reset to defaults"}


# ========================================
# Data Refresh API
# ========================================

# Global status tracking for refresh operations
refresh_status = {
    "running": False,
    "started_at": None,
    "completed_at": None,
    "status": "idle",
    "message": "No refresh in progress",
    "error": None,
    "progress": 0,
    "stage": None,
}
refresh_lock = threading.Lock()


def _update_refresh_progress(progress: int, stage: str, message: str):
    """Update refresh status with progress information."""
    with refresh_lock:
        refresh_status["progress"] = progress
        refresh_status["stage"] = stage
        refresh_status["message"] = message


def _initialize_refresh_status():
    """Initialize refresh status at start of refresh operation."""
    with refresh_lock:
        refresh_status["running"] = True
        refresh_status["started_at"] = datetime.now().isoformat()
        refresh_status["status"] = "running"
        refresh_status["progress"] = 0
        refresh_status["stage"] = "initializing"
        refresh_status["message"] = "Starting data import..."
        refresh_status["error"] = None


def _download_and_parse_metadata():
    """Download and parse eduGAIN metadata.

    Returns:
        Tuple of (xml_root, federation_mapping)
    """
    from ..core.metadata import get_federation_mapping, get_metadata, parse_metadata

    _update_refresh_progress(10, "downloading", "Downloading eduGAIN metadata...")
    xml_content = get_metadata()
    root = parse_metadata(xml_content)
    _update_refresh_progress(20, "downloading", "Metadata downloaded successfully")

    _update_refresh_progress(25, "federations", "Fetching federation names...")
    federation_mapping = get_federation_mapping()
    _update_refresh_progress(30, "federations", "Federation mapping loaded")

    return root, federation_mapping


def _run_analysis(root, federation_mapping, validate_urls):
    """Run entity analysis with optional URL validation.

    Args:
        root: XML root element
        federation_mapping: Federation name mapping
        validate_urls: Whether to validate URLs

    Returns:
        Tuple of (entities_list, stats, federation_stats)
    """
    from ..core.analysis import analyze_privacy_security

    if validate_urls:
        _update_refresh_progress(
            35, "analyzing", "Analyzing entities and validating URLs..."
        )
    else:
        _update_refresh_progress(35, "analyzing", "Analyzing entities...")

    entities_list, stats, federation_stats = analyze_privacy_security(
        root,
        federation_mapping=federation_mapping,
        validate_urls=validate_urls,
        validation_cache=None,
        max_workers=10,
    )

    if validate_urls:
        _update_refresh_progress(70, "analyzing", "URL validation completed")
    else:
        _update_refresh_progress(65, "analyzing", "Analysis completed")

    return entities_list, stats, federation_stats


def _save_snapshot_to_db(entities_list, stats, federation_stats, validate_urls):
    """Save analysis results to database.

    Args:
        entities_list: List of entity data
        stats: Aggregate statistics
        federation_stats: Per-federation statistics
        validate_urls: Whether URL validation data is included
    """
    _update_refresh_progress(75, "saving", "Saving results to database...")

    db = SessionLocal()
    try:
        # Create snapshot
        snapshot = Snapshot(
            timestamp=datetime.now(),
            total_entities=stats["total_entities"],
            total_sps=stats["total_sps"],
            total_idps=stats["total_idps"],
            sps_with_privacy=stats["sps_has_privacy"],
            sps_missing_privacy=stats["sps_missing_privacy"],
            sps_has_security=stats["sps_has_security"],
            idps_has_security=stats["idps_has_security"],
            coverage_pct=(
                stats["sps_has_privacy"] / stats["total_sps"] * 100
                if stats["total_sps"] > 0
                else 0
            ),
        )
        db.add(snapshot)
        db.flush()

        _update_refresh_progress(80, "saving", "Saving federation data...")

        # Create federation records
        federation_id_map = {}
        for fed_name, fed_stats in federation_stats.items():
            federation = Federation(
                snapshot_id=snapshot.id,
                name=fed_name,
                total_entities=fed_stats["total_entities"],
                total_sps=fed_stats["total_sps"],
                total_idps=fed_stats["total_idps"],
                sps_with_privacy=fed_stats["sps_has_privacy"],
                sps_has_security=fed_stats["sps_has_security"],
                idps_has_security=fed_stats["idps_has_security"],
                coverage_pct=(
                    fed_stats["sps_has_privacy"] / fed_stats["total_sps"] * 100
                    if fed_stats["total_sps"] > 0
                    else 0
                ),
            )
            db.add(federation)
            db.flush()
            federation_id_map[fed_name] = federation.id

        _update_refresh_progress(90, "saving", "Saving entity data...")

        # Create entity records
        for entity_data in entities_list:
            _save_entity_to_db(
                db, entity_data, federation_id_map, snapshot.id, validate_urls
            )

        _update_refresh_progress(95, "saving", "Finalizing database commit...")
        db.commit()
        db.close()

        return stats["total_entities"]

    except Exception as e:
        db.rollback()
        db.close()
        raise e


def _save_entity_to_db(db, entity_data, federation_id_map, snapshot_id, validate_urls):
    """Save a single entity to database.

    Args:
        db: Database session
        entity_data: Entity data list
        federation_id_map: Federation ID mapping
        snapshot_id: Snapshot ID
        validate_urls: Whether URL validation data is included
    """
    fed_name = entity_data[0]
    federation_id = federation_id_map.get(fed_name)

    entity = Entity(
        snapshot_id=snapshot_id,
        federation_id=federation_id,
        entity_type=entity_data[1],
        organization_name=entity_data[2],
        entity_id=entity_data[3],
        has_privacy_statement=entity_data[4] == "Yes"
        if entity_data[4] != "N/A"
        else None,
        privacy_statement_url=entity_data[5]
        if entity_data[5] not in ["", "N/A"]
        else None,
        has_security_contact=entity_data[6] == "Yes",
    )
    db.add(entity)

    # Add URL validation if present
    if validate_urls and len(entity_data) > 7:
        db.flush()
        _save_url_validation_to_db(db, entity, entity_data)


def _save_url_validation_to_db(db, entity, entity_data):
    """Save URL validation data to database.

    Args:
        db: Database session
        entity: Entity object
        entity_data: Entity data list with validation info
    """
    # Parse status code safely
    status_code = None
    if len(entity_data) > 7 and entity_data[7]:
        try:
            status_code = int(entity_data[7]) if entity_data[7].isdigit() else None
        except (ValueError, AttributeError):
            status_code = None

    # Parse redirect count safely
    redirect_count = 0
    if len(entity_data) > 10 and entity_data[10]:
        try:
            redirect_count = (
                int(entity_data[10]) if str(entity_data[10]).isdigit() else 0
            )
        except (ValueError, AttributeError):
            redirect_count = 0

    url_validation = URLValidation(
        entity_id=entity.id,
        url=entity_data[5],
        status_code=status_code,
        final_url=entity_data[8]
        if len(entity_data) > 8 and entity_data[8] != ""
        else None,
        accessible=entity_data[9] == "Yes" if len(entity_data) > 9 else None,
        redirect_count=redirect_count,
        validation_error=entity_data[11]
        if len(entity_data) > 11 and entity_data[11] != ""
        else None,
        validated_at=datetime.now(),
    )
    db.add(url_validation)


def _set_refresh_completed(total_entities):
    """Mark refresh as completed successfully."""
    _update_refresh_progress(100, "completed", "Data import completed successfully")
    with refresh_lock:
        refresh_status["running"] = False
        refresh_status["completed_at"] = datetime.now().isoformat()
        refresh_status["status"] = "completed"
        refresh_status["progress"] = 100
        refresh_status["message"] = (
            f"Import completed: {total_entities} entities analyzed"
        )


def _set_refresh_error(error):
    """Mark refresh as failed with error."""
    with refresh_lock:
        refresh_status["running"] = False
        refresh_status["completed_at"] = datetime.now().isoformat()
        refresh_status["status"] = "error"
        refresh_status["message"] = "Data refresh failed"
        refresh_status["error"] = str(error)
        refresh_status["progress"] = 0


def run_refresh(validate_urls: bool = False):
    """Run data refresh in background with progress tracking."""
    try:
        _initialize_refresh_status()
        root, federation_mapping = _download_and_parse_metadata()
        entities_list, stats, federation_stats = _run_analysis(
            root, federation_mapping, validate_urls
        )
        total_entities = _save_snapshot_to_db(
            entities_list, stats, federation_stats, validate_urls
        )
        _set_refresh_completed(total_entities)
    except Exception as e:
        _set_refresh_error(e)


@app.post(
    "/api/refresh",
    tags=["API - Refresh"],
    summary="Trigger data refresh",
    description="""
    Trigger a background task to refresh the analysis data from eduGAIN metadata.

    **Parameters:**
    - `validate_urls`: Enable URL validation (slower but provides accessibility data)

    **Note:** Only one refresh can run at a time. Check `/api/refresh/status` for progress.
    """,
    response_description="Confirmation that refresh has been triggered",
)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    validate_urls: bool = False,
):
    """Trigger a data refresh in the background.

    Args:
        validate_urls: If True, validate privacy statement URLs (slower)

    **Example Response:**
    ```json
    {
      "success": true,
      "message": "Data refresh started",
      "validate_urls": false
    }
    ```
    """
    global refresh_status

    # Check if already running
    if refresh_status["running"]:
        return {
            "success": False,
            "message": "Refresh already in progress",
            "status": refresh_status,
        }

    # Start background task
    background_tasks.add_task(run_refresh, validate_urls)

    return {
        "success": True,
        "message": "Data refresh started",
        "validate_urls": validate_urls,
    }


@app.get(
    "/api/refresh/status",
    tags=["API - Refresh"],
    summary="Get refresh status",
    description="""
    Get the status of the current or last data refresh operation.

    **Status Values:**
    - `idle`: No refresh in progress
    - `running`: Refresh currently in progress
    - `completed`: Last refresh completed successfully
    - `error`: Last refresh failed (check error field)
    """,
    response_description="Refresh operation status",
)
async def get_refresh_status():
    """Get the status of the current/last refresh operation.

    **Example Response:**
    ```json
    {
      "running": false,
      "started_at": "2025-10-02T14:30:00",
      "completed_at": "2025-10-02T14:45:00",
      "status": "completed",
      "message": "Data refresh completed successfully",
      "error": null
    }
    ```
    """
    return refresh_status


# ========================================
# Database Export/Import
# ========================================


@app.get(
    "/api/database/export",
    tags=["API - Database"],
    summary="Export database",
    description="""
    Export the entire SQLite database file for backup or sharing.

    Returns the complete database as a downloadable `.db` file containing all snapshots,
    entities, federations, and validation results.

    **Use Cases:**
    - Backup current data
    - Share data with collaborators
    - Archive historical snapshots
    """,
    response_description="SQLite database file",
)
async def export_database(db: Session = Depends(get_db)):
    """Export the entire SQLite database file.

    Returns the database file as a downloadable attachment.
    Useful for backup and sharing data.
    """
    from .models import get_database_file_path

    # Close the database connection to ensure file is not locked
    db.close()

    # Get database file path
    db_path = get_database_file_path()

    # Read database file
    if not db_path.exists():
        return {"error": "Database file not found"}

    with open(db_path, "rb") as f:
        db_content = f.read()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"edugain_analysis_{timestamp}.db"

    return Response(
        content=db_content,
        media_type="application/x-sqlite3",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post(
    "/api/database/import",
    tags=["API - Database"],
    summary="Import database",
    description="""
    Import a SQLite database file to replace the current database.

    ⚠️ **WARNING:** This operation will:
    - Overwrite all existing data
    - Create a backup of the current database
    - Replace the database with the uploaded file

    **Requirements:**
    - File must be a valid SQLite database
    - File must be uploaded as `multipart/form-data` with field name `database_file`

    **Safety:**
    - Current database is automatically backed up before replacement
    - Backup filename includes timestamp for easy recovery
    """,
    response_description="Import result with backup location",
)
async def import_database(request: Request):
    """Import a SQLite database file.

    Replaces the current database with the uploaded file.
    WARNING: This will overwrite all existing data!

    Returns:
        Success message or error

    **Example Response:**
    ```json
    {
      "success": true,
      "message": "Database imported successfully",
      "backup_path": "/path/to/backup/edugain_analysis_backup_20251002_143000.db"
    }
    ```
    """
    from .models import engine, get_database_file_path

    try:
        # Parse uploaded file
        form = await request.form()
        uploaded_file = form.get("database_file")

        if not uploaded_file:
            return {"success": False, "error": "No file uploaded"}

        # Read file content
        db_content = await uploaded_file.read()

        # Validate it's a SQLite database (basic check)
        if not db_content.startswith(b"SQLite format 3"):
            return {"success": False, "error": "Invalid SQLite database file"}

        # Close all database connections
        engine.dispose()

        # Get database file path
        db_path = get_database_file_path()

        # Backup current database
        backup_path = (
            db_path.parent
            / f"edugain_analysis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        if db_path.exists():
            db_path.rename(backup_path)

        # Write new database
        with open(db_path, "wb") as f:
            f.write(db_content)

        return {
            "success": True,
            "message": "Database imported successfully",
            "backup_path": str(backup_path),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================================
# Health Check
# ========================================


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="""
    Basic health check endpoint for monitoring and load balancers.

    Returns a simple status response indicating the API is operational.
    """,
    response_description="Health status",
)
async def health_check():
    """Health check endpoint.

    **Example Response:**
    ```json
    {
      "status": "healthy",
      "timestamp": "2025-10-02T14:30:00"
    }
    ```
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
