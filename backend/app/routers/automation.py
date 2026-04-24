"""
Automation Agent Management Router
Endpoints to control and monitor the AI Automation Agent
"""
from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_active_user
from app.models import User, UserRole
from app.automation_agent import get_automation_agent, AIAutomationAgent
from datetime import datetime

router = APIRouter()


@router.get("/status")
async def get_agent_status(current_user: User = Depends(get_current_active_user)):
    """Get automation agent status."""
    agent: AIAutomationAgent = get_automation_agent()
    return {
        "agent_status": "running" if agent.is_running else "stopped",
        "auto_execute_enabled": agent.auto_execute,
        "check_interval_seconds": agent.check_interval,
        "processed_alerts": len(agent.processed_alerts),
        "processed_incidents": len(agent.processed_incidents),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/enable")
async def enable_auto_execution(
    current_user: User = Depends(get_current_active_user)
):
    """Enable automatic playbook execution."""
    if current_user.role not in [UserRole.ADMIN, UserRole.ANALYST]:
        raise HTTPException(status_code=403, detail="Only admins/analysts can control automation")

    agent = get_automation_agent()
    agent.auto_execute = True
    return {
        "status": "success",
        "message": "Auto-execution enabled",
        "auto_execute": agent.auto_execute,
    }


@router.post("/disable")
async def disable_auto_execution(
    current_user: User = Depends(get_current_active_user)
):
    """Disable automatic playbook execution."""
    if current_user.role not in [UserRole.ADMIN, UserRole.ANALYST]:
        raise HTTPException(status_code=403, detail="Only admins/analysts can control automation")

    agent = get_automation_agent()
    agent.auto_execute = False
    return {
        "status": "success",
        "message": "Auto-execution disabled",
        "auto_execute": agent.auto_execute,
    }


@router.post("/trigger-cycle")
async def trigger_automation_cycle(
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger an automation cycle."""
    if current_user.role not in [UserRole.ADMIN, UserRole.ANALYST]:
        raise HTTPException(status_code=403, detail="Only admins/analysts can trigger automation")

    try:
        agent = get_automation_agent()
        if not agent.is_running:
            return {"status": "error", "message": "Agent not running"}

        # Note: In production, you'd use proper task scheduling
        return {
            "status": "pending",
            "message": "Automation cycle triggered",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering cycle: {str(e)}")


@router.get("/stats")
async def get_automation_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get automation agent statistics."""
    agent = get_automation_agent()
    return {
        "agent_running": agent.is_running,
        "auto_execute": agent.auto_execute,
        "check_interval": agent.check_interval,
        "processed_alerts_count": len(agent.processed_alerts),
        "processed_incidents_count": len(agent.processed_incidents),
        "timestamp": datetime.utcnow().isoformat(),
    }
