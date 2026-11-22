# Golden Hour Agent Orchestrator — Hackathon Plan

## Overview

**Problem:** In a medical emergency, every second counts. Dispatchers must simultaneously find the nearest available ambulance AND the nearest hospital with an open ICU bed. Manual coordination wastes the critical "golden hour."

**Solution:** A multi-agent AI orchestration system where three specialised agents collaborate in real-time to automatically dispatch the optimal ambulance-to-hospital route for each incoming emergency — with zero human bottleneck.

**Demo Format:** Auto-running simulation — mock emergencies fire automatically every 5 seconds. A live React dashboard shows each agent working, their decisions, and the final dispatch result accumulating in a live feed. Dispatchers can also trigger a manual emergency from any location using a landmark dropdown or GPS geolocation.

**Constraints:**
- Runs 100% locally (no cloud, no API keys)
- All data is in-memory mock data
- Python FastAPI backend + React (Vite) frontend
- Agents are deterministic Python classes (no LLM calls)
- Must be buildable in ~1 hour

---

## System Architecture

### High-Level Components

```
[ React Dashboard :5173 ]
        │
        │  SSE GET /stream          (live simulation feed)
        │  GET /status              (ambulance + hospital state, polled every 3s)
        │  POST /dispatch           (manual patient location input)
        ▼
[ FastAPI Backend :8000 ]
        │  TrustedHostMiddleware    (localhost only)
        │  CORSMiddleware           (port 5173 only, GET+POST)
        │  Security headers         (nosniff, DENY, no-store)
        │  Global exception handler (no stack trace leakage)
        │
        └── CoordinatorAgent
                ├── DispatcherAgent  →  AMBULANCES[]  (10 units, Bangalore)
                └── HospitalAgent   →  HOSPITALS[]   (6 hospitals, Bangalore)
```

### Agent Responsibilities

| Agent | Role | Input | Output |
|---|---|---|---|
| **Dispatcher Agent** | Finds the nearest available ambulance | Patient lat/lon | Closest available `Ambulance` |
| **Hospital Agent** | Finds the nearest hospital with open ICU beds; 20% distance bonus for trauma hospitals on critical emergencies | Patient lat/lon + severity | Best matching `Hospital` |
| **Coordinator Agent** | Orchestrates both agents, computes ETA, assembles full `DispatchPlan` with structured reasoning string | `Emergency` model | `DispatchPlan` |

### Data Flow — Simulation (auto, every 5 s)

```
1. simulation_loop() fires a random Emergency (Bangalore bounds, random severity)
2. CoordinatorAgent.dispatch(emergency) called
3.   → DispatcherAgent.find_nearest_ambulance(lat, lon)
4.   → HospitalAgent.find_nearest_hospital(lat, lon, severity)
5. DispatchPlan assembled (ETA, distances, reasoning string)
6. Ambulance status → "dispatched"; ICU bed count decremented
7. DispatchPlan JSON fanned out to all SSE subscriber queues
8. Ambulance auto-resets to "available" after 30 s
```

### Data Flow — Manual Dispatch (on demand)

```
1. User selects landmark OR clicks "📍 My Location" (browser geolocation)
2. Frontend POSTs { lat, lon, severity } to POST /dispatch
3. Backend validates (WGS-84 bounds, severity enum)
4. CoordinatorAgent.dispatch() runs — same pipeline as simulation
5. DispatchPlan returned immediately in HTTP response
6. Plan also fanned out to SSE subscribers (appears in live feed)
```

### Pydantic Data Models

| Model | Fields |
|---|---|
| `Ambulance` | id, name, lat, lon, status (`available` \| `dispatched` \| `en_route`) |
| `Hospital` | id, name, lat, lon, icu_beds_available, specialties |
| `Emergency` | id, patient_lat, patient_lon, severity (`critical` \| `serious` \| `stable`), timestamp |
| `DispatchPlan` | emergency_id, ambulance, hospital, distance_to_patient_km, distance_to_hospital_km, estimated_eta_min, reasoning, severity |

All string enum fields use `Literal` types — invalid values are rejected at parse time with HTTP 422.

---

## Project Structure

