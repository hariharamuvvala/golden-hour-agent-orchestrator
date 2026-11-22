# 🚑 Golden Hour — Agent Orchestrator

> A multi-agent AI system that automatically dispatches the optimal ambulance-to-hospital route for every incoming emergency — eliminating the manual coordination bottleneck in the critical "golden hour".

---

## What It Does

Mock emergencies fire automatically every 5 seconds. Three specialised Python agents collaborate to handle each one:

| Agent | Responsibility |
|---|---|
| **Dispatcher Agent** | Finds the nearest *available* ambulance using Haversine distance |
| **Hospital Agent** | Finds the nearest hospital with open ICU beds (trauma centres preferred for critical cases) |
| **Coordinator Agent** | Pairs the best ambulance + hospital, computes ETA, produces a full dispatch plan with reasoning |

Results stream live to a React dashboard via Server-Sent Events.

---

## Architecture

```
[ React Dashboard :5173 ]
        │
        │  SSE /stream  +  poll /status
        ▼
[ FastAPI Backend :8000 ]
        │
        └── CoordinatorAgent
                ├── DispatcherAgent  →  10 mock ambulances (Bangalore)
                └── HospitalAgent   →   6 mock hospitals  (Bangalore)
```

**Tech stack:** Python 3.12 · FastAPI · Uvicorn · React 19 · Vite 8  
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
| **Live Dispatch Feed** | Scrolling list of dispatch events — newest on top, colour-coded by severity |
| **Agent Trace** | Step-by-step reasoning for the latest event: Dispatcher → Hospital → Coordinator |
| **Fleet & Hospital Status** | Real-time ambulance availability cards + hospital ICU bed counts |

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Health check |
| `GET /stream` | SSE stream of `DispatchPlan` events (one every ~5 s) |
| `GET /status` | Current state of all ambulances and hospitals |

---

## Project Structure

```
golden-hour-agent-orchestrator/
├── backend/
│   ├── main.py                   # FastAPI app, SSE, simulation loop
│   ├── models.py                 # Pydantic models
│   ├── agents/
│   │   ├── dispatcher_agent.py   # Nearest ambulance
│   │   ├── hospital_agent.py     # Nearest ICU-available hospital
│   │   ├── coordinator_agent.py  # Orchestrator — builds DispatchPlan
│   │   └── utils.py              # Haversine formula
│   └── data/
│       ├── ambulances.py         # 10 mock ambulances (Bangalore)
│       └── hospitals.py          # 6 mock hospitals  (Bangalore)
└── frontend/
    └── src/
        ├── App.jsx
        └── components/
            ├── LiveFeed.jsx
            ├── StatusGrid.jsx
            └── AgentTrace.jsx
```
