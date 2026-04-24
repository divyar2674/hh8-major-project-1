"""
Free AI Chatbot Service — Uses Ollama (local open-source LLM)
No API costs, completely offline, hands-free dashboard control
Supports voice input/output and incident management commands
"""
import json
import logging
import asyncio
from typing import AsyncIterator, Optional
import pyttsx3
from app.models import Incident, IncidentStatus, SeverityLevel

logger = logging.getLogger(__name__)

# ─── Text-to-Speech Engine ────────────────────────────────────────────────────

_tts_engine = None


def get_tts_engine():
    """Get or initialize text-to-speech engine."""
    global _tts_engine
    if _tts_engine is None:
        try:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty('rate', 150)  # Speech rate
            _tts_engine.setProperty('volume', 0.9)  # Volume (0-1)
        except Exception as e:
            logger.warning(f"TTS initialization warning: {e}")
            _tts_engine = None
    return _tts_engine


def speak(text: str):
    """Convert text to speech (non-blocking)."""
    try:
        engine = get_tts_engine()
        if engine:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        logger.debug(f"TTS error: {e}")


# ─── Chatbot System Prompts ────────────────────────────────────────────────────

CHATBOT_SYSTEM = """You are T10 AIRPS - an intelligent security operations assistant.
You help SOC analysts manage security incidents, investigate threats, and respond to attacks.

Key capabilities:
1. Answer security questions about incident types, severity, and response procedures
2. Interpret user commands to manage incidents (create, update, close, assign)
3. Provide incident summaries and recommendations
4. Suggest response playbooks for security threats
5. Explain security concepts and best practices

Be concise, professional, and security-focused. Always prioritize incident containment and response.
When user wants to perform actions (create incident, update status), clearly state the action in JSON format:
{"action": "action_name", "params": {...}}

Supported actions:
- create_incident: {title, description, incident_type, severity}
- update_incident: {incident_id, status, notes}
- close_incident: {incident_id}
- assign_incident: {incident_id, analyst}
- get_incidents: {status, severity, search_term}
- get_playbooks: {incident_type}
- execute_playbook: {incident_id, playbook_id}
- dashboard_summary: {}

Examples of user commands you should interpret:
- "Create a critical malware incident on the database server" → create_incident action
- "Close incident 5" → close_incident action
- "Show me all open incidents" → get_incidents action
- "What playbooks exist for ransomware?" → get_playbooks action
- "Give me a dashboard summary" → dashboard_summary action
"""

CHATBOT_CONTEXT = """Current system info:
- Active incidents: {incident_count}
- Critical threats: {critical_count}
- Your current role: {user_role}
- Time: {timestamp}

You can also help with:
- Security best practices
- Incident response strategies
- Threat assessment guidance
- Playbook recommendations
"""


# ─── Ollama Integration (Free Local LLM) ───────────────────────────────────────

class OllamaChat:
    """Wrapper for Ollama local LLM."""

    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama chat client.
        Download models with: ollama pull mistral
        """
        self.model = model
        self.base_url = base_url
        self.available = False
        self._check_availability()

    def _check_availability(self):
        """Check if Ollama server is running."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self.available = response.status_code == 200
            if self.available:
                logger.info(f"Ollama available - Using model: {self.model}")
            else:
                logger.warning("Ollama not available - Install and run: ollama serve")
        except Exception as e:
            logger.warning(f"Ollama unavailable: {e}")
            logger.info("Install Ollama from https://ollama.ai - no API costs, runs locally!")

    async def chat(self, message: str, system: str = CHATBOT_SYSTEM) -> AsyncIterator[str]:
        """Stream chat response from Ollama."""
        if not self.available:
            yield "ERROR: Ollama not running. Install from https://ollama.ai and run 'ollama serve'"
            return

        try:
            import httpx
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": message},
                        ],
                        "stream": True,
                        "temperature": 0.7,
                    },
                ) as response:
                    if response.status_code != 200:
                        yield f"ERROR: Ollama returned {response.status_code}"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            yield f"ERROR: {str(e)}"


# ─── Command Interpreter ──────────────────────────────────────────────────────

class CommandInterpreter:
    """Extract and validate action commands from chatbot responses."""

    @staticmethod
    def extract_action(response: str) -> Optional[dict]:
        """Extract JSON action from chatbot response."""
        try:
            # Look for JSON action block
            import re
            match = re.search(r'\{"action".*?\}', response, re.DOTALL)
            if match:
                action_str = match.group(0)
                return json.loads(action_str)
        except Exception as e:
            logger.debug(f"Action extraction error: {e}")
        return None

    @staticmethod
    def validate_action(action: dict) -> bool:
        """Validate action format."""
        required = {"action", "params"}
        return isinstance(action, dict) and required.issubset(action.keys())


# ─── Voice Command Support ────────────────────────────────────────────────────

async def process_voice_command(audio_file_path: Optional[str] = None) -> str:
    """
    Convert voice to text using SpeechRecognition.
    Requires: pip install SpeechRecognition pydub
    """
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        if audio_file_path:
            # Load from file
            with sr.AudioFile(audio_file_path) as source:
                audio = recognizer.record(source)
        else:
            # Record from microphone
            with sr.Microphone() as source:
                logger.info("Listening...")
                audio = recognizer.listen(source, timeout=10)

        # Recognize speech
        text = recognizer.recognize_google(audio)
        logger.info(f"Recognized: {text}")
        return text

    except sr.UnknownValueError:
        return "Sorry, I didn't understand that. Please try again."
    except sr.RequestError:
        return "Speech recognition error. Using text input instead."
    except Exception as e:
        logger.warning(f"Voice processing error: {e}")
        return None


# ─── Chatbot Instance ──────────────────────────────────────────────────────────

_ollama_chat = None


def get_ollama_chat(model: str = "mistral") -> OllamaChat:
    """Get or create Ollama chat instance."""
    global _ollama_chat
    if _ollama_chat is None:
        _ollama_chat = OllamaChat(model=model)
    return _ollama_chat


# ─── Dashboard Context Generator ──────────────────────────────────────────────

async def get_dashboard_context(db_session, current_user) -> str:
    """Get current dashboard metrics for chatbot context."""
    from sqlalchemy import select

    try:
        # Count incidents by status
        result = await db_session.execute(
            select(Incident).where(Incident.status == IncidentStatus.OPEN)
        )
        open_count = len(result.scalars().all())

        result = await db_session.execute(
            select(Incident).where(Incident.severity == SeverityLevel.CRITICAL)
        )
        critical_count = len(result.scalars().all())

        return CHATBOT_CONTEXT.format(
            incident_count=open_count,
            critical_count=critical_count,
            user_role=current_user.role.value,
            timestamp=asyncio.get_event_loop().time()
        )
    except Exception as e:
        logger.debug(f"Context generation error: {e}")
        return ""


# ─── Streaming Chat Response ──────────────────────────────────────────────────

async def stream_chatbot_response(
    user_message: str,
    system_prompt: str = CHATBOT_SYSTEM
) -> AsyncIterator[str]:
    """Stream chatbot response with real-time chunks."""
    ollama = get_ollama_chat()

    async for chunk in ollama.chat(user_message, system=system_prompt):
        yield chunk
        # Optional: speak while streaming for hands-free experience
        # if chunk:
        #     speak(chunk[:50])  # Speak small chunks