```
golden-hour-agent-orchestrator/
│
├── backend/
│   ├── main.py                    # FastAPI app, middleware, SSE, simulation, POST /dispatch
│   ├── models.py                  # Pydantic models with Field bounds + Literal enums
│   ├── requirements.txt           # fastapi, uvicorn, pydantic, pytest, httpx
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── dispatcher_agent.py    # DispatcherAgent — nearest available ambulance
│   │   ├── hospital_agent.py      # HospitalAgent — nearest ICU hospital + trauma bonus
│   │   ├── coordinator_agent.py   # CoordinatorAgent — orchestrates both, builds DispatchPlan
│   │   └── utils.py               # haversine(lat1, lon1, lat2, lon2) → km
│   ├── data/
│   │   ├── ambulances.py          # 10 mock ambulances (Bangalore, BLR-01 → BLR-10)
│   │   └── hospitals.py           # 6 mock hospitals (Manipal, Fortis, St. John's, Apollo, Narayana, Victoria)
│   └── tests/
│       └── test_all.py            # 31 pytest tests (utils, models, agents, API endpoints)
│
├── frontend/
│   ├── index.html
│   ├── package.json               # React 19, Vite 8, Vitest, RTL
│   ├── vite.config.js             # jsdom test environment
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                # EventSource + /status polling + state management
│       ├── components/
│       │   ├── LiveFeed.jsx       # Scrolling dispatch feed, severity colour coding
│       │   ├── StatusGrid.jsx     # Ambulance + hospital status cards
│       │   ├── AgentTrace.jsx     # 3-step reasoning: Dispatcher → Hospital → Coordinator
│       │   └── ManualDispatch.jsx # Landmark dropdown + geolocation + POST /dispatch
│       ├── styles/
│       │   └── app.css            # Dark theme (#0d1117), CSS grid, severity colours
│       └── __tests__/
│           ├── setup.js           # @testing-library/jest-dom setup
│           └── ManualDispatch.test.jsx  # 21 Vitest + RTL tests
│
├── GoldenHour-Hackathon.pptx      # 7-slide pitch deck
├── README.md
├── start.md                       # Quick-start: 2 commands + URL
└── golden-hour-plan.md            # This file
```

---

## Sub-Tasks

---

### Sub-Task 0 — Git Repository Initialization

**Status:** ✅ Done (`cf900a2`)

**Outcomes delivered:**
- `git init`, `.gitignore` (Python + Node), initial commit, remote pushed to GitHub

---

### Sub-Task 1 — Backend Scaffolding + Mock Data

**Status:** ✅ Done (`86d4d28`)

**Outcomes delivered:**
- `backend/` with `requirements.txt`, `main.py`, `models.py`
- 10 ambulances across Bangalore (BLR-01 → BLR-10)
- 6 hospitals with ICU beds and specialties
- `GET /health` → `{"status":"ok"}`
- CORS for port 5173

---

### Sub-Task 2 — Agent Classes

**Status:** ✅ Done (`9df2cef`)

**Outcomes delivered:**
- `DispatcherAgent.find_nearest_ambulance(lat, lon)` — Haversine, filters available
- `HospitalAgent.find_nearest_hospital(lat, lon, severity)` — ICU filter, 20% trauma bonus for critical
- `CoordinatorAgent.dispatch(emergency)` — orchestrates both, ETA = total_distance / 60 km/h, structured reasoning string
- `utils.haversine()` shared utility

---

### Sub-Task 3 — Simulation Engine + SSE Endpoint

**Status:** ✅ Done (`33a8163`)

**Outcomes delivered:**
- `asyncio` background loop — random `Emergency` every 5 s (Bangalore bounds)
- Per-client `asyncio.Queue` fan-out (bounded, maxsize=20)
- `GET /stream` — `StreamingResponse` with `text/event-stream`
- Ambulance status flip: `dispatched` → `available` after 30 s
- ICU bed count decremented on dispatch
- `GET /status` — current fleet + hospital state

---

### Sub-Task 4 — React Frontend

**Status:** ✅ Done (`8e3b530`)

**Outcomes delivered:**
- Vite + React 19, `localhost:5173`
- `EventSource` to `/stream` — events prepended to list (capped at 50)
- `/status` polled every 3 s
- `LiveFeed` — severity-coloured left border + badge
- `StatusGrid` — 10 ambulance cards (green/red) + 6 hospital ICU counts
- `AgentTrace` — parses `[Dispatcher]`, `[Hospital]`, `[Coordinator]` tags into 3-step trace
- Dark theme (`#0d1117`), 2-column CSS grid

---

### Sub-Task 5 — Integration + README

**Status:** ✅ Done (`a055908`)

**Outcomes delivered:**
- End-to-end verified: backend → frontend → SSE events in browser
- `README.md` — full setup + architecture + API + project structure
- `start.md` — 2-command quick-start card

---

### Sub-Task 6 — Security & Guardrails

**Status:** ✅ Done (`18f0dbe`)

