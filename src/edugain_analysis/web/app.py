"""FastAPI web application for eduGAIN analysis dashboard."""

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .models import Entity, Federation, Snapshot, URLValidation, get_db

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
        "partials/stats_cards.html", {"request": request, "snapshot": snapshot}
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
# Health Check
# ========================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
