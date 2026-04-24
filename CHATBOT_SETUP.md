# Free AI Chatbot with Hands-Free Dashboard Control

## Overview

T10 AIRPS now includes a **completely free, offline AI chatbot** with voice control for hands-free incident management. No API costs, no external dependencies, runs 100% on your computer.

**Cost: $0** ✓

## What You Get

### 1. **Natural Language Chatbot**
- Ask questions about security incidents
- Get recommendations automatically
- Manage incidents via conversation
- Voice input AND voice output

### 2. **Hands-Free Dashboard Control**
- Create incidents by voice: "Create a critical malware incident"
- Update status: "Close incident 5"
- Get summaries: "Show me dashboard summary"
- No clicking required

### 3. **Voice Interface**
- 🎤 **Voice Input** — Speak your commands (Web Speech API)
- 🔊 **Voice Output** — Hear chatbot responses (Text-to-Speech)
- 100% browser-based, no setup needed

### 4. **Integrated Dashboard Commands**
```
create_incident          - Create new incident
update_incident          - Update incident status
close_incident          - Close an incident
get_incidents           - List incidents (with filters)
get_playbooks           - Find playbooks
execute_playbook        - Run a playbook
dashboard_summary       - Get overview
```

## Installation

### Step 1: Install Ollama (Local LLM Server)

Ollama is a **free, open-source** tool that runs large language models locally on your computer.

**Download from:** https://ollama.ai

**Installation (all platforms):**
- macOS: `brew install ollama`
- Windows: Download installer from https://ollama.ai/download
- Linux: `curl https://ollama.ai/install.sh | sh`

### Step 2: Download a Model

```bash
# Start Ollama server
ollama serve

# In another terminal, pull a model
ollama pull mistral
# or: ollama pull llama2 (alternative, slower)
# or: ollama pull neural-chat (smaller, faster)
```

**Model options:**
| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| mistral | 4GB | Fast ✓ | Excellent |
| neural-chat | 1.3GB | Very Fast | Good |
| llama2 | 3.8GB | Medium | Excellent |

### Step 3: Update Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
# New packages added:
# - ollama==0.1.32 (Ollama client)
# - pyttsx3==2.90 (Text-to-speech)
# - SpeechRecognition==3.10.0 (Speech-to-text)
```

### Step 4: Add Chatbot to Frontend

The chatbot component is already created at:
```
frontend/src/components/Chatbot.vue
```

Import and use in your dashboard:
```vue
<template>
  <div>
    <Chatbot />
  </div>
</template>

<script setup>
import Chatbot from '@/components/Chatbot.vue'
</script>
```

## Running the System

### Terminal 1: Start Ollama Server
```bash
ollama serve
# Output: Listening on 127.0.0.1:11434
```

### Terminal 2: Start Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev
# Open: http://localhost:5173
```

## Using the Chatbot

### Text Commands

Simply type in the chatbot:
```
Create a critical ransomware incident on finance server
Close incident 3
Show me all open incidents
What playbooks exist for malware?
Give me a dashboard summary
```

### Voice Commands

1. Click the **🎤 Voice** button
2. Speak your command
3. Browser transcribes automatically
4. Chatbot responds

### Voice Responses

1. Click the **🔊 On** button to enable
2. Chatbot will speak responses aloud
3. Great for hands-free operation

### Quick Commands

Use the quick command buttons below the text input:
- "Show open incidents"
- "Create incident"
- "Close incident"
- "Dashboard summary"

## Example Workflows

### Workflow 1: Create & Manage Incident (Hands-Free)

```
User: "Create a critical phishing incident - CEO impersonation email"
Chatbot: Creates incident, returns incident ID

User: "What's the recommended playbook?"
Chatbot: Suggests Phishing Attack Response

User: "Execute that playbook"
Chatbot: Executes playbook, tracks steps

User: "Close the incident"
Chatbot: Marks incident as closed
```

### Workflow 2: Voice-Only Operation

```
User: (Voice) "Show me critical incidents"
System: (Voice) "You have 2 critical incidents: ransomware on database, malware on webserver"

User: (Voice) "Create medium malware incident on workstation"
System: (Voice) "Created incident INC-A1B2C3D4"

User: (Voice) "Dashboard summary"
System: (Voice) "3 open incidents, 2 critical, 1 medium. Recent activity on finance servers..."
```

### Workflow 3: Dashboard Automation via Chat

```
User: "List all high and critical incidents from last 24 hours"
Chatbot: Returns filtered incidents

User: "Execute malware playbook on all of them"
Chatbot: Executes on each incident

User: "Update all to investigating status"
Chatbot: Updates all incidents

User: "Send me a report"
Chatbot: Generates summary
```

## Chatbot Capabilities

### Understanding Natural Language
The chatbot understands various ways to phrase commands:

✓ "Create incident for malware"
✓ "I need to create a malware incident"
✓ "New incident: malware detected"
✓ "Add incident - type: malware"

### Dashboard Commands

**Create Incident**
```
"Create a [severity] [type] incident on [asset/system]"
Example: "Create critical ransomware incident on database"
```

**Update Incident**
```
"Update incident [ID] to [status]"
Example: "Update incident 5 to investigating"
```

**Get Incidents**
```
"Show me [status] [severity] incidents"
Example: "Show me all open critical incidents"
```

**Get Playbooks**
```
"What playbooks for [incident_type]?"
Example: "What playbooks for data exfiltration?"
```

