"""
ORM Models — T10 AI Incident Response & Automated Playbook System
Tables: Users, Assets, Alerts, Incidents, Severity_Scores,
        Playbooks, Playbook_Steps, Incident_Actions, Cases, Audit_Logs
"""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


# ─── Enumerations ─────────────────────────────────────────────────────────────

class IncidentType(str, enum.Enum):
    BRUTE_FORCE         = "Brute Force Attack"
    MALWARE             = "Malware Infection"
    PHISHING            = "Phishing Attempt"
    DATA_EXFILTRATION   = "Data Exfiltration"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    RANSOMWARE          = "Ransomware"
    DOS_DDOS            = "DoS/DDoS Attack"
    INSIDER_THREAT      = "Insider Threat"
    UNKNOWN             = "Unknown"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"


class IncidentStatus(str, enum.Enum):
    OPEN          = "Open"
    INVESTIGATING = "Investigating"
    CONTAINED     = "Contained"
    RESOLVED      = "Resolved"
    CLOSED        = "Closed"


class AlertSource(str, enum.Enum):
    SIEM    = "SIEM"
    FIREWALL = "Firewall"
    MANUAL  = "Manual"
    IDS_IPS = "IDS/IPS"
    EDR     = "EDR"
    API     = "API"


class PlaybookStatus(str, enum.Enum):
    PENDING     = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED   = "Completed"
    FAILED      = "Failed"
    SKIPPED     = "Skipped"


class UserRole(str, enum.Enum):
    ADMIN   = "admin"
    ANALYST = "analyst"
    VIEWER  = "viewer"


class CaseStatus(str, enum.Enum):
    ACTIVE   = "Active"
    ON_HOLD  = "On Hold"
    CLOSED   = "Closed"


# ─── Table 1: Users ───────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String(50), unique=True, nullable=False, index=True)
    email          = Column(String(100), unique=True, nullable=False)
    full_name      = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    role           = Column(SAEnum(UserRole), default=UserRole.ANALYST)
    department     = Column(String(100), nullable=True)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    last_login     = Column(DateTime, nullable=True)

    incidents  = relationship("Incident", back_populates="assigned_analyst")
    audit_logs = relationship("AuditLog", back_populates="user")
    cases      = relationship("Case", back_populates="lead_analyst")


# ─── Table 2: Assets ──────────────────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    asset_type  = Column(String(50))
    ip_address  = Column(String(45))
    hostname    = Column(String(100))
    department  = Column(String(100))
    criticality = Column(Float, default=5.0)   # 1–10 scale
    owner       = Column(String(100))
    os_type     = Column(String(50), nullable=True)
    location    = Column(String(100), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="asset")


# ─── Table 3: Alerts ──────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"
    id           = Column(Integer, primary_key=True, index=True)
    alert_id     = Column(String(50), unique=True, nullable=False, index=True)
    source       = Column(SAEnum(AlertSource), nullable=False)
    asset_id     = Column(Integer, ForeignKey("assets.id"), nullable=True)
    event_type   = Column(String(100))
    timestamp    = Column(DateTime, default=datetime.utcnow)
    description  = Column(Text)
    raw_data     = Column(JSON, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    asset    = relationship("Asset", back_populates="alerts")
    incident = relationship("Incident", back_populates="alert", uselist=False)


# ─── Table 4: Incidents ───────────────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"
    id                  = Column(Integer, primary_key=True, index=True)
    incident_id         = Column(String(50), unique=True, nullable=False, index=True)
    title               = Column(String(200), nullable=False)
    description         = Column(Text)
    incident_type       = Column(SAEnum(IncidentType), default=IncidentType.UNKNOWN)
    severity            = Column(SAEnum(SeverityLevel), default=SeverityLevel.MEDIUM)
    status              = Column(SAEnum(IncidentStatus), default=IncidentStatus.OPEN)
    severity_score      = Column(Float, default=0.0)
    alert_id            = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    assigned_analyst_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at         = Column(DateTime, nullable=True)
    notes               = Column(Text, nullable=True)
    evidence            = Column(JSON, nullable=True)
    ai_recommendation   = Column(Text, nullable=True)
    escalation_risk     = Column(Float, default=0.0)
    tags                = Column(JSON, nullable=True)     # list of tag strings
    source_ip           = Column(String(45), nullable=True)
    affected_systems    = Column(JSON, nullable=True)

    alert               = relationship("Alert", back_populates="incident")
    assigned_analyst    = relationship("User", back_populates="incidents")
    severity_scores     = relationship("SeverityScore", back_populates="incident")
    playbook_executions = relationship("PlaybookExecution", back_populates="incident")
    actions             = relationship("IncidentAction", back_populates="incident")
    audit_logs          = relationship("AuditLog", back_populates="incident")
    case_incidents      = relationship("CaseIncident", back_populates="incident")

    # Advanced AI Analyzer Fields (nullable for backward compatibility)
    confidence_score        = Column(Float, nullable=True)  # Bayesian point estimate (0-1)
    confidence_uncertainty  = Column(Float, nullable=True)  # Credible interval width
    confidence_low          = Column(Float, nullable=True)  # 95% lower bound
    confidence_high         = Column(Float, nullable=True)  # 95% upper bound
    anomaly_score           = Column(Float, nullable=True)  # 0-100 behavioral anomaly
    anomaly_type            = Column(String(50), nullable=True)  # behavioral/statistical/temporal
    model_votes             = Column(JSON, nullable=True)  # Individual classifier predictions
    explanation             = Column(JSON, nullable=True)  # Full explainability dict
    classification_time_ms  = Column(Integer, nullable=True)  # Time to classify (ms)
    model_agreement         = Column(String(20), nullable=True)  # UNANIMOUS/MAJORITY/WEAK/CONTRADICTORY


# ─── Table 5: Severity_Scores ─────────────────────────────────────────────────

class SeverityScore(Base):
    __tablename__ = "severity_scores"
    id                   = Column(Integer, primary_key=True, index=True)
    incident_id          = Column(Integer, ForeignKey("incidents.id"))
    asset_criticality    = Column(Float, default=5.0)
    threat_confidence    = Column(Float, default=5.0)
    impact_level         = Column(Float, default=5.0)
    detection_confidence = Column(Float, default=5.0)
    total_score          = Column(Float, default=0.0)
    calculated_at        = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="severity_scores")


