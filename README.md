# 🚑 GoldenMinute — Multi-Agent Emergency Dispatch Orchestrator

> A multi-agent AI system that automatically dispatches the optimal ambulance-to-hospital route for every incoming emergency — eliminating the manual coordination bottleneck in the critical "golden hour".

**GitHub:** https://github.com/hariharamuvvala/golden-hour-agent-orchestrator

---

## What It Does

Mock emergencies fire automatically every 5 seconds. Three specialised Python agents collaborate to handle each one:

| Agent | Responsibility |
|---|---|
| **Dispatcher Agent** | Finds the nearest *available* ambulance using Haversine distance |
| **Hospital Agent** | Finds the nearest hospital with open ICU beds; 20% distance bonus for trauma centres on critical cases |
| **Coordinator Agent** | Pairs the best ambulance + hospital, computes ETA, produces a full dispatch plan with step-by-step reasoning |

Results stream live to a React dashboard via Server-Sent Events. Dispatchers can also trigger a manual emergency from any location using a landmark dropdown or GPS geolocation.

---

## Architecture

```
[ React Dashboard :5173 ]
        │
        │  SSE GET /stream          (live simulation feed, push every ~5 s)
        │  GET /status              (fleet + hospital state, polled every 3 s)
        │  POST /dispatch           (manual patient location)
        ▼
[ FastAPI Backend :8000 ]
        │  TrustedHostMiddleware    (localhost only)
        │  CORSMiddleware           (port 5173 only)
        │  Security headers         (nosniff · DENY · no-store)
        │  Global exception handler (no stack trace leakage)
        │
        └── CoordinatorAgent
                ├── DispatcherAgent  →  10 mock ambulances (Bangalore)
                └── HospitalAgent   →   6 mock hospitals  (Bangalore)
```

**Tech stack:** Python 3.12 · FastAPI · Uvicorn · React 19 · Vite 8 · Vitest · pytest  
**100% local** — no cloud, no API keys, all data in-memory.

---

## Prerequisites

- Python 3.12+
- Node.js 18+ (LTS)

---

## Setup

### 1 — Clone

```bash
git clone https://github.com/hariharamuvvala/golden-hour-agent-orchestrator.git
cd golden-hour-agent-orchestrator
```

### 2 — Backend

```bash
python -m venv .venv

# Windows
.venv\Scripts\pip install -r backend\requirements.txt

# macOS / Linux
.venv/bin/pip install -r backend/requirements.txt
```

### 3 — Frontend

```bash
cd frontend
npm install
cd ..
```

---

## Running the Demo

Open **two terminals** from the project root:

