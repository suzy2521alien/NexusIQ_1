"""
Core graph building logic - creates nodes and relationships
"""

def create_case(tx, case_id, risk_score):
    """Create a Case node with risk score"""
    tx.run("""
        MERGE (c:Case {id: $case_id})
        SET c.risk_score = $risk_score,
            c.created_at = datetime()
    """, case_id=case_id, risk_score=risk_score)


def create_entity(tx, label, value):
    """Create an entity node (Email, Phone, Wallet, etc.)"""
    query = f"""
    MERGE (e:{label} {{value: $value}})
    ON CREATE SET e.first_seen = datetime()
    SET e.last_seen = datetime()
    """
    tx.run(query, value=value)


def link_entity_to_case(tx, label, value, case_id):
    """Link an entity to a case via INVOLVED_IN relationship"""
    query = f"""
    MATCH (e:{label} {{value: $value}})
    MATCH (c:Case {{id: $case_id}})
    MERGE (e)-[:INVOLVED_IN]->(c)
    """
    tx.run(query, value=value, case_id=case_id)


def link_entities(tx, v1, v2):
    """Create a CONNECTED_TO relationship between two entities"""
    tx.run("""
        MATCH (a {value: $v1})
        MATCH (b {value: $v2})
        MERGE (a)-[:CONNECTED_TO]->(b)
    """, v1=v1, v2=v2)


def check_entity_cases(tx, value):
    """
    Check how many cases an entity appears in
    Used for detecting reappearance
    """
    result = tx.run("""
        MATCH (e {value: $value})-[:INVOLVED_IN]->(c:Case)
        RETURN COUNT(c) AS count
    """, value=value)

    record = result.single()
    if record:
        return record["count"]
    return 0
