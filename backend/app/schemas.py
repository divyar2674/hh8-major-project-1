"""
Pydantic schemas — request / response validation
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from app.models import (
    IncidentType, SeverityLevel, IncidentStatus, AlertSource,
    PlaybookStatus, UserRole, CaseStatus
)


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username:   str = Field(..., min_length=3, max_length=50)
    email:      str
    full_name:  Optional[str] = None
    department: Optional[str] = None
    password:   str = Field(..., min_length=6)
    role:       UserRole = UserRole.ANALYST


class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    department: Optional[str]
    role:       UserRole
    is_active:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type:   str
    user:         UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


# ─── Asset ────────────────────────────────────────────────────────────────────

class AssetCreate(BaseModel):
    name:        str
    asset_type:  Optional[str] = None
    ip_address:  Optional[str] = None
    hostname:    Optional[str] = None
    department:  Optional[str] = None
    criticality: float = Field(default=5.0, ge=1.0, le=10.0)
    owner:       Optional[str] = None
    os_type:     Optional[str] = None
    location:    Optional[str] = None


class AssetResponse(BaseModel):
    id:          int
    name:        str
    asset_type:  Optional[str]
    ip_address:  Optional[str]
    hostname:    Optional[str]
    department:  Optional[str]
    criticality: float
    owner:       Optional[str]
    os_type:     Optional[str]
    location:    Optional[str]
    created_at:  datetime
    model_config = {"from_attributes": True}


# ─── Alert ────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    alert_id:   Optional[str] = None
    source:     AlertSource
    asset_id:   Optional[int] = None
    event_type: str
    timestamp:  Optional[datetime] = None
    description: str
    raw_data:   Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    id:           int
    alert_id:     str
    source:       AlertSource
    asset_id:     Optional[int]
    event_type:   str
    timestamp:    datetime
    description:  str
    is_processed: bool
    created_at:   datetime
    model_config = {"from_attributes": True}


# ─── Incident ─────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    title:               str
    description:         str
    alert_id:            Optional[int] = None
    asset_criticality:   float = Field(default=5.0, ge=1.0, le=10.0)
    threat_confidence:   float = Field(default=5.0, ge=1.0, le=10.0)
    impact_level:        float = Field(default=5.0, ge=1.0, le=10.0)
    detection_confidence: float = Field(default=5.0, ge=1.0, le=10.0)
    notes:               Optional[str] = None
    source_ip:           Optional[str] = None
    affected_systems:    Optional[List[str]] = None
    tags:                Optional[List[str]] = None


class IncidentUpdate(BaseModel):
    title:               Optional[str] = None
    description:         Optional[str] = None
    status:              Optional[IncidentStatus] = None
    severity:            Optional[SeverityLevel] = None
    assigned_analyst_id: Optional[int] = None
    notes:               Optional[str] = None
    tags:                Optional[List[str]] = None


class SeverityScoreResponse(BaseModel):
    asset_criticality:    float
    threat_confidence:    float
    impact_level:         float
    detection_confidence: float
    total_score:          float
    model_config = {"from_attributes": True}


class IncidentActionResponse(BaseModel):
    id:           int
    action_type:  str
    description:  str
    performed_at: datetime
    result:       Optional[str]
    model_config = {"from_attributes": True}


class IncidentResponse(BaseModel):
    id:                  int
    incident_id:         str
    title:               str
    description:         str
    incident_type:       IncidentType
    severity:            SeverityLevel
    status:              IncidentStatus
    severity_score:      float
    alert_id:            Optional[int]
    assigned_analyst_id: Optional[int]
    created_at:          datetime
    updated_at:          datetime
    resolved_at:         Optional[datetime]
    notes:               Optional[str]
    ai_recommendation:   Optional[str]
    escalation_risk:     float
    source_ip:           Optional[str]
    tags:                Optional[List[str]]
    model_config = {"from_attributes": True}


class IncidentDetailResponse(IncidentResponse):
    severity_scores: List[SeverityScoreResponse] = []
    actions:         List[IncidentActionResponse] = []


# ─── Playbook ─────────────────────────────────────────────────────────────────

class PlaybookStepCreate(BaseModel):
    order:              int
    title:              str
    description:        Optional[str] = None
    action_type:        str = "manual"
    action_command:     Optional[str] = None
    is_critical:        bool = False
    estimated_duration: int = 5


class PlaybookCreate(BaseModel):
    name:          str
    incident_type: IncidentType
    description:   Optional[str] = None
    steps:         List[PlaybookStepCreate] = []


class PlaybookStepResponse(BaseModel):
    id:                 int
    order:              int
    title:              str
    description:        Optional[str]
    action_type:        str
    is_critical:        bool
    estimated_duration: int
    model_config = {"from_attributes": True}


class PlaybookResponse(BaseModel):
    id:            int
    name:          str
    incident_type: IncidentType
    description:   Optional[str]
    version:       str
    is_active:     bool
    author:        Optional[str]
    steps:         List[PlaybookStepResponse] = []
    model_config = {"from_attributes": True}


class PlaybookExecutionResponse(BaseModel):
    id:            int
    incident_id:   int
    playbook_id:   int
    status:        PlaybookStatus
    started_at:    Optional[datetime]
    completed_at:  Optional[datetime]
    current_step:  int
    step_statuses: Optional[Dict[str, Any]]
    model_config = {"from_attributes": True}


class StepUpdateRequest(BaseModel):
    step_index: int
    status:     str
    result:     Optional[str] = None


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_incidents:         int
    open_incidents:          int
    investigating_incidents: int
    contained_incidents:     int
    closed_incidents:        int
    critical_incidents:      int
    high_incidents:          int
    medium_incidents:        int
    low_incidents:           int
    avg_resolution_time_hours: float
    incidents_today:         int
    playbooks_executed:      int
    total_alerts:            int


class TrendPoint(BaseModel):
    date:     str
    count:    int
    critical: int
    high:     int
    medium:   int
    low:      int


class DepartmentRisk(BaseModel):
    department:        str
    incident_count:    int
    avg_severity_score: float
    risk_level:        str


class DashboardResponse(BaseModel):
    stats:             DashboardStats
    trend:             List[TrendPoint]
    department_risks:  List[DepartmentRisk]
    recent_incidents:  List[IncidentResponse]


# ─── AI / Classification ──────────────────────────────────────────────────────

class ClassificationRequest(BaseModel):
    description: str
    event_type:  Optional[str] = None
    source:      Optional[str] = None


class ClassificationResponse(BaseModel):
    incident_type:       IncidentType
    confidence:          float
    reasoning:           str
    recommended_severity: SeverityLevel
    escalation_risk:     float
    ai_recommendation:   str


# ─── Case ─────────────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    title:          str
    description:    Optional[str] = None
    incident_ids:   List[int] = []
    tags:           Optional[List[str]] = None


class CaseResponse(BaseModel):
    id:          int
    case_id:     str
    title:       str
    description: Optional[str]
    status:      CaseStatus
    created_at:  datetime
    updated_at:  datetime
    tags:        Optional[List[str]]
    model_config = {"from_attributes": True}
