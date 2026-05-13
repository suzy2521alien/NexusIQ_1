"""
Graph Database Indexes - Performance Critical
Ensures O(1) lookups on frequently queried properties
"""

def create_all_indexes(session):
    """
    Create all critical indexes for the graph database
    MUST be run once during system initialization
    
    Indexes significantly improve:
    - Case lookups by ID
    - Entity lookups by value
    - Case linking queries
    - Alert queries
    """
    
    print("[INDEXES] Initializing graph indexes...")
    
    indexes = [
        # Case indexes
        "CREATE INDEX case_id_index IF NOT EXISTS FOR (c:Case) ON (c.id)",
        "CREATE INDEX case_risk_index IF NOT EXISTS FOR (c:Case) ON (c.risk_score)",
        "CREATE INDEX case_created_index IF NOT EXISTS FOR (c:Case) ON (c.created_at)",
        
        # Entity indexes - CRITICAL for similarity queries
        "CREATE INDEX entity_value_index IF NOT EXISTS FOR (e) ON (e.value)",
        "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e) ON (e.type)",
        "CREATE INDEX entity_last_seen_index IF NOT EXISTS FOR (e) ON (e.last_seen)",
        
        # Alert indexes
        "CREATE INDEX alert_type_index IF NOT EXISTS FOR (a:Alert) ON (a.type)",
        "CREATE INDEX alert_case_index IF NOT EXISTS FOR (a:Alert) ON (a.case_id)",
        "CREATE INDEX alert_timestamp_index IF NOT EXISTS FOR (a:Alert) ON (a.timestamp)",
        
        # Relationship indexes for efficient traversal
        "CREATE INDEX involved_in_rel IF NOT EXISTS FOR ()-[r:INVOLVED_IN]-() ON (r.weight)",
        "CREATE INDEX connected_to_rel IF NOT EXISTS FOR ()-[r:CONNECTED_TO]-() ON (r.weight)",
        "CREATE INDEX related_to_rel IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.score)",
    ]
    
    success_count = 0
    for idx_query in indexes:
        try:
            session.run(idx_query)
            print(f"  ✓ {idx_query.split('ON')[0].strip()}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Error creating index: {str(e)}")
    
    print(f"[INDEXES] {success_count}/{len(indexes)} indexes created successfully\n")
    
    return success_count == len(indexes)


def get_index_stats(session):
    """
    Retrieve statistics about existing indexes
    Useful for monitoring database health
    """
    try:
        result = session.run("""
            CALL db.indexes()
            YIELD name, state, type, properties
            RETURN name, state, type, properties
        """)
        
        stats = []
        for record in result:
            stats.append({
                "name": record["name"],
                "state": record["state"],
                "type": record["type"],
                "properties": record["properties"]
            })
        
        return stats
    except:
        return []


def verify_indexes(session):
    """
    Verify all critical indexes are in place
    Returns True if all indexes exist and are valid
    """
    critical_indexes = [
        "case_id_index",
        "entity_value_index",
        "alert_type_index",
        "related_to_rel"
    ]
    
    try:
        stats = get_index_stats(session)
        index_names = [s["name"] for s in stats]
        
        missing = [idx for idx in critical_indexes if idx not in index_names]
        
        if missing:
            print(f"[WARNING] Missing critical indexes: {missing}")
            return False
        
        print("[INDEXES] All critical indexes verified ✓")
        return True
    except:
        return False
