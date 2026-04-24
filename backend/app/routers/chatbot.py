"""
Chatbot Router — WebSocket streaming chat, voice commands, dashboard control
Completely free and offline - uses Ollama local LLM
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, Incident, IncidentStatus, SeverityLevel, Playbook
from app.chatbot import (
    get_ollama_chat,
    stream_chatbot_response,
    CommandInterpreter,
    get_dashboard_context,
    process_voice_command,
    speak,
    CHATBOT_SYSTEM,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── WebSocket Chat Endpoint ──────────────────────────────────────────────────


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time chatbot streaming.
    Supports text messages and voice commands.
    """
    await websocket.accept()

    try:
        # Send welcome message
        await websocket.send_text(
            json.dumps({
                "type": "status",
                "message": "Connected to T10 AIRPS chatbot. Type your question or say 'help' for commands.",
                "ollama_status": "checking...",
            })
        )

        # Check Ollama status
        ollama = get_ollama_chat()
        status = "ready" if ollama.available else "not_available"
        await websocket.send_text(
            json.dumps({
                "type": "status",
                "ollama_status": status,
                "message": "Ollama not running. Install from https://ollama.ai" if not ollama.available else "Ollama ready!",
            })
        )

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "").strip()
                message_type = message_data.get("type", "text")  # text, voice, command

                if not user_message:
                    continue

                logger.info(f"Chat input ({message_type}): {user_message[:100]}")

                # Get user from token (if available)
                token = message_data.get("token")
                current_user = None
                try:
                    if token:
                        from app.auth import get_current_active_user
                        from fastapi import Depends
                        # Note: Proper token validation would happen at route level
                        # For WebSocket, we'd need custom validation
                        pass
                except:
                    pass

                # Get dashboard context
                dashboard_context = ""
                try:
                    dashboard_context = await get_dashboard_context(db, current_user or User(role="analyst"))
                except:
                    pass

                # Build system prompt with context
                system_prompt = CHATBOT_SYSTEM + "\n\n" + dashboard_context

                # Stream response
                full_response = ""
                async for chunk in stream_chatbot_response(user_message, system_prompt=system_prompt):
                    full_response += chunk
                    await websocket.send_text(
                        json.dumps({
                            "type": "stream",
                            "chunk": chunk,
                        })
                    )

                # Check for action commands in response
                action = CommandInterpreter.extract_action(full_response)
                if action and CommandInterpreter.validate_action(action):
                    await websocket.send_text(
                        json.dumps({
                            "type": "action",
                            "action": action["action"],
                            "params": action["params"],
                        })
                    )

                # Send end-of-response marker
                await websocket.send_text(
                    json.dumps({
                        "type": "done",
                        "message": "Response complete",
                    })
                )

                # Optional: Speak response for hands-free
                if message_data.get("voice_response"):
                    # Get first sentence for TTS
                    first_sentence = full_response.split(".")[0] + "."
                    speak(first_sentence[:200])

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                    })
                )
            except Exception as e:
                logger.error(f"Chat processing error: {e}")
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "message": str(e),
                    })
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1000)
        except:
            pass


# ─── REST Endpoints for Chatbot ────────────────────────────────────────────────


