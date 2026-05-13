"""
Comprehensive System Logging & Audit Trail
Maintains detailed execution logs for all operations and compliance
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional
import os


class GraphLogger:
    """Centralized logging for graph operations"""
    
    def __init__(self, log_dir="Graph_engine/logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, f"graph_operations_{datetime.now().strftime('%Y%m%d')}.log")
        self.audit_file = os.path.join(log_dir, f"audit_trail_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Create log directory if needed
        os.makedirs(log_dir, exist_ok=True)
    
    def log_case_processing(self, case_id: str, risk_score: int, entity_count: int, status: str = "success"):
        """Log case ingestion"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "CASE_PROCESSING",
            "case_id": case_id,
            "risk_score": risk_score,
            "entity_count": entity_count,
            "status": status
        }
        self._write_log(self.log_file, log_entry)
        print(f"[LOG] {log_entry['operation']}: {case_id} ({entity_count} entities, score: {risk_score})")
    
    def log_entity_creation(self, entity_type: str, entity_value: str, case_id: str):
        """Log entity creation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "ENTITY_CREATION",
            "entity_type": entity_type,
            "entity_value": entity_value,
            "case_id": case_id
        }
        self._write_log(self.log_file, log_entry)
    
    def log_alert_triggered(self, alert_type: str, entity_value: str, case_id: str, severity: int):
        """Log alert triggering"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "ALERT_TRIGGERED",
            "alert_type": alert_type,
            "entity_value": entity_value,
            "case_id": case_id,
            "severity": severity
        }
        self._write_log(self.log_file, log_entry)
        self._write_audit(log_entry)
        print(f"[ALERT] {alert_type}: {entity_value} (severity: {severity})")
    
    def log_case_linking(self, case1_id: str, case2_id: str, similarity_score: float):
        """Log case linking discovery"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "CASE_LINKING",
            "case1": case1_id,
            "case2": case2_id,
            "similarity_score": similarity_score
        }
        self._write_log(self.log_file, log_entry)
        print(f"[LINKING] {case1_id} → {case2_id} (similarity: {similarity_score:.2f})")
    
    def log_cluster_detection(self, cluster_size: int, threat_level: str, member_cases: list):
        """Log fraud ring detection"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "CLUSTER_DETECTION",
            "cluster_size": cluster_size,
            "threat_level": threat_level,
            "member_cases": member_cases
        }
        self._write_log(self.log_file, log_entry)
        self._write_audit(log_entry)
        print(f"[CLUSTER] Detected {threat_level} ring with {cluster_size} cases")
    
    def log_query_execution(self, query_type: str, execution_time_ms: float, result_count: int):
        """Log query execution"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "QUERY_EXECUTION",
            "query_type": query_type,
            "execution_time_ms": execution_time_ms,
            "result_count": result_count
        }
        self._write_log(self.log_file, log_entry)
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict] = None):
        """Log system errors"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "ERROR",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        self._write_log(self.log_file, log_entry)
        self._write_audit(log_entry)
        print(f"[ERROR] {error_type}: {error_message}")
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Log performance metrics"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": "PERFORMANCE_METRIC",
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        }
        self._write_log(self.log_file, log_entry)
    
    def _write_log(self, filepath: str, entry: Dict[str, Any]):
        """Write log entry to file"""
        try:
            with open(filepath, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"[LOG_ERROR] Failed to write log: {str(e)}")
    
    def _write_audit(self, entry: Dict[str, Any]):
        """Write to audit trail (compliance)"""
        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"[AUDIT_ERROR] Failed to write audit: {str(e)}")
    
    def get_recent_logs(self, operation_type: Optional[str] = None, limit: int = 100):
        """Retrieve recent logs"""
        if not os.path.exists(self.log_file):
            return []
        
        logs = []
        with open(self.log_file, 'r') as f:
            for line in f.readlines()[-limit:]:
                try:
                    entry = json.loads(line)
                    if operation_type is None or entry.get("operation") == operation_type:
                        logs.append(entry)
                except:
                    pass
        
        return logs
    
    def get_audit_trail(self, limit: int = 100):
        """Retrieve audit trail"""
        if not os.path.exists(self.audit_file):
            return []
        
        entries = []
        with open(self.audit_file, 'r') as f:
            for line in f.readlines()[-limit:]:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
        
        return entries
    
    def summarize_logs(self, hours: int = 24):
        """Summarize logs from last N hours"""
        logs = self.get_recent_logs()
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        recent_logs = []
        for log in logs:
            try:
                log_time = datetime.fromisoformat(log["timestamp"]).timestamp()
                if log_time >= cutoff:
                    recent_logs.append(log)
            except:
                pass
        
        # Aggregate by operation type
        summary = {}
        for log in recent_logs:
            op_type = log.get("operation", "UNKNOWN")
            if op_type not in summary:
                summary[op_type] = {"count": 0, "entries": []}
            summary[op_type]["count"] += 1
            summary[op_type]["entries"].append(log)
        
        return {
            "time_period_hours": hours,
            "total_operations": len(recent_logs),
            "operations_by_type": summary,
            "start_time": datetime.fromtimestamp(cutoff).isoformat(),
            "end_time": datetime.now().isoformat()
        }


# Global logger instance
_logger = None


def get_logger():
    """Get or create global logger"""
    global _logger
    if _logger is None:
        _logger = GraphLogger()
    return _logger


def log_case_processing(case_id: str, risk_score: int, entity_count: int, status: str = "success"):
    """Convenience function to log case processing"""
    get_logger().log_case_processing(case_id, risk_score, entity_count, status)


def log_alert_triggered(alert_type: str, entity_value: str, case_id: str, severity: int):
    """Convenience function to log alerts"""
    get_logger().log_alert_triggered(alert_type, entity_value, case_id, severity)


def log_case_linking(case1_id: str, case2_id: str, similarity_score: float):
    """Convenience function to log case linking"""
    get_logger().log_case_linking(case1_id, case2_id, similarity_score)


def log_cluster_detection(cluster_size: int, threat_level: str, member_cases: list):
    """Convenience function to log cluster detection"""
    get_logger().log_cluster_detection(cluster_size, threat_level, member_cases)


def log_error(error_type: str, error_message: str, context: Optional[Dict] = None):
    """Convenience function to log errors"""
    get_logger().log_error(error_type, error_message, context)
