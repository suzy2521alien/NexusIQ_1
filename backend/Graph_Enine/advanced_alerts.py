"""
Advanced Alert System - Intelligent threat detection
Implements 4+ alert types for comprehensive fraud detection
"""

def create_alert(tx, alert_type, entity_value, case_id=None, metadata=None):
    """
    Create an Alert node with metadata
    """
    import json as _json
    metadata_str = _json.dumps(metadata or {})
    
    tx.run("""
        CREATE (a:Alert {
            type: $type,
            entity: $entity,
            case_id: $case_id,
            timestamp: datetime(),
            metadata: $metadata,
            severity: $severity
        })
    """, 
    type=alert_type, 
    entity=entity_value, 
    case_id=case_id,
    metadata=metadata_str,
    severity=determine_severity(alert_type))


def determine_severity(alert_type):
    """Determine alert severity level (1-5)"""
    severity_map = {
        "HIGH_RISK_CASE": 5,
        "PROXIMITY_ALERT": 4,
        "MULTI_CASE_ENTITY": 4,
        "BURST_ACTIVITY": 3,
        "REAPPEARANCE": 3,
        "NETWORK_CLUSTERING": 4,
        "THRESHOLD_BREACH": 2
    }
    return severity_map.get(alert_type, 2)


# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE 1: HIGH RISK CASE
# ─────────────────────────────────────────────────────────────────────────────

def check_high_risk_case(tx, case_id, risk_score):
    """
    Alert Rule 1: HIGH_RISK_CASE
    
    Triggers when case risk score >= 80
    Indicates: Strong fraud signal
    """
    if risk_score >= 80:
        return {
            "triggered": True,
            "alert_type": "HIGH_RISK_CASE",
            "severity": 5,
            "reason": f"Risk score {risk_score} exceeds threshold (80)"
        }
    return {"triggered": False}


# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE 2: REAPPEARANCE
# ─────────────────────────────────────────────────────────────────────────────

def check_reappearance(tx, entity_value):
    """
    Alert Rule 2: REAPPEARANCE
    
    Triggers when entity appears in 3+ cases
    Indicates: Repeat actor or shared infrastructure
    """
    result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN COUNT(c) AS count
    """, value=entity_value)
    
    record = result.single()
    count = record["count"] if record else 0
    
    if count >= 3:
        return {
            "triggered": True,
            "alert_type": "REAPPEARANCE",
            "severity": 3,
            "reason": f"Entity appears in {count} cases (threshold: 3)",
            "metadata": {"case_count": count}
        }
    return {"triggered": False}


# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE 3: PROXIMITY ALERT (NEW)
# ─────────────────────────────────────────────────────────────────────────────

def check_proximity_alert(tx, entity_value):
    """
    Alert Rule 3: PROXIMITY_ALERT
    Triggers when entity connects to high-risk entities
    """
    result = tx.run("""
        MATCH (e {value: $value})-[:CONNECTED_TO|:INVOLVED_IN]-(n)-[:INVOLVED_IN]->(c:Case)
        WHERE c.risk_score >= 80
        RETURN COUNT(DISTINCT n) AS risky_neighbors
    """, value=entity_value)
    
    record = result.single()
    risky_neighbors = record["risky_neighbors"] if record else 0
    
    if risky_neighbors > 0:
        return {
            "triggered": True,
            "alert_type": "PROXIMITY_ALERT",
            "severity": 4,
            "reason": f"Entity connected to {risky_neighbors} high-risk entities",
            "metadata": {"risky_neighbors": risky_neighbors}
        }
    return {"triggered": False}


# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE 4: MULTI-CASE ENTITY (NEW)
# ─────────────────────────────────────────────────────────────────────────────

def check_multi_case_entity(tx, entity_value):
    """
    Alert Rule 4: MULTI_CASE_ENTITY
    
    Triggers when entity appears in 2-3 cases (before REAPPEARANCE)
    Indicates: Early indication of network formation
    """
    result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN COUNT(c) AS count
    """, value=entity_value)
    
    record = result.single()
    count = record["count"] if record else 0
    
    if 2 <= count < 3:
        return {
            "triggered": True,
            "alert_type": "MULTI_CASE_ENTITY",
            "severity": 4,
            "reason": f"Entity appears in {count} cases (potential network)",
            "metadata": {"case_count": count}
        }
    return {"triggered": False}


# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE 5: BURST ACTIVITY (NEW)
# ─────────────────────────────────────────────────────────────────────────────