**Dashboard Summary**
```
"Give me a dashboard summary"
"What's the current threat status?"
"How many incidents are open?"
```

## Security Features

- **Offline Processing** — No data sent to external APIs
- **Local LLM** — Model runs on your computer
- **Authentication** — Chatbot respects JWT tokens
- **Role-Based Access** — Commands respect user roles
- **Audit Trail** — All incidents logged

## Performance

| Operation | Time |
|-----------|------|
| First startup | ~5 sec (model initialization) |
| Chat response | 1-3 seconds |
| Command execution | < 500ms |
| Voice input | < 2 sec recognition |
| Voice output | Depends on response length |

## Troubleshooting

### "Ollama not running"
**Solution:**
```bash
# Make sure Ollama server is started in separate terminal
ollama serve
```

### "Model not found"
**Solution:**
```bash
ollama pull mistral
# Wait for download (4GB)
```

### Voice input not working
**Solution:**
- Check browser microphone permissions
- Chrome/Edge works best
- Safari requires HTTPS (use localhost with port 443 for testing)

### Chatbot responses are slow
**Solution:**
- Use faster model: `ollama pull neural-chat`
- Allocate more RAM to Ollama
- Reduce other background processes

### TTS (Voice Output) not working
**Solution:**
- Windows: Usually works out of box
- macOS: May require `brew install espeak`
- Linux: `sudo apt-get install espeak`

## Customization

### Change Default Model

In `backend/app/chatbot.py`:
```python
def get_ollama_chat(model: str = "neural-chat") -> OllamaChat:  # Change "mistral"
```

### Adjust Voice Speed

In `backend/app/chatbot.py`:
```python
_tts_engine.setProperty('rate', 150)  # Change speed (80-300)
_tts_engine.setProperty('volume', 0.9)  # Change volume (0-1)
```

### Modify System Prompt

Edit `CHATBOT_SYSTEM` in `backend/app/chatbot.py` to customize behavior.

## API Endpoints

### WebSocket Chat (Real-time)
```
ws://localhost:8000/api/chatbot/ws/chat

Message format:
{
  "message": "Create critical incident",
  "type": "text",
  "voice_response": false,
  "token": "jwt_token_here"
}
```

### REST Chat Endpoint
```
POST /api/chatbot/chat
Parameters:
  - message: "Your message"
  - voice_response: true/false
  - token: JWT token

Response:
{
  "message": "...",
  "response": "...",
  "action": {...}
}
```

### Command Execution
```
POST /api/chatbot/execute-command
Body:
{
  "action": "create_incident",
  "params": {
    "title": "...",
    "description": "..."
  }
}
```

### Chatbot Status
```
GET /api/chatbot/chatbot/status

Response:
{
  "status": "online",
  "model": "mistral",
  "ollama_available": true,
  "features": [...],
  "cost": "FREE - 100% offline"
}
```

### Help
```
GET /api/chatbot/chatbot/help

Returns:
- Example commands
- Voice command instructions
- Installation links
- Supported actions
```

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| Ollama | FREE | Open-source |
| Model (Mistral) | FREE | Open-source 4GB |
| Backend additions | FREE | pyttsx3, SpeechRecognition |
| Frontend component | FREE | Vue.js component |
| Voice API | FREE | Browser Web Speech API |
| TTS | FREE | OS native or pyttsx3 |
| **TOTAL** | **$0** | **No API subscriptions** |

## Comparison with Paid Solutions

| Feature | T10 Chatbot | Claude API | OpenAI GPT-4 |
|---------|------------|-----------|--------------|
| Cost | $0 | $3-15/1M tokens | $0.01-0.06/1K tokens |
| Privacy | 100% offline | Uploaded to API | Uploaded to API |
| Latency | ~2 sec | ~2 sec | ~2 sec |
| Customization | Full | Limited | Limited |
| Voice I/O | Yes | No | No |
| Dashboard control | Yes | No | No |
| Hallucinations | Possible | Less likely | Less likely |
| Model size | 4GB RAM | - | - |
| Setup time | ~15 min | ~5 min | ~5 min |

## Limitations

- Model size (~4GB) requires adequate disk space
- Response quality depends on model size
- Offline = no real-time threat intelligence
- Hallucinations possible (AI model behavior)
- Not as capable as cloud LLMs for complex reasoning

## Future Enhancements

- [ ] Multi-model support (switch at runtime)
- [ ] Fine-tuning on security incident data
- [ ] Custom knowledge base integration
- [ ] Sentiment analysis for security alerts
- [ ] Automated incident response scripts
- [ ] Integration with external threat feeds
- [ ] Multi-language support

## References

- **Ollama:** https://ollama.ai
- **Mistral Model:** https://mistral.ai
- **Web Speech API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
- **pyttsx3:** https://pyttsx3.readthedocs.io
- **SpeechRecognition:** https://pypi.org/project/SpeechRecognition/

---

## Quick Start (TL;DR)

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Start Ollama in terminal
ollama serve

# 3. In another terminal, get a model
ollama pull mistral

# 4. Install backend packages
cd backend && pip install -r requirements.txt

# 5. Start backend
python -m uvicorn main:app --port 8000

# 6. Start frontend
cd frontend && npm run dev

# 7. Open http://localhost:5173
# 8. Click chatbot 🤖
# 9. Type or click 🎤 for voice!
```

**That's it! 100% free, zero API costs, hands-free operation. 🚀**
