"""
Case Linking Module - Find related cases using shared entities and similarity scoring
Implements cross-case intelligence for fraud network discovery
"""


def find_related_cases(tx, case_id):
    """
    Find cases that share entities with a given case (baseline)
    
    This is the simplest signal: cases sharing the same entities
    (email, phone, wallet, etc.)
    
    Args:
        tx: Neo4j transaction
        case_id: The case ID to find links for
    
    Returns:
        List of dicts with case_id and shared_entities count
    """
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        WHERE c1 <> c2
        RETURN c2.id AS case_id, COUNT(e) AS shared_entities
        ORDER BY shared_entities DESC
    """, case_id=case_id)

    return [record.data() for record in result]


def compute_case_similarity(tx, case_id):
    """
    Compute Jaccard similarity between case and all other cases.
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
             size(e1s) + size(e2s) - size([x IN e1s WHERE x IN e2s]) AS union_size

        WHERE union_size > 0
        RETURN c2.id AS case_id,
               intersection,
               union_size AS union,
               (1.0 * intersection / union_size) AS similarity
        ORDER BY similarity DESC
    """, case_id=case_id)

    return [record.data() for record in result]


def filter_links(results, threshold=0.2):
    """
    Filter case links by similarity threshold
    
    Removes low-confidence matches to reduce noise.
    
    Args:
        results: List of dicts from compute_case_similarity()
        threshold: Minimum similarity score (0.0 to 1.0)
                   Default: 0.2 (20% entity overlap)
    
    Returns:
        Filtered list of results above threshold
    
    Examples:
        threshold=0.0   → All links (no filtering)
        threshold=0.2   → At least 20% shared entities
        threshold=0.5   → At least 50% shared entities
        threshold=1.0   → Exact match (identical entities)
    """
    if not results:
        return []
    
    filtered = [r for r in results if r.get("similarity", 0) >= threshold]
    return filtered


def create_case_link(tx, c1, c2, score):
    """
    Create a persistent case relationship in Neo4j
    
    Stores the similarity score as relationship property for future queries.
    Uses MERGE to avoid duplicates.
    
    Args:
        tx: Neo4j transaction
        c1: First case ID
        c2: Second case ID
        score: Similarity score (0.0 to 1.0)
    """
    tx.run("""
        MATCH (c1:Case {id: $c1})
        MATCH (c2:Case {id: $c2})
        MERGE (c1)-[:RELATED_TO {score: $score}]->(c2)
    """, c1=c1, c2=c2, score=score)


def get_case_links_from_graph(tx, case_id, min_score=0.0):
    """
    Query existing case links from the graph
    
    Args:
        tx: Neo4j transaction
        case_id: Case ID to get links for
        min_score: Minimum relationship score to return (default: 0.0, return all)
    
    Returns:
        List of related cases with their link scores
    """
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})-[rel:RELATED_TO]->(c2:Case)
        WHERE rel.score >= $min_score
        RETURN c2.id AS case_id, rel.score AS score
        ORDER BY rel.score DESC
    """, case_id=case_id, min_score=min_score)

    return [record.data() for record in result]


def analyze_case_network(tx, case_id):
    """
    Get comprehensive case linking analysis
    
    Includes:
    - Direct links (1st degree)
    - Network stats
    - Risk assessment based on network
    
    Args:
        tx: Neo4j transaction
        case_id: Case ID to analyze
    
    Returns:
        Dict with analysis results
    """
    # Get the case itself
    case_result = tx.run("""
        MATCH (c:Case {id: $case_id})
        RETURN c.risk_score AS risk_score
    """, case_id=case_id)
    
    case_record = case_result.single()
    if not case_record:
        return {
            "case_id": case_id,
            "found": False,
            "error": "Case not found"
        }
    
    case_risk = case_record.get("risk_score", 0)
    
    # Get direct links
    links_result = tx.run("""
        MATCH (c1:Case {id: $case_id})-[rel:RELATED_TO]->(c2:Case)
        RETURN c2.id AS case_id, 
               rel.score AS similarity,
               c2.risk_score AS risk_score
        ORDER BY rel.score DESC
    """, case_id=case_id)
    
    links = [record.data() for record in links_result]
    
    # Calculate network risk (average risk of linked cases)
    if links:
        avg_linked_risk = sum(l.get("risk_score", 0) for l in links) / len(links)
    else:
        avg_linked_risk = 0
    
    return {
        "case_id": case_id,
        "found": True,
        "case_risk_score": case_risk,
        "related_cases": links,
        "related_count": len(links),
        "avg_related_risk": round(avg_linked_risk, 2),
        "network_risk_level": "CRITICAL" if avg_linked_risk >= 80 else 
                              "HIGH" if avg_linked_risk >= 60 else
                              "MEDIUM" if avg_linked_risk >= 40 else
                              "LOW"
    }
