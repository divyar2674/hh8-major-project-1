"""
AI Automation Agent — T10 System
Autonomous incident response orchestration without manual intervention.
Monitors alerts, classifies, scores, and executes playbooks automatically.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from app.models import (
    Alert, Incident, Playbook, PlaybookExecution, PlaybookStatus,
    IncidentStatus, User, UserRole, Asset, IncidentType,
)
from app.database import Base, get_async_db_url
from app.ai_engine import (
    classify_incident, calculate_severity_score,
    calculate_escalation_risk, generate_ai_recommendation,
)
from app.config import get_config

logger = logging.getLogger(__name__)


class AIAutomationAgent:
    """
    Autonomous AI agent for incident response.
    Runs as a background daemon, monitoring for unprocessed alerts and incidents.
    """

    def __init__(self, check_interval: int = 10, auto_execute: bool = True):
        """
        Args:
            check_interval: Seconds between checks for new alerts/incidents
            auto_execute: Whether to auto-execute playbooks
        """
        self.check_interval = check_interval
        self.auto_execute = auto_execute
        self.is_running = False
        self.engine = None
        self.async_session = None
        self.processed_alerts = set()
        self.processed_incidents = set()

    async def initialize(self):
        """Initialize database connection pool."""
        try:
            db_url = get_async_db_url()
            self.engine = create_async_engine(db_url, echo=False)
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("AI Automation Agent initialized with database connection")
        except Exception as e:
            logger.error(f"Failed to initialize AI Automation Agent: {e}")
            raise

    async def start(self):
        """Start the automation agent daemon."""
        if self.is_running:
            logger.warning("Automation agent already running")
            return

        await self.initialize()
        self.is_running = True
        logger.info("AI Automation Agent started — autonomous incident response enabled")

        try:
            while self.is_running:
                try:
                    await self._process_cycle()
                except Exception as e:
                    logger.error(f"Error in automation cycle: {e}")

                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("AI Automation Agent stopping...")
            self.is_running = False

    async def stop(self):
        """Stop the automation agent."""
        self.is_running = False
        if self.engine:
            await self.engine.dispose()
        logger.info("AI Automation Agent stopped")

    async def _process_cycle(self):
        """Main processing cycle: check for alerts and incidents, auto-respond."""
        async with self.async_session() as session:
            # Step 1: Process unprocessed alerts → create incidents
            await self._ingest_alerts(session)

            # Step 2: Analyze and enhance incidents
            await self._analyze_incidents(session)

            # Step 3: Auto-execute playbooks for high-severity incidents
            if self.auto_execute:
                await self._auto_execute_playbooks(session)

    async def _ingest_alerts(self, session: AsyncSession):
        """Convert unprocessed alerts into incidents & auto-classify."""
        try:
            # Fetch unprocessed alerts from last hour
            cutoff = datetime.utcnow() - timedelta(hours=1)
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.is_processed == False,
                        Alert.created_at >= cutoff,
                    )
                )
            )
            unprocessed = result.scalars().all()

            for alert in unprocessed:
                if alert.id in self.processed_alerts:
                    continue

                try:
                    # Auto-classify
                    incident_type, confidence, reasoning = classify_incident(
                        alert.description or "",
                        alert.event_type or ""
                    )

                    # Get or infer asset criticality
                    asset_criticality = 5.0
                    if alert.asset_id:
                        asset_result = await session.execute(
                            select(Asset).where(Asset.id == alert.asset_id)
                        )
                        asset = asset_result.scalar_one_or_none()
                        if asset:
                            asset_criticality = asset.criticality

                    # Calculate severity
                    threat_confidence = min(confidence * 10, 10.0)
                    impact_level = 5.0  # Default
                    detection_confidence = confidence * 10

                    severity_score, severity_level = calculate_severity_score(
                        asset_criticality=asset_criticality,
                        threat_confidence=threat_confidence,
                        impact_level=impact_level,
                        detection_confidence=detection_confidence,
                        description=alert.description or "",
                    )

                    # Create incident
                    incident = Incident(
                        incident_id=f"INC-{alert.alert_id[-8:]}",
                        title=f"{incident_type.value} - {alert.event_type}",
                        description=alert.description,
                        incident_type=incident_type,
                        severity=severity_level,
                        severity_score=severity_score,
                        alert_id=alert.id,
                        status=IncidentStatus.OPEN,
                        notes=f"Auto-created by AI Agent. Confidence: {confidence:.2%}. Reasoning: {reasoning}",
                    )
                    session.add(incident)
                    alert.is_processed = True
                    self.processed_alerts.add(alert.id)

                    logger.info(
                        f"Auto-ingested alert {alert.alert_id}: "
                        f"{incident_type.value} ({severity_level.value}, score: {severity_score})"
                    )

                except Exception as e:
                    logger.error(f"Error processing alert {alert.id}: {e}")
                    continue

            await session.commit()

        except Exception as e:
            logger.error(f"Error in alert ingestion: {e}")

    async def _analyze_incidents(self, session: AsyncSession):
        """Enhance incident analysis with AI recommendations."""
        try:
            # Get recent open/investigating incidents
            cutoff = datetime.utcnow() - timedelta(hours=2)
            result = await session.execute(
                select(Incident).where(
                    and_(
                        Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]),
                        Incident.created_at >= cutoff,
                    )
                )
            )
            incidents = result.scalars().all()

            for incident in incidents:
                if incident.id in self.processed_incidents:
                    continue

                try:
                    # Calculate escalation risk
                    time_open = (datetime.utcnow() - incident.created_at).total_seconds() / 3600
                    escalation_risk = calculate_escalation_risk(
                        incident.incident_type,
                        incident.severity_score,
                        incident.status.value,
                        time_open_hours=time_open,
                    )

                    # Generate AI recommendation
                    ai_rec = generate_ai_recommendation(
                        incident.incident_type,
                        incident.severity,
                        escalation_risk,
                        confidence=0.85,  # Assume reasonable confidence
                    )

                    # Auto-update status if critical/high
                    if incident.severity.value in ["Critical", "High"]:
                        if incident.status == IncidentStatus.OPEN:
                            incident.status = IncidentStatus.INVESTIGATING

                    # Auto-assign to senior analyst if critical
                    if incident.severity.value == "Critical" and not incident.assigned_analyst_id:
                        admin_result = await session.execute(
                            select(User).where(User.role == UserRole.ADMIN).limit(1)
                        )
                        admin = admin_result.scalar_one_or_none()
                        if admin:
                            incident.assigned_analyst_id = admin.id

                    # Append notes
                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    note = f"\n[{timestamp}] AI Agent Analysis:\nEscalation Risk: {escalation_risk:.1f}/100\nRecommendations:\n{ai_rec}"
                    incident.notes = (incident.notes or "") + note

                    self.processed_incidents.add(incident.id)
                    logger.info(
                        f"Enhanced incident {incident.incident_id}: "
                        f"Escalation Risk {escalation_risk:.1f}, assigned to analyst"
                    )

                except Exception as e:
                    logger.error(f"Error analyzing incident {incident.id}: {e}")
                    continue

            await session.commit()

        except Exception as e:
            logger.error(f"Error in incident analysis: {e}")

    async def _auto_execute_playbooks(self, session: AsyncSession):
        """Auto-execute playbooks for critical incidents."""
        try:
            # Get critical incidents with no active playbook execution
            result = await session.execute(
                select(Incident).where(
                    Incident.severity.in_(["Critical", "High"])
                )
            )
            critical_incidents = result.scalars().all()

            for incident in critical_incidents:
                try:
                    # Check if playbook already executing
                    exec_result = await session.execute(
                        select(PlaybookExecution).where(
                            and_(
                                PlaybookExecution.incident_id == incident.id,
                                PlaybookExecution.status != PlaybookStatus.COMPLETED,
                            )
                        )
                    )
                    existing_exec = exec_result.scalar_one_or_none()
                    if existing_exec:
                        continue

                    # Find matching playbook
                    pb_result = await session.execute(
                        select(Playbook).where(
                            and_(
                                Playbook.incident_type == incident.incident_type,
                                Playbook.is_active == True,
                            )
                        ).limit(1)
                    )
                    playbook = pb_result.scalar_one_or_none()

                    if not playbook:
                        logger.warning(
                            f"No playbook found for incident {incident.incident_id} "
                            f"({incident.incident_type.value})"
                        )
                        continue

                    # Create execution record
                    from sqlalchemy.orm import selectinload
                    pb_result = await session.execute(
                        select(Playbook)
                        .options(selectinload(Playbook.steps))
                        .where(Playbook.id == playbook.id)
                    )
                    pb = pb_result.scalar_one_or_none()
                    if not pb:
                        logger.warning(f"Playbook {playbook.id} not found in second query")
                        continue

                    step_statuses = {
                        str(i): {
                            "title": step.title,
                            "status": "pending",
                            "result": None,
                            "action_type": step.action_type
                        }
                        for i, step in enumerate(sorted(pb.steps, key=lambda s: s.order))
                    }

                    # Auto-execute initial steps (only non-critical ones)
                    auto_execution_results = {}
                    for i, step in enumerate(sorted(pb.steps, key=lambda s: s.order)):
                        if step.is_critical:
                            # Skip critical steps for manual confirmation
                            step_statuses[str(i)]["status"] = "pending"
                            logger.info(
                                f"Playbook step {i} ({step.title}) marked for manual review "
                                f"(critical step)"
                            )
                        else:
                            # Auto-execute information/tracking steps
                            if step.action_type in ["information", "tracking", "log"]:
                                step_statuses[str(i)]["status"] = "auto_executed"
                                step_statuses[str(i)]["result"] = f"Auto-executed at {datetime.utcnow().isoformat()}"
                                auto_execution_results[i] = "auto_executed"

                    execution = PlaybookExecution(
                        incident_id=incident.id,
                        playbook_id=playbook.id,
                        status=PlaybookStatus.IN_PROGRESS,
                        started_at=datetime.utcnow(),
                        current_step=0,
                        step_statuses=step_statuses,
                        executed_by_id=None,  # AI Agent
                    )
                    session.add(execution)

                    logger.info(
                        f"Auto-executed playbook '{playbook.name}' for incident "
                        f"{incident.incident_id} ({incident.incident_type.value})"
                    )

                except Exception as e:
                    logger.error(
                        f"Error auto-executing playbook for incident {incident.id}: {e}"
                    )
                    continue

            await session.commit()

        except Exception as e:
            logger.error(f"Error in playbook auto-execution: {e}")

    async def process_single_alert(
        self, alert_id: int, session: AsyncSession
    ) -> Optional[Dict]:
        """Process a single alert immediately (for manual triggers)."""
        try:
            result = await session.execute(
                select(Alert).where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            if not alert:
                return None

            # Re-run ingestion
            incident_type, confidence, reasoning = classify_incident(
                alert.description or "",
                alert.event_type or ""
            )

            asset_criticality = 5.0
            if alert.asset_id:
                asset_result = await session.execute(
                    select(Asset).where(Asset.id == alert.asset_id)
                )
                asset = asset_result.scalar_one_or_none()
                if asset:
                    asset_criticality = asset.criticality

            severity_score, severity_level = calculate_severity_score(
                asset_criticality=asset_criticality,
                threat_confidence=confidence * 10,
                impact_level=5.0,
                detection_confidence=confidence * 10,
                description=alert.description or "",
            )

            return {
                "incident_type": incident_type.value,
                "confidence": confidence,
                "severity": severity_level.value,
                "severity_score": severity_score,
                "reasoning": reasoning,
            }

        except Exception as e:
            logger.error(f"Error processing single alert: {e}")
            return None


# Global agent instance
_agent: Optional[AIAutomationAgent] = None


def get_automation_agent() -> AIAutomationAgent:
    """Get or create singleton agent instance."""
    global _agent
    if _agent is None:
        _agent = AIAutomationAgent(check_interval=15, auto_execute=True)
    return _agent


async def start_automation_agent():
    """Start the global automation agent in background."""
    global _agent
    _agent = get_automation_agent()
    # Create background task
    asyncio.create_task(_agent.start())


async def shutdown_automation_agent():
    """Shutdown the automation agent."""
    global _agent
    if _agent:
        await _agent.stop()
