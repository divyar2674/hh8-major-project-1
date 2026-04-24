"""
Windows System Monitor
Reads live data from:
  - psutil: CPU, memory, disk, network I/O, processes, connections
  - win32evtlog: Windows Security/System/Application Event Logs
  - pywin32: Windows-native APIs

Auto-generates security alerts from suspicious patterns.
"""
import asyncio
import psutil
import json
import socket
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from collections import defaultdict, deque

# Windows Event Log – graceful if not on Windows
try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    import win32security
    WINDOWS_EVTLOG_AVAILABLE = True
except ImportError:
    WINDOWS_EVTLOG_AVAILABLE = False

from app.ml_engine import ml_engine, WINDOWS_EVENT_MAP, SUSPICIOUS_PROCESSES, SUSPICIOUS_PORTS
from app.models import IncidentType, SeverityLevel

# ─── Globals ──────────────────────────────────────────────────────────────────

# Ring buffer for recent events (max 500)
RECENT_EVENTS: deque = deque(maxlen=500)
# Baseline metrics (populated after first few readings)
BASELINE: Dict[str, float] = {}
# Failed login counter per hour
FAILED_LOGINS: deque = deque(maxlen=1000)
# Callbacks to push events → WebSocket
_broadcast_callbacks: List[Callable] = []


def register_broadcast(cb: Callable):
    _broadcast_callbacks.append(cb)


def unregister_broadcast(cb: Callable):
    if cb in _broadcast_callbacks:
        _broadcast_callbacks.remove(cb)


async def _broadcast(event: Dict):
    RECENT_EVENTS.appendleft(event)
    for cb in list(_broadcast_callbacks):
        try:
            await cb(event)
        except Exception:
            pass


# ─── System Metrics ───────────────────────────────────────────────────────────

