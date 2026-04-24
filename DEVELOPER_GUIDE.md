# T10 AIRPS - Developer Guide

## Architecture Overview

The T10 AI Incident Response & Automated Playbook System is built with a modular, extensible architecture.

### Component Diagram

```
┌──────────────────────────────────────────────────────┐
│                    t10_airps/                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐│
│  │  backend/        (FastAPI + SQLAlchemy)        ││
│  │  ├── main.py           (Entry point)           ││
│  │  ├── requirements.txt   (Dependencies)         ││
│  │  │                                              ││
│  │  └── app/                                       ││
│  │      ├── models.py           (ORM Models)      ││
│  │      ├── schemas.py          (Pydantic Models) ││
│  │      ├── database.py         (SQLAlchemy)      ││
│  │      ├── auth.py             (JWT Auth)        ││
│  │      ├── config.py           (Settings)        ││
│  │      ├── ai_engine.py        (Classification)  ││
│  │      ├── ml_engine.py        (ML Models)       ││
│  │      ├── system_monitor.py   (Metrics)         ││
│  │      ├── automation_agent.py (AI CORE)         ││
│  │      ├── seed.py             (DB Seed)         ││
│  │      │                                          ││
│  │      └── routers/            (API Routes)      ││
│  │          ├── auth.py         (Auth endpoints)  ││
│  │          ├── incidents.py    (Incidents CRUD)  ││
│  │          ├── playbooks.py    (Playbooks)       ││
│  │          ├── dashboard.py    (Metrics)         ││
│  │          ├── monitor.py      (WebSocket)       ││
│  │          └── automation.py   (Agent Control)   ││
│  │                                                 ││
│  └────────────────────────────────────────────────┘│
│                                                      │
│  ┌────────────────────────────────────────────────┐│
│  │  frontend/       (React + Vite)                ││
│  │  ├── package.json                              ││
│  │  ├── vite.config.js                            ││
│  │  │                                              ││
│  │  └── src/                                       ││
│  │      ├── main.jsx           (Entry)            ││
│  │      ├── App.jsx            (Router)           ││
│  │      ├── api.js             (API Client)       ││
│  │      │                                          ││
│  │      ├── context/           (Global State)     ││
│  │      │  ├── AuthContext.jsx                    ││
│  │      │  └── ToastContext.jsx                   ││
│  │      │                                          ││
│  │      ├── hooks/             (Custom Hooks)     ││
│  │      │  └── useMonitorWebSocket.js             ││
│  │      │                                          ││
│  │      ├── components/        (Reusable UI)      ││
│  │      │  ├── Sidebar.jsx                        ││
│  │      │  ├── Topbar.jsx                         ││
│  │      │  └── CreateIncidentModal.jsx            ││
│  │      │                                          ││
│  │      └── pages/             (Full Pages)       ││
│  │          ├── LoginPage.jsx                     ││
│  │          ├── DashboardPage.jsx                 ││
│  │          ├── IncidentsPage.jsx                 ││
│  │          ├── IncidentDetailPage.jsx            ││
│  │          ├── PlaybooksPage.jsx                 ││
│  │          ├── AlertsPage.jsx                    ││
│  │          ├── AuditPage.jsx                     ││
│  │          └── AIAnalyzePage.jsx                 ││
│  │                                                 ││
│  └────────────────────────────────────────────────┘│
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Core Components Explained

### 1. AI Classification Engine (ai_engine.py)

**Purpose:** Classify incidents into predefined types using rule-based keyword matching.

**Key Functions:**

```python
classify_incident(description, event_type) -> (IncidentType, float, str)
```
- Takes alert text and event type
- Matches against keyword rules
- Returns: (incident_type, confidence 0-1, reasoning)

```python
calculate_severity_score(asset_criticality, threat_confidence,
                        impact_level, detection_confidence) -> (float, SeverityLevel)
