"""
Graph Query Intelligence - k-hop neighbor queries and entity analysis
Turns the graph into a usable knowledge base for investigation
"""

from datetime import datetime
from typing import List, Dict, Optional


def get_all_cases(tx, limit=100):
    """
    Retrieve all cases from the graph with their network metadata
    """
    result = tx.run("""
        MATCH (c:Case)
        OPTIONAL MATCH (c)<-[:INVOLVED_IN]-(e)
        WITH c, COUNT(DISTINCT e) AS entity_count
        OPTIONAL MATCH (c)-[:RELATED_TO]-(c2:Case)
        WITH c, entity_count, COUNT(DISTINCT c2) AS linked_cases
        RETURN c.id AS id, c.risk_score AS risk_score, c.created_at AS created_at, 
               entity_count, linked_cases
        ORDER BY c.risk_score DESC
        LIMIT $limit
    """, limit=limit)
    
    cases = []
    for record in result:
        cases.append({
            "id": record["id"],
            "risk_score": record["risk_score"],
            "created_at": str(record["created_at"]) if record["created_at"] else None,
            "entity_count": record["entity_count"],
            "linked_cases": record["linked_cases"]
        })
    return cases


def get_entity_neighbors(tx, entity_value, depth=2):
    """
    Get all entities within k-hops of a given entity
    
    Args:
        tx: Neo4j transaction
        entity_value: The entity value to start from (email, phone, wallet, etc.)
        depth: Number of hops (default 2)
    
    Returns:
        Dict with neighbor entities grouped by relationship type
    """
    
    result = tx.run(f"""
        MATCH (e {{value: $value}})-[*1..{depth}]-(n)
        RETURN DISTINCT n, type(relationships(path)[-1]) AS rel_type
    """, value=entity_value)
    
    neighbors = {
        "direct": [],
        "two_hop": [],
        "relationships": []
    }
    
    # This would need proper path tracking
    # For now, simplified version:
    result = tx.run(f"""
        MATCH (e {{value: $value}})-[*1..{depth}]-(n)
        WHERE n.value IS NOT NULL
        RETURN DISTINCT labels(n)[0] AS type, n.value AS value, 
               n.risk_score AS risk_score, n.last_seen AS last_seen
    """, value=entity_value)
    
    for record in result:
        neighbors["direct"].append({
            "type": record["type"],
            "value": record["value"],
            "risk_score": record.get("risk_score", 0),
            "last_seen": record.get("last_seen")
        })
    
    return neighbors


def get_case_entities(tx, case_id):
    """
    Get all entities involved in a case
    
    Args:
        tx: Neo4j transaction
        case_id: The case ID
    
    Returns:
        List of entity dicts with type, value, and metadata
    """
    
    result = tx.run("""
        MATCH (c:Case {id: $case_id})<-[:INVOLVED_IN]-(e)
        RETURN labels(e)[0] AS entity_type, 
               e.value AS value,
               e.first_seen AS first_seen,
               e.last_seen AS last_seen,
               e.activity_count AS activity_count
        ORDER BY entity_type
    """, case_id=case_id)
    
    entities = []
    for record in result:
        entities.append({
            "type": record["entity_type"],
            "value": record["value"],
            "first_seen": str(record["first_seen"]) if record["first_seen"] else None,
            "last_seen": str(record["last_seen"]) if record["last_seen"] else None,
            "activity_count": record["activity_count"] or 0,
            "span_days": compute_span_days(record["first_seen"], record["last_seen"])
        })
    
    return entities


def get_case_network(tx, case_id):
    """
    Get the full network (nodes and edges) for a specific case.
    Formatted specifically for D3/React-Force-Graph.
    """
    result = tx.run("""
        MATCH (c:Case {id: $case_id})<-[r:INVOLVED_IN]-(e)
        OPTIONAL MATCH (e)-[r2]-(e2)
        WHERE (e2)-[:INVOLVED_IN]->(c) OR e2:Case
        
        WITH c, e, r, r2, e2
        
        // Collect nodes
        WITH collect(DISTINCT {id: c.id, group: "Case", label: c.id, val: 20}) + 
             collect(DISTINCT {id: e.value, group: labels(e)[0], label: e.value, val: 10}) +
             collect(DISTINCT CASE WHEN e2 IS NOT NULL THEN {id: e2.value, group: labels(e2)[0], label: e2.value, val: 5} ELSE null END) AS nodes_raw,
             
             // Collect links
             collect(DISTINCT {source: e.value, target: c.id, type: type(r)}) +
             collect(DISTINCT CASE WHEN e2 IS NOT NULL AND r2 IS NOT NULL THEN {source: e.value, target: e2.value, type: type(r2)} ELSE null END) AS links_raw
             
        RETURN nodes_raw, links_raw
    """, case_id=case_id)
    
    record = result.single()
    if not record:
        return {"nodes": [], "links": []}
        
    # Clean out nulls from nodes and links
    nodes = {n["id"]: n for n in record["nodes_raw"] if n is not None}.values()
    links = [l for l in record["links_raw"] if l is not None]
    
    return {
        "nodes": list(nodes),
        "links": links
    }


