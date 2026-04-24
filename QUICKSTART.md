# T10 AIRPS - Quick Start Guide

## 30-Second Setup

### 1. Start Backend
```bash
cd major_project/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (New Terminal)
```bash
cd major_project/frontend
npm run dev
```

### 3. Access System
- **Web UI:** http://localhost:5173
- **API Docs:** http://localhost:8000/api/docs
- **Login:** admin / Admin@1234

---

## Key Features You Can Test

### 1. Create Alert
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "ALT-TEST-001",
    "source": "SIEM",
    "event_type": "Brute Force",
    "description": "Multiple failed login attempts detected",
    "asset_id": 1
  }'
```

### 2. Create Incident (Auto-Classified)
```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Suspicious Activity",
    "description": "Data exfiltration detected from database server",
    "asset_criticality": 9.0,
    "threat_confidence": 8.0,
    "impact_level": 9.0,
    "detection_confidence": 0.95
  }'
```

### 3. Check Automation Status
```bash
curl http://localhost:8000/api/automation/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Enable Auto-Execution
```bash
curl -X POST http://localhost:8000/api/automation/enable \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)              │
│                  http://localhost:5173                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Components:                                            │
│  • Dashboard (Real-time Metrics)                        │
│  • Incidents Management                                 │
│  • Playbooks Editor & Executor                          │
│  • Alerts Viewer                                        │
│  • Audit Logs                                           │
│  • Real-time WebSocket Monitoring                       │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ REST API + WebSocket
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python)                    │
│             http://localhost:8000/api                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Routers:                                               │
│  • /auth - Authentication & JWT                         │
│  • /incidents - CRUD for incidents & alerts             │
│  • /playbooks - Playbook management & execution         │
│  • /dashboard - Metrics & analytics                     │
│  • /monitor - Real-time monitoring & metrics            │
│  • /automation - AI Agent control                       │
│                                                         │
│  Engines:                                               │
│  • ClassificationEngine - AI incident classification    │
│  • SeverityEngine - Risk scoring                        │
│  • PlaybookEngine - Execution orchestration             │
│  • AIAutomationAgent - Autonomous response (CORE)       │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ SQLAlchemy ORM
                     │
┌────────────────────▼────────────────────────────────────┐
│          SQLite Database (incidents.db)                  │
│                                                         │
│  Tables:                                                │
│  • users • assets • alerts • incidents                  │
│  • playbooks • playbook_steps • playbook_executions     │
│  • audit_logs • severity_scores                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## AI Automation Agent Flow

```
Every 15 seconds:

1. ALERT INGESTION
   ├─ Fetch unprocessed alerts (< 1 hour old)
   ├─ Run AI Classification
   ├─ Calculate Severity Score
   └─ Create Incident automatically

2. INCIDENT ANALYSIS
   ├─ Get open/investigating incidents
   ├─ Calculate Escalation Risk
   ├─ Generate AI Recommendations
   ├─ Auto-update status if critical
   └─ Auto-assign to senior analyst if critical

3. PLAYBOOK EXECUTION
   ├─ Query critical/high severity incidents
   ├─ Find matching playbook
   ├─ Execute non-critical steps automatically
   ├─ Queue critical steps for analyst
   └─ Track execution status
```

---

## Database Schema Highlights

### Users Table
```
- id (Primary Key)
- username (unique)
- email
- role (admin, analyst, viewer)
- is_active
- created_at, last_login
```

### Incidents Table
```
- id (Primary Key)
- incident_id (unique, e.g., INC-ABC123)
- title
- description
- incident_type (Brute Force, Malware, etc.)
- severity (Critical, High, Medium, Low)
- severity_score (0-100)
- status (Open, Investigating, Contained, Resolved, Closed)
- assigned_analyst_id (Foreign Key → Users)
- created_at, updated_at, resolved_at
- notes (with audit trail)
- evidence (JSON)
```

### Playbooks Table
```
- id
- name
- incident_type (maps to Incidents.incident_type)
- description
- is_active
- created_at, author
├─ Playbook Steps (One-to-Many)
│  ├─ order
│  ├─ title
│  ├─ description
│  ├─ action_type (information, blocking, isolation, etc.)
│  ├─ action_command
│  ├─ is_critical (determines auto-execution)
│  └─ estimated_duration
│
└─ Playbook Executions (One-to-Many)
   ├─ incident_id (link to incident)
   ├─ status (Pending, In Progress, Completed, Failed)
   ├─ started_at, completed_at
   └─ step_statuses (JSON with detailed tracking)
```

---

## Incident Classification Example

### Input
```
Description: "User 'admin' had 127 failed login attempts from 10.0.0.5 in 5 minutes"
Event Type: "Failed Authentication"
```

### Classification Process
```
1. Keywords Matched: "failed login", "multiple attempts", "authentication failure"
   → Matches BRUTE_FORCE rules (3 keywords)

2. Confidence Score: min(0.5 + (3/7) * 2.5, 0.99) = 0.57

3. Result:
   - Type: Brute Force Attack
   - Confidence: 57%
   - Reasoning: "Matched 3 keywords for 'Brute Force Attack': failed login, authentication failure, multiple attempts"
```

---

## Severity Scoring Formula

