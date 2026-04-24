#!/usr/bin/env python
"""
T10 AI Incident Response System - Complete Demo & Automation Test
Tests all features including autonomous AI agent functionality
"""
import asyncio
import json
import requests
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Default credentials from seed data
ADMIN_CREDENTIALS = {"username": "admin", "password": "Admin@1234"}
ANALYST_CREDENTIALS = {"username": "analyst", "password": "Analyst@1234"}

admin_token = None
analyst_token = None


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(msg):
    """Print success message"""
    print(f"[SUCCESS] {msg}")


def print_error(msg):
    """Print error message"""
    print(f"[ERROR] {msg}")


def print_info(msg):
    """Print info message"""
    print(f"[INFO] {msg}")


async def authenticate():
    """Authenticate as admin"""
    global admin_token, analyst_token

    print_info("Authenticating as admin...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=ADMIN_CREDENTIALS,
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()
        admin_token = data.get("access_token")
        print_success(f"Admin authenticated: {admin_token[:40]}...")
    else:
        print_error(f"Authentication failed: {response.text}")
        sys.exit(1)


async def test_automation_status():
    """Check automation agent status"""
    print_section("TEST 1: AI Automation Agent Status")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/automation/status", headers=headers)

    if response.status_code == 200:
        status = response.json()
        print_success("Automation Agent Status Retrieved:")
        print(json.dumps(status, indent=2))
        return status
    else:
        print_error(f"Failed to get status: {response.text}")
        return None


async def test_create_alert():
    """Create a test alert"""
    print_section("TEST 2: Create Security Alert (Brute Force Attack)")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}

    alert_data = {
        "alert_id": "ALT-BRUTE-001",
        "source": "SIEM",
        "event_type": "Multiple failed login attempts",
        "description": "User account 'jsmith' experienced 50+ failed authentication attempts from IP 192.168.1.100 within 10 minutes. This indicates a brute force attack pattern.",
        "asset_id": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "raw_data": {
            "failed_attempts": 57,
            "source_ip": "192.168.1.100",
            "target_user": "jsmith",
            "duration_minutes": 10
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/alerts",
        json=alert_data,
        headers=headers
    )

    if response.status_code == 201:
        alert = response.json()
        print_success(f"Alert created: {alert['alert_id']}")
        print(json.dumps(alert, indent=2))
        return alert
    else:
        print_error(f"Failed to create alert: {response.text}")
        return None


async def test_create_incident():
    """Create incident with AI classification"""
    print_section("TEST 3: AI Auto-Classification & Severity Scoring")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}

    incident_data = {
        "title": "Suspected Data Exfiltration",
        "description": "Large data exfiltration detected from critical database server. Unauthorized transfer of sensitive customer data to external IP. Database dump of 2GB transferred outbound. PII exposure confirmed.",
        "asset_criticality": 9.5,
        "threat_confidence": 8.0,
        "impact_level": 9.0,
        "detection_confidence": 0.95,
        "alert_id": None
    }

    response = requests.post(
        f"{BASE_URL}/api/incidents",
        json=incident_data,
        headers=headers
    )

    if response.status_code == 201:
        incident = response.json()
        print_success(f"Incident created with AI analysis: {incident['incident_id']}")
        print(json.dumps({
            "incident_id": incident.get("incident_id"),
            "title": incident.get("title"),
            "incident_type": incident.get("incident_type"),
            "severity": incident.get("severity"),
            "severity_score": incident.get("severity_score"),
            "status": incident.get("status")
        }, indent=2))
        return incident
    else:
        print_error(f"Failed to create incident: {response.text}")
        return None


async def test_list_incidents():
    """List all incidents"""
    print_section("TEST 4: List Incidents with Status")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/incidents", headers=headers)

    if response.status_code == 200:
        incidents = response.json()
        print_success(f"Retrieved {len(incidents)} incidents")
        for inc in incidents[:5]:  # Show first 5
            print(f"  - {inc['incident_id']}: {inc['title']} [{inc['severity']}]")
        return incidents
    else:
        print_error(f"Failed to list incidents: {response.text}")
        return None


async def test_get_playbooks():
    """Retrieve available playbooks"""
    print_section("TEST 5: Available Automated Playbooks")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/playbooks/", headers=headers)

    if response.status_code == 200:
        playbooks = response.json()
        print_success(f"Retrieved {len(playbooks)} playbooks")
        for pb in playbooks[:3]:  # Show first 3
            steps_count = len(pb.get('steps', []))
            print(f"  - {pb['name']}: {pb['incident_type']} ({steps_count} steps)")
        return playbooks
    else:
        print_error(f"Failed to get playbooks: {response.text}")
        return None