def get_related_cases(tx, case_id, min_score=0.0):
    """
    Get all cases related to a given case via case linking
    
    Args:
        tx: Neo4j transaction
        case_id: The case ID
        min_score: Minimum similarity score threshold
    
    Returns:
        List of related cases with similarity scores
    """
    
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})-[r:RELATED_TO]-(c2)
        WHERE r.score >= $min_score
        RETURN c2.id AS case_id,
               c2.risk_score AS risk_score,
               c2.created_at AS created_at,
               r.score AS similarity_score
        ORDER BY r.score DESC
    """, case_id=case_id, min_score=min_score)
    
    related = []
    for record in result:
        related.append({
            "case_id": record["case_id"],
            "risk_score": record["risk_score"],
            "similarity_score": record["similarity_score"],
            "created_at": str(record["created_at"]) if record["created_at"] else None
        })
    
    return related


def get_entity_timeline(tx, entity_value):
    """
    Get timeline of entity activity across cases
    
    Shows when and where an entity has appeared
    """
    
    result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN c.id AS case_id,
               c.risk_score AS risk_score,
               c.created_at AS case_created,
               e.last_seen AS last_seen,
               e.first_seen AS first_seen
        ORDER BY c.created_at ASC
    """, value=entity_value)
    
    timeline = []
    for record in result:
        timeline.append({
            "case_id": record["case_id"],
            "risk_score": record["risk_score"],
            "case_created": record["case_created"],
            "entity_first_seen": record["first_seen"],
            "entity_last_seen": record["last_seen"]
        })
    
    return timeline


