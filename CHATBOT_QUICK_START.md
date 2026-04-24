# T10 AIRPS - FREE AI CHATBOT
## Quick Reference Guide

---

## 🚀 STARTUP CHECKLIST

### Prerequisites (One-Time Setup)
- [ ] Ollama downloaded from https://ollama.ai
- [ ] Ollama installed on your system
- [ ] Backend Python packages installed: `pip install -r requirements.txt`

### Before First Use
- [ ] Download a model: `ollama pull mistral`

---

## 📋 STARTUP SEQUENCE

### Terminal 1: Start Ollama Server
```bash
ollama serve
# Wait for: "Listening on 127.0.0.1:11434"
```

### Terminal 2: Start Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Wait for: "Application startup complete"
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev
# Will open browser automatically, or visit: http://localhost:5173
```

---

## 🎯 USING THE CHATBOT

### Text Input
1. Find chatbot in dashboard
2. Type your command
3. Press Enter or click Send
4. Response appears with streaming text

### Voice Input
1. Click **🎤 Voice** button
2. Speak your command clearly
3. Wait for recognition (blue indicator)
4. Command executes automatically

### Voice Output
1. Click **🔊 Off** to toggle **On**
2. Chatbot will speak responses
3. Great for hands-free operation

---

## 💬 EXAMPLE COMMANDS

### Create Incident
```
"Create critical malware incident on web server"
"New high severity ransomware incident"
"Add critical incident for data exfiltration"
```

### Update Incident
```
"Close incident 5"
"Update incident 3 to investigating"
"Change incident 2 status to contained"
```

### Get Information
```
"Show me all open incidents"
"What critical incidents are there?"
"List high severity threats"
"Dashboard summary"
```

### Playbook Management
```
"What playbooks for malware?"
"Execute ransomware playbook on incident 3"
"Show available incident responses"
```

### General Questions
```
"What incident types do you support?"
"How do I respond to a phishing attack?"
"What's the incident severity scale?"
```

---

## 🔧 TROUBLESHOOTING

### "Ollama not running"
```bash
# Make sure Terminal 1 is running
ollama serve
# And model is downloaded
ollama pull mistral
```

### "Cannot connect to backend"
```bash
# Make sure Terminal 2 is running and shows "startup complete"
cd backend
python -m uvicorn main:app --port 8000
```

### "Voice not working"
- Check microphone permissions in browser
- Try Chrome or Edge (Safari needs HTTPS)
- Ensure microphone is not muted
- Check volume settings

### "Slow responses"
- Try faster model: `ollama pull neural-chat`
- Close other applications
- Check CPU/RAM usage
- Restart Ollama

---

## 📊 SYSTEM REQUIREMENTS

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4GB | 8GB+ |
| Disk | 6GB | 10GB+ |
| CPU | 2 cores | 4+ cores |
| Model Size | 1.3GB | 4GB (Mistral) |

---

## 🎓 FEATURES

✅ Text & voice input  
✅ Real-time chat streaming  
✅ Voice output (text-to-speech)  
✅ Incident creation via chat  
✅ Dashboard control via voice  
✅ Playbook recommendations  
✅ Security best practices  
✅ Natural language understanding  
✅ 100% offline operation  
✅ Zero API costs  

---

## 📞 HELP & DOCS

| Resource | Location |
|----------|----------|
| Setup Guide | `CHATBOT_SETUP.md` |
| Full Details | `CHATBOT_COMPLETE.md` |
| API Docs | http://localhost:8000/api/docs |
| Test Script | `python backend/test_chatbot.py` |

---

## 💰 COST

**$0/month** - Completely free!

- Ollama: Free & open-source
- AI Models: Free & open-source
- No API subscriptions
- Runs entirely on your computer
- Offline operation

---

## ⚡ QUICK COMMANDS

```bash
# Download Ollama
# Go to: https://ollama.ai

# Start Ollama
ollama serve

# Get AI model
ollama pull mistral

# Install Python packages
pip install -r requirements.txt

# Start backend
python -m uvicorn main:app --port 8000

# Start frontend
npm run dev

# Test chatbot
python test_chatbot.py
```

---

## 🎤 VOICE CONTROL TIPS

1. **Speak naturally** - Use conversational phrases
2. **Be clear** - Pronounce words clearly
3. **Wait for confirmation** - Listen for recognition
4. **Use quick commands** - Click buttons for speed
5. **Enable voice output** - Hear responses aloud

---

## 📝 INCIDENT MANAGEMENT WORKFLOW

```
1. User: "Create critical incident"
2. Chatbot: Creates incident, returns ID
3. User: "What's recommended?"
4. Chatbot: Suggests playbook
5. User: "Execute it"
6. Chatbot: Runs playbook, updates incident
7. User: "Close this one"
8. Chatbot: Marks as closed
```

---

## 🔒 SECURITY & PRIVACY

✅ 100% offline - No data sent externally  
✅ Private - Runs on your computer  
✅ Secure - Uses existing JWT tokens  
✅ Audited - All actions logged  
✅ Open-source - Code is transparent  

---

## 🆘 EMERGENCY QUICK SUPPORT

**Backend won't start:**
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```

**Ollama disconnected:**
```bash
# Kill and restart
ollama serve
```

**Need to reset:**
- Close all terminals
- Restart Ollama: `ollama serve`
- Restart backend
- Restart frontend

---

## 📊 STATUS INDICATORS

| Indicator | Meaning |
|-----------|---------|
| 🟢 Green dot | Connected & ready |
| 🟡 Yellow dot | Connecting... |
| 🔴 Red dot | Disconnected |
| 🎤 Voice button | Click to speak |
| 🔊 Volume button | Toggle voice response |
| ❓ Help button | Show help |

---

## 💡 TIPS & TRICKS

1. **Quick Commands** - Use button shortcuts
2. **Voice Notes** - Hands-free incident logging
3. **Dashboard View** - Chat while monitoring
4. **Bulk Operations** - "Close all open incidents"
5. **Scripting** - Automate via REST API

---

**Ready to use! Download Ollama and follow the startup sequence above.**

**Questions? Check CHATBOT_SETUP.md for detailed guide.**
