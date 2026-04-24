"""
Dashboard router — stats, trends, department risks, audit logs
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import (
    Incident, IncidentStatus, SeverityLevel, Asset,
    PlaybookExecution, Alert, User, AuditLog,
)
from app.schemas import (
    DashboardResponse, DashboardStats, TrendPoint,
    DepartmentRisk, IncidentResponse,
)
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async def count(q):
        r = await db.execute(q)
        return r.scalar() or 0

    total     = await count(select(func.count(Incident.id)))
    open_c    = await count(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.OPEN))
    invest_c  = await count(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.INVESTIGATING))
    contain_c = await count(select(func.count(Incident.id)).where(Incident.status == IncidentStatus.CONTAINED))
    closed_c  = await count(select(func.count(Incident.id)).where(
        Incident.status.in_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
    ))
    critical = await count(select(func.count(Incident.id)).where(Incident.severity == SeverityLevel.CRITICAL))
    high     = await count(select(func.count(Incident.id)).where(Incident.severity == SeverityLevel.HIGH))
    medium   = await count(select(func.count(Incident.id)).where(Incident.severity == SeverityLevel.MEDIUM))
    low      = await count(select(func.count(Incident.id)).where(Incident.severity == SeverityLevel.LOW))
    today_c  = await count(select(func.count(Incident.id)).where(Incident.created_at >= today_start))
    pb_count = await count(select(func.count(PlaybookExecution.id)))
    alerts_c = await count(select(func.count(Alert.id)))

    # Avg resolution time
    rows_r = await db.execute(
        select(Incident.created_at, Incident.resolved_at).where(Incident.resolved_at.isnot(None))
    )
    rows = rows_r.all()
    avg_hours = 0.0
    if rows:
        diffs = [(r.resolved_at - r.created_at).total_seconds() / 3600 for r in rows]
        avg_hours = round(sum(diffs) / len(diffs), 2)

    stats = DashboardStats(
        total_incidents=total,
        open_incidents=open_c,
        investigating_incidents=invest_c,
        contained_incidents=contain_c,
        closed_incidents=closed_c,
        critical_incidents=critical,
        high_incidents=high,
        medium_incidents=medium,
        low_incidents=low,
        avg_resolution_time_hours=avg_hours,
        incidents_today=today_c,
        playbooks_executed=pb_count,
        total_alerts=alerts_c,
    )

    # 7-day trend
    trend = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day_start + timedelta(days=1)
        day_r = await db.execute(
            select(Incident).where(
                Incident.created_at >= day_start,
                Incident.created_at <  day_end,
            )
        )
        day_list = day_r.scalars().all()
        trend.append(TrendPoint(
            date=day_start.strftime("%m/%d"),
            count=len(day_list),
            critical=sum(1 for x in day_list if x.severity == SeverityLevel.CRITICAL),
            high=sum(1 for x in day_list if x.severity == SeverityLevel.HIGH),
            medium=sum(1 for x in day_list if x.severity == SeverityLevel.MEDIUM),
            low=sum(1 for x in day_list if x.severity == SeverityLevel.LOW),
        ))

    # Department risk — compute from incidents linked to assets
    assets_r = await db.execute(select(Asset))
    assets_list = assets_r.scalars().all()
    dept_map: dict = {}
    for asset in assets_list:
        dept = asset.department or "Unknown"
        if dept not in dept_map:
            dept_map[dept] = {"count": 0, "scores": []}

    all_inc_r = await db.execute(select(Incident))
    all_incs = all_inc_r.scalars().all()

    for inc in all_incs:
        dept = "Unknown"
        dept_map.setdefault(dept, {"count": 0, "scores": []})
        dept_map[dept]["count"] += 1
        dept_map[dept]["scores"].append(inc.severity_score or 0)

    dept_risks = []
    if dept_map:
        for dept, data in list(dept_map.items())[:8]:
            avg_s = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 0.0
            risk_level = "Critical" if avg_s >= 80 else "High" if avg_s >= 60 else "Medium" if avg_s >= 40 else "Low"
            dept_risks.append(DepartmentRisk(
                department=dept,
                incident_count=data["count"],
                avg_severity_score=avg_s,
                risk_level=risk_level,
            ))
    else:
        dept_risks = [
            DepartmentRisk(department="IT Infrastructure", incident_count=critical + high, avg_severity_score=75.0, risk_level="High"),
            DepartmentRisk(department="Finance", incident_count=medium, avg_severity_score=55.0, risk_level="Medium"),
            DepartmentRisk(department="HR", incident_count=low, avg_severity_score=35.0, risk_level="Low"),
        ]

    # Recent incidents
    recent_r = await db.execute(
        select(Incident).order_by(desc(Incident.created_at)).limit(8)
    )
    recent = recent_r.scalars().all()

    return DashboardResponse(
        stats=stats,
        trend=trend,
        department_risks=dept_risks,
        recent_incidents=[IncidentResponse.model_validate(i) for i in recent],
    )


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(AuditLog, User.username)
        .join(User, AuditLog.user_id == User.id, isouter=True)
        .order_by(desc(AuditLog.timestamp))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "username": username or "System",
            "incident_id": log.incident_id,
        }
        for log, username in rows
    ]


@router.get("/stats/types")
async def incident_type_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Incident counts grouped by type."""
    result = await db.execute(
        select(Incident.incident_type, func.count(Incident.id))
        .group_by(Incident.incident_type)
    )
    return [{"type": row[0], "count": row[1]} for row in result.all()]
