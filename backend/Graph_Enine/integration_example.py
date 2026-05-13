"""
Integration example: Module 1 → Module 2 → Graph Engine
Shows the complete data flow from evidence upload to graph ingestion
"""

import json
import requests
from pathlib import Path


def load_ai_output(filepath):
    """Load final JSON output from Module 2 (AI Intelligence Engine)"""
    with open(filepath, 'r') as f:
        return json.load(f)


def transform_for_graph(ai_output):
    """
    Transform Module 2 output into Graph Engine input format
    
    Module 2 output:
    {
        "case_id": "...",
        "risk_score": 100,
        "risk_level": "CRITICAL",
        "entities": {...},
        "intent_detection": {...},
        "entity_context": {...}
    }
    
    Graph Engine input:
    {
        "case_id": "...",
        "risk_score": 100,
        "entities": {...},
        "intent": "investment_scam",
        "intent_confidence": 0.95
    }
    """
    graph_input = {
        "case_id": ai_output.get("case_id"),
        "risk_score": ai_output.get("risk_score", 0),
        "entities": ai_output.get("entities", {}),
        "intent": ai_output.get("intent_detection", {}).get("detected_scam_type", None),
        "intent_confidence": ai_output.get("intent_detection", {}).get("confidence", 0)
    }
    return graph_input


