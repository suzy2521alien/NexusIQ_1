"""
Alert engine - triggers alerts based on graph rules
"""

def create_alert(tx, alert_type, entity_value, case_id=None):
    """
    Create an Alert node
    
    Args:
        tx: Neo4j transaction
        alert_type: Type of alert (HIGH_RISK_CASE, REAPPEARANCE, etc.)
        entity_value: The entity that triggered the alert
        case_id: Associated case ID
    """
    tx.run("""
        CREATE (a:Alert {
            type: $type,
            entity: $entity,
            case_id: $case_id,
            timestamp: datetime()
        })
    """, type=alert_type, entity=entity_value, case_id=case_id)


def handle_alerts(session, case_id, entities, risk_score):
    """
    Main alert logic - applies all alert rules
    
    Rules:
    1. HIGH_RISK_CASE: Risk score >= 80
    2. REAPPEARANCE: Entity appears in multiple cases
    """
    
    # Rule 1: High Risk Case
    if risk_score >= 80:
        session.execute_write(create_alert, "HIGH_RISK_CASE", case_id, case_id)
        print(f"[ALERT] HIGH_RISK_CASE triggered for {case_id} (score: {risk_score})")

    # Rule 2: Reappearance
    for e in entities:
        value = e["value"]
        label = e["type"]

        # Import here to avoid circular imports
        from graph_builder import check_entity_cases
        
        count = session.execute_read(check_entity_cases, value)

        # If entity appears in more than 1 case, flag as reappearance
        if count > 1:
            session.execute_write(create_alert, "REAPPEARANCE", value, case_id)
            print(f"[ALERT] REAPPEARANCE: {label} '{value}' found in {count} cases")