def get_system_metrics() -> Dict[str, Any]:
    """Collect current system health metrics."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    net_io = psutil.net_io_counters()

    # Active network connections
    connections = []
    suspicious_conns = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                rport = conn.raddr.port
                raddr = conn.raddr.ip
                entry = {
                    "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                    "remote": f"{raddr}:{rport}",
                    "status": conn.status,
                    "pid": conn.pid,
                    "suspicious": False,
                }
                # Check suspicious ports
                if rport in SUSPICIOUS_PORTS:
                    entry["suspicious"] = True
                    entry["reason"] = SUSPICIOUS_PORTS[rport][1]
                    suspicious_conns.append(entry)
                connections.append(entry)
    except (psutil.AccessDenied, Exception):
        pass

    # Running processes — check for suspicious ones
    suspicious_procs = []
    top_procs = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'create_time']):
            try:
                pinfo = proc.info
                top_procs.append(pinfo)
                result = ml_engine.check_suspicious_process(pinfo.get('name', ''))
                if result:
                    suspicious_procs.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "incident_type": result[0].value,
                        "risk_score": result[1],
                        "username": pinfo.get('username', 'unknown'),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    # Top 10 CPU-consuming processes
    top_cpu = sorted(
        [p for p in top_procs if p.get('cpu_percent', 0) is not None],
        key=lambda x: x.get('cpu_percent', 0) or 0,
        reverse=True
    )[:10]

    # Failed logins in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    failed_logins_1h = sum(1 for ts in FAILED_LOGINS if ts > one_hour_ago)

    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": cpu,
        "cpu_count": psutil.cpu_count(),
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / (1024**3), 2),
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "net_bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
        "net_bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
        "net_packets_sent": net_io.packets_sent,
        "net_packets_recv": net_io.packets_recv,
        "active_connections": len(connections),
        "suspicious_connections": len(suspicious_conns),
        "suspicious_processes": len(suspicious_procs),
        "suspicious_procs_list": suspicious_procs[:5],
        "suspicious_conns_list": suspicious_conns[:5],
        "top_cpu_procs": top_cpu[:5],
        "failed_logins_1h": failed_logins_1h,
        "total_processes": len(top_procs),
    }

    metrics["anomaly_score"] = ml_engine.compute_anomaly_score(metrics)
    return metrics


# ─── Windows Event Log Reader ─────────────────────────────────────────────────

def read_windows_security_events(max_events: int = 50) -> List[Dict]:
    """Read recent Security/System events from Windows Event Log."""
    events = []
    if not WINDOWS_EVTLOG_AVAILABLE:
        return events

    interesting_ids = set(WINDOWS_EVENT_MAP.keys())

    for log_type in ["Security", "System", "Application"]:
        try:
            hand = win32evtlog.OpenEventLog(None, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            total = win32evtlog.GetNumberOfEventLogRecords(hand)

            events_read = win32evtlog.ReadEventLog(hand, flags, 0)
            count = 0
            for ev in (events_read or []):
                if count >= max_events:
                    break
                eid = ev.EventID & 0xFFFF

                if eid not in interesting_ids and log_type == "Security":
                    continue

                try:
                    strings = list(ev.StringInserts) if ev.StringInserts else []
                    description = " | ".join(str(s) for s in strings[:6] if s)
                except Exception:
                    description = ""

                event_info = WINDOWS_EVENT_MAP.get(eid)
                entry = {
                    "event_id": eid,
                    "log_type": log_type,
                    "source": str(ev.SourceName),
                    "timestamp": ev.TimeGenerated.Format() if ev.TimeGenerated else "",
                    "description": description[:300],
                    "incident_type": event_info[0].value if event_info else None,
                    "classification_hint": event_info[1] if event_info else None,
                    "severity": _event_type_to_severity(ev.EventType),
                    "computer": str(ev.ComputerName),
                }

                # Track failed logins
                if eid == 4625:
                    FAILED_LOGINS.append(datetime.utcnow())

                events.append(entry)
                count += 1

            win32evtlog.CloseEventLog(hand)
        except Exception:
            pass

    return events[:max_events]


def _event_type_to_severity(event_type: int) -> str:
    mapping = {
        win32evtlog.EVENTLOG_ERROR_TYPE: "error",
        win32evtlog.EVENTLOG_WARNING_TYPE: "warning",
        win32evtlog.EVENTLOG_INFORMATION_TYPE: "info",
        win32evtlog.EVENTLOG_AUDIT_FAILURE: "audit_failure",
        win32evtlog.EVENTLOG_AUDIT_SUCCESS: "audit_success",
    } if WINDOWS_EVTLOG_AVAILABLE else {}
    return mapping.get(event_type, "info")


# ─── Threat Detection ─────────────────────────────────────────────────────────

def analyze_event_for_threat(event: Dict) -> Optional[Dict]:
    """
    Analyze a Windows event and return threat alert if suspicious.
    """
    eid = event.get("event_id")
    description = event.get("description", "")

    # Known dangerous event IDs
    if eid in WINDOWS_EVENT_MAP:
        itype, hint = WINDOWS_EVENT_MAP[eid]
        severity_score, severity = ml_engine.assess_severity_from_text(description + " " + hint)

        # Amplify known high-risk events
        high_risk = {1102, 4728, 4732, 4756}
        if eid in high_risk:
            severity_score = min(severity_score + 20, 100)

        return {
            "alert_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "source": "Windows Event Log",
            "event_type": hint,
            "event_id": eid,
            "description": f"[Windows Event {eid}] {hint}: {description[:200]}",
            "incident_type": itype.value,
            "severity_score": severity_score,
            "severity": severity.value,
            "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
            "computer": event.get("computer", socket.gethostname()),
            "auto_generated": True,
        }
    return None


def analyze_metrics_for_threats(metrics: Dict) -> List[Dict]:
    """
    Analyze system metrics and generate threat alerts for anomalies.
    """
    alerts = []
    ts = metrics.get("timestamp", datetime.utcnow().isoformat())
    host = socket.gethostname()

    # High CPU anomaly
    if metrics.get("cpu_percent", 0) > 85:
        alerts.append({
            "alert_id": f"CPU-{uuid.uuid4().hex[:6].upper()}",
            "source": "System Monitor",
            "event_type": "Resource Exhaustion",
            "description": f"CPU usage at {metrics['cpu_percent']}% on {host}. Possible cryptominer, malware, or DoS.",
            "incident_type": IncidentType.MALWARE.value,
            "severity_score": 60 + min((metrics['cpu_percent'] - 85), 15),
            "severity": SeverityLevel.HIGH.value,
            "timestamp": ts,
            "computer": host,
            "auto_generated": True,
        })

    # Suspicious processes
    for proc in metrics.get("suspicious_procs_list", []):
        alerts.append({
            "alert_id": f"PROC-{uuid.uuid4().hex[:6].upper()}",
            "source": "Process Monitor",
            "event_type": "Suspicious Process Detected",
            "description": f"Suspicious process '{proc['name']}' (PID {proc['pid']}) running as '{proc.get('username','')}'. Risk score: {proc['risk_score']}.",
            "incident_type": proc["incident_type"],
            "severity_score": proc["risk_score"],
            "severity": SeverityLevel.CRITICAL.value if proc["risk_score"] >= 85 else SeverityLevel.HIGH.value,
            "timestamp": ts,
            "computer": host,
            "auto_generated": True,
        })

    # Suspicious network connections
    for conn in metrics.get("suspicious_conns_list", []):
        alerts.append({
            "alert_id": f"NET-{uuid.uuid4().hex[:6].upper()}",
            "source": "Network Monitor",
            "event_type": "Suspicious Network Connection",
            "description": f"Suspicious connection to {conn['remote']} — {conn.get('reason', 'known malicious port')}.",
            "incident_type": IncidentType.MALWARE.value,
            "severity_score": 72,
            "severity": SeverityLevel.HIGH.value,
            "timestamp": ts,
            "computer": host,
            "auto_generated": True,
        })

    # Brute force via failed logins
    failed = metrics.get("failed_logins_1h", 0)
    if failed >= 10:
        alerts.append({
            "alert_id": f"AUTH-{uuid.uuid4().hex[:6].upper()}",
            "source": "Authentication Monitor",
            "event_type": "Authentication Failure Spike",
            "description": f"{failed} failed login attempts detected in the last hour on {host}. Possible brute force attack.",
            "incident_type": IncidentType.BRUTE_FORCE.value,
            "severity_score": min(40 + failed * 2, 95),
            "severity": SeverityLevel.CRITICAL.value if failed >= 50 else SeverityLevel.HIGH.value,
            "timestamp": ts,
            "computer": host,
            "auto_generated": True,
        })

    return alerts


# ─── Background Monitor Task ──────────────────────────────────────────────────

class SystemMonitorDaemon:
    """
    Background async daemon that continuously monitors the system
    and broadcasts events via WebSocket.
    """

    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._alert_cooldown: Dict[str, datetime] = {}  # type → last triggered

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()

    def _should_alert(self, key: str, cooldown_seconds: int = 60) -> bool:
        last = self._alert_cooldown.get(key)
        if last is None or (datetime.utcnow() - last).total_seconds() > cooldown_seconds:
            self._alert_cooldown[key] = datetime.utcnow()
            return True
        return False

    async def _run(self):
        metrics_interval = 5   # seconds
        events_interval = 15   # seconds
        last_events = datetime.utcnow() - timedelta(seconds=events_interval)

        while self.running:
            try:
                # ── System metrics broadcast ──────────────────────────────
                metrics = get_system_metrics()
                await _broadcast({
                    "type": "metrics",
                    "data": metrics,
                })

                # Auto-alerts from metrics
                metric_alerts = analyze_metrics_for_threats(metrics)
                for alert in metric_alerts:
                    key = f"metric_{alert['incident_type']}_{alert['event_type']}"
                    if self._should_alert(key, 120):
                        await _broadcast({
                            "type": "threat_alert",
                            "data": alert,
                        })

                # ── Windows Event Log poll ────────────────────────────────
                now = datetime.utcnow()
                if (now - last_events).total_seconds() >= events_interval:
                    last_events = now
                    win_events = read_windows_security_events(max_events=30)
                    for ev in win_events:
                        threat = analyze_event_for_threat(ev)
                        if threat:
                            key = f"evtlog_{ev['event_id']}_{ev.get('description','')[:40]}"
                            if self._should_alert(key, 300):
                                await _broadcast({
                                    "type": "windows_event",
                                    "data": {**ev, "threat": threat},
                                })

                await asyncio.sleep(metrics_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await asyncio.sleep(metrics_interval)


# Singleton daemon
monitor_daemon = SystemMonitorDaemon()
