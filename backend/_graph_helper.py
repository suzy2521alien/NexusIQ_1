#!/usr/bin/env python3
"""
Graph Engine helper — runs inside Graph_engine/ working directory
so bare imports (from models import ...) resolve correctly.
Called by pipeline_test.py as a subprocess.
"""
import sys, os, json

# Force UTF-8 output to avoid Windows charmap encoding errors
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Must run with cwd = Graph_engine/
sys.path.insert(0, os.getcwd())

from graph_service import batch_process_cases
from db import get_session
from case_linking import compute_case_similarity, filter_links, analyze_case_network
from fraud_ring_detector import detect_all_clusters, get_cluster_statistics

inputs_path  = sys.argv[1]
results_path = os.path.join(os.path.dirname(inputs_path), "_graph_results.json")

with open(inputs_path) as f:
    graph_inputs = json.load(f)

# ── Batch ingest ──
print(f"\n[GRAPH HELPER] Ingesting {len(graph_inputs)} cases into Neo4j...")
batch_results = batch_process_cases(graph_inputs)
case_ids = [r.get("case_id") for r in graph_inputs]

# ── Node counts ──
with get_session() as session:
    case_count   = session.run("MATCH (c:Case) WHERE c.id IN $ids RETURN COUNT(c) AS n", ids=case_ids).single()["n"]
    entity_count = session.run("MATCH (e)-[:INVOLVED_IN]->(c:Case) WHERE c.id IN $ids RETURN COUNT(DISTINCT e) AS n", ids=case_ids).single()["n"]
    alert_count  = session.run("MATCH (a:Alert) WHERE a.case_id IN $ids RETURN COUNT(a) AS n", ids=case_ids).single()["n"]
    rel_count    = session.run("MATCH (c1:Case)-[r:RELATED_TO]->(c2:Case) WHERE c1.id IN $ids RETURN COUNT(r) AS n", ids=case_ids).single()["n"]

print(f"[GRAPH HELPER] Nodes: {case_count} cases, {entity_count} entities, {alert_count} alerts, {rel_count} RELATED_TO links")

# ── Case linking on first case ──
test_case = case_ids[0]
linking = {"total_candidates": 0, "filtered_count": 0, "found": False, "network_risk_level": "UNKNOWN", "top_links": []}
try:
    with get_session() as session:
        links    = session.execute_read(compute_case_similarity, test_case)
        filtered = filter_links(links, threshold=0.1)
        analysis = session.execute_read(analyze_case_network, test_case)
    linking = {
        "total_candidates": len(links),
        "filtered_count":   len(filtered),
        "found":            analysis.get("found", False),
        "network_risk_level": analysis.get("network_risk_level", "UNKNOWN"),
        "top_links": [{"case_id": l.get("case_id"), "similarity": l.get("similarity", 0)} for l in filtered[:5]]
    }
except Exception as e:
    print(f"[GRAPH HELPER] Case linking warning: {e}")

# ── Fraud ring detection ──
rings = {"cluster_count": 0, "stats": {"total_clusters": 0}, "clusters": []}
try:
    with get_session() as session:
        clusters = session.execute_read(detect_all_clusters)
        stats    = session.execute_read(get_cluster_statistics)
    rings = {
        "cluster_count": len(clusters),
        "stats": stats,
        "clusters": [
            {
                "cluster_size":    c.get("cluster_size"),
                "threat_level":    c.get("threat_level"),
                "avg_risk":        c.get("avg_risk", 0),
                "member_cases":    c.get("member_cases", []),
                "shared_entities": c.get("shared_entities", [])[:5]
            }
            for c in clusters[:5]
        ]
    }
except Exception as e:
    print(f"[GRAPH HELPER] Fraud ring detection warning: {e}")

output = {
    "batch_results": batch_results,
    "stats": {
        "case_count":   case_count,
        "entity_count": entity_count,
        "alert_count":  alert_count,
        "rel_count":    rel_count
    },
    "linking": linking,
    "rings":   rings
}

with open(results_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"[GRAPH HELPER] Done. Results written to {results_path}")
