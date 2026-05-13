"""
Visualization Support - Graph data formatted for frontend visualization
Supports Cytoscape.js, D3.js, and other network visualization libraries
"""

from typing import Dict, List, Optional


def prepare_case_visualization(tx, case_id: str) -> Dict:
    """
    Prepare case graph for frontend visualization
    
    Returns data in Cytoscape.js format:
    {
        "nodes": [...],
        "edges": [...]
    }
    
    Args:
        tx: Neo4j transaction
        case_id: Case to visualize
    """
    
    nodes = []
    edges = []
    node_ids = set()
    
    # Get case node
    case_result = tx.run("""
        MATCH (c:Case {id: $case_id})
        RETURN c.id, c.risk_score
    """, case_id=case_id)
    
    case_record = case_result.single()
    if case_record:
        case_id_val = case_record["c.id"]
        nodes.append({
            "data": {
                "id": f"case_{case_id_val}",
                "label": case_id_val,
                "type": "Case",
                "risk_score": case_record["c.risk_score"],
                "color": get_risk_color(case_record["c.risk_score"])
            }
        })
        node_ids.add(f"case_{case_id_val}")
    
    # Get entities involved in case
    entity_result = tx.run("""
        MATCH (c:Case {id: $case_id})<-[:INVOLVED_IN]-(e)
        RETURN labels(e)[0] AS type, e.value AS value
    """, case_id=case_id)
    
    for entity_record in entity_result:
        entity_type = entity_record["type"]
        entity_value = entity_record["value"]
        node_id = f"{entity_type}_{entity_value}"
        
        if node_id not in node_ids:
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": entity_value[:20],  # Truncate long values
                    "type": entity_type,
                    "full_value": entity_value
                }
            })
            node_ids.add(node_id)
        
        # Edge from entity to case
        edges.append({
            "data": {
                "source": node_id,
                "target": f"case_{case_id_val}",
                "relationship": "INVOLVED_IN"
            }
        })
    
    # Get entity connections
    connection_result = tx.run("""
        MATCH (c:Case {id: $case_id})<-[:INVOLVED_IN]-(e1)-[:CONNECTED_TO]-(e2)
        RETURN labels(e1)[0] AS type1, e1.value AS value1,
               labels(e2)[0] AS type2, e2.value AS value2
    """, case_id=case_id)
    
    for conn_record in connection_result:
        node1 = f"{conn_record['type1']}_{conn_record['value1']}"
        node2 = f"{conn_record['type2']}_{conn_record['value2']}"
        
        if node1 not in node_ids:
            nodes.append({
                "data": {
                    "id": node1,
                    "label": conn_record['value1'][:20],
                    "type": conn_record['type1'],
                    "full_value": conn_record['value1']
                }
            })
            node_ids.add(node1)
        
        if node2 not in node_ids:
            nodes.append({
                "data": {
                    "id": node2,
                    "label": conn_record['value2'][:20],
                    "type": conn_record['type2'],
                    "full_value": conn_record['value2']
                }
            })
            node_ids.add(node2)
        
        edges.append({
            "data": {
                "source": node1,
                "target": node2,
                "relationship": "CONNECTED_TO"
            }
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "case_id": case_id,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


def prepare_case_network_visualization(tx, case_id: str, depth: int = 2) -> Dict:
    """
    Prepare extended case network including related cases
    
    Shows case linking relationships
    """
    
    vis_data = prepare_case_visualization(tx, case_id)
    nodes = vis_data["nodes"]
    edges = vis_data["edges"]
    node_ids = set(n["data"]["id"] for n in nodes)
    
    # Get related cases
    related_result = tx.run("""
        MATCH (c1:Case {id: $case_id})-[r:RELATED_TO]-(c2:Case)
        RETURN c2.id, r.score, c2.risk_score
        ORDER BY r.score DESC
        LIMIT 10
    """, case_id=case_id)
    
    for rel_record in related_result:
        related_case_id = rel_record["c2.id"]
        score = rel_record["r.score"]
        risk = rel_record["c2.risk_score"]
        
        node_id = f"case_{related_case_id}"
        
        if node_id not in node_ids:
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": related_case_id,
                    "type": "Case",
                    "risk_score": risk,
                    "color": get_risk_color(risk),
                    "similarity": score
                }
            })
            node_ids.add(node_id)
        
        edges.append({
            "data": {
                "source": f"case_{case_id}",
                "target": node_id,
                "relationship": "RELATED_TO",
                "score": score,
                "weight": score * 2  # Make stronger links thicker
            }
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "case_id": case_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "visualization_type": "case_network"
    }


def prepare_entity_network_visualization(tx, entity_value: str, depth: int = 2) -> Dict:
    """
    Prepare entity-centric network visualization
    
    Shows entity connections and associated cases
    """
    
    nodes = []
    edges = []
    node_ids = set()
    
    # Add central entity
    entity_type_result = tx.run("""
        MATCH (e {value: $value})
        RETURN labels(e)[0] AS type
        LIMIT 1
    """, value=entity_value)
    
    entity_type_record = entity_type_result.single()
    if not entity_type_record:
        return {"nodes": [], "edges": [], "error": "Entity not found"}
    
    entity_type = entity_type_record["type"]
    central_id = f"{entity_type}_{entity_value}"
    
    nodes.append({
        "data": {
            "id": central_id,
            "label": entity_value[:20],
            "type": entity_type,
            "full_value": entity_value,
            "size": 30  # Central node is larger
        }
    })
    node_ids.add(central_id)
    
    # Get connected entities
    connected_result = tx.run("""
        MATCH (e {value: $value})-[:CONNECTED_TO]-(e2)
        RETURN labels(e2)[0] AS type, e2.value AS value
    """, value=entity_value)
    
    for conn in connected_result:
        conn_type = conn["type"]
        conn_value = conn["value"]
        conn_id = f"{conn_type}_{conn_value}"
        
        if conn_id not in node_ids:
            nodes.append({
                "data": {
                    "id": conn_id,
                    "label": conn_value[:20],
                    "type": conn_type,
                    "full_value": conn_value
                }
            })
            node_ids.add(conn_id)
        
        edges.append({
            "data": {
                "source": central_id,
                "target": conn_id,
                "relationship": "CONNECTED_TO"
            }
        })
    
    # Get involved cases
    case_result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN c.id, c.risk_score
    """, value=entity_value)
    
    for case in case_result:
        case_id = case["c.id"]
        case_node_id = f"case_{case_id}"
        
        if case_node_id not in node_ids:
            nodes.append({
                "data": {
                    "id": case_node_id,
                    "label": case_id,
                    "type": "Case",
                    "risk_score": case["c.risk_score"],
                    "color": get_risk_color(case["c.risk_score"])
                }
            })
            node_ids.add(case_node_id)
        
        edges.append({
            "data": {
                "source": central_id,
                "target": case_node_id,
                "relationship": "INVOLVED_IN"
            }
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "central_entity": entity_value,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "visualization_type": "entity_network"
    }


def prepare_cluster_visualization(tx, cluster_case_ids: List[str]) -> Dict:
    """
    Prepare fraud ring/cluster visualization
    
    Shows all cases and entities within a cluster
    """
    
    nodes = []
    edges = []
    node_ids = set()
    
    # Add case nodes
    case_result = tx.run("""
        MATCH (c:Case)
        WHERE c.id IN $case_ids
        RETURN c.id, c.risk_score
    """, case_ids=cluster_case_ids)
    
    for case in case_result:
        case_id = case["c.id"]
        case_node_id = f"case_{case_id}"
        
        nodes.append({
            "data": {
                "id": case_node_id,
                "label": case_id,
                "type": "Case",
                "risk_score": case["c.risk_score"],
                "color": get_risk_color(case["c.risk_score"])
            }
        })
        node_ids.add(case_node_id)
    
    # Add entities and connections
    entity_result = tx.run("""
        MATCH (c:Case)<-[:INVOLVED_IN]-(e)
        WHERE c.id IN $case_ids
        RETURN labels(e)[0] AS type, e.value AS value, 
               COUNT(DISTINCT c) AS case_count
    """, case_ids=cluster_case_ids)
    
    for entity in entity_result:
        entity_type = entity["type"]
        entity_value = entity["value"]
        entity_node_id = f"{entity_type}_{entity_value}"
        
        # Size based on how many cases it bridges
        size = 10 + (entity["case_count"] * 2)
        
        if entity_node_id not in node_ids:
            nodes.append({
                "data": {
                    "id": entity_node_id,
                    "label": entity_value[:15],
                    "type": entity_type,
                    "full_value": entity_value,
                    "bridges": entity["case_count"],
                    "size": size
                }
            })
            node_ids.add(entity_node_id)
    
    # Add relationships
    involved_result = tx.run("""
        MATCH (c:Case {id: $case_ids[0]})<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        WHERE c2.id IN $case_ids
        RETURN labels(e)[0] AS type, e.value AS value, c2.id AS case_id
    """, case_ids=cluster_case_ids)
    
    for rel in involved_result:
        entity_node_id = f"{rel['type']}_{rel['value']}"
        case_node_id = f"case_{rel['case_id']}"
        
        edges.append({
            "data": {
                "source": entity_node_id,
                "target": case_node_id,
                "relationship": "INVOLVED_IN"
            }
        })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "cluster_cases": cluster_case_ids,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "visualization_type": "cluster"
    }


def get_risk_color(risk_score: int) -> str:
    """Get color for risk score"""
    if risk_score >= 80:
        return "#DC2626"  # Red
    elif risk_score >= 60:
        return "#EA580C"  # Orange
    elif risk_score >= 40:
        return "#FBBF24"  # Yellow
    else:
        return "#10B981"  # Green


def prepare_alerts_timeline(tx, case_id: str) -> Dict:
    """
    Prepare alerts as timeline for visualization
    """
    
    result = tx.run("""
        MATCH (a:Alert {case_id: $case_id})
        RETURN a.type, a.entity, a.timestamp, a.severity
        ORDER BY a.timestamp ASC
    """, case_id=case_id)
    
    timeline = []
    for record in result:
        timeline.append({
            "type": record["a.type"],
            "entity": record["a.entity"],
            "timestamp": record["a.timestamp"],
            "severity": record["a.severity"],
            "color": get_severity_color(record["a.severity"])
        })
    
    return {
        "case_id": case_id,
        "timeline": timeline,
        "total_events": len(timeline)
    }


def get_severity_color(severity: int) -> str:
    """Get color for alert severity"""
    if severity >= 5:
        return "#DC2626"  # Red
    elif severity >= 4:
        return "#EA580C"  # Orange
    elif severity >= 3:
        return "#FBBF24"  # Yellow
    else:
        return "#3B82F6"  # Blue