def find_entity_bridges(tx, case_id):
    """
    Find entities that connect this case to other cases
    These are the "bridge" entities for case linking
    
    Returns:
        Sorted list of bridge entities by number of connections
    """
    
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        WHERE c1 <> c2
        WITH e, collect(DISTINCT c2.id) AS connected_cases
        RETURN labels(e)[0] AS entity_type,
               e.value AS value,
               size(connected_cases) AS connection_count,
               connected_cases
        ORDER BY connection_count DESC
    """, case_id=case_id)
    
    bridges = []
    for record in result:
        bridges.append({
            "type": record["entity_type"],
            "value": record["value"],
            "connection_count": record["connection_count"],
            "connects_to_cases": record["connected_cases"]
        })
    
    return bridges


def get_entity_risk_network(tx, entity_value, depth=2):
    """
    Get risk-weighted network around an entity
    
    Shows the entity's involvement in high-risk cases and connections
    """
    
    result = tx.run(f"""
        MATCH (e {{value: $value}})-[:INVOLVED_IN]->(c:Case)
        RETURN DISTINCT c.id AS case_id, c.risk_score AS risk_score
    """, value=entity_value)
    
    cases = []
    for record in result:
        cases.append({
            "case_id": record["case_id"],
            "risk_score": record["risk_score"]
        })
    
    total_risk = sum(c["risk_score"] for c in cases)
    avg_risk = total_risk / len(cases) if cases else 0
    
    return {
        "entity": entity_value,
        "involved_cases": len(cases),
        "total_risk": total_risk,
        "avg_risk": avg_risk,
        "max_risk": max((c["risk_score"] for c in cases), default=0),
        "cases": cases,
        "network_threat_level": "CRITICAL" if avg_risk >= 80 else ("HIGH" if avg_risk >= 60 else "MEDIUM" if avg_risk >= 40 else "LOW")
    }


def search_entities(tx, pattern, entity_type=None):
    """
    Search for entities by pattern
    
    Args:
        tx: Neo4j transaction
        pattern: Search pattern (supports * wildcards)
        entity_type: Optional filter by type (Email, Phone, Wallet, etc.)
    
    Returns:
        List of matching entities with metadata
    """
    
    if entity_type:
        result = tx.run(f"""
            MATCH (e:{entity_type})
            WHERE e.value CONTAINS $pattern
            RETURN labels(e)[0] AS type,
                   e.value AS value,
                   COUNT(()-[:INVOLVED_IN]->(c:Case {{e}})) AS case_count,
                   e.last_seen AS last_seen
            ORDER BY case_count DESC
            LIMIT 100
        """, pattern=pattern.replace("*", ""))
    else:
        result = tx.run("""
            MATCH (e)
            WHERE e.value CONTAINS $pattern
            RETURN labels(e)[0] AS type,
                   e.value AS value,
                   COUNT(()-[:INVOLVED_IN]->(c:Case)) AS case_count,
                   e.last_seen AS last_seen
            ORDER BY case_count DESC
            LIMIT 100
        """, pattern=pattern.replace("*", ""))
    
    entities = []
    for record in result:
        entities.append({
            "type": record["type"],
            "value": record["value"],
            "case_count": record["case_count"],
            "last_seen": record["last_seen"]
        })
    
    return entities


def get_entity_metadata(tx, entity_value):
    """
    Get comprehensive metadata for an entity
    """
    
    result = tx.run("""
        MATCH (e {value: $value})
        RETURN labels(e)[0] AS type,
               e.value AS value,
               e.first_seen AS first_seen,
               e.last_seen AS last_seen,
               e.activity_count AS activity_count,
               e.risk_score AS risk_score
    """, value=entity_value)
    
    record = result.single()
    if not record:
        return None
    
    # Get connected information
    cases_result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN COUNT(c) AS case_count, avg(c.risk_score) AS avg_case_risk
    """, value=entity_value)
    
    cases_info = cases_result.single()
    
    neighbors_result = tx.run("""
        MATCH (e {value: $value})-[:CONNECTED_TO]-(n)
        RETURN COUNT(DISTINCT n) AS neighbor_count
    """, value=entity_value)
    
    neighbors_info = neighbors_result.single()
    
    return {
        "type": record["type"],
        "value": record["value"],
        "first_seen": record["first_seen"],
        "last_seen": record["last_seen"],
        "activity_span_days": compute_span_days(record["first_seen"], record["last_seen"]),
        "activity_count": record["activity_count"] or 0,
        "risk_score": record["risk_score"],
        "involved_in_cases": cases_info["case_count"],
        "avg_case_risk": cases_info["avg_case_risk"] or 0,
        "connected_entities": neighbors_info["neighbor_count"]
    }


def compute_span_days(first_seen, last_seen):
    """Helper: Calculate activity span in days"""
    if first_seen and last_seen:
        try:
            delta = last_seen - first_seen
            return delta.days if hasattr(delta, 'days') else 0
        except:
            return 0
    return 0


def get_investigation_summary(tx, case_id):
    """
    Get comprehensive investigation summary for a case
    
    Combines case data, entities, relationships, alerts, and related cases
    """
    
    # Case data
    case_result = tx.run("""
        MATCH (c:Case {id: $case_id})
        RETURN c.risk_score AS risk_score, c.created_at AS created_at
    """, case_id=case_id)
    
    case_data = case_result.single()
    if not case_data:
        return None
    
    entities = get_case_entities(tx, case_id)
    related_cases = get_related_cases(tx, case_id, min_score=0.2)
    bridges = find_entity_bridges(tx, case_id)
    
    # Get alerts
    alerts_result = tx.run("""
        MATCH (a:Alert {case_id: $case_id})
        RETURN a.type AS type, a.severity AS severity
    """, case_id=case_id)
    
    alerts = [record.data() for record in alerts_result]
    
    return {
        "case_id": case_id,
        "risk_score": case_data["risk_score"],
        "created_at": str(case_data["created_at"]) if case_data["created_at"] else None,
        "entity_count": len(entities),
        "entities": entities,
        "related_cases_count": len(related_cases),
        "related_cases": related_cases,
        "bridge_entities": bridges,
        "alerts_count": len(alerts),
        "alerts": alerts,
        "investigation_summary": {
            "primary_risk": case_data["risk_score"],
            "key_entities": [e["value"] for e in entities[:3]],
            "connected_network_size": len(related_cases),
            "critical_connections": len([r for r in related_cases if r["similarity_score"] >= 0.5])
        }
    }