async def test_dashboard():
    """Get dashboard statistics"""
    print_section("TEST 6: Real-time Incident Dashboard")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=headers)

    if response.status_code == 200:
        dashboard = response.json()
        print_success("Dashboard Summary:")
        print(json.dumps({
            "total_incidents": dashboard.get("total_incidents"),
            "open_incidents": dashboard.get("open_incidents"),
            "critical_count": dashboard.get("critical_count"),
            "high_count": dashboard.get("high_count"),
            "medium_count": dashboard.get("medium_count"),
            "low_count": dashboard.get("low_count"),
            "avg_response_time_hours": dashboard.get("avg_response_time_hours")
        }, indent=2))
        return dashboard
    else:
        print_error(f"Failed to get dashboard: {response.text}")
        return None


async def test_enable_automation():
    """Enable automatic playbook execution"""
    print_section("TEST 7: Enable AI Auto-Execution")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"{BASE_URL}/api/automation/enable", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print_success(f"Auto-execution enabled: {result.get('auto_execute')}")
        print(json.dumps(result, indent=2))
        return result
    else:
        print_error(f"Failed to enable automation: {response.text}")
        return None


async def test_trigger_automation():
    """Trigger automation cycle"""
    print_section("TEST 8: Trigger AI Automation Cycle")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"{BASE_URL}/api/automation/trigger-cycle", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print_success(f"Automation cycle triggered: {result.get('status')}")
        print(json.dumps(result, indent=2))
        return result
    else:
        print_error(f"Failed to trigger cycle: {response.text}")
        return None


async def test_automation_stats():
    """Get automation statistics"""
    print_section("TEST 9: AI Automation Statistics")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/automation/stats", headers=headers)

    if response.status_code == 200:
        stats = response.json()
        print_success("Automation Stats:")
        print(json.dumps(stats, indent=2))
        return stats
    else:
        print_error(f"Failed to get stats: {response.text}")
        return None


async def test_threat_summary():
    """Get threat summary from monitor"""
    print_section("TEST 10: Real-time Threat Summary")

    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/monitor/threat-summary", headers=headers)

    if response.status_code == 200:
        threat = response.json()
        print_success(f"Current Threat Level: {threat.get('threat_level')}")
        print(json.dumps({
            "threat_level": threat.get("threat_level"),
            "anomaly_score": threat.get("anomaly_score"),
            "active_alerts": threat.get("active_alerts"),
            "timestamp": threat.get("timestamp")
        }, indent=2))
        return threat
    else:
        print_error(f"Failed to get threat summary: {response.text}")
        return None


async def run_all_tests():
    """Run all tests"""
    print_section("T10 AI INCIDENT RESPONSE SYSTEM - FULL DEMO")
    print("Testing autonomous incident classification, severity scoring, and playbook execution")

    await authenticate()
    await asyncio.sleep(1)

    await test_automation_status()
    await asyncio.sleep(1)

    await test_create_alert()
    await asyncio.sleep(2)

    await test_create_incident()
    await asyncio.sleep(1)

    await test_list_incidents()
    await asyncio.sleep(1)

    await test_get_playbooks()
    await asyncio.sleep(1)

    await test_dashboard()
    await asyncio.sleep(1)

    await test_enable_automation()
    await asyncio.sleep(1)

    await test_trigger_automation()
    await asyncio.sleep(2)

    await test_automation_stats()
    await asyncio.sleep(1)

    await test_threat_summary()

    print_section("DEMO COMPLETE")
    print("\nT10 System Features Demonstrated:")
    print("  1. Alert Ingestion from Multiple Sources")
    print("  2. AI-Powered Incident Classification (Rule-based ML)")
    print("  3. Dynamic Severity & Risk Scoring")
    print("  4. Automated Incident Lifecycle Management")
    print("  5. Intelligent Playbook Selection & Execution")
    print("  6. Real-time Dashboard & Monitoring")
    print("  7. Autonomous Response Orchestration")
    print("  8. Escalation Risk Prediction")
    print("\nKey Innovation: AI Automation Agent")
    print("  - Continuous monitoring of unprocessed alerts")
    print("  - Automatic incident classification")
    print("  - Real-time severity assessment")
    print("  - Autonomous playbook execution for critical incidents")
    print("  - No administrator/analyst intervention required during normal operations")
    print("\nAccess the Web UI at: http://localhost:5173")
    print("API Documentation at: http://localhost:8000/api/docs")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
