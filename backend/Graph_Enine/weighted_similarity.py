"""
Weighted Similarity Scoring - Advanced case correlation
Implements weighted Jaccard similarity considering entity types
This is the publishable contribution aspect
"""

# Entity type weights - based on uniqueness and fraud signal
ENTITY_WEIGHTS = {
    "Wallet": 3,        # Unique, hard to change, high signal
    "Phone": 2,         # Medium uniqueness
    "Email": 1,         # Common, easy to create, lower signal
    "URL": 2,           # Medium uniqueness
    "Person": 1,        # Common identifier
    "IP": 3,            # Unique, hard to fake
}


def get_entity_weight(entity_type):
    """Get weight for entity type"""
    return ENTITY_WEIGHTS.get(entity_type, 1)


def compute_weighted_similarity(tx, case_id):
    """
    Compute weighted Jaccard similarity between case and all other cases
    
    Formula: Similarity = sum(weight * intersection) / sum(weight * union)
    
    This accounts for entity importance - a case sharing a wallet is more
    significant than sharing an email.
    
    Args:
        tx: Neo4j transaction
        case_id: The case ID to compute similarity for
    
    Returns:
        List of dicts with case_id, weighted_similarity, and breakdown
    """
    
    result = tx.run("""
        // Get entities for case 1 with types
        MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e1)
        WITH c1, collect({entity: e1, type: labels(e1)[0]}) AS entities_c1
        
        // Get entities for all other cases
        MATCH (c2:Case)<-[:INVOLVED_IN]-(e2)
        WHERE c2 <> c1
        WITH c1, entities_c1, c2, collect({entity: e2, type: labels(e2)[0]}) AS entities_c2
        
        // Calculate weighted intersection and union
        WITH c1, c2,
             entities_c1,
             entities_c2,
             [e IN entities_c1 WHERE any(x IN entities_c2 WHERE x.entity = e.entity)] AS intersection,
             apoc.coll.toSet(entities_c1 + entities_c2) AS union_entities
        
        // Calculate weights
        WITH c1, c2,
             intersection,
             union_entities,
             reduce(w = 0, e IN intersection | 
                w + CASE labels(e.entity)[0]
                    WHEN 'Wallet' THEN 3
                    WHEN 'IP' THEN 3
                    WHEN 'Phone' THEN 2
                    WHEN 'URL' THEN 2
                    ELSE 1
                END) AS intersection_weight,
             reduce(w = 0, e IN union_entities | 
                w + CASE labels(e.entity)[0]
                    WHEN 'Wallet' THEN 3
                    WHEN 'IP' THEN 3
                    WHEN 'Phone' THEN 2
                    WHEN 'URL' THEN 2
                    ELSE 1
                END) AS union_weight
        
        WHERE union_weight > 0
        RETURN c2.id AS case_id,
               size(intersection) AS shared_entities,
               size(union_entities) AS total_entities,
               intersection_weight,
               union_weight,
               (1.0 * intersection_weight / union_weight) AS weighted_similarity
        ORDER BY weighted_similarity DESC
    """, case_id=case_id)
    
    return [record.data() for record in result]


def compute_unweighted_similarity(tx, case_id):
    """
    Compute simple Jaccard similarity (for comparison)
    
    Formula: Similarity = intersection_size / union_size
    """
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e1)
        WITH c1, collect(DISTINCT e1) AS e1s

        MATCH (c2:Case)<-[:INVOLVED_IN]-(e2)
        WHERE c2 <> c1
        WITH c1, e1s, c2, collect(DISTINCT e2) AS e2s

        WITH c1, c2,
             size([x IN e1s WHERE x IN e2s]) AS intersection,
             size(apoc.coll.toSet(e1s + e2s)) AS union

        WHERE union > 0
        RETURN c2.id AS case_id,
               intersection,
               union,
               (1.0 * intersection / union) AS unweighted_similarity
        ORDER BY unweighted_similarity DESC
    """, case_id=case_id)
    
    return [record.data() for record in result]


def compare_similarity_methods(tx, case_id):
    """
    Compare weighted vs unweighted similarity for research purposes
    
    Shows the impact of entity weighting on case linking
    Useful for publishable results
    """
    weighted = compute_weighted_similarity(tx, case_id)
    unweighted = compute_unweighted_similarity(tx, case_id)
    
    # Create mapping for comparison
    comparison = []
    
    weighted_map = {w["case_id"]: w for w in weighted}
    unweighted_map = {u["case_id"]: u for u in unweighted}
    
    all_cases = set(weighted_map.keys()) | set(unweighted_map.keys())
    
    for other_case in sorted(all_cases):
        w_data = weighted_map.get(other_case, {})
        u_data = unweighted_map.get(other_case, {})
        
        comparison.append({
            "case_id": other_case,
            "weighted_score": w_data.get("weighted_similarity", 0),
            "unweighted_score": u_data.get("unweighted_similarity", 0),
            "difference": abs(w_data.get("weighted_similarity", 0) - u_data.get("unweighted_similarity", 0)),
            "shared_entities": u_data.get("intersection", 0),
            "weighted_signal": w_data.get("intersection_weight", 0),
            "weighted_total": w_data.get("union_weight", 0)
        })
    
    return comparison


def filter_weighted_links(results, threshold=0.2):
    """
    Filter case links by weighted similarity threshold
    
    Args:
        results: Output from compute_weighted_similarity
        threshold: Minimum similarity score (default 0.2)
    
    Returns:
        Filtered list of related cases above threshold
    """
    filtered = [r for r in results if r.get("weighted_similarity", 0) >= threshold]
    return sorted(filtered, key=lambda x: x["weighted_similarity"], reverse=True)


def get_similarity_statistics(tx):
    """
    Get statistics about case similarity across the entire graph
    Useful for threshold tuning and metrics
    """
    result = tx.run("""
        MATCH (c1:Case)<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        WHERE c1 <> c2
        
        // Count entity types
        WITH c1, c2,
             COUNT(e) AS shared_count,
             collect(DISTINCT labels(e)[0]) AS entity_types
        
        RETURN COUNT(DISTINCT c1) AS cases_with_links,
               COUNT(DISTINCT {c1: c1, c2: c2}) AS case_pairs,
               avg(shared_count) AS avg_shared_entities,
               max(shared_count) AS max_shared_entities,
               min(shared_count) AS min_shared_entities
    """)
    
    record = result.single()
    return {
        "cases_with_links": record["cases_with_links"],
        "case_pairs": record["case_pairs"],
        "avg_shared_entities": record["avg_shared_entities"],
        "max_shared_entities": record["max_shared_entities"],
        "min_shared_entities": record["min_shared_entities"]
    }


def get_entity_type_distribution(tx, case_id):
    """
    Get distribution of entity types for a case
    Useful for understanding case composition
    """
    result = tx.run("""
        MATCH (c:Case {id: $case_id})<-[:INVOLVED_IN]-(e)
        WITH labels(e)[0] AS entity_type, COUNT(e) AS count
        RETURN entity_type, count
        ORDER BY count DESC
    """, case_id=case_id)
    
    return {record["entity_type"]: record["count"] for record in result}
