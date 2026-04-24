"""
Database seeder — users, assets, playbooks, sample incidents
Gracefully handles schema mismatches during development
"""
import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from app.database import init_db, AsyncSessionLocal
from app.models import (
    User, Asset, Alert, Incident, SeverityScore, Playbook, PlaybookStep,
    IncidentType, UserRole, AlertSource, IncidentStatus, SeverityLevel, AuditLog
)
from app.auth import get_password_hash
from app.ai_engine import classify_incident, calculate_severity_score, calculate_escalation_risk, generate_ai_recommendation
from sqlalchemy import select

logger = logging.getLogger(__name__)

PLAYBOOKS_DATA = [
    {"name": "Brute Force Attack Response", "incident_type": IncidentType.BRUTE_FORCE,
     "description": "Standard response for brute force and credential stuffing attacks", "author": "SOC Team",
     "steps": [
         {"order":1,"title":"Lock User Account","description":"Immediately lock targeted user accounts.","action_type":"automated","is_critical":True,"estimated_duration":2},
         {"order":2,"title":"Block Source IP","description":"Add attacking IP to firewall block list.","action_type":"automated","is_critical":True,"estimated_duration":3},
         {"order":3,"title":"Force Password Reset","description":"Issue mandatory password reset for all affected accounts.","action_type":"manual","is_critical":True,"estimated_duration":10},
         {"order":4,"title":"Enable MFA","description":"Enable multi-factor authentication for affected users.","action_type":"manual","is_critical":False,"estimated_duration":15},
         {"order":5,"title":"Notify Administrator","description":"Send notification to security team and account owners.","action_type":"automated","is_critical":False,"estimated_duration":2},
         {"order":6,"title":"Review Auth Logs","description":"Examine authentication logs for past 24–48 hours.","action_type":"manual","is_critical":False,"estimated_duration":30},
         {"order":7,"title":"Document Investigation","description":"Log all findings and remediation steps.","action_type":"manual","is_critical":False,"estimated_duration":15},
     ]},
]

SAMPLE_ASSETS = [
    {"name":"Web Server 01","asset_type":"Server","ip_address":"192.168.1.10","hostname":"webserv01","department":"IT Infrastructure","criticality":9.0,"owner":"IT Team","os_type":"Linux","location":"DC-1"},
    {"name":"Database Server","asset_type":"Server","ip_address":"192.168.1.20","hostname":"dbserv01","department":"IT Infrastructure","criticality":10.0,"owner":"DBA Team","os_type":"Linux","location":"DC-1"},
]


async def seed():
    """Seed database with demo data. Gracefully handles schema mismatches."""
    try:
        await init_db()
        async with AsyncSessionLocal() as db:
            # Seed users
            try:
                existing = await db.execute(select(User).where(User.username == "admin"))
                if not existing.scalar_one_or_none():
                    for u in [
                        User(username="admin", email="admin@airps.local", full_name="System Administrator", department="Security Operations", hashed_password=get_password_hash("Admin@1234"), role=UserRole.ADMIN, is_active=True),
                        User(username="analyst", email="analyst@airps.local", full_name="SOC Analyst", department="Security Operations", hashed_password=get_password_hash("Analyst@1234"), role=UserRole.ANALYST, is_active=True),
                        User(username="viewer", email="viewer@airps.local", full_name="Security Viewer", department="IT", hashed_password=get_password_hash("Viewer@1234"), role=UserRole.VIEWER, is_active=True),
                    ]:
                        db.add(u)
                    logger.info("Created demo users")
            except Exception as e:
                logger.warning(f"Could not seed users: {e}")

            # Seed assets
            try:
                existing_assets = await db.execute(select(Asset))
                if not existing_assets.scalars().all():
                    for a in SAMPLE_ASSETS:
                        db.add(Asset(**a))
                    logger.info("Created sample assets")
            except Exception as e:
                logger.warning(f"Could not seed assets: {e}")

            # Seed playbooks
            try:
                existing_pbs = await db.execute(select(Playbook))
                if not existing_pbs.scalars().all():
                    for pb_data in PLAYBOOKS_DATA:
                        steps = pb_data.pop("steps")
                        pb = Playbook(**pb_data)
                        db.add(pb)
                        await db.flush()
                        for s in steps:
                            db.add(PlaybookStep(playbook_id=pb.id, **s))
                        pb_data["steps"] = steps
                    logger.info("Created playbooks")
            except Exception as e:
                logger.warning(f"Could not seed playbooks: {e}")

            await db.commit()
            logger.info("Database seeding complete!")
            logger.info("Demo credentials: admin/Admin@1234 | analyst/Analyst@1234 | viewer/Viewer@1234")

    except Exception as e:
        logger.error(f"Fatal seeding error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(seed())