```
- Calculates numeric score (0-100)
- Applies severity modifiers (critical, production, test)
- Returns: (score, level)

```python
calculate_escalation_risk(incident_type, severity_score, status, time_open_hours) -> float
```
- Predicts likelihood of incident worsening
- Time-decay function
- Type-specific risk multipliers

```python
generate_ai_recommendation(incident_type, severity, escalation_risk, confidence) -> str
```
- Provides next-best-action recommendations
- Type-specific playbooks
- Confidence-based manual review suggestions

**Extension Point:** Add new incident types and keywords in the `RULES` dictionary and `SEVERITY_BOOSTERS`/`SEVERITY_DAMPERS` lists.

### 2. Automation Agent (automation_agent.py)

**Purpose:** Autonomous daemon for continuous incident detection and response.

**Core Class:** `AIAutomationAgent`

**Key Methods:**

```python
async def start()
```
- Initializes database connection
- Starts infinite monitoring loop
- Processes new alerts/incidents every 15 seconds

```python
async def _ingest_alerts()
```
- Fetches unprocessed alerts
- Auto-classifies with AI engine
- Creates incidents automatically
- Marks alerts as processed

```python
async def _analyze_incidents()
```
- Updates incident status based on severity
- Auto-assigns to senior analyst if critical
- Generates AI recommendations
- Appends notes with timestamp

```python
async def _auto_execute_playbooks()
```
- Finds matching playbooks for incidents
- Executes non-critical steps automatically
- Queues critical steps for analyst review
- Tracks execution status

**Extension Point:** Modify processing cycles to add custom logic or integrate with external systems.

### 3. Database Models (models.py)

**Key Tables:**

```python
class User(Base)              # System users with roles
class Asset(Base)             # Monitored infrastructure
class Alert(Base)             # Raw security alerts
class Incident(Base)          # Classified incidents
class SeverityScore(Base)     # Scoring calculations
class Playbook(Base)          # Response procedures
class PlaybookStep(Base)      # Individual steps
class PlaybookExecution(Base) # Execution tracking
class IncidentAction(Base)    # Remediation actions
class AuditLog(Base)          # Complete audit trail
```

**Relationships:** All tables are properly linked with foreign keys and SQLAlchemy relationships.

### 4. Pydantic Schemas (schemas.py)

Defines request/response validation for all API endpoints.

**Example:**
```python
class IncidentCreate(BaseModel):
    title: str
    description: str
    asset_criticality: float  # 1-10
    threat_confidence: float   # 1-10
    impact_level: float        # 1-10
    detection_confidence: float # 1-10
    alert_id: Optional[int] = None
```

**Extension Point:** Add new schemas for custom fields or new endpoints.

---

## Data Flow Architecture

### Alert-to-Response Flow

```
┌─────────────────┐
│  Alert Created  │ (SIEM, Firewall, Manual API)
└────────┬────────┘
         │
         ▼
┌──────────────────────────────┐
│  AI Automation Agent         │
│  (15-second monitoring cycle)│
├──────────────────────────────┤
│ 1. Detect unprocessed alert  │
│ 2. Classify with AI engine   │
│ 3. Calculate severity score  │
│ 4. Create Incident record    │
│ 5. Update status             │
│ 6. Auto-assign analyst       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Find Matching Playbook      │
├──────────────────────────────┤
│ incident_type → playbook     │
│ (Rule-based mapping)         │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Execute Playbook Steps      │
├──────────────────────────────┤
│ Non-critical steps:          │
│ - Log incident (AUTO)        │
│ - Notify admin (AUTO)        │
│ - Track actions (AUTO)       │
│                              │
│ Critical steps:              │
│ - Lock account (QUEUE)       │
│ - Block IP (QUEUE)           │
│ - Reset password (QUEUE)     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Analyst Review & Action     │
├──────────────────────────────┤
│ Review recommendations       │
│ Approve critical steps       │
│ Document findings            │
│ Close incident               │
└──────────────────────────────┘
```

---

## API Router Structure

### Authentication Router (routers/auth.py)
```python
@router.post("/login")           # JWT login
@router.get("/me")               # Get current user
@router.post("/logout")          # Logout (optional)
```

### Incidents Router (routers/incidents.py)
```python
@router.post("/alerts")          # Create alert
@router.get("/alerts")           # List alerts
@router.post("/incidents")       # Create incident (with AI)
@router.get("/incidents")        # List incidents
@router.patch("/incidents/{id}") # Update incident
```

### Playbooks Router (routers/playbooks.py)
```python
@router.get("/")                 # List playbooks
@router.post("/")                # Create playbook
@router.post("/{id}/execute/{incident_id}")  # Execute
@router.patch("/executions/{id}/step")       # Update step
```

### Dashboard Router (routers/dashboard.py)
```python
@router.get("/summary")          # Dashboard metrics
@router.get("/incident-stats")   # Incident analytics
```

### Monitor Router (routers/monitor.py)
```
@router.websocket("/ws")         # Real-time streaming
@router.get("/metrics")          # Current metrics
@router.get("/threat-summary")   # Threat level
```

### Automation Router (routers/automation.py)
```python
@router.get("/status")           # Agent status
@router.get("/stats")            # Statistics
@router.post("/enable")          # Enable auto-exec
@router.post("/disable")         # Disable auto-exec
@router.post("/trigger-cycle")   # Manual trigger
```

---

## Adding New Features

### Example 1: Add New Incident Type

**Step 1: Update Models**
```python
# backend/app/models.py
class IncidentType(str, enum.Enum):
    SUPPLY_CHAIN_ATTACK = "Supply Chain Attack"  # NEW
    # ... rest
