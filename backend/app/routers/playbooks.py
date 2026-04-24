"""
Playbooks router — CRUD + execution tracking
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Playbook, PlaybookStep, PlaybookExecution, PlaybookStatus, IncidentType, User
from app.schemas import (
    PlaybookCreate, PlaybookResponse,
    PlaybookExecutionResponse, StepUpdateRequest,
)
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[PlaybookResponse])
async def list_playbooks(
    incident_type: Optional[IncidentType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        select(Playbook)
        .options(selectinload(Playbook.steps))
        .where(Playbook.is_active == True)
        .order_by(Playbook.name)
    )
    if incident_type:
        query = query.where(Playbook.incident_type == incident_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PlaybookResponse, status_code=201)
async def create_playbook(
    pb_data: PlaybookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playbook = Playbook(
        name=pb_data.name,
        incident_type=pb_data.incident_type,
        description=pb_data.description,
        author=current_user.full_name or current_user.username,
    )
    db.add(playbook)
    await db.flush()

    for step_data in pb_data.steps:
        db.add(PlaybookStep(
            playbook_id=playbook.id,
            order=step_data.order,
            title=step_data.title,
            description=step_data.description,
            action_type=step_data.action_type,
            action_command=step_data.action_command,
            is_critical=step_data.is_critical,
            estimated_duration=step_data.estimated_duration,
        ))

    await db.commit()
    result = await db.execute(
        select(Playbook).options(selectinload(Playbook.steps)).where(Playbook.id == playbook.id)
    )
    return result.scalar_one()


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Playbook).options(selectinload(Playbook.steps)).where(Playbook.id == playbook_id)
    )
    pb = result.scalar_one_or_none()
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return pb


# ─── Playbook Execution ───────────────────────────────────────────────────────

@router.post("/{playbook_id}/execute/{incident_id}", response_model=PlaybookExecutionResponse)
async def execute_playbook(
    playbook_id: int,
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pb_result = await db.execute(
        select(Playbook).options(selectinload(Playbook.steps)).where(Playbook.id == playbook_id)
    )
    playbook = pb_result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    step_statuses = {
        str(i): {"title": step.title, "status": "pending", "result": None, "action_type": step.action_type}
        for i, step in enumerate(sorted(playbook.steps, key=lambda s: s.order))
    }

    execution = PlaybookExecution(
        incident_id=incident_id,
        playbook_id=playbook_id,
        status=PlaybookStatus.IN_PROGRESS,
        started_at=datetime.utcnow(),
        current_step=0,
        step_statuses=step_statuses,
        executed_by_id=current_user.id,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


@router.patch("/executions/{execution_id}/step", response_model=PlaybookExecutionResponse)
async def update_execution_step(
    execution_id: int,
    step_update: StepUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(PlaybookExecution).where(PlaybookExecution.id == execution_id))
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    step_statuses = dict(execution.step_statuses or {})
    step_key = str(step_update.step_index)
    if step_key in step_statuses:
        step_statuses[step_key]["status"] = step_update.status
        step_statuses[step_key]["result"] = step_update.result
        step_statuses[step_key]["completed_at"] = datetime.utcnow().isoformat()

    execution.step_statuses = step_statuses
    execution.current_step  = step_update.step_index + 1

    all_done = all(s["status"] in ("completed", "skipped") for s in step_statuses.values())
    if all_done:
        execution.status       = PlaybookStatus.COMPLETED
        execution.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(execution)
    return execution


@router.get("/executions/incident/{incident_id}", response_model=List[PlaybookExecutionResponse])
async def get_incident_executions(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(PlaybookExecution)
        .where(PlaybookExecution.incident_id == incident_id)
        .order_by(desc(PlaybookExecution.started_at))
    )
    return result.scalars().all()

