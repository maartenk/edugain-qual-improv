# AI Implementation Prompt: Public-Facing Quality Dashboard

**Feature ID**: 3.1 from ROADMAP.md
**Priority**: MEDIUM
**Effort**: 2-3 months
**Type**: Infrastructure, Report
**Dependencies**: Feature branch `feature/webapp-htmx-mvp` (if exists)

## Objective

Build a public-facing web application for eduGAIN quality statistics, similar to SSL Labs or Security Headers, providing global dashboards, per-federation scorecards (opt-in), entity checker tool, and REST API for transparency and community engagement.

## Context

**Current State**:
- CLI tool only, no web interface
- No public visibility into eduGAIN quality
- Federation operators can't share scorecards publicly
- No anonymous entity checking tool
- No programmatic API access

**Problem**:
- Transparency: Community can't see overall eduGAIN quality trends
- Motivation: Federations can't showcase their quality publicly
- Accessibility: Non-technical users can't check entity quality
- Integration: Third-party tools can't access quality data

**Vision**: Create SSL Labs-style dashboard at `quality.edugain.org`

## Requirements

### Core Functionality

1. **Global Dashboard** (Public, No Auth Required):
   - Overall eduGAIN statistics (total entities, federations, compliance rates)
   - Live trend graphs (updated daily from historical snapshots)
   - Hall of Fame: Top 10 federations by compliance
   - Privacy: 85.2% | Security: 63.4% | SIRTFI: 28.9%
   - Last updated: 2026-01-18 14:30 UTC

2. **Per-Federation Scorecards** (Opt-In, Public if Enabled):
   - Federation opts-in via admin panel
   - Detailed statistics, trends, rankings
   - Comparison to peer federations (same size category)
   - Embed code for federation websites:
     ```html
     <iframe src="https://quality.edugain.org/embed/InCommon"
             width="400" height="300"></iframe>
     ```
   - Social sharing (Twitter, LinkedIn)

3. **Entity Checker Tool** (Anonymous, Privacy-Respecting):
   - Input: Entity ID URL
   - Output: Instant quality report
   - Shows: Privacy, security, SIRTFI, completeness score, recommendations
   - No data stored (ephemeral analysis)
   - Rate-limited to prevent abuse

4. **REST API** (Public, Rate-Limited):
   - Endpoints:
     - `GET /api/v1/stats/global` - Global statistics
     - `GET /api/v1/federations` - List all federations
     - `GET /api/v1/federations/{name}` - Federation details (if public)
     - `GET /api/v1/trends?days=30` - Trend data
     - `GET /api/v1/check/{entityID}` - Check entity (rate-limited)
   - Authentication: API keys (optional, for higher limits)
   - OpenAPI/Swagger documentation

5. **Admin Panel** (Authentication Required):
   - Federation operators log in (OAuth/SAML)
   - Enable/disable public scorecard
   - Configure scorecard settings (colors, logo)
   - View private statistics
   - Download reports (CSV, PDF)

6. **Community Features**:
   - Best practices documentation
   - Federation success stories (curated)
   - Quality improvement guides
   - RSS feed for updates

### Technology Stack

**Backend**:
- FastAPI (Python web framework)
- SQLAlchemy (ORM for database access)
- Pydantic (data validation)
- Alembic (database migrations)

**Frontend**:
- HTMX for interactivity (no React/Vue, keep it simple)
- TailwindCSS for styling
- Chart.js for graphs
- Server-side rendering (Jinja2 templates)

**Database**:
- PostgreSQL (production)
- SQLite (development/testing)
- Reuse `history.db` schema from Feature 1.4

**Deployment**:
- Docker containers
- Nginx reverse proxy
- Let's Encrypt SSL certificates
- Cloud hosting: Heroku, DigitalOcean, AWS, etc.

### Architecture

```
┌─────────────────┐
│  Nginx (SSL)    │
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI App    │
│  (uvicorn)      │
└────────┬────────┘
         │
┌────────▼────────┐       ┌──────────────┐
│  PostgreSQL     │◄──────┤ Cron Job     │
│  (history.db)   │       │ (daily stats)│
└─────────────────┘       └──────────────┘
```

**Data Flow**:
1. Cron job runs `edugain-analyze` daily
2. Results stored in PostgreSQL `history.db`
3. Web app queries database (read-only)
4. HTMX triggers partial page updates
5. API serves JSON responses

### Page Structure

