# T10 SYSTEM - FEATURE MODIFICATION & EXTENSION GUIDE

## How to Customize and Extend the T10 System

---

## Table of Contents
1. [Adding New Incident Types](#adding-new-incident-types)
2. [Creating Custom Playbooks](#creating-custom-playbooks)
3. [Modifying API Endpoints](#modifying-api-endpoints)
4. [Extending the AI Engine](#extending-the-ai-engine)
5. [Adding User Roles](#adding-user-roles)
6. [Creating Integrations](#creating-integrations)
7. [Customizing the Frontend](#customizing-the-frontend)
8. [Best Practices](#best-practices)

---

## Adding New Incident Types

### Step 1: Add to Models

**File:** `backend/app/models.py`

```python
class IncidentType(str, enum.Enum):
    # ... existing types ...
    SUPPLY_CHAIN_ATTACK = "Supply Chain Attack"  # NEW
    ADVANCED_PERSISTENT_THREAT = "Advanced Persistent Threat"  # NEW
```

### Step 2: Add Classification Rules

**File:** `backend/app/ai_engine.py`

```python
RULES: Dict[IncidentType, Dict] = {
    # ... existing rules ...
    
    IncidentType.SUPPLY_CHAIN_ATTACK: {
        "keywords": [
            "supply chain", "third-party vendor", "external dependency",
            "software update", "vendor compromise", "compromised library",
            "npm package", "open source", "dependency injection"
        ],
        "weight": 1.4,  # Higher weight = more serious threat
    },
    
    IncidentType.ADVANCED_PERSISTENT_THREAT: {
        "keywords": [
            "apt", "advanced persistent threat", "state-sponsored",
            "lateral movement", "persistent access", "command and control",
            "c2 server", "beaconing", "exfiltration tunnel"
        ],
        "weight": 1.5,
    },
}
```

### Step 3: Add AI Recommendations

**File:** `backend/app/ai_engine.py`

```python
def generate_ai_recommendation(...):
    recs_map = {
        # ... existing recommendations ...
        
        IncidentType.SUPPLY_CHAIN_ATTACK: [
            "Identify all systems using the compromised component",
            "Check logs for unauthorized access from that component",
            "Isolate affected systems if exploitation is detected",
            "Update to patched version of the component",
            "Review vendor's incident response communication",
            "Notify customers if their data could be affected",
            "Engage security researchers for deeper analysis",
        ],
        
        IncidentType.ADVANCED_PERSISTENT_THREAT: [
            "CRITICAL: This indicates a sophisticated, persistent attacker",
            "Assume widespread network compromise",
            "Engage external incident response team immediately",
            "Preserve all forensic evidence",
            "Check for lateral movement to critical systems",
            "Review 6+ months of logs for attacker footprints",
            "Consider law enforcement notification",
            "Prepare for potential ransomware or data exfiltration",
        ],
    }
```

### Step 4: Add Escalation Risk

**File:** `backend/app/ai_engine.py`

```python
def calculate_escalation_risk(...):
    type_risk = {
        # ... existing ...
        IncidentType.SUPPLY_CHAIN_ATTACK: 25,      # Moderate risk
        IncidentType.ADVANCED_PERSISTENT_THREAT: 35,  # Very high risk
    }
```

### Step 5: Create Playbook

Use the API or UI to create a playbook:

```bash
curl -X POST http://localhost:8000/api/playbooks \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Supply Chain Attack Response",
    "incident_type": "Supply Chain Attack",
    "description": "Response for compromised third-party components",
    "steps": [
      {
        "order": 1,
        "title": "Inventory Affected Systems",
        "description": "Find all systems using the compromised component",
        "action_type": "information",
        "is_critical": false,
        "estimated_duration": 30
      },
      {
        "order": 2,
        "title": "Isolate Critical Systems",
        "description": "Disconnect critical systems from network",
        "action_type": "isolation",
        "is_critical": true,
        "estimated_duration": 10
      },
      {
        "order": 3,
        "title": "Apply Patch Update",
        "description": "Update to latest patched version",
        "action_type": "blocking",
        "is_critical": true,
        "estimated_duration": 60
      }
    ]
  }'
```

### Step 6: Test

```bash
# Test classification
curl -X POST http://localhost:8000/api/incidents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Compromised npm Package",
    "description": "Our supply chain was compromised. A popular npm package we depend on was hacked.",
    "asset_criticality": 8,
    "threat_confidence": 9,
    "impact_level": 8,
    "detection_confidence": 9
  }'

# Should classify as SUPPLY_CHAIN_ATTACK with high confidence
```

---

## Creating Custom Playbooks

### Playbook Structure

```
Playbook
  ├─ name: "Descriptive Name"
  ├─ incident_type: "Matches IncidentType enum"
  ├─ description: "What this playbook does"
  ├─ author: "Who created it"
  ├─ is_active: true/false
  │
  └─ steps: [
      {
        "order": 1,
        "title": "Step Title",
        "description": "What to do",
        "action_type": "information|blocking|isolation|notification|tracking",
        "action_command": "Optional system command",
        "is_critical": true/false,
        "estimated_duration": minutes
      }
    ]
```

### Action Types

| Type | Purpose | Auto-Execute |
|------|---------|--------------|
| **information** | Gather data, log, document | ✅ Auto |
| **notification** | Alert users, send notifications | ✅ Auto |
| **tracking** | Record actions for audit | ✅ Auto |
| **blocking** | Block IPs, URLs, accounts | ❌ Manual |
| **isolation** | Disconnect systems, revoke access | ❌ Manual |

### Example: Advanced Playbook

```python
CUSTOM_PLAYBOOK = {
    "name": "Ransomware Emergency Response",
    "incident_type": "Ransomware",
    "description": "CRITICAL response for ransomware infections",
    "steps": [
        # IMMEDIATE ACTIONS (Critical)
        {
            "order": 1,
            "title": "ISOLATE — Network Disconnect",
            "description": "Immediately disconnect ALL affected systems",
            "action_type": "isolation",
            "is_critical": True,
            "estimated_duration": 5
        },
        {
            "order": 2,
            "title": "Activate Incident Command",
            "description": "Assemble incident response team",
            "action_type": "notification",
            "is_critical": True,
            "estimated_duration": 15
        },
        
        # INVESTIGATION (Mixed)
        {
            "order": 3,
            "title": "Identify Ransomware Variant",
            "description": "Determine ransomware family and version",
            "action_type": "information",
            "is_critical": False,
            "estimated_duration": 30
        },
        
        # DECISION POINT (Critical)
        {
            "order": 4,
            "title": "DO NOT PAY RANSOM",
            "description": "Document decision and notify law enforcement",
            "action_type": "tracking",
            "is_critical": True,
            "estimated_duration": 60
        },
        
        # RECOVERY (Critical)
        {
            "order": 5,
            "title": "Verify Backup Integrity",
            "description": "Ensure backups are clean and valid",
            "action_type": "information",
            "is_critical": True,
            "estimated_duration": 120
        },
        {
            "order": 6,
            "title": "Execute Disaster Recovery",
            "description": "Restore systems from clean backups",
            "action_type": "blocking",
            "is_critical": True,
            "estimated_duration": 480  # 8 hours
        },
        
        # POST-RECOVERY (Non-critical)
        {
            "order": 7,
            "title": "Harden Systems",
            "description": "Apply security improvements",
            "action_type": "blocking",
            "is_critical": False,
            "estimated_duration": 240  # 4 hours
        },
        {
            "order": 8,
            "title": "Post-Incident Review",
            "description": "Document lessons learned",
            "action_type": "tracking",
            "is_critical": False,
            "estimated_duration": 120  # 2 hours
        }
    ]
}
```

---

## Modifying API Endpoints

### Adding a New Endpoint

**File:** `backend/app/routers/custom.py` (create new file)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Incident, IncidentStatus

router = APIRouter()

@router.get("/incidents/critical-only")
async def get_critical_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get only critical incidents."""
    result = await db.execute(
        select(Incident)
        .where(Incident.severity == "Critical")
        .order_by(Incident.created_at.desc())
    )
    return result.scalars().all()


@router.post("/incidents/{id}/escalate-to-management")
async def escalate_incident(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Escalate incident to management."""
    result = await db.execute(select(Incident).where(Incident.id == id))
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Send notification to management
    # Update incident flags
    # Log action
    
    return {
        "status": "escalated",
        "incident_id": incident.incident_id,
        "timestamp": datetime.utcnow()
    }


@router.get("/dashboard/custom-metrics")
async def get_custom_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get custom dashboard metrics."""
    total = await db.execute(select(func.count(Incident.id)))
    critical = await db.execute(
        select(func.count(Incident.id))
        .where(Incident.severity == "Critical")
    )
    
    return {
        "total_incidents": total.scalar() or 0,
        "critical_incidents": critical.scalar() or 0,
        "custom_metric_1": 42,
        "custom_metric_2": 99
    }
```

### Register the Router

**File:** `backend/main.py`

```python
from app.routers import custom

app.include_router(custom.router, prefix="/api/custom", tags=["Custom Endpoints"])
```

### Test the New Endpoint

```bash
curl http://localhost:8000/api/custom/incidents/critical-only \
  -H "Authorization: Bearer TOKEN"
```

---

## Extending the AI Engine

### Adding Machine Learning Classification

**File:** `backend/app/ml_engine.py` (already exists - extend it)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle

class MLClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = MultinomialNB()
        self.is_trained = False
    
    def train(self, descriptions: List[str], types: List[str]):
        """Train classifier on historical incidents."""
        X = self.vectorizer.fit_transform(descriptions)
        self.model.fit(X, types)
        self.is_trained = True
        self.save_model()
    
    def predict(self, description: str) -> Tuple[str, float]:
        """Predict incident type with confidence."""
        if not self.is_trained:
            return None, 0.0
        
        X = self.vectorizer.transform([description])
        prediction = self.model.predict(X)[0]
        confidence = max(self.model.predict_proba(X)[0])
        return prediction, confidence
    
    def save_model(self):
        """Save trained model to disk."""
        with open("models/classifier.pkl", "wb") as f:
            pickle.dump((self.vectorizer, self.model), f)
    
    def load_model(self):
        """Load trained model from disk."""
        try:
            with open("models/classifier.pkl", "rb") as f:
                self.vectorizer, self.model = pickle.load(f)
            self.is_trained = True
        except FileNotFoundError:
            pass
```

### Integrating ML with Classification

```python
# In ai_engine.py
from app.ml_engine import MLClassifier

ml_classifier = MLClassifier()
ml_classifier.load_model()

def classify_incident(description: str, event_type: str = "") -> Tuple[IncidentType, float, str]:
    """Use both rule-based and ML classification."""
    text = (description + " " + event_type).lower()
    
    # Try ML first if trained
    if ml_classifier.is_trained:
        predicted_type, ml_confidence = ml_classifier.predict(description)
        if ml_confidence > 0.75:  # High confidence
            return predicted_type, ml_confidence, f"ML classified with {ml_confidence:.0%} confidence"
    
    # Fall back to rule-based
    scores: Dict[IncidentType, float] = {}
    for itype, cfg in RULES.items():
        matches = [kw for kw in cfg["keywords"] if kw.lower() in text]
        if matches:
            scores[itype] = (len(matches) / len(cfg["keywords"])) * cfg["weight"]
    
    if not scores:
        return IncidentType.UNKNOWN, 0.30, "No matching patterns"
    
    best = max(scores, key=scores.get)
    confidence = min(0.50 + scores[best] * 2.5, 0.99)
    return best, confidence, f"Rule-based match with {confidence:.0%} confidence"
```

---

## Adding User Roles

### Step 1: Add Role to Models

**File:** `backend/app/models.py`

```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    MANAGER = "manager"  # NEW
    AUDITOR = "auditor"   # NEW
```

### Step 2: Add Role Permissions

**File:** `backend/app/auth.py` (create new section)

```python
ROLE_PERMISSIONS = {
    "admin": {
        "create_incident": True,
        "delete_incident": True,
        "manage_users": True,
        "manage_playbooks": True,
        "view_audit_logs": True,
        "export_data": True,
    },
    "analyst": {
        "create_incident": True,
        "delete_incident": False,
        "manage_users": False,
        "manage_playbooks": False,
        "view_audit_logs": True,
        "export_data": True,
    },
    "manager": {
        "create_incident": False,
        "delete_incident": False,
        "manage_users": False,
        "manage_playbooks": False,
        "view_audit_logs": True,
        "export_data": True,
    },
    "auditor": {
        "create_incident": False,
        "delete_incident": False,
        "manage_users": False,
        "manage_playbooks": False,
        "view_audit_logs": True,  # Full access
        "export_data": True,
    },
}

def require_permission(permission: str):
    """Dependency to check user permission."""
    async def check_permission(current_user: User = Depends(get_current_active_user)):
        if ROLE_PERMISSIONS.get(current_user.role.value, {}).get(permission, False):
            return current_user
        raise HTTPException(status_code=403, detail="Permission denied")
    return check_permission
```

### Step 3: Use Permission Checks

```python
@router.delete("/incidents/{id}")
async def delete_incident(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("delete_incident"))
):
    """Delete an incident (admin only)."""
    result = await db.execute(select(Incident).where(Incident.id == id))
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    await db.delete(incident)
    await db.commit()
    return {"status": "deleted", "incident_id": incident.incident_id}
```

---

## Creating Integrations

### SIEM Integration Example (Splunk)

**File:** `backend/app/integrations/splunk.py`

```python
import requests
from typing import List, Dict

class SplunkIntegration:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.base_url = f"https://{host}:{port}"
        self.auth = (username, password)
        self.session = requests.Session()
    
    def search_alerts(self, query: str, earliest_time: str = "-24h") -> List[Dict]:
        """Search Splunk for alerts."""
        endpoint = f"{self.base_url}/services/search/jobs"
        
        data = {
            "search": query,
            "earliest_time": earliest_time,
            "output_mode": "json"
        }
        
        response = self.session.post(endpoint, data=data, auth=self.auth, verify=False)
        return response.json()
    
    def create_alert(self, alert_dict: Dict):
        """Create alert in our system from Splunk."""
        # Map Splunk fields to our Alert model
        alert = Alert(
            alert_id=alert_dict.get("_raw", {}).get("alert_id"),
            source="SIEM",
            event_type=alert_dict.get("_raw", {}).get("event_type"),
            description=alert_dict.get("_raw", {}).get("description"),
            raw_data=alert_dict
        )
        return alert


# Usage in a route
@router.post("/integrations/splunk/ingest")
async def ingest_from_splunk(
    query: str = "sourcetype=alert",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ingest alerts from Splunk."""
    splunk = SplunkIntegration(
        host="splunk.example.com",
        port=8089,
        username="admin",
        password="password"
    )
    
    results = splunk.search_alerts(query)
    
    # Create alerts in our system
    for result in results:
        alert = splunk.create_alert(result)
        db.add(alert)
    
    await db.commit()
    return {"status": "ingested", "count": len(results)}
```

### Slack Notification Integration

**File:** `backend/app/integrations/slack.py`

```python
import aiohttp
from typing import Dict

class SlackIntegration:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(self, message: Dict):
        """Send notification to Slack."""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=message) as resp:
                return resp.status == 200
    
    async def notify_critical_incident(self, incident):
        """Notify team of critical incident."""
        message = {
            "text": f":warning: CRITICAL INCIDENT: {incident.title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{incident.title}*\n{incident.description}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{incident.incident_type.value}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{incident.severity.value}"
                        }
                    ]
                }
            ]
        }
        await self.send_notification(message)
```

---

## Customizing the Frontend

### Adding a New Page

**File:** `frontend/src/pages/CustomPage.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function CustomPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(
          'http://localhost:8000/api/custom/incidents/critical-only',
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="custom-page">
      <h1>Critical Incidents Only</h1>
      <div className="incident-list">
        {data && data.map(incident => (
          <div key={incident.id} className="incident-card">
            <h3>{incident.title}</h3>
            <p>Severity: {incident.severity}</p>
            <p>Type: {incident.incident_type}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Add Route to App

**File:** `frontend/src/App.jsx`

```jsx
import CustomPage from './pages/CustomPage';

<Route path="/custom" element={<CustomPage />} />
```

### Add Navigation Link

**File:** `frontend/src/components/Sidebar.jsx`

```jsx
<nav>
  {/* ... existing links ... */}
  <Link to="/custom">Custom Reports</Link>
</nav>
```

---

## Best Practices

### 1. Always Test Changes
```bash
# Test new endpoint
curl -X GET http://localhost:8000/api/your-endpoint \
  -H "Authorization: Bearer TOKEN"

# Test with demo_test.py
python demo_test.py
```

### 2. Follow Code Style
- Use type hints
- Document functions with docstrings
- Follow existing naming conventions
- Keep functions small and focused

### 3. Update Documentation
- Add comments explaining complex logic
- Update API docs
- Document new features
- Update this guide!

### 4. Version Your Changes
```bash
git add backend/app/your_file.py
git commit -m "feat: add supply chain attack detection"
git push origin feature/supply-chain-detection
```

### 5. Test Before Merging
- Unit tests for new functions
- Integration tests with real database
- Manual testing via API/UI
- Load testing for performance

### 6. Database Migrations
If you add new database fields:
```bash
# Generate migration
alembic revision --autogenerate -m "add new field"

# Apply migration
alembic upgrade head
```

---

## Common Customization Patterns

### Pattern 1: Add Custom Field to Incident

1. Add to models.py: `new_field = Column(String(255))`
2. Add to schemas.py: `new_field: str`
3. Update API responses
4. Update database migration

### Pattern 2: Add Custom Metric to Dashboard

1. Create calculation function
2. Add endpoint to return metric
3. Call from frontend component
4. Display in dashboard UI

### Pattern 3: Add Approval Workflow

1. Add status enum: `PENDING_APPROVAL`, `APPROVED`
2. Create approval endpoint
3. Check approval before execution
4. Log approvals in audit log

---

## Next Steps

- 🚀 Deploy your customizations
- 📊 Integrate with your SIEM
- 🔔 Add notifications
- 📈 Add custom dashboards
- 🔐 Enhance security features

**Remember: Always test in development before production!**
