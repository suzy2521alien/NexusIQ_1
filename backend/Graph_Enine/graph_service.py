"""
Graph Service - executes the complete pipeline
Converts Module 2 JSON output to graph writes + relationships + alerts + intelligence
Integrates all Phase 1-10 functionality
"""

from db import get_session
from graph_builder import (
    create_case,
    create_entity,
    link_entity_to_case,
    link_entities,
)
from models import normalize_entities
from advanced_alerts import handle_alerts as advanced_handle_alerts
from case_linking import (
    compute_case_similarity,
    filter_links,
    create_case_link,
)
from system_logging import (
    log_case_processing,
    log_alert_triggered,
    get_logger
)
from weighted_similarity import compute_weighted_similarity, filter_weighted_links
import time


def process_case(data):
    """
    Main processing function - takes Module 2 output JSON and writes to graph
    
    Args:
        data: Dict containing:
            - case_id: Unique case identifier
            - risk_score: Numeric risk score (0-100)
            - entities: Dict with entity types (wallets, emails, phones, urls, names)
            - intent: (optional) Detected scam type
            - intent_confidence: (optional) Confidence score
    
    Returns:
        Dict with status and case_id and metrics
    """
    start_time = time.time()
    case_id = data.get("case_id")
    risk_score = data.get("risk_score", 0)
    raw_entities = data.get("entities", {})

    if not case_id:
        raise ValueError("case_id is required")

    # Normalize entities to standardized format
    entities = normalize_entities(raw_entities)

    print(f"\n[PROCESSING] Case: {case_id}")
    print(f"[RISK SCORE] {risk_score}/100")
    print(f"[ENTITIES] {len(entities)} entities found")
    
    # Log case processing start
    log_case_processing(case_id, risk_score, len(entities), status="processing")

    with get_session() as session:
        # Step 1: Create case node
        session.execute_write(create_case, case_id, risk_score)
        print(f"✓ Case node created")

        values = []
        alerts_triggered = []

        # Step 2: Create entity nodes and link to case
        for e in entities:
            label = e["type"]
            value = e["value"]

            session.execute_write(create_entity, label, value)
            session.execute_write(link_entity_to_case, label, value, case_id)

            values.append(value)
            print(f"✓ Entity created: {label}:{value}")

        # Step 3: Create connections between entities
        connection_count = 0
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                session.execute_write(link_entities, values[i], values[j])
                connection_count += 1

        print(f"✓ {connection_count} entity connections created")

        # Step 4: Trigger ADVANCED alerts (5 alert types)
        alerts_triggered = advanced_handle_alerts(session, case_id, entities, risk_score)

        # Step 5: Find and link related cases using similarity
        print(f"\n[LINKING] Searching for related cases...")
        links = session.execute_read(compute_case_similarity, case_id)
        filtered_links = filter_links(links, threshold=0.2)
        
        related_cases_found = 0
        if filtered_links:
            print(f"✓ Found {len(filtered_links)} related cases:")
            for link in filtered_links:
                related_case = link.get("case_id")
                similarity = link.get("similarity", 0)
                print(f"  - {related_case}: {similarity:.2%} similarity")
                
                # Store the link in graph (SYMMETRIC)
                session.execute_write(
                    create_case_link,
                    case_id,
                    related_case,
                    similarity
                )
                related_cases_found += 1
        else:
            print(f"ℹ No related cases found (threshold: 20%)")

    # Calculate processing time
    processing_time_ms = (time.time() - start_time) * 1000
    
    # Log successful completion
    log_case_processing(case_id, risk_score, len(entities), status="success")
    
    print(f"✓ Case {case_id} successfully ingested into graph ({processing_time_ms:.0f}ms)\n")

    return {
        "status": "success",
        "case_id": case_id,
        "entities_processed": len(entities),
        "alerts_triggered": len(alerts_triggered),
        "related_cases_found": related_cases_found,
        "processing_time_ms": processing_time_ms
    }


def batch_process_cases(data_list):
    """
    Process multiple cases in batch
    
    Args:
        data_list: List of case data dicts
    
    Returns:
        List of results
    """
    results = []
    for data in data_list:
        try:
            result = process_case(data)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "case_id": data.get("case_id"),
                "error": str(e)
            })
    return results
