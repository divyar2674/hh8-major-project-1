"""
Incidents & Alerts router
Handles: Alert CRUD, Incident CRUD, AI classification endpoint
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import (
    Alert, Incident, SeverityScore, IncidentAction, AuditLog,
    IncidentStatus, SeverityLevel, AlertSource, User,
)
from app.schemas import (
    AlertCreate, AlertResponse,
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentDetailResponse,
    ClassificationRequest, ClassificationResponse,
)
from app.ai_engine import (
    classify_incident, calculate_severity_score,
    calculate_escalation_risk, generate_ai_recommendation,
)
from app.auth import get_current_active_user

router = APIRouter()


# ─── Alerts ───────────────────────────────────────────────────────────────────

@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert_id = alert_data.alert_id or f"ALT-{uuid.uuid4().hex[:8].upper()}"
    alert = Alert(
        alert_id=alert_id,
        source=alert_data.source,
        asset_id=alert_data.asset_id,
        event_type=alert_data.event_type,
        timestamp=alert_data.timestamp or datetime.utcnow(),
        description=alert_data.description,
        raw_data=alert_data.raw_data,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    source: Optional[AlertSource] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Alert).order_by(desc(Alert.created_at)).offset(skip).limit(limit)
    if source:
        query = query.where(Alert.source == source)
    result = await db.execute(query)
    return result.scalars().all()


# ─── Incidents ────────────────────────────────────────────────────────────────

@router.post("/incidents", response_model=IncidentDetailResponse, status_code=201)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    description = incident_data.description
    if incident_data.alert_id:
        alert_result = await db.execute(select(Alert).where(Alert.id == incident_data.alert_id))
        alert = alert_result.scalar_one_or_none()
        if alert:
            description = f"{description} {alert.description} {alert.event_type}"
            alert.is_processed = True

    # AI Classification
    incident_type, confidence, reasoning = classify_incident(description)

    # Severity scoring
    severity_score, severity_level = calculate_severity_score(
        asset_criticality=incident_data.asset_criticality,
        threat_confidence=incident_data.threat_confidence,
        impact_level=incident_data.impact_level,
        detection_confidence=incident_data.detection_confidence,
        description=description,
    )

    escalation_risk = calculate_escalation_risk(incident_type, severity_score, "open", 0)
    ai_rec = generate_ai_recommendation(incident_type, severity_level, escalation_risk, confidence)

    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    incident = Incident(
        incident_id=incident_id,
        title=incident_data.title,
        description=incident_data.description,
        incident_type=incident_type,
        severity=severity_level,
        severity_score=severity_score,
        alert_id=incident_data.alert_id,
        notes=incident_data.notes,
        ai_recommendation=ai_rec,
        escalation_risk=escalation_risk,
        source_ip=incident_data.source_ip,
        affected_systems=incident_data.affected_systems,
        tags=incident_data.tags,
    )
    db.add(incident)
    await db.flush()

    # Severity score record
    score_record = SeverityScore(
        incident_id=incident.id,
        asset_criticality=incident_data.asset_criticality,
        threat_confidence=incident_data.threat_confidence,
        impact_level=incident_data.impact_level,
        detection_confidence=incident_data.detection_confidence,
        total_score=severity_score,
    )
    db.add(score_record)

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        incident_id=incident.id,
        action="CREATE_INCIDENT",
        entity_type="incident",
        entity_id=incident.id,
        new_value={"incident_id": incident_id, "type": incident_type.value, "severity": severity_level.value},
    ))
    await db.commit()

    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.severity_scores), selectinload(Incident.actions))
        .where(Incident.id == incident.id)
    )
    return result.scalar_one()


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[IncidentStatus] = None,
    severity: Optional[SeverityLevel] = None,
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Incident).order_by(desc(Incident.created_at)).offset(skip).limit(limit)
    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if search:
        query = query.where(
            Incident.title.ilike(f"%{search}%") | Incident.description.ilike(f"%{search}%")
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Incident)
        .options(selectinload(Incident.severity_scores), selectinload(Incident.actions))
        .where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    update_data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_values = {
        "status": incident.status.value if incident.status else None,
        "severity": incident.severity.value if incident.severity else None,
    }

    for field, value in update_data.model_dump(exclude_none=True).items():
        setattr(incident, field, value)

    if update_data.status in (IncidentStatus.RESOLVED, IncidentStatus.CLOSED):
        if not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()

    incident.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        incident_id=incident.id,
        action="UPDATE_INCIDENT",
        entity_type="incident",
        entity_id=incident.id,
        old_value=old_values,
        new_value=update_data.model_dump(exclude_none=True),
    ))
    await db.commit()
    await db.refresh(incident)
    return incident


@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    await db.delete(incident)
    await db.commit()


@router.post("/incidents/{incident_id}/actions", status_code=201)
async def add_incident_action(
    incident_id: int,
    action_type: str,
    description: str,
    result: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    action = IncidentAction(
        incident_id=incident_id,
        action_type=action_type,
        description=description,
        performed_by_id=current_user.id,
        result=result,
    )
    db.add(action)
    await db.commit()
    return {"status": "ok"}


# ─── Assets ───────────────────────────────────────────────────────────────────

from app.models import Asset
from app.schemas import AssetCreate, AssetResponse


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Asset).order_by(Asset.name))
    return result.scalars().all()


@router.post("/assets", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    asset = Asset(**data.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ─── AI Classification ────────────────────────────────────────────────────────

@router.post("/classify", response_model=ClassificationResponse)
async def classify(
    req: ClassificationRequest,
    current_user: User = Depends(get_current_active_user),
):
    incident_type, confidence, reasoning = classify_incident(req.description, req.event_type or "")
    score, severity = calculate_severity_score(5.0, confidence * 10, 5.0, 5.0, req.description)
    escalation_risk = calculate_escalation_risk(incident_type, score, "open", 0)
    ai_rec = generate_ai_recommendation(incident_type, severity, escalation_risk, confidence)
    return ClassificationResponse(
        incident_type=incident_type,
        confidence=round(confidence, 3),
        reasoning=reasoning,
        recommended_severity=severity,
        escalation_risk=escalation_risk,
        ai_recommendation=ai_rec,
    )

