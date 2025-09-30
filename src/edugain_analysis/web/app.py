"""FastAPI web application for eduGAIN analysis dashboard."""

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .models import Federation, Snapshot, get_db

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


# ========================================
# API Endpoints (JSON)
# ========================================


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
