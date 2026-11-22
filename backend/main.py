import sys
import os

# Allow imports from the backend/ directory itself
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents.coordinator_agent import CoordinatorAgent
from data.ambulances import AMBULANCES
from data.hospitals import HOSPITALS
from models import Emergency

logger = logging.getLogger("golden_hour")

app = FastAPI(
    title="Golden Hour Agent Orchestrator",
    docs_url=None,      # disable Swagger UI in production
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# Only accept requests from localhost (guards against DNS-rebinding)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver"],  # testserver = pytest TestClient
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Security response headers on every reply
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["Cache-Control"]          = "no-store"
    return response


# ---------------------------------------------------------------------------
# Global exception handler — never leak stack traces to the client
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ---------------------------------------------------------------------------
# SSE subscriber registry — capped to prevent resource exhaustion
# ---------------------------------------------------------------------------
_MAX_SUBSCRIBERS = 10
_subscribers: list[asyncio.Queue] = []

coordinator = CoordinatorAgent()


# ---------------------------------------------------------------------------
# Background simulation loop
# ---------------------------------------------------------------------------
async def simulation_loop():
    """Generates a random emergency every 5 seconds and dispatches it."""
    while True:
        await asyncio.sleep(5)

        emergency = Emergency(
            id=str(uuid.uuid4())[:8],
            patient_lat=round(random.uniform(12.92, 13.02), 6),
            patient_lon=round(random.uniform(77.55, 77.65), 6),
            severity=random.choice(["critical", "serious", "stable"]),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        plan = coordinator.dispatch(emergency)
        if plan is None:
            continue

        # Mark ambulance as dispatched
        for amb in AMBULANCES:
            if amb.id == plan.ambulance.id:
                amb.status = "dispatched"
                asyncio.create_task(_reset_ambulance(amb.id, 30))
                break

        # Decrement ICU bed count
        for hosp in HOSPITALS:
            if hosp.id == plan.hospital.id and hosp.icu_beds_available > 0:
                hosp.icu_beds_available -= 1
                break

        payload = "data: " + plan.model_dump_json() + "\n\n"

        for q in list(_subscribers):
            await q.put(payload)


async def _reset_ambulance(ambulance_id: str, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    for amb in AMBULANCES:
        if amb.id == ambulance_id:
            amb.status = "available"
            break


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stream")
async def stream():
    """SSE endpoint — emits a DispatchPlan JSON event every ~5 seconds.
    Rejects connections when the subscriber cap is reached.
    """
    if len(_subscribers) >= _MAX_SUBSCRIBERS:
        raise HTTPException(status_code=503, detail="Too many concurrent stream connections")

    queue: asyncio.Queue = asyncio.Queue(maxsize=20)  # bounded queue per client
    _subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            if queue in _subscribers:
                _subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/status")
def status():
    """Returns current ambulance and hospital states for dashboard polling."""
    return {
        "ambulances": [a.model_dump() for a in AMBULANCES],
        "hospitals":  [h.model_dump() for h in HOSPITALS],
    }


# ---------------------------------------------------------------------------
# Manual dispatch request model
# ---------------------------------------------------------------------------
class ManualDispatchRequest(BaseModel):
    lat: float      = Field(ge=-90.0,  le=90.0,  description="Patient latitude")
    lon: float      = Field(ge=-180.0, le=180.0, description="Patient longitude")
    severity: str   = Field(pattern="^(critical|serious|stable)$")


@app.post("/dispatch")
async def manual_dispatch(body: ManualDispatchRequest):
    """Accept a real patient location and return an immediate DispatchPlan.
    The result is also fanned out to all SSE subscribers so the dashboard
    shows it live alongside the auto-generated events.
    """
    emergency = Emergency(
        id="MANUAL-" + str(uuid.uuid4())[:6].upper(),
        patient_lat=body.lat,
        patient_lon=body.lon,
        severity=body.severity,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    plan = coordinator.dispatch(emergency)
    if plan is None:
        raise HTTPException(status_code=503, detail="No available ambulance or hospital")

    # Mark ambulance as dispatched
    for amb in AMBULANCES:
        if amb.id == plan.ambulance.id:
            amb.status = "dispatched"
            asyncio.create_task(_reset_ambulance(amb.id, 30))
            break

    # Decrement ICU bed
    for hosp in HOSPITALS:
        if hosp.id == plan.hospital.id and hosp.icu_beds_available > 0:
            hosp.icu_beds_available -= 1
            break

    # Fan-out to SSE subscribers so the dashboard shows it live
    payload = "data: " + plan.model_dump_json() + "\n\n"
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass  # slow client — skip rather than block

    return plan
