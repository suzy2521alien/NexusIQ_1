"""
Fraud Ring Detection - Community detection and clustering
Identifies groups of related cases forming fraudulent networks
"""


def detect_entity_clusters(tx):
    """
    Find clusters of cases sharing entities
    
    Algorithm: Community detection via entity bridges
    An entity that appears in multiple cases bridges them into a cluster
    
    Returns:
        List of clusters, each containing case IDs that are connected
    """
    
    # Find all connected components
    result = tx.run("""
        MATCH (c1:Case)<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        WHERE c1 <> c2
        WITH DISTINCT c1, c2
        
        // Get all cases connected through any entity
        MATCH path = (c1)-[:INVOLVED_IN*1..3]-(c2)
        RETURN c1.id, c2.id
    """)
    
    # Build graph of case connections
    graph = {}
    for record in result:
        c1 = record["c1.id"]
        c2 = record["c2.id"]
        
        if c1 not in graph:
            graph[c1] = set()
        if c2 not in graph:
            graph[c2] = set()
        
        graph[c1].add(c2)
        graph[c2].add(c1)
    
    # Find connected components (clusters)
    visited = set()
    clusters = []
    
    def dfs(node, cluster):
        visited.add(node)
        cluster.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, cluster)
    
    for node in graph:
        if node not in visited:
            cluster = set()
            dfs(node, cluster)
            if len(cluster) > 1:  # Only report clusters of size > 1
                clusters.append(sorted(list(cluster)))
    
    return clusters


def analyze_cluster(tx, cluster_case_ids):
    """
    Deep analysis of a fraud cluster
    
    Returns:
        Cluster statistics including:
        - Member cases
        - Shared entities
        - Risk levels
        - Network structure
    """
    
    if not cluster_case_ids:
        return None
    
    # Get cluster statistics
    result = tx.run("""
        MATCH (c:Case)
        WHERE c.id IN $case_ids
        RETURN 
            collect(c.id) AS member_cases,
            avg(c.risk_score) AS avg_risk,
            max(c.risk_score) AS max_risk,
            min(c.risk_score) AS min_risk,
            count(c) AS cluster_size
    """, case_ids=cluster_case_ids)
    
    stats = result.single()
    if not stats:
        return None
    
    # Get shared entities
    shared_result = tx.run("""
        MATCH (c:Case)<-[:INVOLVED_IN]-(e)
        WHERE c.id IN $case_ids
        
        WITH e, COUNT(DISTINCT c) AS case_count
        WHERE case_count > 1
        
        WITH labels(e)[0] AS entity_type, e.value AS value, case_count
        RETURN entity_type, value, case_count
        ORDER BY case_count DESC, entity_type
    """, case_ids=cluster_case_ids)
    
    shared_entities = []
    for record in shared_result:
        shared_entities.append({
            "type": record["entity_type"],
            "value": record["value"],
            "appears_in": record["case_count"],
            "cases": cluster_case_ids
        })
    
    # Determine cluster threat level
    avg_risk = stats["avg_risk"] or 0
    if avg_risk >= 80:
        threat_level = "CRITICAL"
    elif avg_risk >= 60:
        threat_level = "HIGH"
    elif avg_risk >= 40:
        threat_level = "MEDIUM"
    else:
        threat_level = "LOW"
    
    return {
        "member_cases": stats["member_cases"],
        "cluster_size": stats["cluster_size"],
        "avg_risk": avg_risk,
        "max_risk": stats["max_risk"],
        "min_risk": stats["min_risk"],
        "threat_level": threat_level,
        "shared_entities": shared_entities,
        "shared_entity_count": len(shared_entities)
    }


def detect_all_clusters(tx):
    """
    Detect and analyze all fraud rings/clusters in the graph
    
    Returns:
        List of cluster analyses sorted by threat level
    """
    
    clusters = detect_entity_clusters(tx)
    
    analyzed_clusters = []
    for cluster in clusters:
        analysis = analyze_cluster(tx, cluster)
        if analysis:
            analyzed_clusters.append(analysis)
    
    # Sort by threat level and risk
    threat_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    analyzed_clusters.sort(
        key=lambda x: (threat_order[x["threat_level"]], -x["avg_risk"])
    )
    
    return analyzed_clusters


