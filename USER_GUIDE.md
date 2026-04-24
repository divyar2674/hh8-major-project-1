# T10 SYSTEM - COMPLETE USER GUIDE

## Table of Contents
1. [Getting Started](#getting-started)
2. [Using the Web Dashboard](#using-the-web-dashboard)
3. [Working with Incidents](#working-with-incidents)
4. [Understanding Playbooks](#understanding-playbooks)
5. [API Usage](#api-usage)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Access the System

**Web Dashboard:**
```
URL: http://localhost:5173
Username: admin
Password: Admin@1234
```

**API Documentation:**
```
URL: http://localhost:8000/api/docs
(Interactive Swagger UI - try requests directly)
```

### User Roles

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | Full system control, user management | Security managers |
| **Analyst** | Incident management, playbook execution | SOC analysts |
| **Viewer** | Read-only dashboards, reports | Management, executives |

---

## Using the Web Dashboard

### Dashboard Home
When you login, you see the main dashboard with:
- **Total Incidents** - Count of all incidents
- **Open Incidents** - Currently active incidents needing action
- **Critical Incidents** - High-priority incidents
- **Average Response Time** - Performance metric
- **Incident Trend Graph** - Historical trends
- **Real-time Alerts** - Live incident stream

### Navigation

| Section | Purpose |
|---------|---------|
| **Incidents** | View, create, and manage incidents |
| **Playbooks** | View available response procedures |
| **Alerts** | View raw security alerts |
| **Analyze** | AI analysis and recommendations |
| **Audit** | View action history and logs |

---

## Working with Incidents

### Creating an Incident Manually

**Step 1: Go to Incidents → Create New**

**Step 2: Fill in the form:**
- **Title:** Descriptive name (e.g., "SSH Brute Force on Web Server")
- **Description:** Detailed description of the incident
- **Asset Criticality:** 1-10 scale (10 = most critical)
- **Threat Confidence:** 1-10 scale (10 = very confident)
- **Impact Level:** 1-10 scale (10 = highest impact)
- **Detection Confidence:** 1-10 scale (10 = very confident)

**Step 3: Submit**

The system will:
- ✓ Auto-classify the incident type
- ✓ Calculate severity score (0-100)
- ✓ Generate AI recommendations
- ✓ Assign to analyst (if critical)
- ✓ Display results

### Understanding Incident Details

When you click on an incident, you see:

**Incident Header:**
- Incident ID (unique identifier)
- Title and status
- Severity level (color-coded)
- Severity score (0-100)

**Details Tab:**
- Description
- Incident type
- Assigned analyst
- Created/updated timestamps

**AI Analysis Tab:**
- Classification details
- Confidence score
- Escalation risk assessment
- AI-generated recommendations

**Playbook Tab:**
- Available playbooks for this type
- Execution status
- Step-by-step progress

**Audit Log Tab:**
- All actions taken on this incident
- Timestamps
- Who made changes

### Changing Incident Status

**Click Status dropdown:**
1. **OPEN** → **INVESTIGATING** (start analysis)
2. **INVESTIGATING** → **CONTAINED** (attack blocked/mitigated)
3. **CONTAINED** → **RESOLVED** (vulnerability fixed)
4. **RESOLVED** → **CLOSED** (case complete)

### Adding Notes

Click **Add Note** to document:
- Investigation findings
- Actions taken
- Evidence gathered
- Lessons learned

These appear in the audit log with timestamps.

---

## Understanding Playbooks

### What is a Playbook?

A playbook is a **step-by-step response procedure** for a specific incident type.

**Example - Brute Force Attack Response:**
```
Step 1: Lock User Account          (Critical - Requires approval)
Step 2: Block Source IP            (Critical - Requires approval)
Step 3: Force Password Reset       (Critical - Requires approval)
Step 4: Enable MFA                 (Non-critical - Auto-executes)
Step 5: Notify Administrator       (Non-critical - Auto-executes)
Step 6: Review Auth Logs           (Non-critical - Auto-executes)
Step 7: Document Investigation     (Non-critical - Auto-executes)
```

### Playbook Types

| Type | Auto-Execute | Example |
|------|--------------|---------|
| **Critical** | ❌ Manual | Block IP, lock account, reset password |
| **Non-Critical** | ✅ Automatic | Logging, notifications, documentation |

### Executing a Playbook

**Option 1: From Incident Detail Page**
1. Click "Playbooks" tab
2. Click "Execute" on the matching playbook
3. Review and approve each critical step

**Option 2: From Playbook Page**
1. Go to Playbooks
2. Click the playbook
3. Click "Execute for Incident"
4. Select the incident from the dropdown
5. Execute

### Monitoring Playbook Progress

In the playbook execution view:
- ✓ Completed steps are marked green
- ⏳ In-progress steps show current action
- ⭕ Pending steps are awaiting execution
- ⚠️ Failed steps show error details

---

## API Usage

### Getting a Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@1234"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

```bash
curl http://localhost:8000/api/incidents \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Common API Requests

**Create Alert:**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_id": "ALT-2024-001",
    "source": "SIEM",
    "event_type": "Failed Login",
    "description": "Multiple failed login attempts detected",
    "asset_id": 1
  }'
```

**Create Incident (Auto-Classified):**
```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SSH Brute Force",
    "description": "Multiple SSH login attempts on web server",
    "asset_criticality": 9,
    "threat_confidence": 8,
    "impact_level": 7,
    "detection_confidence": 9
  }'
```

**List Incidents:**
```bash
curl "http://localhost:8000/api/incidents?skip=0&limit=10" \
  -H "Authorization: Bearer TOKEN"
```

**Get Incident Detail:**
```bash
curl http://localhost:8000/api/incidents/1 \
  -H "Authorization: Bearer TOKEN"
```

**List Playbooks:**
```bash
curl http://localhost:8000/api/playbooks/ \
  -H "Authorization: Bearer TOKEN"
```

**Execute Playbook:**
```bash
curl -X POST http://localhost:8000/api/playbooks/1/execute/5 \
  -H "Authorization: Bearer TOKEN"
```

**Update Playbook Step:**
```bash
curl -X PATCH http://localhost:8000/api/playbooks/executions/1/step \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "step_index": 0,
    "status": "completed",
    "result": "User account locked successfully"
  }'
```

---

## Common Tasks

### Task 1: Respond to a Brute Force Attack

**Step 1: Alert Arrives**
- SIEM detects 100+ failed login attempts

**Step 2: System Auto-Creates Incident**
- Type: Brute Force Attack
- Severity: Critical (score: 85+)
- Status: Open

**Step 3: Analyst Reviews**
1. Open incident
2. Read AI recommendations
3. Review "Brute Force Attack Response" playbook

**Step 4: Execute Playbook**
1. Click "Execute Playbook"
2. System auto-executes:
   - Logging
   - Notifications
3. You manually approve:
   - Lock user account
   - Block source IP
   - Reset password

**Step 5: Update Status**
1. Change status to "CONTAINED"
2. Add note: "Attack blocked, user notified"
3. Change status to "RESOLVED"

### Task 2: Investigate Data Exfiltration

**Step 1: Create Incident**
```
Title: Data Exfiltration - Database Server
Description: 5GB of customer data transferred to external IP
Asset Criticality: 10 (database is critical)
Threat Confidence: 9
Impact: 10
```

**Step 2: Review AI Analysis**
- Type: Data Exfiltration
- Severity: Critical (score: 95+)
- Escalation Risk: Very High
- AI Recommendations:
  - Block outbound connections
  - Revoke all sessions
  - Notify legal/compliance
  - Preserve evidence

**Step 3: Execute Playbook**
- System auto-blocks connections
- You manually:
  - Identify what data was accessed
  - Contact legal department
  - Preserve forensic evidence

**Step 4: Document & Close**
- Add detailed notes
- Upload evidence
- Mark as RESOLVED

### Task 3: Handle Unknown Incident

**When AI Classification is Uncertain:**
1. System marks type as "Unknown"
2. AI recommends "Escalate to analyst for manual review"
3. You:
   - Review raw alert data
   - Correlate with other alerts
   - Determine true incident type
   - Manually update incident type
   - Select appropriate playbook
   - Execute response

---

## Troubleshooting

### Issue: Incident Not Auto-Creating from Alert

**Solution:**
1. Check alert contains description and event_type
2. Verify AI classification engine is running
3. Check logs: `tail -f logs/backend.log`

### Issue: Playbook Steps Not Executing

**Solution:**
1. Verify playbook is marked "is_active"
2. Check incident type matches playbook type
3. Verify you're logged in as analyst/admin
4. Check step status isn't already "completed"

### Issue: Cannot Login

**Solution:**
1. Verify credentials are correct
2. Check database is initialized: `python -c "from app.models import *; print('DB OK')"`
3. Restart backend service
4. Check logs for auth errors

### Issue: Automation Agent Not Processing Alerts

**Solution:**
1. Check agent status: http://localhost:8000/api/automation/status
2. Verify auto_execute is enabled
3. Check agent logs in backend.log
4. Verify alerts have is_processed = False

### Issue: API Returns 401 Unauthorized

**Solution:**
1. Get new token: POST /api/auth/login
2. Include in header: "Authorization: Bearer TOKEN"
3. Verify token isn't expired (1440 minutes)

### Issue: WebSocket Not Connecting

**Solution:**
1. Check connection to http://localhost:5173
2. Open browser console (F12) for errors
3. Verify ws:// protocol in browser (not http://)
4. Check firewall isn't blocking port 5173

---

## Advanced Features

### AI Recommendations

The system analyzes each incident and provides:
- ✓ Incident-specific next-best-actions
- ✓ Severity escalation suggestions
- ✓ Risk assessment
- ✓ Confidence-based manual review flags

**Example for Ransomware:**
```
CRITICAL: Isolate ALL affected systems from the network.
Do NOT pay ransom — contact law enforcement immediately.
Initiate disaster recovery from clean, verified backups.
Preserve forensic evidence before any remediation.
Engage external incident response firm if needed.
```

### Escalation Risk Prediction

Calculated based on:
- Incident type (ransomware = highest risk)
- Severity score
- Time since incident occurred (older = higher risk)
- Current status

**Risk Levels:**
- 70+ = HIGH escalation risk (recommend immediate executive notification)
- 50-69 = MODERATE risk (escalate within 1 hour)
- <50 = LOW risk (standard handling)

### Real-time Threat Monitoring

Dashboard shows:
- Current threat level (LOW, MEDIUM, HIGH, CRITICAL)
- Anomaly score (0-100)
- Active alerts
- System metrics (CPU, memory, disk)

---

## Best Practices

### Incident Response
1. ✓ Always review AI recommendations
2. ✓ Document your actions in notes
3. ✓ Approve critical playbook steps carefully
4. ✓ Update incident status as you progress
5. ✓ Close incidents once resolved

### Playbook Management
1. ✓ Review playbooks regularly
2. ✓ Update playbook steps based on lessons learned
3. ✓ Test playbooks before critical incidents occur
4. ✓ Mark outdated playbooks as inactive

### Security
1. ✓ Change default passwords (especially admin)
2. ✓ Use strong passwords
3. ✓ Don't share tokens
4. ✓ Review audit logs regularly
5. ✓ Disable inactive user accounts

---

## Next Steps

- 📖 Read QUICKSTART.md for API examples
- 🔧 Read DEVELOPER_GUIDE.md to add features
- 🚀 Deploy to production with PostgreSQL
- 📊 Integrate with your SIEM platform
- 🔔 Set up notifications (email, Slack, PagerDuty)

---

**The T10 system is designed to be intuitive and powerful. Start with the web UI, then explore the API for deeper integration!**
