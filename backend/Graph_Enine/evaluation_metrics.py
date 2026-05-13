"""
Evaluation Metrics & System Measurement
IEEE-compliant evaluation framework for research publications
"""

from datetime import datetime
from typing import Dict, List, Optional


class SystemMetrics:
    """Comprehensive system metrics for evaluation"""
    
    def __init__(self, tx):
        self.tx = tx
    
    # ─────────────────────────────────────────────────────────────────────────
    # GRAPH STATISTICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_graph_statistics(self) -> Dict:
        """Get comprehensive graph statistics"""
        
        # Count nodes
        case_count_result = self.tx.run("MATCH (c:Case) RETURN COUNT(c) AS count")
        case_count = case_count_result.single()["count"]
        
        entity_count_result = self.tx.run("MATCH (e) WHERE labels(e) <> ['Case', 'Alert'] RETURN COUNT(e) AS count")
        entity_count = entity_count_result.single()["count"]
        
        alert_count_result = self.tx.run("MATCH (a:Alert) RETURN COUNT(a) AS count")
        alert_count = alert_count_result.single()["count"]
        
        # Count relationships
        involved_in_result = self.tx.run("MATCH ()-[r:INVOLVED_IN]->() RETURN COUNT(r) AS count")
        involved_in_count = involved_in_result.single()["count"]
        
        connected_to_result = self.tx.run("MATCH ()-[r:CONNECTED_TO]->() RETURN COUNT(r) AS count")
        connected_to_count = connected_to_result.single()["count"]
        
        related_to_result = self.tx.run("MATCH ()-[r:RELATED_TO]->() RETURN COUNT(r) AS count")
        related_to_count = related_to_result.single()["count"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                "cases": case_count,
                "entities": entity_count,
                "alerts": alert_count,
                "total": case_count + entity_count + alert_count
            },
            "relationships": {
                "involved_in": involved_in_count,
                "connected_to": connected_to_count,
                "related_to": related_to_count,
                "total": involved_in_count + connected_to_count + related_to_count
            },
            "graph_density": self._calculate_graph_density(case_count, entity_count, involved_in_count + connected_to_count)
        }
    
    def _calculate_graph_density(self, nodes: int, entities: int, edges: int) -> float:
        """Calculate graph density"""
        if nodes < 2:
            return 0
        max_edges = nodes * (nodes - 1) / 2
        return edges / max_edges if max_edges > 0 else 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # ALERT METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_alert_metrics(self) -> Dict:
        """Get alert system metrics"""
        
        # Total alerts by type
        alert_type_result = self.tx.run("""
            MATCH (a:Alert)
            RETURN a.type AS type, COUNT(a) AS count
            ORDER BY count DESC
        """)
        
        alerts_by_type = {}
        total_alerts = 0
        for record in alert_type_result:
            alert_type = record["type"]
            count = record["count"]
            alerts_by_type[alert_type] = count
            total_alerts += count
        
        # Critical alerts (severity >= 4)
        critical_result = self.tx.run("""
            MATCH (a:Alert)
            WHERE a.severity >= 4
            RETURN COUNT(a) AS count
        """)
        critical_count = critical_result.single()["count"]
        
        # High risk cases
        high_risk_result = self.tx.run("""
            MATCH (c:Case)
            WHERE c.risk_score >= 80
            RETURN COUNT(c) AS count
        """)
        high_risk_count = high_risk_result.single()["count"]
        
        return {
            "total_alerts": total_alerts,
            "alerts_by_type": alerts_by_type,
            "critical_alerts": critical_count,
            "high_risk_cases": high_risk_count,
            "alert_density": total_alerts / (high_risk_count + 1),  # Alerts per high-risk case
            "alert_effectiveness": {
                "critical_percentage": (critical_count / total_alerts * 100) if total_alerts > 0 else 0
            }
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # CASE LINKING METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_case_linking_metrics(self) -> Dict:
        """Get case linking quality metrics"""
        
        # Total links
        link_count_result = self.tx.run("""
            MATCH (c1:Case)-[r:RELATED_TO]-(c2:Case)
            RETURN COUNT(r) AS count
        """)
        link_count = link_count_result.single()["count"]
        
        # Link quality distribution
        link_quality_result = self.tx.run("""
            MATCH (c1:Case)-[r:RELATED_TO]-(c2:Case)
            RETURN 
                size([r WHERE r.score >= 0.7]) AS high_quality,
                size([r WHERE r.score >= 0.5 AND r.score < 0.7]) AS medium_quality,
                size([r WHERE r.score >= 0.3 AND r.score < 0.5]) AS low_quality,
                size([r WHERE r.score < 0.3]) AS very_low_quality
        """)
        
        quality = link_quality_result.single()
        
        # Average similarity
        avg_sim_result = self.tx.run("""
            MATCH (c1:Case)-[r:RELATED_TO]-(c2:Case)
            RETURN avg(r.score) AS avg_score, 
                   max(r.score) AS max_score, 
                   min(r.score) AS min_score
        """)
        
        sim_stats = avg_sim_result.single()
        
        # Cases with links
        linked_cases_result = self.tx.run("""
            MATCH (c:Case)-[r:RELATED_TO]-()
            RETURN COUNT(DISTINCT c) AS count
        """)
        linked_cases = linked_cases_result.single()["count"]
        
        # Total cases
        total_cases_result = self.tx.run("MATCH (c:Case) RETURN COUNT(c) AS count")
        total_cases = total_cases_result.single()["count"]
        
        return {
            "total_links": link_count,
            "cases_with_links": linked_cases,
            "cases_linked_percentage": (linked_cases / total_cases * 100) if total_cases > 0 else 0,
            "link_quality_distribution": {
                "high_quality_70plus": quality["high_quality"],
                "medium_quality_50_70": quality["medium_quality"],
                "low_quality_30_50": quality["low_quality"],
                "very_low_quality_below_30": quality["very_low_quality"]
            },
            "similarity_statistics": {
                "average_score": sim_stats["avg_score"] or 0,
                "max_score": sim_stats["max_score"] or 0,
                "min_score": sim_stats["min_score"] or 0
            }
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # FRAUD RING METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_fraud_ring_metrics(self) -> Dict:
        """Get fraud ring/clustering metrics"""
        
        # This requires importing fraud_ring_detector, so we'll keep it simple
        # Count cases connected through entities
        connected_result = self.tx.run("""
            MATCH (c1:Case)<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(c2:Case)
            WHERE c1 <> c2
            RETURN COUNT(DISTINCT c1) AS connected_count
        """)
        connected_count = connected_result.single()["connected_count"]
        
        # Total cases
        total_result = self.tx.run("MATCH (c:Case) RETURN COUNT(c) AS count")
        total_cases = total_result.single()["count"]
        
        # Multi-case entities
        multi_entity_result = self.tx.run("""
            MATCH (e)-[:INVOLVED_IN]->(c:Case)
            WITH e, COUNT(DISTINCT c) AS case_count
            WHERE case_count > 1
            RETURN COUNT(e) AS multi_entity_count
        """)
        multi_entity_count = multi_entity_result.single()["multi_entity_count"]
        
        return {
            "cases_in_clusters": connected_count,
            "isolated_cases": total_cases - connected_count,
            "clustering_coefficient": (connected_count / total_cases) if total_cases > 0 else 0,
            "bridge_entities": multi_entity_count,
            "total_cases": total_cases,
            "network_structure": {
                "clustered_percentage": (connected_count / total_cases * 100) if total_cases > 0 else 0,
                "isolated_percentage": ((total_cases - connected_count) / total_cases * 100) if total_cases > 0 else 0
            }
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # ENTITY METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_entity_metrics(self) -> Dict:
        """Get entity-level metrics"""
        
        # Entity counts by type
        entity_type_result = self.tx.run("""
            MATCH (e)
            WHERE labels(e) <> ['Case', 'Alert']
            RETURN labels(e)[0] AS type, COUNT(e) AS count
            ORDER BY count DESC
        """)
        
        entity_counts = {}
        for record in entity_type_result:
            entity_counts[record["type"]] = record["count"]
        
        # Reused entities (appear in 2+ cases)
        reused_result = self.tx.run("""
            MATCH (e)-[:INVOLVED_IN]->(c:Case)
            WITH e, COUNT(DISTINCT c) AS case_count
            WHERE case_count >= 2
            RETURN COUNT(e) AS reused_count
        """)
        reused_count = reused_result.single()["reused_count"]
        
        # Total entities
        total_entities = sum(entity_counts.values())
        
        return {
            "entity_counts_by_type": entity_counts,
            "total_entities": total_entities,
            "reused_entities": reused_count,
            "reuse_percentage": (reused_count / total_entities * 100) if total_entities > 0 else 0,
            "average_entities_per_case": self._get_avg_entities_per_case()
        }
    
    def _get_avg_entities_per_case(self) -> float:
        """Calculate average entities per case"""
        result = self.tx.run("""
            MATCH (c:Case)<-[:INVOLVED_IN]-(e)
            WITH c, COUNT(e) AS entity_count
            RETURN avg(entity_count) AS avg_count
        """)
        
        record = result.single()
        return record["avg_count"] or 0 if record else 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # RISK METRICS
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_risk_metrics(self) -> Dict:
        """Get risk-related metrics"""
        
        risk_result = self.tx.run("""
            MATCH (c:Case)
            RETURN 
                avg(c.risk_score) AS avg_risk,
                max(c.risk_score) AS max_risk,
                min(c.risk_score) AS min_risk,
                count(c) AS total_cases,
                size([c WHERE c.risk_score >= 80]) AS critical_cases,
                size([c WHERE c.risk_score >= 60 AND c.risk_score < 80]) AS high_cases,
                size([c WHERE c.risk_score >= 40 AND c.risk_score < 60]) AS medium_cases
        """)
        
        risk_stats = risk_result.single()
        
        return {
            "risk_score_statistics": {
                "average": risk_stats["avg_risk"] or 0,
                "maximum": risk_stats["max_risk"] or 0,
                "minimum": risk_stats["min_risk"] or 0
            },
            "case_distribution_by_risk": {
                "critical_80plus": risk_stats["critical_cases"],
                "high_60_79": risk_stats["high_cases"],
                "medium_40_59": risk_stats["medium_cases"],
                "low_below_40": risk_stats["total_cases"] - (risk_stats["critical_cases"] + risk_stats["high_cases"] + risk_stats["medium_cases"])
            },
            "critical_percentage": (risk_stats["critical_cases"] / risk_stats["total_cases"] * 100) if risk_stats["total_cases"] > 0 else 0
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # COMPREHENSIVE REPORT
    # ─────────────────────────────────────────────────────────────────────────
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive evaluation report"""
        
        return {
            "generated_at": datetime.now().isoformat(),
            "graph_statistics": self.get_graph_statistics(),
            "alert_metrics": self.get_alert_metrics(),
            "case_linking_metrics": self.get_case_linking_metrics(),
            "fraud_ring_metrics": self.get_fraud_ring_metrics(),
            "entity_metrics": self.get_entity_metrics(),
            "risk_metrics": self.get_risk_metrics(),
            "evaluation_summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict:
        """Generate evaluation summary"""
        graph_stats = self.get_graph_statistics()
        alert_metrics = self.get_alert_metrics()
        linking_metrics = self.get_case_linking_metrics()
        
        return {
            "total_nodes": graph_stats["nodes"]["total"],
            "total_relationships": graph_stats["relationships"]["total"],
            "total_alerts": alert_metrics["total_alerts"],
            "case_links_discovered": linking_metrics["total_links"],
            "avg_similarity_score": linking_metrics["similarity_statistics"]["average_score"],
            "system_readiness": "PRODUCTION_READY" if graph_stats["nodes"]["cases"] > 10 else "DEVELOPMENT"
        }


def evaluate_system(session) -> Dict:
    """Main evaluation function"""
    
    def run_metrics(tx):
        metrics = SystemMetrics(tx)
        return metrics.generate_comprehensive_report()
    
    return session.execute_read(run_metrics)