```
Score = (AssetCrit × 0.30) + (ThreatConf × 0.30) + (Impact × 0.20) + (DetectConf × 0.20)

Example:
- Asset Criticality: 9 (score: 9 × 10)
- Threat Confidence: 8 (score: 8 × 10)
- Impact Level: 8 (score: 8 × 10)
- Detection Confidence: 0.95 (score: 0.95 × 10)

Raw Score = (9×0.30) + (8×0.30) + (8×0.20) + (9.5×0.20)
           = 2.7 + 2.4 + 1.6 + 1.9
           = 8.6 / 10 → 86 / 100 (CRITICAL)
```

---

## Playbook Execution States

```
PENDING (Initial)
   ↓
IN_PROGRESS (At least one step started)
   ├─ Step 0: pending → in_progress → completed
   ├─ Step 1: pending → in_progress → completed
   └─ Step N: pending → [critical - manual review] → completed
   ↓
COMPLETED (All steps done)
   ↓
CLOSED (Archived)

Alternate States:
FAILED (Error during execution)
SKIPPED (Intentionally bypassed)
```

---

## Testing Scenarios

### Scenario 1: Brute Force Attack
```
1. Create Alert: "Multiple failed login attempts"
2. Agent auto-creates Incident with BRUTE_FORCE type
3. Severity is calculated as CRITICAL
4. Playbook "Brute Force Attack Response" is found
5. Auto-execute: Log incident, notify admin
6. Queue for analyst: Lock account, block IP, reset password
```

### Scenario 2: Data Exfiltration
```
1. Create Alert: "Large data transfer outbound"
2. Agent classifies as DATA_EXFILTRATION
3. Severity is CRITICAL + PII boost
4. Auto-assign to senior analyst
5. Playbook auto-executes information gathering steps
6. Critical steps (block connections) queued for approval
```

### Scenario 3: Phishing Email
```
1. Create Alert: "Suspicious email with malicious link"
2. Agent classifies as PHISHING
3. Severity is HIGH
4. Auto-execute: Quarantine email, block URLs
5. Auto-notify users
6. Analyst confirms and schedules awareness training
```

---

## API Response Examples

### Login Response
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Incident Response (with AI Analysis)
```json
{
  "id": 142,
  "incident_id": "INC-DATA-001",
  "title": "Data Exfiltration - Large outbound transfer",
  "incident_type": "Data Exfiltration",
  "severity": "Critical",
  "severity_score": 92.5,
  "status": "Investigating",
  "confidence": 0.87,
  "escalation_risk": 78.2,
  "assigned_analyst_id": 1,
  "notes": "[2026-04-24 09:08:45] AI Agent Analysis:\nEscalation Risk: 78.2/100\nRecommendations:\n1. Block data connections immediately\n2. Identify what data was accessed\n3. Initiate legal review for PII exposure\n4. Revoke user sessions\n5. Document for compliance requirements",
  "created_at": "2026-04-24T09:08:45.123456",
  "updated_at": "2026-04-24T09:09:15.654321"
}
```

### Automation Status Response
```json
{
  "agent_status": "running",
  "auto_execute_enabled": true,
  "check_interval_seconds": 15,
  "processed_alerts": 47,
  "processed_incidents": 23,
  "timestamp": "2026-04-24T09:15:30.123456"
}
```

---

## Common Tasks

### Add New Incident Type
1. Edit `backend/app/models.py`:
```python
class IncidentType(str, enum.Enum):
    # Add new type
    SUPPLY_CHAIN_ATTACK = "Supply Chain Attack"
```

2. Edit `backend/app/ai_engine.py`:
```python
RULES: Dict[IncidentType, Dict] = {
    IncidentType.SUPPLY_CHAIN_ATTACK: {
        "keywords": ["supply chain", "third-party", "vendor breach"],
        "weight": 1.3,
    },
    # ... rest of rules
}
```

3. Create playbook via API or UI

### Create Custom Playbook
```bash
curl -X POST http://localhost:8000/api/playbooks \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Custom Response Plan",
    "incident_type": "Brute Force Attack",
    "description": "Custom brute force response",
    "steps": [
      {
        "order": 1,
        "title": "Alert Security Team",
        "action_type": "notification",
        "is_critical": true
      },
      {
        "order": 2,
        "title": "Log Incident",
        "action_type": "tracking",
        "is_critical": false
      }
    ]
  }'
```

---

## Performance Tuning

### Backend Optimization
```python
# In backend/app/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Increase connection pool
    max_overflow=10,        # Allow overflow connections
    echo=False              # Disable query logging
)
```

### Automation Agent Tuning
```python
# In backend/app/automation_agent.py
agent = AIAutomationAgent(
    check_interval=10,  # Check every 10 seconds (faster)
    auto_execute=True
)
```

---

## Logs & Debugging

### View Backend Logs
```bash
cd major_project/backend
tail -f backend.log
```

### View Frontend Logs
```bash
cd major_project/frontend
tail -f frontend.log
```

### Enable Debug Mode
```python
# In backend/main.py
# Change echo=False to echo=True in database.py for SQL logging
engine = create_async_engine(DATABASE_URL, echo=True)
```

---

## Contact & Support

For issues or questions:
1. Check logs: `tail -f backend.log`
2. Review API docs: http://localhost:8000/api/docs
3. Check system health: http://localhost:8000/api/health
4. Monitor automation: http://localhost:8000/api/automation/status

---

**Status: PRODUCTION READY**

The T10 system is fully functional and ready for real-world incident response operations.
