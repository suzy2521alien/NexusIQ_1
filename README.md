# NexusIQ Digital Evidence Intelligence System

NexusIQ is a full-stack cybercrime investigation workspace for ingesting digital evidence, extracting forensic entities, running ML-backed intelligence analysis, and visualizing relationships in a Neo4j graph.

The app is organized as a FastAPI backend plus a React/Vite frontend. It supports evidence upload, case management, risk scoring, semantic search, timeline reconstruction, watchlists, collaboration notes, report generation, and interactive link analysis.

## Features

- Evidence ingestion for text-like investigative artifacts
- SHA-256 hashing and chain-of-custody metadata
- Entity extraction for wallets, emails, phone numbers, URLs, and names
- ML/rule-backed scam intent and risk assessment pipeline
- Neo4j graph ingestion for cases, entities, entity links, and related cases
- Interactive Cytoscape.js link analysis
- Geospatial projection of extracted entities
- Timeline view of evidence, hash, entity, graph, and risk events
- Semantic search over processed evidence
- Risk scorecard for high-value targets
- Watchlist and live alert views
- Admin health, audit log, and analysis reconciliation endpoint

## Project Structure

```text
.
+-- backend/
|   +-- app/
|   |   +-- api/routes.py              # Main API routes
|   |   +-- main.py                    # FastAPI app entrypoint
|   |   +-- services/                  # Parsing, extraction, preprocessing
|   +-- Graph_engine/Graph_engine/     # Neo4j graph engine
|   +-- person2_ai_engine/             # Intelligence and embedding pipeline
|   +-- output/                        # Processed evidence JSON files
|   +-- pipeline_test_results.json     # Materialized ML/risk results
|   +-- requirements.txt
+-- frontend/
|   +-- src/pages/                     # Workspace pages
|   +-- src/App.tsx                    # Routes and shell layout
|   +-- package.json
+-- README.md
```

## Pipeline

```text
Evidence upload
  -> parsing and text normalization
  -> entity extraction
  -> processed JSON saved in backend/output
  -> ML/risk analysis saved in pipeline_test_results.json
  -> Neo4j graph ingestion
  -> frontend workspace APIs render dashboard, graph, timeline, risk, search, watchlist
```

For existing parsed evidence, use the reconciliation endpoint to ensure ML and graph analysis are materialized:

```bash
curl -X POST http://localhost:8000/admin/reconcile-analysis \
  -H "Content-Type: application/json" \
  -d "{\"force\": false}"
```

Use `force: true` only when you intentionally want to re-run graph ingestion.

## Requirements

- Python 3.10+
- Node.js 20+
- Neo4j Aura or local Neo4j instance
- Recommended: a Python virtual environment

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install neo4j
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173
```

Build:

```bash
npm run build
```

## Important Backend Endpoints

- `GET /cases/list` - list cases
- `GET /cases/{case_id}` - dashboard case details
- `POST /cases/create` - create a case
- `POST /evidence/upload` - upload and process evidence
- `GET /evidence/results/{case_id}` - evidence vault data
- `GET /graph/{case_id}` - interactive graph payload
- `GET /graph/{case_id}/geo` - geospatial entity projections
- `GET /graph/timeline/{case_id}` - investigation timeline
- `POST /intelligence/semantic-search` - evidence search
- `GET /intelligence/risk-targets?case_id=...` - risk scorecard targets
- `GET /watchlist/list/{case_id}` - case watchlist
- `GET /alerts/live/{case_id}` - alert feed
- `GET /admin/system-health` - system status
- `POST /admin/reconcile-analysis` - backfill ML + graph analysis for parsed evidence

## Running the Full App

Start backend:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

Then log in through the UI. The demo login flow accepts arbitrary credentials and moves through MFA/biometric screens.

## Data Files

- `backend/output/*_processed.json` contains parsed evidence output.
- `backend/pipeline_test_results.json` contains ML/risk pipeline results.
- `backend/case_registry.json` may be created when cases are added through the UI.
- `backend/audit_events.json`, `collab_comments.json`, and `watchlist_overrides.json` store local app state.
- Neo4j stores case/entity graph data.

## Neo4j Configuration

The current graph engine reads Neo4j connection details from:

```text
backend/Graph_engine/Graph_engine/db.py
```

Before sharing or deploying, move credentials out of source code and load them from environment variables, for example:

```text
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
NEO4J_DATABASE
```

## Troubleshooting

If a case has parsed evidence but the UI says analysis is pending:

1. Check `backend/output` for the case processed JSON.
2. Check `backend/pipeline_test_results.json` for a matching `case_id` and `source_file`.
3. Run:

```bash
curl -X POST http://localhost:8000/admin/reconcile-analysis \
  -H "Content-Type: application/json" \
  -d "{\"force\": false}"
```

If the graph looks empty or generic:

- Confirm Neo4j is reachable with `GET /admin/system-health`.
- Open `GET /graph/{case_id}` and verify it returns real nodes and edges.
- Re-run reconciliation if pipeline rows were missing.

If frontend requests fail:

- Confirm backend is running on `http://localhost:8000`.
- Confirm frontend is running on `http://127.0.0.1:5173`.
- Check browser console for CORS or network errors.

## Current Notes

- Graph ingestion can take time for cases with many entities because entity-to-entity relationships and related-case links are written to Neo4j.
- `POST /admin/reconcile-analysis` is intended for backfills and repair, not frequent normal page refreshes.
- Frontend production build can be checked with `npm run build`.