**Home Page** (`/`):
```
┌──────────────────────────────────────┐
│ eduGAIN Quality Dashboard            │
├──────────────────────────────────────┤
│ Overall Statistics                   │
│ ┌────────┬────────┬────────┐        │
│ │Privacy │Security│ SIRTFI │        │
│ │  85.2% │  63.4% │  28.9% │        │
│ └────────┴────────┴────────┘        │
│                                      │
│ ▁▂▃▅▆▇█ Trend Graph (30 days)       │
│                                      │
│ 🏆 Top Federations                  │
│  1. GÉANT - 92.3%                   │
│  2. InCommon - 89.1%                │
│  ...                                 │
└──────────────────────────────────────┘
```

**Federation Page** (`/federation/{name}`):
```
┌──────────────────────────────────────┐
│ InCommon Quality Scorecard           │
├──────────────────────────────────────┤
│ 🏆 Rank #2 / 45 federations         │
│ 📊 Overall Score: 89.1/100           │
│                                      │
│ Detailed Metrics:                    │
│ ✅ Privacy: 89.2% (rank #2)         │
│ ⚠️  Security: 71.3% (rank #12)      │
│ ✅ SIRTFI: 35.7% (rank #4)          │
│                                      │
│ Trend (90 days): ▁▂▃▄▅▆▇█           │
│                                      │
│ Peer Comparison (Large Federations):│
│ Above average: +5.2%                 │
└──────────────────────────────────────┘
```

**Entity Checker** (`/check`):
```
┌──────────────────────────────────────┐
│ Check Your Entity                    │
├──────────────────────────────────────┤
│ Entity ID:                           │
│ [https://sp.example.edu          ▶] │
│                                      │
│ Results:                             │
│ ✅ Privacy Statement: Found          │
│ ✅ Security Contact: Present         │
│ ❌ SIRTFI: Not compliant            │
│ 📊 Completeness: 72/100 (C+)        │
│                                      │
│ Recommendations:                     │
│ - Add SIRTFI compliance             │
│ - Improve metadata completeness     │
└──────────────────────────────────────┘
```

## Implementation Guidance

### Step 1: Set Up FastAPI Project

```python
# src/edugain_dashboard/__init__.py
# src/edugain_dashboard/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="eduGAIN Quality Dashboard",
    description="Public dashboard for eduGAIN federation quality metrics",
    version="1.0.0"
)

# Static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
from .routers import dashboard, api, admin

app.include_router(dashboard.router)
app.include_router(api.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/admin")

@app.get("/")
async def home(request: Request):
    """Global dashboard homepage."""
    return templates.TemplateResponse("home.html", {
        "request": request,
        "stats": await get_global_stats()
    })
```

### Step 2: Database Models

```python
# src/edugain_dashboard/models.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Federation(Base):
    """Federation table."""
    __tablename__ = "federations"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    is_public = Column(Boolean, default=False)  # Opt-in for public scorecard
    logo_url = Column(String)
    created_at = Column(DateTime)

class Snapshot(Base):
    """Daily snapshot table (reuse from Feature 1.4)."""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    total_entities = Column(Integer)
    privacy_coverage = Column(Float)
    security_coverage = Column(Float)
    sirtfi_compliance = Column(Float)
    # ... more stats
```

### Step 3: API Endpoints

```python
# src/edugain_dashboard/routers/api.py

from fastapi import APIRouter, HTTPException, Depends
from ..database import get_db

router = APIRouter()

@router.get("/stats/global")
async def get_global_stats(db = Depends(get_db)):
    """Get global eduGAIN statistics."""
    latest_snapshot = db.query(Snapshot).order_by(Snapshot.timestamp.desc()).first()

    return {
        "total_entities": latest_snapshot.total_entities,
        "total_federations": db.query(Federation).count(),
        "privacy_coverage": latest_snapshot.privacy_coverage,
        "security_coverage": latest_snapshot.security_coverage,
        "sirtfi_compliance": latest_snapshot.sirtfi_compliance,
        "last_updated": latest_snapshot.timestamp.isoformat()
    }

@router.get("/federations")
async def list_federations(db = Depends(get_db)):
    """List all federations."""
    federations = db.query(Federation).all()

    return [
        {
            "name": f.name,
            "display_name": f.display_name,
            "is_public": f.is_public,
        }
        for f in federations
    ]

@router.get("/federations/{name}")
async def get_federation(name: str, db = Depends(get_db)):
    """Get federation details."""
    federation = db.query(Federation).filter(Federation.name == name).first()

    if not federation:
        raise HTTPException(status_code=404, detail="Federation not found")

    if not federation.is_public:
        raise HTTPException(status_code=403, detail="Federation scorecard is private")

    # Get latest stats for this federation
    # ... query database ...

    return {
        "name": federation.name,
        "display_name": federation.display_name,
        "statistics": {
            # ... federation stats ...
        }
    }

@router.get("/check/{entity_id:path}")
@limiter.limit("10/minute")  # Rate limiting
async def check_entity(entity_id: str):
    """Check entity quality (ephemeral, no storage)."""
    # Fetch entity metadata (from live source or cache)
    # Run quality checks
    # Return results without storing

    return {
        "entity_id": entity_id,
        "has_privacy": True,
        "has_security_contact": True,
        "has_sirtfi": False,
        "completeness_score": 72,
        "recommendations": [
            "Add SIRTFI compliance",
            "Improve metadata completeness"
        ]
    }
```