def get_cluster_for_case(tx, case_id):
    """
    Get the cluster (if any) that a case belongs to
    
    Returns:
        Cluster analysis or None if case is isolated
    """
    
    # Find all cases connected to this case
    result = tx.run("""
        MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
        RETURN DISTINCT c2.id AS related_case
    """, case_id=case_id)
    
    related_cases = [record["related_case"] for record in result]
    
    if not related_cases:
        return None
    
    # Perform BFS to find full cluster
    cluster = {case_id}
    queue = [case_id]
    
    while queue:
        current = queue.pop(0)
        result = tx.run("""
            MATCH (c1:Case {id: $case_id})<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
            RETURN DISTINCT c2.id AS related_case
        """, case_id=current)
        
        for record in result:
            related = record["related_case"]
            if related not in cluster:
                cluster.add(related)
                queue.append(related)
    
    return analyze_cluster(tx, list(cluster))


def identify_ring_leaders(tx, cluster_case_ids):
    """
    Identify leadership/core actors in a fraud ring
    
    Leaders are entities that:
    1. Appear in the most cases
    2. Connect to the highest-risk cases
    3. Have longest activity duration
    """
    
    result = tx.run("""
        MATCH (c:Case)<-[:INVOLVED_IN]-(e)
        WHERE c.id IN $case_ids
        
        WITH e, 
             COUNT(DISTINCT c) AS case_appearances,
             avg(c.risk_score) AS avg_risk_connected,
             max(c.risk_score) AS max_risk_connected,
             collect(DISTINCT c.id) AS connected_cases,
             duration.between(min(e.first_seen), max(e.last_seen)).days AS activity_days
        
        RETURN labels(e)[0] AS entity_type,
               e.value AS entity_value,
               case_appearances,
               avg_risk_connected,
               max_risk_connected,
               activity_days,
               connected_cases
        
        ORDER BY case_appearances DESC, avg_risk_connected DESC
        LIMIT 10
    """, case_ids=cluster_case_ids)
    
    leaders = []
    for record in result:
        leaders.append({
            "type": record["entity_type"],
            "value": record["entity_value"],
            "appears_in_cases": record["case_appearances"],
            "avg_risk_connected": record["avg_risk_connected"],
            "max_risk_connected": record["max_risk_connected"],
            "activity_span_days": record["activity_days"],
            "leadership_score": (
                record["case_appearances"] * 0.4 +
                record["avg_risk_connected"] / 100 * 0.3 +
                (record["activity_days"] / 365 if record["activity_days"] else 0) * 0.3
            )
        })
    
    return sorted(leaders, key=lambda x: x["leadership_score"], reverse=True)


def get_cluster_statistics(tx):
    """
    Get overall statistics about fraud rings in the system
    """
    
    clusters = detect_all_clusters(tx)
    
    if not clusters:
        return {
            "total_clusters": 0,
            "cluster_sizes": [],
            "avg_cluster_size": 0,
            "max_cluster_size": 0,
            "critical_clusters": 0,
            "high_clusters": 0,
            "cases_in_clusters": 0,
            "isolated_cases": 0
        }
    
    cluster_sizes = [c["cluster_size"] for c in clusters]
    threat_levels = [c["threat_level"] for c in clusters]
    
    # Count isolated cases
    result = tx.run("""
        MATCH (c:Case)
        WHERE NOT EXISTS {
            MATCH (c)<-[:INVOLVED_IN]-()-[:INVOLVED_IN]->(other:Case)
            WHERE c <> other
        }
        RETURN COUNT(c) AS isolated_count
    """)
    
    isolated = result.single()["isolated_count"] if result else 0
    cases_in_clusters = sum(cluster_sizes)
    
    return {
        "total_clusters": len(clusters),
        "cluster_sizes": cluster_sizes,
        "avg_cluster_size": sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0,
        "max_cluster_size": max(cluster_sizes) if cluster_sizes else 0,
        "min_cluster_size": min(cluster_sizes) if cluster_sizes else 1,
        "critical_clusters": threat_levels.count("CRITICAL"),
        "high_clusters": threat_levels.count("HIGH"),
        "medium_clusters": threat_levels.count("MEDIUM"),
        "low_clusters": threat_levels.count("LOW"),
        "cases_in_clusters": cases_in_clusters,
        "isolated_cases": isolated,
        "clustering_coefficient": cases_in_clusters / (cases_in_clusters + isolated) if (cases_in_clusters + isolated) > 0 else 0
    }
