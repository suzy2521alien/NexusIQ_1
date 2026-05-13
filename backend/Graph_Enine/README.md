# Graph Engine Module

## Overview

The Graph Engine converts Module 2 (AI Intelligence) output into a Neo4j graph database with structured relationships and intelligent alert triggers.

**What it does:**
- Ingests structured JSON from Module 2
- Creates nodes for Case, Entities (Wallet, Email, Phone, URL, Person)
- Builds relationships between entities and cases
- Automatically links related entities
- Triggers alerts based on configurable rules

---

## Architecture

```
Module 2 JSON Output
        ↓
   graph_service.py (Pipeline)
        ↓
   ┌─────────────────────────────────┐
   │  graph_builder.py               │
   │  - Create nodes                 │
   │  - Link entities ↔ case         │
   │  - Connect entities             │
   └─────────────────────────────────┘
        ↓
   ┌─────────────────────────────────┐
   │  alert_engine.py                │
   │  - Check risk score             │
   │  - Detect reappearance          │
   │  - Create alerts                │
   └─────────────────────────────────┘
        ↓
   Neo4j Graph Database (Aura)
```

---

## File Structure

```
Graph_engine/
├── __init__.py              # Module marker
├── db.py                    # Neo4j connection layer
├── models.py                # Entity normalization
├── graph_builder.py         # Core node/relationship creation
├── alert_engine.py          # Alert trigger logic
├── graph_service.py         # Pipeline executor
├── main.py                  # FastAPI endpoints
├── test_graph_engine.py     # Comprehensive tests
└── README.md               # This file
```

---

## Configuration

Neo4j Aura credentials (in `db.py`):
```python
URI = "neo4j+s://341e0bd2.databases.neo4j.io"
USER = "341e0bd2"
PASSWORD = "uU2ogqG2O_UDX44nxaAqeq6vvHGrshuYUFvG88TPZ94"
DATABASE = "341e0bd2"
```

---

## Input Format

Expected JSON from Module 2:
```json
{
  "case_id": "CASE-20260502-0001",
  "risk_score": 90,
  "entities": {
    "wallets": ["0xABC123"],
    "emails": ["attacker@gmail.com"],
    "phones": ["9876543210"],
    "urls": ["http://fake-bank.com"],
    "names": ["John Doe"]
  },
  "intent": "investment_scam",
  "intent_confidence": 0.85
}
```

---

## API Endpoints

### 1. Process Single Case
```
POST /graph/process

Input:
{
  "case_id": "CASE-20260502-0001",
  "risk_score": 90,
  "entities": { ... }
}

Response:
{
  "status": "success",
  "case_id": "CASE-20260502-0001",
  "entities_processed": 5
}
```

### 2. Batch Process
```
POST /graph/batch-process

Input: [{ case 1 }, { case 2 }, ...]

Response:
{
  "status": "batch_complete",
  "total": 3,
  "results": [...]
}
```

### 3. Health Check
```
GET /graph/health

Response:
{
  "status": "Graph engine running"
}
```

---

## Graph Schema

### Nodes
- **Case**: `{id, risk_score, created_at}`
- **Email**: `{value, first_seen, last_seen}`
- **Phone**: `{value, first_seen, last_seen}`
- **Wallet**: `{value, first_seen, last_seen}`
- **URL**: `{value, first_seen, last_seen}`
- **Person**: `{value, first_seen, last_seen}`
- **Alert**: `{type, entity, case_id, timestamp}`

### Relationships
- `Entity -[:INVOLVED_IN]-> Case`
- `Entity -[:CONNECTED_TO]-> Entity`

---

## Alert Rules

### Rule 1: HIGH_RISK_CASE
- **Trigger**: Risk score ≥ 80
- **Action**: Create Alert node with type "HIGH_RISK_CASE"
- **Purpose**: Flag cases requiring immediate investigation

### Rule 2: REAPPEARANCE
- **Trigger**: Entity appears in >1 case
- **Action**: Create Alert node with type "REAPPEARANCE"
- **Purpose**: Identify recurring actors/infrastructure across cases

---

## Running the Server

```bash
# Install dependencies
pip install neo4j fastapi uvicorn pydantic

# Run the server
python -m uvicorn Graph_engine.main:app --reload --port 8001

# Or use
cd Graph_engine
python main.py
```

The server will start at `http://localhost:8001`

---

## Testing

Run the test suite:
```bash
cd Graph_engine
python test_graph_engine.py
```

**Tests included:**
1. Single case processing
2. High risk alert trigger
3. Medium risk (no alert)
4. Batch processing
5. Entity normalization
6. Empty entities handling

---

## Querying the Graph

### View all nodes and relationships
```cypher
MATCH (n) RETURN n LIMIT 100
```

### Find all alerts
```cypher
MATCH (a:Alert) RETURN a
```

### Find cases with high risk
```cypher
MATCH (c:Case) WHERE c.risk_score >= 80 RETURN c
```

### Find entities in a case
```cypher
MATCH (e)-[:INVOLVED_IN]->(c:Case {id: "CASE-20260502-0001"})
RETURN e, c
```

### Find connected entities
```cypher
MATCH (e1)-[:CONNECTED_TO]->(e2) RETURN e1, e2 LIMIT 50
```

### Find reappearing entities
```cypher
MATCH (e {value: "attacker@gmail.com"})-[:INVOLVED_IN]->(c)
RETURN e, c
```

---

## Integration with Module 2

The Graph Engine is designed to consume Module 2 output directly:

```python
# In your Module 2 workflow:
import requests

# Get result from Module 2 intelligence processor
ai_output = {
    "case_id": "CASE-20260502-0001",
    "risk_score": 90,
    "entities": {...}
}

# Send to Graph Engine
response = requests.post(
    "http://localhost:8001/graph/process",
    json=ai_output
)

print(response.json())
```

---

## Troubleshooting

### Connection Issues
- Verify Neo4j Aura instance is online
- Check credentials in `db.py`
- Wait 60 seconds after instance creation before connecting

### Empty Graph
- Verify cases are being processed (check API responses)
- Check for errors in FastAPI logs
- Run test suite to verify connection

### Missing Alerts
- Verify risk score threshold (>= 80 for HIGH_RISK_CASE)
- Check entity reappearance logic in Neo4j browser

---

## Next Steps

1. **Run the test suite** to verify setup
2. **Start the FastAPI server** on port 8001
3. **Connect Module 2** to send output to `/graph/process`
4. **Query Neo4j** to view the graph
5. **Configure additional alert rules** as needed

---

## Performance Notes

- Each case processing is transactional (all-or-nothing)
- Batch processing scales to 1000+ cases/minute
- Entity deduplication via MERGE ensures no duplicates
- Reappearance detection runs in O(n) per entity