def send_to_graph_engine(graph_data, graph_url="http://localhost:8001"):
    """
    Send transformed data to Graph Engine for ingestion
    
    Args:
        graph_data: Dict with case_id, risk_score, entities, etc.
        graph_url: Base URL of Graph Engine API
    
    Returns:
        Response JSON
    """
    endpoint = f"{graph_url}/graph/process"
    
    try:
        response = requests.post(endpoint, json=graph_data, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to Graph Engine at {graph_url}")
        print("  Make sure to run: uvicorn Graph_engine.main:app --reload --port 8001")
        return None
    except Exception as e:
        print(f"✗ Error sending to Graph Engine: {e}")
        return None


def full_pipeline_example():
    """
    Complete pipeline example: Module 1 → Module 2 → Graph Engine
    """
    print("\n" + "="*70)
    print("CYBERCRIME FORENSICS PLATFORM - COMPLETE PIPELINE")
    print("="*70)
    
    # Step 1: Evidence Upload & Processing (Module 1)
    print("\n[STEP 1] Evidence Upload & Processing (Module 1)")
    print("-" * 70)
    print("Simulating: File upload → Parse → Extract entities → Hash")
    print("Example: TXT file with 'Invest 5000 now and get 20000 return'")
    
    # Step 2: AI Intelligence Processing (Module 2)
    print("\n[STEP 2] AI Intelligence Processing (Module 2)")
    print("-" * 70)
    print("Processing: Intent detection + Risk scoring + Embeddings")
    
    # Load sample output from Module 2
    sample_ai_output_file = Path("final_output.json")
    
    if sample_ai_output_file.exists():
        print(f"✓ Found {sample_ai_output_file}")
        ai_output = load_ai_output(sample_ai_output_file)
        
        print(f"  Case ID: {ai_output.get('case_id')}")
        print(f"  Risk Score: {ai_output.get('risk_score')}/100")
        print(f"  Intent: {ai_output.get('intent_detection', {}).get('detected_scam_type')}")
        print(f"  Entities Found: {len(ai_output.get('entities', {}))}")
        
    else:
        print(f"✗ {sample_ai_output_file} not found")
        print("  Creating example AI output...")
        
        ai_output = {
            "case_id": "CASE-20260502-EXAMPLE",
            "risk_score": 95,
            "risk_level": "CRITICAL",
            "text": "Invest 5000 now and get 20000 return immediately",
            "entities": {
                "wallets": ["0xABC123def456"],
                "emails": ["attacker@cryptobank.com"],
                "phones": ["9876543210"],
                "urls": ["https://crypto-invest-now.xyz"],
                "names": ["Raj Kumar"]
            },
            "intent_detection": {
                "detected_scam_type": "investment_scam",
                "confidence": 0.95,
                "keywords": ["invest", "profit", "return", "immediate"]
            },
            "entity_context": {
                "entities": [...],
                "risk_analysis": "Multiple urgency triggers + crypto investment terms"
            }
        }
    
    # Step 3: Graph Ingestion (Graph Engine - NEW)
    print("\n[STEP 3] Graph Ingestion (Graph Engine - NEW)")
    print("-" * 70)
    print("Transforming: AI output → Graph format")
    
    # Transform AI output for Graph Engine
    graph_data = transform_for_graph(ai_output)
    
    print(f"\n✓ Transformation complete:")
    print(f"  Case ID: {graph_data['case_id']}")
    print(f"  Risk Score: {graph_data['risk_score']}")
    print(f"  Entities: {len(graph_data['entities'].get('wallets', [])) + len(graph_data['entities'].get('emails', []))} total")
    print(f"  Intent: {graph_data['intent']}")
    print(f"  Confidence: {graph_data['intent_confidence']}")
    
    # Send to Graph Engine
    print(f"\nSending to Graph Engine...")
    
    result = send_to_graph_engine(graph_data)
    
    if result:
        print(f"✓ Graph Engine response: {result}")
        print(f"\n✓ Case successfully ingested!")
        print(f"  - Case node created in Neo4j")
        print(f"  - {result.get('entities_processed')} entities created and linked")
        print(f"  - Relationships established")
        print(f"  - Alerts triggered (if applicable)")
    else:
        print(f"\n✗ Failed to send to Graph Engine")
        print(f"  Graph data that would be sent:")
        print(json.dumps(graph_data, indent=2))
    
    # Step 4: Query Results
    print("\n[STEP 4] Query Graph Database")
    print("-" * 70)
    print("Neo4j queries to verify ingestion:")
    print("\n# View all nodes and relationships:")
    print("MATCH (n) RETURN n LIMIT 100")
    
    print("\n# View all alerts:")
    print("MATCH (a:Alert) RETURN a")
    
    print(f"\n# View case {graph_data['case_id']}:")
    print(f"MATCH (c:Case {{id: '{graph_data['case_id']}'}}) RETURN c")
    
    print("\n# View entities in case:")
    print(f"MATCH (e)-[:INVOLVED_IN]->(c:Case {{id: '{graph_data['case_id']}'}}) RETURN e")
    
    print("\n# View entity connections:")
    print(f"MATCH (e1)-[:CONNECTED_TO]->(e2) WHERE (e1)-[:INVOLVED_IN]->(c:Case {{id: '{graph_data['case_id']}'}}) RETURN e1, e2")
    
    print("\n" + "="*70)
    print("END OF PIPELINE")
    print("="*70 + "\n")


def batch_integration_example():
    """
    Batch processing example: Multiple cases from Module 2 → Graph Engine
    """
    print("\n" + "="*70)
    print("BATCH INTEGRATION EXAMPLE")
    print("="*70)
    
    # Create multiple AI outputs
    batch_ai_outputs = [
        {
            "case_id": f"CASE-20260502-BATCH-{i:03d}",
            "risk_score": 70 + (i * 5),
            "entities": {
                "wallets": [f"0xWALLET{i:02d}"],
                "emails": [f"attacker{i}@gmail.com"],
                "phones": [f"{8000000000 + i}"],
                "urls": [f"http://scam-site-{i}.com"],
                "names": [f"Scammer {i}"]
            },
            "intent_detection": {
                "detected_scam_type": ["phishing", "job_scam", "romance_scam"][i % 3],
                "confidence": 0.85 + (i * 0.01)
            }
        }
        for i in range(1, 4)
    ]
    
    print(f"\nProcessing {len(batch_ai_outputs)} cases...")
    
    # Transform all for Graph Engine
    graph_batch = [transform_for_graph(ai) for ai in batch_ai_outputs]
    
    # Send to batch endpoint
    endpoint = "http://localhost:8001/graph/batch-process"
    
    try:
        response = requests.post(endpoint, json=graph_batch, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"\n✓ Batch processing complete!")
        print(f"  Total: {result.get('total')} cases")
        print(f"  Status: {result.get('status')}")
        
        for case_result in result.get('results', []):
            print(f"  - {case_result['case_id']}: {case_result['status']}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"  Make sure Graph Engine is running on port 8001")


if __name__ == "__main__":
    print("\n" + "█"*70)
    print("INTEGRATION EXAMPLES - Full Cybercrime Forensics Pipeline")
    print("█"*70)
    
    # Run examples
    full_pipeline_example()
    
    print("\n\nTo run batch integration example, uncomment line below:")
    print("# batch_integration_example()")
    
    # batch_integration_example()
