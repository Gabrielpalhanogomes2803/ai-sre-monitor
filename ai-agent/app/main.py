from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.emailer import send_incident_email
from app.prometheus import collect_incident_context
from app.loki import collect_log_context
from app.ai import analyze_incident
from app.storage import save_incident, list_incidents, init_db
from app.chat import answer_incident_question

app = FastAPI(
    title="AI SRE Incident Analyzer",
    version="0.7.0"
)

CHAT_HTML = Path("/app/app/static/chat.html")


class ChatRequest(BaseModel):
    question: str


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ai-sre-agent"
    }


@app.get("/assistant")
async def assistant():
    return FileResponse(CHAT_HTML)


@app.get("/context")
async def context():
    metrics = await collect_incident_context()
    logs = await collect_log_context()

    return {
        "status": "ok",
        "metrics": metrics,
        "logs": logs
    }


@app.get("/incidents")
async def incidents(limit: int = Query(default=50, ge=1, le=200)):
    return {
        "status": "ok",
        "incidents": list_incidents(limit)
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    result = answer_incident_question(request.question)

    return {
        "status": "ok",
        "question": request.question,
        "result": result
    }


@app.post("/webhook/grafana")
async def grafana_webhook(request: Request):
    payload = await request.json()

    metrics = await collect_incident_context()
    logs = await collect_log_context()

    ai_analysis = analyze_incident(
        alert=payload,
        metrics=metrics,
        logs=logs
    )

    incident_id = save_incident(
        alert=payload,
        metrics=metrics,
        logs=logs,
        analysis=ai_analysis
    )

    send_incident_email(
        alert=payload,
        analysis=ai_analysis
    )

    incident = {
        "id": incident_id,
        "alert": payload,
        "prometheus_context": metrics,
        "loki_context": logs,
        "ai_analysis": ai_analysis
    }

    print("=== GRAFANA ALERT RECEIVED ===")
    print(incident)

    return {
        "status": "received",
        "incident": incident
    }
