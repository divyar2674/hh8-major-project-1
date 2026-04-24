# T10 - AI Incident Response & Automated Playbook System

## Overview
An AI-driven Incident Response platform that automatically classifies security incidents, assigns severity scores, recommends response actions, and executes predefined automated playbooks.

## Architecture
- **Frontend**: React.js (Vite) with modern UI
- **Backend**: Python FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **AI Engine**: Rule-based + ML classification

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Modules
- Incident Intake & Classification Engine
- Severity & Risk Scoring Engine  
- Automated Playbook Engine
- Incident Lifecycle Management
- AI Recommendation Layer
- Real-time Response Dashboard