def check_burst_activity(tx, entity_value):
    """
    Alert Rule 5: BURST_ACTIVITY
    
    Triggers when entity activity spikes within time window
    Indicates: Sudden fraudulent behavior pattern
    """
    result = tx.run("""
        MATCH (e {value: $value})
        WHERE e.activity_count > 0
        RETURN e.activity_count AS count, 
               duration.between(e.first_seen, e.last_seen) AS lifespan
    """, value=entity_value)
    
    record = result.single()
    if not record:
        return {"triggered": False}
    
    activity_count = record["count"]
    lifespan = record["lifespan"]
    
    # Burst = many activities in short time
    if activity_count >= 5 and lifespan.days < 1:
        return {
            "triggered": True,
            "alert_type": "BURST_ACTIVITY",
            "severity": 3,
            "reason": f"Burst: {activity_count} activities in < 1 day",
            "metadata": {"activity_count": activity_count, "lifespan_days": lifespan.days}
        }
    return {"triggered": False}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ALERT ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def handle_alerts(session, case_id, entities, risk_score):
    """
    Main alert orchestrator - applies all alert rules
    
    Rules:
    1. HIGH_RISK_CASE (risk >= 80)
    2. REAPPEARANCE (entity in 3+ cases)
    3. PROXIMITY_ALERT (connected to high-risk entities)
    4. MULTI_CASE_ENTITY (entity in 2-3 cases)
    5. BURST_ACTIVITY (activity spike)
    
    Args:
        session: Neo4j session
        case_id: Case being processed
        entities: List of entity dicts with type and value
        risk_score: Case risk score
    """
    
    alerts_triggered = []
    print(f"\n[ALERTS] Processing {len(entities)} entities for case {case_id}")
    
    # Rule 1: HIGH_RISK_CASE
    high_risk = session.execute_read(check_high_risk_case, case_id, risk_score)
    if high_risk["triggered"]:
        session.execute_write(create_alert, high_risk["alert_type"], case_id, case_id, 
                                 {"reason": high_risk["reason"]})
        alerts_triggered.append(f"HIGH_RISK_CASE (severity: 5)")
        print(f"  🔴 HIGH_RISK_CASE: {high_risk['reason']}")
    
    # Process entity-based alerts
    for entity in entities:
        value = entity["value"]
        entity_type = entity["type"]
        
        # Rule 2: REAPPEARANCE
        reappear = session.execute_read(check_reappearance, value)
        if reappear["triggered"]:
            session.execute_write(create_alert, reappear["alert_type"], value, case_id,
                                     reappear.get("metadata"))
            alerts_triggered.append(f"REAPPEARANCE({entity_type})")
            print(f"  🟠 REAPPEARANCE: {entity_type} '{value}' - {reappear['reason']}")
        
        # Rule 3: PROXIMITY_ALERT
        proximity = session.execute_read(check_proximity_alert, value)
        if proximity["triggered"]:
            session.execute_write(create_alert, proximity["alert_type"], value, case_id,
                                     proximity.get("metadata"))
            alerts_triggered.append(f"PROXIMITY_ALERT({entity_type})")
            print(f"  🟡 PROXIMITY_ALERT: {entity_type} '{value}' - {proximity['reason']}")
        
        # Rule 4: MULTI_CASE_ENTITY
        multi = session.execute_read(check_multi_case_entity, value)
        if multi["triggered"]:
            session.execute_write(create_alert, multi["alert_type"], value, case_id,
                                     multi.get("metadata"))
            alerts_triggered.append(f"MULTI_CASE_ENTITY({entity_type})")
            print(f"  🔵 MULTI_CASE_ENTITY: {entity_type} '{value}' - {multi['reason']}")
        
        # Rule 5: BURST_ACTIVITY
        burst = session.execute_read(check_burst_activity, value)
        if burst["triggered"]:
            session.execute_write(create_alert, burst["alert_type"], value, case_id,
                                     burst.get("metadata"))
            alerts_triggered.append(f"BURST_ACTIVITY({entity_type})")
            print(f"  ⚡ BURST_ACTIVITY: {entity_type} '{value}' - {burst['reason']}")
    
    print(f"[ALERTS] Total alerts triggered: {len(alerts_triggered)}")
    return alerts_triggered


def get_alerts_for_case(tx, case_id):
    """Query all alerts associated with a case"""
    result = tx.run("""
        MATCH (a:Alert {case_id: $case_id})
        RETURN a.type, a.entity, a.timestamp, a.severity
        ORDER BY a.timestamp DESC
    """, case_id=case_id)
    
    return [record.data() for record in result]


def get_alerts_by_type(tx, alert_type, limit=100):
    """Query alerts by type"""
    result = tx.run("""
        MATCH (a:Alert {type: $type})
        RETURN a.case_id, a.entity, a.timestamp, a.severity
        ORDER BY a.timestamp DESC
        LIMIT $limit
    """, type=alert_type, limit=limit)
    
    return [record.data() for record in result]


def get_critical_alerts(tx, min_severity=4, limit=50):
    """Query critical alerts (severity >= 4)"""
    result = tx.run("""
        MATCH (a:Alert)
        WHERE a.severity >= $min_severity
        RETURN a.type, a.case_id, a.entity, a.timestamp, a.severity
        ORDER BY a.timestamp DESC, a.severity DESC
        LIMIT $limit
    """, min_severity=min_severity, limit=limit)
    
    return [record.data() for record in result]