**Terminal 1 — Backend**
```bash
# Windows
.venv\Scripts\uvicorn backend.main:app --port 8000

# macOS / Linux
.venv/bin/uvicorn backend.main:app --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.  
Within 5 seconds, dispatch events will start populating the live feed automatically.

---

## Dashboard Panels

| Panel | Description |
|---|---|
| **Manual Dispatch** | Landmark dropdown (14 Bangalore areas) + 📍 My Location GPS button + severity selector — dispatches instantly |
| **Live Dispatch Feed** | Scrolling list of dispatch events — newest on top, colour-coded by severity (red/orange/green) |
| **Agent Trace** | Step-by-step reasoning for the latest event: Dispatcher → Hospital → Coordinator |
| **Fleet & Hospital Status** | Real-time ambulance cards (green=available, red=dispatched) + hospital ICU bed counts |

---

## Manual Dispatch

Three ways to set a patient location:

1. **Landmark dropdown** — select from 14 Bangalore neighbourhoods (Koramangala, Indiranagar, Whitefield, etc.)
2. **📍 My Location** — click to use browser GPS; fills coordinates automatically
3. **Custom** — select "Custom (enter coordinates)" from the dropdown to enter raw lat/lon

Then pick severity (Critical / Serious / Stable) and click **🚑 Dispatch Now**.  
The result appears instantly at the top of the Live Dispatch Feed.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check → `{"status":"ok"}` |
| `GET` | `/stream` | SSE stream of `DispatchPlan` events (~5 s interval, max 10 clients) |
| `GET` | `/status` | Current state of all ambulances and hospitals |
| `POST` | `/dispatch` | Manual dispatch — body: `{ lat, lon, severity }` → `DispatchPlan` |

### POST /dispatch — Request body

```json
{
  "lat": 12.9279,
  "lon": 77.6271,
  "severity": "critical"
}
```

Severity must be `"critical"`, `"serious"`, or `"stable"`. Invalid values return HTTP 422.

---

## Running Tests

**Backend — 31 pytest tests**
```bash
.venv\Scripts\pytest backend/tests/test_all.py -v
# macOS/Linux: .venv/bin/pytest backend/tests/test_all.py -v
```

Covers: Haversine utility · Pydantic model validation · DispatcherAgent · HospitalAgent · CoordinatorAgent · all API endpoints

**Frontend — 21 Vitest tests**
```bash
cd frontend
npm test
```

Covers: ManualDispatch rendering · landmark dropdown · severity selector · successful dispatch · error handling · geolocation (supported / success / permission denied)

---

## Security

| Guard | Detail |
|---|---|
| Input validation | Pydantic `Literal` enums + `Field(ge/le)` bounds — invalid data rejected at parse time (HTTP 422) |
| Trusted host | `TrustedHostMiddleware` — only `localhost` / `127.0.0.1` accepted |
| CORS | `allow_origins=["http://localhost:5173"]`, `allow_methods=["GET","POST"]` |
| Security headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store` |
| Exception handler | Unhandled errors return generic 500 — stack traces logged server-side, never exposed to client |
| SSE subscriber cap | Max 10 concurrent `/stream` connections → HTTP 503 beyond limit |
| Bounded queues | Per-client `asyncio.Queue(maxsize=20)` — slow clients skipped, not blocked |

---

## Project Structure

```
golden-hour-agent-orchestrator/
├── backend/
│   ├── main.py                    # FastAPI app, middleware, SSE, simulation, POST /dispatch
│   ├── models.py                  # Pydantic models with Literal enums + Field bounds
│   ├── requirements.txt           # fastapi, uvicorn, pydantic, pytest, httpx
│   ├── agents/
│   │   ├── dispatcher_agent.py    # Nearest available ambulance
│   │   ├── hospital_agent.py      # Nearest ICU-available hospital + trauma bonus
│   │   ├── coordinator_agent.py   # Orchestrator — builds DispatchPlan
│   │   └── utils.py               # haversine(lat1, lon1, lat2, lon2) → km
│   ├── data/
│   │   ├── ambulances.py          # 10 mock ambulances (BLR-01 → BLR-10, Bangalore)
│   │   └── hospitals.py           # 6 mock hospitals (Manipal, Fortis, St. John's, Apollo, Narayana, Victoria)
│   └── tests/
│       └── test_all.py            # 31 pytest tests
├── frontend/
│   ├── vite.config.js             # jsdom test environment
│   └── src/
│       ├── App.jsx                # EventSource + /status polling + state
│       ├── components/
│       │   ├── LiveFeed.jsx       # Scrolling dispatch feed
│       │   ├── StatusGrid.jsx     # Ambulance + hospital cards
│       │   ├── AgentTrace.jsx     # 3-step reasoning trace
│       │   └── ManualDispatch.jsx # Landmark dropdown + geolocation + POST /dispatch
│       ├── styles/app.css         # Dark theme, CSS grid
│       └── __tests__/
│           └── ManualDispatch.test.jsx  # 21 Vitest + RTL tests
├── GoldenHour-Hackathon.pptx      # 7-slide pitch deck
├── start.md                       # Quick-start: 2 commands + URL
└── golden-hour-plan.md            # Full architecture + sub-task log
```

---

## Demo Tips (for Judges)

1. **Watch the auto feed** — dispatches appear every 5 seconds with no interaction needed
2. **Click Agent Trace** — shows exactly why each ambulance and hospital was chosen
3. **Try Manual Dispatch** — select "Koramangala", set severity to "Critical", hit Dispatch Now
4. **Watch the Status Grid** — ambulance turns red immediately, resets green after 30 seconds
5. **Try 📍 My Location** — if you're in Bangalore, your GPS coordinates dispatch a real emergency
