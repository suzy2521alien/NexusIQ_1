"""
FastAPI layer for graph ingestion
Exposes endpoints for processing cases into graph database
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json

from graph_service import process_case, batch_process_cases
from case_linking import (
    compute_case_similarity,
    filter_links,
    get_case_links_from_graph,
    analyze_case_network,
)
from db import get_session, close_driver
from graph_intelligence import (
    get_entity_neighbors,
    get_case_entities,
    get_related_cases,
    get_investigation_summary,
    search_entities,
    find_entity_bridges,
    get_all_cases,
    get_case_network
)
from fraud_ring_detector import (
    detect_all_clusters,
    identify_ring_leaders,
    get_cluster_statistics
)
from advanced_alerts import get_alerts_for_case, get_critical_alerts, get_alerts_by_type
from weighted_similarity import compute_weighted_similarity, filter_weighted_links
from evaluation_metrics import evaluate_system
from visualization_support import (
    prepare_case_visualization,
    prepare_case_network_visualization,
    prepare_entity_network_visualization,
    prepare_cluster_visualization
)
from graph_indexes import create_all_indexes, verify_indexes
from system_logging import log_case_processing, log_alert_triggered, get_logger
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI(
    title="Graph Ingestion Engine",
    description="Converts Module 2 AI output to Neo4j graph with alerts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EntityData(BaseModel):
    """Entity structure in case data"""
    wallets: Optional[List[str]] = []
    emails: Optional[List[str]] = []
    phones: Optional[List[str]] = []
    urls: Optional[List[str]] = []
    names: Optional[List[str]] = []


class CaseData(BaseModel):
    """Case data structure from Module 2"""
    case_id: str
    risk_score: int
    entities: Dict[str, List[str]]
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None


@app.post("/graph/process")
def process_graph(data: Dict) -> Dict:
    """
    Process a single case into the graph
    
    Expected input:
    {
        "case_id": "CASE-20260502-0001",
        "risk_score": 90,
        "entities": {
            "wallets": ["0xABC123"],
            "emails": ["attacker@gmail.com"],
            "phones": ["9999999999"],
            "urls": ["http://fake-bank.com"],
            "names": ["John Doe"]
        }
    }
    """
    try:
        result = process_case(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/graph/batch-process")
def batch_process_graph(data_list: List[Dict]) -> Dict:
    """
    Process multiple cases into the graph
    
    Expected input: List of case dicts (same structure as /graph/process)
    """
    try:
        results = batch_process_cases(data_list)
        return {
            "status": "batch_complete",
            "total": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/health")
def health_check() -> Dict:
    """Health check endpoint"""
    return {"status": "Graph engine running"}


@app.get("/graph/case-links/{case_id}")
def get_case_links(case_id: str, threshold: float = 0.2) -> Dict:
    """
    Get related cases for a given case ID
    
    Returns cases that share entities with the queried case,
    scored by similarity (Jaccard index).
    
    Args:
        case_id: The case ID to find links for
        threshold: Minimum similarity score (0.0 to 1.0), default 0.2 (20%)
    
    Example:
        GET /graph/case-links/CASE-20260502-0001
        GET /graph/case-links/CASE-20260502-0001?threshold=0.3
    """
    try:
        with get_session() as session:
            results = session.execute_read(compute_case_similarity, case_id)
            filtered = filter_links(results, threshold=threshold)

            return {
                "status": "success",
                "case_id": case_id,
                "threshold": threshold,
                "related_cases": filtered,
                "count": len(filtered)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/case-analysis/{case_id}")
def analyze_case(case_id: str) -> Dict:
    """
    Get comprehensive case network analysis
    
    Returns related cases, network statistics, and network risk level.
    
    Example:
        GET /graph/case-analysis/CASE-20260502-0001
    """
    try:
        with get_session() as session:
            analysis = session.execute_read(analyze_case_network, case_id)

            return {
                "status": "success" if analysis.get("found") else "not_found",
                "data": analysis
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 2: GRAPH INTELLIGENCE APIs
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/neighbors/{entity_value}")
def get_entity_neighbors_api(entity_value: str, depth: int = 2) -> Dict:
    """
    Get all entities within k-hops of a given entity
    
    Args:
        entity_value: The entity value to start from
        depth: Number of hops (1-3), default 2
    
    Example:
        GET /graph/neighbors/attacker@gmail.com?depth=2
    """
    try:
        depth = min(max(depth, 1), 3)  # Clamp between 1-3
        with get_session() as session:
            neighbors = session.execute_read(get_entity_neighbors, entity_value, depth)
            return {
                "status": "success",
                "entity": entity_value,
                "depth": depth,
                "neighbors": neighbors
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/case/{case_id}/entities")
def get_case_entities_api(case_id: str) -> Dict:
    """
    Get all entities involved in a case
    
    Args:
        case_id: The case ID
    
    Example:
        GET /graph/case/CASE-20260502-0001/entities
    """
    try:
        with get_session() as session:
            entities = session.execute_read(get_case_entities, case_id)
            return {
                "status": "success",
                "case_id": case_id,
                "entity_count": len(entities),
                "entities": entities
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/case/{case_id}/related")
def get_related_cases_api(case_id: str, min_score: float = 0.0) -> Dict:
    """
    Get cases related to a given case via case linking
    
    Args:
        case_id: The case ID
        min_score: Minimum similarity score threshold
    
    Example:
        GET /graph/case/CASE-20260502-0001/related?min_score=0.2
    """
    try:
        with get_session() as session:
            related = session.execute_read(get_related_cases, case_id, min_score)
            return {
                "status": "success",
                "case_id": case_id,
                "min_score": min_score,
                "related_count": len(related),
                "related_cases": related
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/investigation/{case_id}")
def get_investigation_api(case_id: str) -> Dict:
    """
    Get comprehensive investigation summary for a case
    
    Combines entities, relationships, alerts, and related cases
    
    Example:
        GET /graph/investigation/CASE-20260502-0001
    """
    try:
        with get_session() as session:
            summary = session.execute_read(get_investigation_summary, case_id)
            return {
                "status": "success" if summary else "case_not_found",
                "investigation": summary
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 3: ADVANCED ALERTS APIs
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/alerts/case/{case_id}")
def get_case_alerts_api(case_id: str) -> Dict:
    """
    Get all alerts associated with a case
    
    Example:
        GET /graph/alerts/case/CASE-20260502-0001
    """
    try:
        with get_session() as session:
            alerts = session.execute_read(get_alerts_for_case, case_id)
            return {
                "status": "success",
                "case_id": case_id,
                "alert_count": len(alerts),
                "alerts": alerts
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/alerts/critical")
def get_critical_alerts_api(min_severity: int = 4, limit: int = 50) -> Dict:
    """
    Get critical alerts (severity >= 4)
    
    Example:
        GET /graph/alerts/critical?min_severity=4&limit=50
    """
    try:
        with get_session() as session:
            alerts = session.execute_read(get_critical_alerts, min_severity, limit)
            return {
                "status": "success",
                "min_severity": min_severity,
                "alert_count": len(alerts),
                "alerts": alerts
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/alerts/type/{alert_type}")
def get_alerts_by_type_api(alert_type: str, limit: int = 100) -> Dict:
    """
    Get alerts by type
    
    Example:
        GET /graph/alerts/type/HIGH_RISK_CASE
        GET /graph/alerts/type/REAPPEARANCE?limit=50
    """
    try:
        with get_session() as session:
            alerts = session.execute_read(get_alerts_by_type, alert_type, limit)
            return {
                "status": "success",
                "alert_type": alert_type,
                "count": len(alerts),
                "alerts": alerts
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 4: WEIGHTED SIMILARITY & ADVANCED ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/case-links/weighted/{case_id}")
def get_weighted_case_links(case_id: str, threshold: float = 0.2) -> Dict:
    """
    Get related cases using weighted similarity (considers entity importance)
    
    Entity weights:
    - Wallet: 3 (high signal)
    - Phone: 2 (medium signal)
    - Email: 1 (low signal)
    
    Example:
        GET /graph/case-links/weighted/CASE-20260502-0001?threshold=0.2
    """
    try:
        with get_session() as session:
            results = session.execute_read(compute_weighted_similarity, case_id)
            filtered = filter_weighted_links(results, threshold=threshold)
            return {
                "status": "success",
                "case_id": case_id,
                "similarity_method": "weighted",
                "threshold": threshold,
                "related_cases": filtered,
                "count": len(filtered)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 5: FRAUD RING DETECTION & CLUSTERING
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/clusters")
def get_all_clusters_api() -> Dict:
    """
    Get all detected fraud rings/clusters
    
    Example:
        GET /graph/clusters
    """
    try:
        with get_session() as session:
            clusters = session.execute_read(detect_all_clusters)
            stats = session.execute_read(get_cluster_statistics)
            return {
                "status": "success",
                "cluster_count": len(clusters),
                "statistics": stats,
                "clusters": clusters
            }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/ring-leaders/{case_id}")
def get_ring_leaders_api(case_id: str) -> Dict:
    """
    Identify leadership/core actors in a fraud ring
    
    Example:
        GET /graph/ring-leaders/CASE-20260502-0001
    """
    try:
        from fraud_ring_detector import get_cluster_for_case, identify_ring_leaders as get_leaders
        
        with get_session() as session:
            cluster = session.execute_read(get_cluster_for_case, case_id)
            
            if not cluster or not cluster.get("member_cases"):
                return {
                    "status": "not_found",
                    "message": "Case not part of any cluster"
                }
            
            leaders = session.execute_read(
                get_leaders, 
                cluster["member_cases"]
            )
            
            return {
                "status": "success",
                "cluster_size": len(cluster["member_cases"]),
                "leader_count": len(leaders),
                "leaders": leaders
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 7: EVALUATION & METRICS
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/metrics")
def get_system_metrics_api() -> Dict:
    """
    Get comprehensive system evaluation metrics
    
    Returns graph statistics, alert metrics, linking quality, etc.
    
    Example:
        GET /graph/metrics
    """
    try:
        with get_session() as session:
            metrics = evaluate_system(session)
            return {
                "status": "success",
                "metrics": metrics
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# PHASE 9: VISUALIZATION SUPPORT
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/graph/visual/case/{case_id}")
def get_case_visualization_api(case_id: str, include_network: bool = False) -> Dict:
    """
    Get case graph in Cytoscape.js format for visualization
    
    Args:
        case_id: The case ID
        include_network: Include related cases (default False)
    
    Example:
        GET /graph/visual/case/CASE-20260502-0001
        GET /graph/visual/case/CASE-20260502-0001?include_network=true
    """
    try:
        with get_session() as session:
            if include_network:
                vis_data = session.execute_read(
                    prepare_case_network_visualization, 
                    case_id
                )
            else:
                vis_data = session.execute_read(
                    prepare_case_visualization,
                    case_id
                )
            
            return {
                "status": "success",
                "visualization": vis_data
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/visual/entity/{entity_value}")
def get_entity_visualization_api(entity_value: str) -> Dict:
    """
    Get entity network in visualization format
    
    Example:
        GET /graph/visual/entity/attacker@gmail.com
    """
    try:
        with get_session() as session:
            vis_data = session.execute_read(
                prepare_entity_network_visualization,
                entity_value
            )
            
            return {
                "status": "success",
                "visualization": vis_data
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def root() -> Dict:
    """Root endpoint with comprehensive API documentation"""
    return {
        "name": "Graph-Based Cybercrime Intelligence System",
        "version": "2.0.0",
        "status": "PRODUCTION_READY",
        "core_endpoints": {
            "POST /graph/process": "Process single case",
            "POST /graph/batch-process": "Process multiple cases",
            "GET /graph/health": "Health check"
        },
        "intelligence_endpoints": {
            "GET /graph/neighbors/{entity_value}": "K-hop entity neighbors",
            "GET /graph/case/{case_id}/entities": "Get case entities",
            "GET /graph/case/{case_id}/related": "Get related cases",
            "GET /graph/investigation/{case_id}": "Comprehensive investigation summary"
        },
        "alert_endpoints": {
            "GET /graph/alerts/case/{case_id}": "Get case alerts",
            "GET /graph/alerts/critical": "Get critical alerts",
            "GET /graph/alerts/type/{alert_type}": "Get alerts by type"
        },
        "case_linking_endpoints": {
            "GET /graph/case-links/{case_id}": "Case links (Jaccard similarity)",
            "GET /graph/case-analysis/{case_id}": "Case network analysis",
            "GET /graph/case-links/weighted/{case_id}": "Weighted similarity links"
        },
        "clustering_endpoints": {
            "GET /graph/clusters": "All detected fraud rings",
            "GET /graph/ring-leaders/{case_id}": "Fraud ring leadership analysis"
        },
        "metrics_endpoints": {
            "GET /graph/metrics": "Comprehensive system evaluation metrics"
        },
        "visualization_endpoints": {
            "GET /graph/visual/case/{case_id}": "Case visualization (Cytoscape format)",
            "GET /graph/visual/entity/{entity_value}": "Entity network visualization"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/graph/cases")
def get_all_cases_api(limit: int = 100) -> Dict:
    """
    Get all cases in the system, enriched with department routing metadata
    """
    try:
        with get_session() as session:
            cases = session.execute_read(get_all_cases, limit)
            
            # Enrich with realistic Cyber Crime Department workflow state
            for c in cases:
                risk = c.get("risk_score", 0)
                
                if risk >= 80:
                    c["status"] = "INVESTIGATION"
                    c["assignedTo"] = "Investigator Alpha"  # Route Critical to Alpha
                    c["stage"] = "INVESTIGATION"
                elif risk >= 60:
                    c["status"] = "INVESTIGATION"
                    c["assignedTo"] = "Investigator Beta"   # Route High to Beta
                    c["stage"] = "ASSIGNED"
                elif risk >= 40:
                    c["status"] = "COMPLAINT"
                    c["assignedTo"] = "Unassigned"          
                    c["stage"] = "REVIEW"
                else:
                    c["status"] = "COMPLAINT"
                    c["assignedTo"] = "Unassigned"          # Route Low to Intake
                    c["stage"] = "COMPLAINT"
                    
            return {
                "status": "success",
                "count": len(cases),
                "cases": cases
            }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/case/{case_id}/network")
def get_case_network_api(case_id: str) -> Dict:
    """
    Get the full node and edge network for a specific case, formatted for the UI graph visualizer.
    """
    try:
        with get_session() as session:
            network = session.execute_read(get_case_network, case_id)
            return {
                "status": "success",
                "case_id": case_id,
                "network": network
            }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


import hashlib
@app.get("/graph/case/{case_id}/geo")
def get_case_geo_api(case_id: str) -> Dict:
    """
    Extract geographical data from the case's evidence network.
    Simulates a GeoIP resolution engine for IP addresses and Phone numbers.
    """
    try:
        with get_session() as session:
            # We reuse the network extraction, then filter and resolve to coordinates
            network = session.execute_read(get_case_network, case_id)
            
            locations = []
            
            # Simulated cybercrime hotspots (Lat, Lng)
            hotspots = [
                {"name": "Moscow, Russia", "lat": 55.7558, "lng": 37.6173, "threat": "CRITICAL"},
                {"name": "Saint Petersburg, Russia", "lat": 59.9311, "lng": 30.3609, "threat": "HIGH"},
                {"name": "Beijing, China", "lat": 39.9042, "lng": 116.4074, "threat": "HIGH"},
                {"name": "Guangzhou, China", "lat": 23.1291, "lng": 113.2644, "threat": "MEDIUM"},
                {"name": "Lagos, Nigeria", "lat": 6.5244, "lng": 3.3792, "threat": "CRITICAL"},
                {"name": "Miami, USA", "lat": 25.7617, "lng": -80.1918, "threat": "LOW"},
                {"name": "London, UK", "lat": 51.5074, "lng": -0.1278, "threat": "MEDIUM"},
                {"name": "Pyongyang, North Korea", "lat": 39.0392, "lng": 125.7625, "threat": "CRITICAL"},
                {"name": "Dubai, UAE", "lat": 25.2048, "lng": 55.2708, "threat": "MEDIUM"},
                {"name": "Kyiv, Ukraine", "lat": 50.4501, "lng": 30.5234, "threat": "HIGH"}
            ]
            
            for node in network["nodes"]:
                # Only resolve specific types to physical locations
                if node["group"] in ["IPAddress", "Phone", "Wallet", "Location", "Email", "URL"]:
                    # Use a hash of the node ID to deterministically assign it a location
                    hash_idx = int(hashlib.md5(node["id"].encode()).hexdigest(), 16) % len(hotspots)
                    loc = hotspots[hash_idx]
                    
                    locations.append({
                        "id": node["id"],
                        "type": node["group"],
                        "value": node["label"],
                        "location_name": loc["name"],
                        "lat": loc["lat"] + ((hash_idx % 10) * 0.1), # Add slight jitter so nodes don't perfectly overlap
                        "lng": loc["lng"] + ((hash_idx % 15) * 0.1),
                        "threat_level": loc["threat"]
                    })
                    
            return {
                "status": "success",
                "case_id": case_id,
                "data": locations
            }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.on_event("startup")
def startup_event():
    """Initialize system on startup"""
    print("[STARTUP] Initializing Graph Ingestion Engine...")
    try:
        with get_session() as session:
            session.execute_write(create_all_indexes)
            verify_indexes(session.execute_read(lambda tx: tx))
        print("[STARTUP] System ready ✓")
    except Exception as e:
        print(f"[STARTUP] Warning: {str(e)}")


@app.on_event("shutdown")
def shutdown_event():
    """Close Neo4j connection on shutdown"""
    close_driver()
    print("[SHUTDOWN] Graph engine closed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