# ─── Table 6: Playbooks ───────────────────────────────────────────────────────

class Playbook(Base):
    __tablename__ = "playbooks"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(200), nullable=False)
    incident_type = Column(SAEnum(IncidentType), nullable=False)
    description   = Column(Text)
    version       = Column(String(20), default="1.0")
    is_active     = Column(Boolean, default=True)
    author        = Column(String(100), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps      = relationship("PlaybookStep", back_populates="playbook", order_by="PlaybookStep.order")
    executions = relationship("PlaybookExecution", back_populates="playbook")


# ─── Table 7: Playbook_Steps ──────────────────────────────────────────────────

class PlaybookStep(Base):
    __tablename__ = "playbook_steps"
    id                 = Column(Integer, primary_key=True, index=True)
    playbook_id        = Column(Integer, ForeignKey("playbooks.id"))
    order              = Column(Integer, nullable=False)
    title              = Column(String(200), nullable=False)
    description        = Column(Text)
    action_type        = Column(String(50))        # "manual" | "automated"
    action_command     = Column(Text, nullable=True)
    is_critical        = Column(Boolean, default=False)
    estimated_duration = Column(Integer, default=5)  # minutes

    playbook = relationship("Playbook", back_populates="steps")


# ─── Table 8: Incident_Actions ────────────────────────────────────────────────

class IncidentAction(Base):
    __tablename__ = "incident_actions"
    id              = Column(Integer, primary_key=True, index=True)
    incident_id     = Column(Integer, ForeignKey("incidents.id"))
    action_type     = Column(String(100))
    description     = Column(Text)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    performed_at    = Column(DateTime, default=datetime.utcnow)
    result          = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="actions")


# ─── Table 9: Cases ───────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"
    id               = Column(Integer, primary_key=True, index=True)
    case_id          = Column(String(50), unique=True, nullable=False, index=True)
    title            = Column(String(200), nullable=False)
    description      = Column(Text, nullable=True)
    status           = Column(SAEnum(CaseStatus), default=CaseStatus.ACTIVE)
    lead_analyst_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at        = Column(DateTime, nullable=True)
    tags             = Column(JSON, nullable=True)

    lead_analyst    = relationship("User", back_populates="cases")
    case_incidents  = relationship("CaseIncident", back_populates="case")


class CaseIncident(Base):
    __tablename__ = "case_incidents"
    id          = Column(Integer, primary_key=True, index=True)
    case_id     = Column(Integer, ForeignKey("cases.id"))
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    added_at    = Column(DateTime, default=datetime.utcnow)

    case     = relationship("Case", back_populates="case_incidents")
    incident = relationship("Incident", back_populates="case_incidents")


# ─── Table 10: Audit_Logs ─────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    action      = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id   = Column(Integer)
    old_value   = Column(JSON, nullable=True)
    new_value   = Column(JSON, nullable=True)
    ip_address  = Column(String(45), nullable=True)
    timestamp   = Column(DateTime, default=datetime.utcnow)

    user     = relationship("User", back_populates="audit_logs")
    incident = relationship("Incident", back_populates="audit_logs")


# ─── PlaybookExecution ────────────────────────────────────────────────────────

class PlaybookExecution(Base):
    __tablename__ = "playbook_executions"
    id              = Column(Integer, primary_key=True, index=True)
    incident_id     = Column(Integer, ForeignKey("incidents.id"))
    playbook_id     = Column(Integer, ForeignKey("playbooks.id"))
    status          = Column(SAEnum(PlaybookStatus), default=PlaybookStatus.PENDING)
    started_at      = Column(DateTime, nullable=True)
    completed_at    = Column(DateTime, nullable=True)
    current_step    = Column(Integer, default=0)
    step_statuses   = Column(JSON, nullable=True)
    executed_by_id  = Column(Integer, ForeignKey("users.id"), nullable=True)

    incident = relationship("Incident", back_populates="playbook_executions")
    playbook = relationship("Playbook", back_populates="executions")
