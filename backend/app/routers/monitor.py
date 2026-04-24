"""
WebSocket Manager + Monitor Router
Real-time system event streaming to connected clients
"""
import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.system_monitor import (
    get_system_metrics, read_windows_security_events,
    register_broadcast, unregister_broadcast,
    RECENT_EVENTS, monitor_daemon
)
from app.auth import get_current_active_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── WebSocket Connection Manager ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.discard(ws)

    async def broadcast(self, message: dict):
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.add(ws)
        self.active_connections -= dead


manager = ConnectionManager()


@router.websocket("/ws")
async def monitor_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system monitoring.
    Streams: metrics, threat_alerts, windows_events
    """
    await manager.connect(websocket)

    async def send_to_client(event: dict):
        try:
            await websocket.send_text(json.dumps(event, default=str))
        except Exception:
            pass

    register_broadcast(send_to_client)

    try:
        # Send snapshot of recent events on connect
        for ev in list(RECENT_EVENTS)[:20]:
            await websocket.send_text(json.dumps(ev, default=str))
            await asyncio.sleep(0.02)

        # Keep alive — wait for client to disconnect
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_text(json.dumps({"type": "keepalive"}))
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        unregister_broadcast(send_to_client)
        manager.disconnect(websocket)


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@router.get("/metrics")
async def get_live_metrics(current_user: User = Depends(get_current_active_user)):
    """Get current system metrics snapshot."""
    return get_system_metrics()


@router.get("/events")
async def get_recent_events(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """Get recent security events from the ring buffer."""
    return list(RECENT_EVENTS)[:limit]


@router.get("/windows-events")
async def get_windows_events(
    current_user: User = Depends(get_current_active_user),
):
    """Read latest Windows Security/System event logs."""
    events = read_windows_security_events(max_events=50)
    return {"count": len(events), "events": events}


@router.get("/threat-summary")
async def get_threat_summary(current_user: User = Depends(get_current_active_user)):
    """Compute current threat posture from system state."""
    metrics = get_system_metrics()
    from app.system_monitor import analyze_metrics_for_threats
    alerts = analyze_metrics_for_threats(metrics)

    threat_level = "LOW"
    if metrics["anomaly_score"] >= 70 or len(alerts) >= 3:
        threat_level = "CRITICAL"
    elif metrics["anomaly_score"] >= 50 or len(alerts) >= 2:
        threat_level = "HIGH"
    elif metrics["anomaly_score"] >= 30 or len(alerts) >= 1:
        threat_level = "MEDIUM"

    return {
        "threat_level": threat_level,
        "anomaly_score": metrics["anomaly_score"],
        "active_alerts": len(alerts),
        "alerts": alerts,
        "metrics_snapshot": {
            "cpu_percent": metrics["cpu_percent"],
            "memory_percent": metrics["memory_percent"],
            "disk_percent": metrics["disk_percent"],
            "suspicious_connections": metrics["suspicious_connections"],
            "suspicious_processes": metrics["suspicious_processes"],
            "failed_logins_1h": metrics["failed_logins_1h"],
            "active_connections": metrics["active_connections"],
        },
        "timestamp": metrics["timestamp"],
    }


@router.post("/auto-ingest")
async def auto_ingest_alert(
    current_user: User = Depends(get_current_active_user),
):
    """
    Scan current system state and auto-create incidents for any detected threats.
    Returns list of created incident IDs.
    """
    from app.system_monitor import analyze_metrics_for_threats
    from app.database import AsyncSessionLocal
    from app.models import Alert, Incident, SeverityScore, AuditLog, AlertSource, IncidentStatus
    from app.ml_engine import ml_engine
    from app.ai_engine import calculate_escalation_risk, generate_ai_recommendation
    from app.models import IncidentType
    import uuid as _uuid
    from datetime import datetime

    metrics = get_system_metrics()
    threats = analyze_metrics_for_threats(metrics)

    if not threats:
        return {"message": "No active threats detected", "created": []}

    created_ids = []

    async with AsyncSessionLocal() as db:
        for threat in threats[:5]:  # max 5 at once
            try:
                itype_val = threat.get("incident_type", IncidentType.UNKNOWN.value)
                try:
                    itype = IncidentType(itype_val)
                except ValueError:
                    itype = IncidentType.UNKNOWN

                severity_score = threat.get("severity_score", 50.0)
                from app.models import SeverityLevel
                try:
                    severity = SeverityLevel(threat.get("severity", SeverityLevel.MEDIUM.value))
                except ValueError:
                    severity = SeverityLevel.MEDIUM

                escalation = calculate_escalation_risk(itype, severity_score, "open", 0)
                ai_rec = generate_ai_recommendation(itype, severity, escalation, 0.85)

                # Create alert
                alert = Alert(
                    alert_id=threat["alert_id"],
                    source=AlertSource.API,
                    event_type=threat["event_type"],
                    description=threat["description"],
                    is_processed=True,
                )
                db.add(alert)
                await db.flush()

                # Create incident
                inc = Incident(
                    incident_id=f"INC-{_uuid.uuid4().hex[:8].upper()}",
                    title=f"[AUTO] {threat['event_type']}",
                    description=threat["description"],
                    incident_type=itype,
                    severity=severity,
                    severity_score=severity_score,
                    alert_id=alert.id,
                    status=IncidentStatus.OPEN,
                    ai_recommendation=ai_rec,
                    escalation_risk=escalation,
                )
                db.add(inc)
                await db.flush()

                score = SeverityScore(
                    incident_id=inc.id,
                    asset_criticality=8.0,
                    threat_confidence=8.5,
                    impact_level=severity_score / 10,
                    detection_confidence=9.0,
                    total_score=severity_score,
                )
                db.add(score)

                audit = AuditLog(
                    user_id=current_user.id,
                    incident_id=inc.id,
                    action="AUTO_INGEST",
                    entity_type="incident",
                    entity_id=inc.id,
                    new_value={"source": "system_monitor", "trigger": threat["event_type"]},
                )
                db.add(audit)
                created_ids.append(inc.incident_id)
            except Exception as e:
                logger.error(f"Failed to auto-ingest threat: {threat.get('event_type', 'UNKNOWN')} - Error: {str(e)}", exc_info=True)

        await db.commit()

    return {
        "message": f"Auto-ingested {len(created_ids)} incident(s) from system threats",
        "created": created_ids,
        "total_threats_detected": len(threats),
    }