```

**Step 2: Add Classification Rules**
```python
# backend/app/ai_engine.py
RULES[IncidentType.SUPPLY_CHAIN_ATTACK] = {
    "keywords": [
        "supply chain", "third-party vendor", "external dependency",
        "vendor compromise", "software update", "compromised library"
    ],
    "weight": 1.4,  # High weight - serious threat
}
```

**Step 3: Add Recommendations**
```python
# In generate_ai_recommendation()
IncidentType.SUPPLY_CHAIN_ATTACK: [
    "Identify all affected systems using the compromised component",
    "Check logs for unauthorized access from supply chain component",
    "Isolate affected systems if exploitation detected",
    "Update to patched version of component",
    "Review vendor communication for incident details",
    "Notify customers if their data affected"
],
```

**Step 4: Create Playbook**
```bash
curl -X POST http://localhost:8000/api/playbooks \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Supply Chain Attack Response",
    "incident_type": "Supply Chain Attack",
    "description": "Response for compromised third-party components",
    "steps": [
      {"order": 1, "title": "Identify affected systems", "action_type": "tracking", "is_critical": false},
      {"order": 2, "title": "Alert security team", "action_type": "notification", "is_critical": false},
      {"order": 3, "title": "Isolate affected systems", "action_type": "isolation", "is_critical": true},
      {"order": 4, "title": "Update component", "action_type": "blocking", "is_critical": true}
    ]
  }'
```

### Example 2: Custom API Endpoint

**Step 1: Create Router**
```python
# backend/app/routers/custom.py
from fastapi import APIRouter, Depends
from app.auth import get_current_active_user
from app.models import User

router = APIRouter()

@router.get("/my-stats")
async def get_my_stats(current_user: User = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "incidents_handled": len(current_user.incidents),
        "role": current_user.role,
    }
```

**Step 2: Register Router**
```python
# backend/main.py
from app.routers import custom

app.include_router(custom.router, prefix="/api/custom", tags=["Custom"])
```

### Example 3: Extend Automation Agent

**Step 1: Add Custom Processing**
```python
# backend/app/automation_agent.py
async def _custom_processing(self, session: AsyncSession):
    """Custom processing logic"""
    # Your implementation here
    pass

# Step 2: Call in _process_cycle
async def _process_cycle(self):
    async with self.async_session() as session:
        await self._ingest_alerts(session)
        await self._analyze_incidents(session)
        await self._custom_processing(session)  # ADD THIS
        if self.auto_execute:
            await self._auto_execute_playbooks(session)
```

---

## Testing Strategy

### Unit Tests (Backend)

```bash
# Backend testing
cd backend
pytest tests/
```

### Integration Tests

```bash
# Run demo with actual system
python demo_test.py
```

### Frontend Tests

```bash
# Frontend testing
cd frontend
npm test
```

---

## Performance Optimization

### Database Query Optimization
```python
# Use selectinload to eager-load relationships
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Playbook)
    .options(selectinload(Playbook.steps))
    .where(Playbook.id == playbook_id)
)
playbook = result.scalar_one()
```

### Async Operations
```python
# Use async/await for I/O operations
async def fetch_data():
    async with self.async_session() as session:
        result = await session.execute(select(...))
        return result.scalars().all()
```

### Connection Pooling
```python
# Configure in database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,      # Increase pool size
    max_overflow=10,   # Allow overflow
    pool_pre_ping=True # Verify connections
)
```

---

## Security Best Practices

### Input Validation
```python
# Use Pydantic for automatic validation
class AlertCreate(BaseModel):
    alert_id: str
    source: AlertSource
    event_type: str
    description: str
    # All fields validated automatically
```

### Authentication
```python
# JWT token with expiration
@router.post("/login")
async def login(credentials: LoginRequest):
    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=EXPIRATION_MINUTES)
    )
```

### Role-Based Access Control
```python
async def get_current_active_user(token: str) -> User:
    # Validate token, get user, check if active
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403)
```

### SQL Injection Prevention
```python
# SQLAlchemy parameterized queries (automatic)
result = await db.execute(
    select(User).where(User.username == username)
)
# No string concatenation → No SQL injection
```

---

## Deployment Checklist

- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Database initialized
- [ ] Environment variables configured
- [ ] JWT secret key set
- [ ] CORS origins configured
- [ ] SSL certificates (if production)
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Performance tested under load

---

## Troubleshooting Development

### Issue: AsyncIO RuntimeError
**Cause:** Trying to use async functions synchronously
**Solution:** Use `asyncio.run()` or run within async context

### Issue: Database Locked
**Cause:** SQLite locks under concurrent writes
**Solution:** Switch to PostgreSQL for production

### Issue: JWT Token Invalid
**Cause:** Token expired or wrong secret key
**Solution:** Check SECRET_KEY and token expiration time

### Issue: CORS Error
**Cause:** Frontend URL not in CORS allow list
**Solution:** Update CORS origins in main.py

---

## Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **React Docs:** https://react.dev/
- **AsyncIO Guide:** https://docs.python.org/3/library/asyncio.html

---

## Code Style Guidelines

### Backend (Python)
```python
# Use PEP 8
# Docstrings for all functions
# Type hints for all parameters
# Async/await for I/O operations
# Explicit error handling
```

### Frontend (JavaScript)
```javascript
// Use ES6+ features
// Component-based architecture
// Props validation
// Error boundaries
// Custom hooks for logic
```

---

**Happy Coding!**

The T10 system is designed to be extended and customized. Follow the patterns established and you'll be able to add new features quickly and reliably.
