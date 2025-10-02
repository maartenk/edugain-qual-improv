"""FastAPI web application for eduGAIN analysis dashboard."""

# ruff: noqa: B008 - Depends in defaults is standard FastAPI pattern

import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .models import Entity, Federation, Settings, Snapshot, URLValidation, get_db

# Initialize FastAPI app
app = FastAPI(title="eduGAIN Quality Dashboard", version="1.0.0")

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
            "empty.html", {"request": request, "title": "eduGAIN Quality Dashboard"}
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
        "dashboard.html",
        {
            "request": request,
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
            "empty.html",
            {"request": request, "title": "Federations"},
        )

    federations = (
        db.query(Federation)
        .filter(Federation.snapshot_id == snapshot.id)
        .order_by(Federation.name)
        .all()
    )

    return templates.TemplateResponse(
        "federations.html",
        {
            "request": request,
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
            "empty.html", {"request": request, "title": "Federation Detail"}
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
            "empty.html",
            {
                "request": request,
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
        "federation_detail.html",
        {
            "request": request,
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
            "empty.html", {"request": request, "title": "Entity Detail"}
        )

    # Get entity from latest snapshot
    entity = (
        db.query(Entity)
        .filter(Entity.snapshot_id == snapshot.id, Entity.entity_id == entity_id)
        .first()
    )

    if not entity:
        return templates.TemplateResponse(
            "empty.html",
            {
                "request": request,
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
        "entity_detail.html",
        {
            "request": request,
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
            "empty.html",
            {"request": request, "title": "URL Validation"},
        )

    # Get all URL validations for the latest snapshot
    query = (
        db.query(URLValidation, Entity)
        .join(Entity, URLValidation.entity_id == Entity.id)
        .filter(Entity.snapshot_id == snapshot.id)
    )

    # Apply status filter
    if status_filter == "accessible":
        query = query.filter(URLValidation.accessible.is_(True))
    elif status_filter == "redirect":
        query = query.filter(
            URLValidation.status_code >= 300, URLValidation.status_code < 400
        )
    elif status_filter == "error":
        query = query.filter(URLValidation.status_code >= 400)
    elif status_filter == "timeout":
        query = query.filter(URLValidation.validation_error.isnot(None))

    validations = query.order_by(URLValidation.validated_at.desc()).limit(500).all()

    # Get validation stats
    total_validations = (
        db.query(URLValidation)
        .join(Entity)
        .filter(Entity.snapshot_id == snapshot.id)
        .count()
    )
    accessible_count = (
        db.query(URLValidation)
        .join(Entity)
        .filter(Entity.snapshot_id == snapshot.id, URLValidation.accessible.is_(True))
        .count()
    )
    redirect_count = (
        db.query(URLValidation)
        .join(Entity)
        .filter(
            Entity.snapshot_id == snapshot.id,
            URLValidation.status_code >= 300,
            URLValidation.status_code < 400,
        )
        .count()
    )
    error_count = (
        db.query(URLValidation)
        .join(Entity)
        .filter(Entity.snapshot_id == snapshot.id, URLValidation.status_code >= 400)
        .count()
    )

    return templates.TemplateResponse(
        "validation.html",
        {
            "request": request,
            "snapshot": snapshot,
            "validations": validations,
            "status_filter": status_filter,
            "total_validations": total_validations,
            "accessible_count": accessible_count,
            "redirect_count": redirect_count,
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
        "config.html",
        {
            "request": request,
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
            "empty.html",
            {"request": request, "title": "Historical Analysis"},
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
        "history.html",
        {
            "request": request,
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
        "partials/stats_cards.html",
        {"request": request, "snapshot": snapshot, "now": datetime.now()},
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
        "partials/federation_table.html",
        {
            "request": request,
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
        "partials/trend_chart.html",
        {"request": request, "snapshots": snapshots, "days": days},
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
        "partials/search_results.html",
        {
            "request": request,
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
        "partials/federation_comparison_chart.html",
        {"request": request, "federations": federations},
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
        "partials/entity_changes.html",
        {
            "request": request,
            "changes": changes,
            "snapshot1": snapshot1,
            "snapshot2": snapshot2,
        },
    )


@app.get("/partials/entity_table", response_class=HTMLResponse)
async def entity_table_partial(
    request: Request,
    federation_id: int | None = None,
    entity_type: str | None = None,
    privacy_filter: str | None = None,
    security_filter: str | None = None,
    sort_by: str = "organization",
    sort_order: str = "asc",
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
        limit: Max entities to return
    """
    snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()
    if not snapshot:
        return "<p>No data available</p>"

    # Build query
    query = db.query(Entity).filter(Entity.snapshot_id == snapshot.id)

    # Apply filters
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

    # Apply sorting
    if sort_by == "organization":
        sort_col = Entity.organization_name
    elif sort_by == "type":
        sort_col = Entity.entity_type
    elif sort_by == "privacy":
        sort_col = Entity.has_privacy_statement
    elif sort_by == "security":
        sort_col = Entity.has_security_contact
    else:
        sort_col = Entity.organization_name

    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Get entities
    entities = query.limit(limit).all()

    # Get federation info if filtering by federation
    federation = None
    if federation_id:
        federation = db.query(Federation).filter(Federation.id == federation_id).first()

    return templates.TemplateResponse(
        "partials/entity_table.html",
        {
            "request": request,
            "entities": entities,
            "federation": federation,
            "snapshot": snapshot,
            "entity_type": entity_type,
            "privacy_filter": privacy_filter,
            "security_filter": security_filter,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "now": datetime.now(),
        },
    )


# ========================================
# API Endpoints (JSON)
# ========================================


@app.get("/api/search")
async def search(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    """Search for entities and federations.

    Full-text search on:
    - Entity names (organization_name)
    - Entity IDs
    - Federation names
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


@app.get("/api/snapshot/latest")
async def get_latest_snapshot(db: Session = Depends(get_db)):
    """Get latest snapshot as JSON."""
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


@app.get("/api/federations")
async def get_federations_json(db: Session = Depends(get_db)):
    """Get all federations as JSON."""
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


@app.get("/api/export/entities")
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

    # Build query (same logic as entity_table_partial)
    query = db.query(Entity).filter(Entity.snapshot_id == snapshot.id)

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

    entities = query.order_by(Entity.organization_name).all()

    # CSV export
    if export_format == "csv":
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

        csv_content = output.getvalue()
        timestamp = snapshot.timestamp.strftime("%Y%m%d")
        filename = f"edugain_entities_{timestamp}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # JSON export
    else:
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

        timestamp = snapshot.timestamp.strftime("%Y%m%d")
        filename = f"edugain_entities_{timestamp}.json"

        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@app.get("/api/export/federations")
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


@app.get("/api/cache/status")
async def cache_status(db: Session = Depends(get_db)):
    """Get cache status information."""
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


@app.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Get current settings."""
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


@app.post("/api/settings")
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


@app.post("/api/settings/reset")
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
# Health Check
# ========================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