@router.post("/chat")
async def chat_message(
    message: str,
    voice_response: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send a message to the chatbot and get a complete response.
    For streaming, use WebSocket endpoint instead.
    """
    try:
        # Get dashboard context
        dashboard_context = await get_dashboard_context(db, current_user)
        system_prompt = CHATBOT_SYSTEM + "\n\n" + dashboard_context

        # Get response
        full_response = ""
        async for chunk in stream_chatbot_response(message, system_prompt=system_prompt):
            full_response += chunk

        # Extract actions
        action = CommandInterpreter.extract_action(full_response)

        response = {
            "message": message,
            "response": full_response,
            "action": action if action and CommandInterpreter.validate_action(action) else None,
        }

        # Optional: Speak response
        if voice_response:
            first_sentence = full_response.split(".")[0] + "."
            speak(first_sentence[:200])

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbot/status")
async def chatbot_status(current_user: User = Depends(get_current_active_user)):
    """Get chatbot status and configuration."""
    ollama = get_ollama_chat()
    return {
        "status": "online",
        "model": ollama.model,
        "ollama_available": ollama.available,
        "features": [
            "natural_language_chat",
            "incident_management_commands",
            "dashboard_control",
            "voice_input_support",
            "voice_output_support",
            "playbook_suggestions",
            "threat_assessment",
        ],
        "supported_commands": [
            "create_incident",
            "update_incident",
            "close_incident",
            "get_incidents",
            "get_playbooks",
            "execute_playbook",
            "dashboard_summary",
        ],
        "installation": "https://ollama.ai",
        "cost": "FREE - Runs completely offline",
    }


@router.post("/chatbot/execute-command")
async def execute_chatbot_command(
    action: str,
    params: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Execute dashboard management commands from chatbot.
    Supports: create_incident, update_incident, close_incident, etc.
    """
    try:
        if action == "create_incident":
            # Create incident
            from app.ai_engine import classify_incident, calculate_severity_score, calculate_escalation_risk, generate_ai_recommendation
            import uuid

            title = params.get("title", "")
            description = params.get("description", "")
            incident_type, conf, _ = classify_incident(description)

            incident = Incident(
                incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
                title=title,
                description=description,
                incident_type=incident_type,
                severity=SeverityLevel(params.get("severity", "Medium")),
            )
            db.add(incident)
            await db.commit()
            return {"status": "created", "incident_id": incident.incident_id}

        elif action == "update_incident":
            # Update incident
            incident_id = params.get("incident_id")
            result = await db.execute(select(Incident).where(Incident.id == incident_id))
            incident = result.scalar_one_or_none()
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")

            if "status" in params:
                incident.status = IncidentStatus(params["status"])
            if "notes" in params:
                incident.notes = params["notes"]

            await db.commit()
            return {"status": "updated", "incident_id": incident_id}

        elif action == "close_incident":
            # Close incident
            incident_id = params.get("incident_id")
            result = await db.execute(select(Incident).where(Incident.id == incident_id))
            incident = result.scalar_one_or_none()
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found")

            incident.status = IncidentStatus.CLOSED
            await db.commit()
            return {"status": "closed", "incident_id": incident_id}

        elif action == "get_incidents":
            # Get incidents with filters
            query = select(Incident).order_by(desc(Incident.created_at))

            if params.get("status"):
                query = query.where(Incident.status == IncidentStatus(params["status"]))
            if params.get("severity"):
                query = query.where(Incident.severity == SeverityLevel(params["severity"]))

            result = await db.execute(query.limit(20))
            incidents = result.scalars().all()
            return {
                "count": len(incidents),
                "incidents": [{"id": i.id, "title": i.title, "status": i.status.value} for i in incidents]
            }

        elif action == "get_playbooks":
            # Get playbooks for incident type
            incident_type = params.get("incident_type")
            query = select(Playbook).where(Playbook.is_active == True)
            if incident_type:
                from app.models import IncidentType
                query = query.where(Playbook.incident_type == IncidentType(incident_type))

            result = await db.execute(query)
            playbooks = result.scalars().all()
            return {
                "count": len(playbooks),
                "playbooks": [{"id": p.id, "name": p.name} for p in playbooks]
            }

        elif action == "dashboard_summary":
            # Get dashboard summary
            open_result = await db.execute(select(Incident).where(Incident.status == IncidentStatus.OPEN))
            open_count = len(open_result.scalars().all())

            critical_result = await db.execute(select(Incident).where(Incident.severity == SeverityLevel.CRITICAL))
            critical_count = len(critical_result.scalars().all())

            return {
                "open_incidents": open_count,
                "critical_incidents": critical_count,
                "summary": f"{open_count} open, {critical_count} critical incidents",
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Command execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chatbot/voice-input")
async def voice_input(
    message: str = Query(..., description="Voice-to-text transcribed message"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Process voice input transcribed to text.
    Frontend can use Web Speech API to transcribe voice.
    """
    return await chat_message(message, voice_response=True, db=db, current_user=current_user)


@router.get("/chatbot/help")
async def chatbot_help():
    """Get help on chatbot commands and usage."""
    return {
        "intro": "T10 AIRPS Chatbot - Free, offline AI for incident management",
        "examples": [
            "Create a critical malware incident on web server",
            "Show me all open incidents",
            "Close incident 5",
            "What playbooks exist for ransomware?",
            "Give me a security incident summary",
            "How do I respond to a data exfiltration?",
        ],
        "voice_commands": [
            "Works with browser microphone (Web Speech API)",
            "Automatic speech recognition to text",
            "Text-to-speech voice responses",
        ],
        "installation": "Ollama - Download from https://ollama.ai",
        "setup": [
            "1. Install Ollama from https://ollama.ai",
            "2. Run: ollama serve",
            "3. In another terminal: ollama pull mistral",
            "4. Start T10 backend - chatbot will auto-detect Ollama",
        ],
        "cost": "100% FREE - No API subscriptions, runs completely offline",
    }