**Outcomes delivered:**
- `Literal` enums on severity and status — invalid values rejected at parse time (HTTP 422)
- `Field(ge/le)` bounds on all numeric fields (lat/lon WGS-84, ICU beds, distances)
- `TrustedHostMiddleware` — localhost/127.0.0.1 only (DNS-rebinding protection)
- `CORSMiddleware` — `allow_methods=["GET","POST"]` only
- Security response headers on every reply: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store`
- Global exception handler — 500 with generic message, stack trace logged server-side only
- SSE subscriber cap: `_MAX_SUBSCRIBERS = 10` → HTTP 503 when exceeded
- Bounded per-client queue: `asyncio.Queue(maxsize=20)` — slow clients skipped, not blocked

---

### Sub-Task 7 — Manual Dispatch Endpoint

**Status:** ✅ Done (`0ef50c3`)

**Outcomes delivered:**
- `POST /dispatch` — accepts `{ lat, lon, severity }`, validates WGS-84 bounds
- Emergency ID prefixed `MANUAL-` to distinguish from simulation events
- Result fanned out to SSE subscribers (appears in live feed instantly)
- `ManualDispatch.jsx` form in dashboard
- `dispatch-btn` colour matches severity (red/orange/green)

---

### Sub-Task 8 — Unit Tests

**Status:** ✅ Done (`f000096`, `7e9813b`)

**Outcomes delivered:**
- **Backend** — 31 pytest tests in `backend/tests/test_all.py`:
  - `TestHaversine` (3) — same point, known distance, symmetry
  - `TestModelValidation` (5) — valid + invalid severity/status/lat/lon/ICU
  - `TestDispatcherAgent` (3) — nearest, excludes dispatched, None when all dispatched
  - `TestHospitalAgent` (3) — ICU filter, full hospitals, trauma bonus
  - `TestCoordinatorAgent` (6) — plan, ETA, distances, reasoning tags, severity, None on no resources
  - `TestHealthEndpoint` (2) — 200 OK, security headers
  - `TestStatusEndpoint` (3) — 10 ambulances + 6 hospitals, field presence
  - `TestManualDispatchEndpoint` (6) — valid, bad severity, lat/lon OOB, missing fields, 503
- **Frontend** — 21 Vitest + RTL tests in `src/__tests__/ManualDispatch.test.jsx`:
  - Rendering (7), landmark dropdown (3), severity dropdown (2), successful dispatch (4), errors (2), geolocation (3)

---

### Sub-Task 9 — Location UX (Landmark + Geolocation)

**Status:** ✅ Done (`db15d76`, `36c28b9`)

**Outcomes delivered:**
- `ManualDispatch.jsx` upgraded from raw lat/lon inputs to:
  - 14-landmark dropdown (Bangalore neighbourhoods) — no coordinates needed
  - "Custom (enter coordinates)" option — reveals raw lat/lon fields
  - **📍 My Location** button — `navigator.geolocation.getCurrentPosition()` with graceful fallback
  - `step="any"`, global WGS-84 bounds — full GPS precision accepted
- Backend `ManualDispatchRequest` widened to global WGS-84 bounds

---

## Technology Decisions

| Concern | Decision | Reason |
|---|---|---|
| Agent logic | Deterministic Python (Haversine + rules) | No LLM = no credits, no keys, fully reliable |
| Real-time feed | SSE (Server-Sent Events) | Simpler than WebSockets for one-way push, native browser support |
| Frontend framework | React 19 + Vite 8 | Fast setup, component model suits the multi-panel layout |
| Data persistence | In-memory Python lists | No DB setup time, sufficient for demo |
| Distance calculation | Haversine formula | Accurate for mock lat/lon, pure math, no dependency |
| Styling | Plain CSS (dark theme `#0d1117`) | No install overhead, full control, matches GitHub dark |
| Input validation | Pydantic `Literal` + `Field` bounds | Validation at the model layer — agents never receive invalid data |
| Security headers | Custom `@app.middleware("http")` | Standard browser hardening in one place |
| Host trust | `TrustedHostMiddleware` | Prevents DNS-rebinding attacks in local demo context |
| Backend testing | pytest + FastAPI `TestClient` (httpx) | Idiomatic for FastAPI; in-process, no network required |
| Frontend testing | Vitest + React Testing Library | Native Vite integration, fast jsdom runner, RTL for behaviour-first tests |
| Location input | Landmark dropdown + `navigator.geolocation` | Zero friction for demo (no typing), real GPS for real deployments |

---

## What This Demonstrates for Judges

1. **Multi-agent architecture** — 3 agents with distinct responsibilities, coordinated by an orchestrator; each agent is independently testable
2. **AI SDLC with IBM Bob** — plan-first, review-gated, sub-task-by-sub-task; every commit traces to a spec item
3. **Real-world problem** — emergency dispatch is tangible and high-stakes; the golden hour is a genuine medical concept
4. **Live demo** — auto-running simulation is visually compelling, no manual clicks needed to show value
5. **Responsible AI** — transparent agent reasoning in the UI; every dispatch decision is explained step-by-step, never a black box
6. **Production-grade guardrails** — input validation, security headers, trusted host, subscriber cap, bounded queues, global error handler
7. **Test coverage** — 52 automated tests (31 backend + 21 frontend) covering agents, models, API contracts, and UI behaviour