### Step 4: HTMX Templates

```html
<!-- templates/home.html -->
<!DOCTYPE html>
<html>
<head>
    <title>eduGAIN Quality Dashboard</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold mb-8">eduGAIN Quality Dashboard</h1>

        <!-- Overall Statistics -->
        <div class="grid grid-cols-3 gap-4 mb-8">
            <div class="bg-white p-6 rounded shadow">
                <h3 class="text-gray-500 text-sm">Privacy Coverage</h3>
                <p class="text-3xl font-bold">{{ stats.privacy_coverage }}%</p>
            </div>
            <div class="bg-white p-6 rounded shadow">
                <h3 class="text-gray-500 text-sm">Security Contacts</h3>
                <p class="text-3xl font-bold">{{ stats.security_coverage }}%</p>
            </div>
            <div class="bg-white p-6 rounded shadow">
                <h3 class="text-gray-500 text-sm">SIRTFI Compliance</h3>
                <p class="text-3xl font-bold">{{ stats.sirtfi_compliance }}%</p>
            </div>
        </div>

        <!-- Trend Graph (Chart.js) -->
        <div class="bg-white p-6 rounded shadow mb-8">
            <canvas id="trendChart"></canvas>
        </div>

        <!-- Top Federations -->
        <div class="bg-white p-6 rounded shadow">
            <h2 class="text-2xl font-bold mb-4">🏆 Top Federations</h2>
            <div hx-get="/api/v1/federations/top" hx-trigger="load" hx-swap="innerHTML">
                Loading...
            </div>
        </div>
    </div>
</body>
</html>
```

### Step 5: Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "edugain_dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/edugain
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: edugain
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
```

## Acceptance Criteria

- [ ] Global dashboard displays current statistics
- [ ] Federation scorecards work (opt-in)
- [ ] Entity checker tool returns accurate results
- [ ] REST API returns correct data
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Authentication for admin panel
- [ ] Rate limiting prevents abuse
- [ ] Mobile-responsive design
- [ ] Performance: Page load < 2s
- [ ] Deployment documentation

## Testing Strategy

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from edugain_dashboard.main import app

client = TestClient(app)

def test_global_stats():
    """Test global stats endpoint."""
    response = client.get("/api/v1/stats/global")
    assert response.status_code == 200
    assert "privacy_coverage" in response.json()

def test_federation_not_found():
    """Test 404 for non-existent federation."""
    response = client.get("/api/v1/federations/nonexistent")
    assert response.status_code == 404

def test_rate_limiting():
    """Test API rate limiting."""
    # Make 11 requests (limit is 10/minute)
    for i in range(11):
        response = client.get("/api/v1/check/sp.example.edu")

    # 11th request should be rate-limited
    assert response.status_code == 429
```

## Success Metrics

- Monthly active users (MAU) > 500 in first 6 months
- 20+ federations opt-in to public scorecards
- API usage by third-party tools
- Positive community feedback
- Increased transparency and quality awareness

## References

- FastAPI documentation: https://fastapi.tiangolo.com/
- HTMX documentation: https://htmx.org/
- Similar tools: SSL Labs, Security Headers, Mozilla Observatory

## Future Enhancements

- OAuth/SAML authentication for federation operators
- GraphQL API alongside REST
- Real-time updates with WebSockets
- Mobile app (React Native)
- Internationalization (i18n)
