"""
T10 – AI Incident Response & Automated Playbook System
FastAPI Backend Entry Point
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import init_db
from app.routers import auth, incidents, playbooks, dashboard, monitor, automation, chatbot
from app.seed import seed
from app.automation_agent import start_automation_agent, shutdown_automation_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed()

    # Start AI Automation Agent
    try:
        await start_automation_agent()
        print("[SYSTEM] AI Automation Agent started successfully")
    except Exception as e:
        print(f"[WARNING] Failed to start automation agent: {e}")

    yield

    # Shutdown AI Automation Agent
    try:
        await shutdown_automation_agent()
        print("[SYSTEM] AI Automation Agent shut down")
    except Exception as e:
        print(f"[WARNING] Error shutting down agent: {e}")


app = FastAPI(
    title="T10 – AI Incident Response & Automated Playbook System",
    description="AI-driven platform for incident classification, severity scoring, and automated playbook execution.",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/auth",        tags=["Authentication"])
app.include_router(incidents.router,  prefix="/api",            tags=["Incidents & Alerts"])
app.include_router(playbooks.router,  prefix="/api/playbooks",  tags=["Playbooks"])
app.include_router(dashboard.router,  prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(monitor.router,    prefix="/api/monitor",    tags=["Monitor"])
app.include_router(automation.router,  prefix="/api/automation", tags=["AI Automation"])
app.include_router(chatbot.router,    prefix="/api/chatbot",    tags=["Chatbot"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "operational", "system": "T10 AIRPS", "version": "3.0.0"}


@app.get("/api/health", tags=["Health"])
async def health():
    return JSONResponse({"status": "healthy", "service": "T10-AIRPS-Backend"})
