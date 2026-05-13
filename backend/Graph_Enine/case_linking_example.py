"""
Case Linking Integration Example
Demonstrates the complete workflow for finding related cases
"""

import requests
import json
from pathlib import Path


def demonstrate_case_linking():
    """
    Complete demonstration of case linking workflow
    """
    
    base_url = "http://localhost:8001"
    
    print("\n" + "█" * 70)
    print("CASE LINKING DEMONSTRATION")
    print("█" * 70)
    
    # Step 1: Create multiple related cases
    print("\n" + "="*70)
    print("STEP 1: Ingest Multiple Related Cases")
    print("="*70)
    
    cases = [
        {
            "case_id": "CASE-INVESTMENT-001",
            "risk_score": 95,
            "entities": {
                "emails": ["attacker@cryptobank.com"],
                "wallets": ["0xABC123"],
                "phones": ["8800000001"],
                "urls": ["https://crypto-invest.xyz"],
                "names": ["Raj Kumar"]
            }
        },
        {
            "case_id": "CASE-INVESTMENT-002",
            "risk_score": 90,
            "entities": {
                "emails": ["attacker@cryptobank.com"],  # SHARED with CASE-001
                "wallets": ["0xDEF456"],
                "phones": ["8800000002"],
                "urls": ["https://crypto-invest.xyz"],  # SHARED
                "names": ["Priya Singh"]
            }
        },
        {
            "case_id": "CASE-INVESTMENT-003",
            "risk_score": 85,
            "entities": {
                "emails": ["attacker@cryptobank.com"],  # SHARED
                "wallets": ["0xGHI789"],
                "phones": ["8800000003"],
                "urls": ["https://crypto-profits.com"],
                "names": ["Amit Patel"]
            }
        },
        {
            "case_id": "CASE-PHISHING-001",
            "risk_score": 70,
            "entities": {
                "emails": ["phisher@fakebank.com"],  # DIFFERENT
                "urls": ["https://fake-bank.com"],  # DIFFERENT
                "phones": ["9900000001"],
                "names": ["Unknown"]
            }
        }
    ]
    
    print("\nIngesting 4 test cases...")
    print("- 3 investment scam cases (2 shared attributes)")
    print("- 1 phishing case (isolated)")
    
    for case in cases:
        try:
            response = requests.post(f"{base_url}/graph/process", json=case, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ {case['case_id']}")
                print(f"  Risk Score: {case['risk_score']}")
                print(f"  Entities: {result['entities_processed']}")
            else:
                print(f"\n✗ {case['case_id']}: {response.status_code}")
        except Exception as e:
            print(f"\n✗ {case['case_id']}: {e}")
    
    # Step 2: Query case links
    print("\n" + "="*70)
    print("STEP 2: Query Case Links")
    print("="*70)
    
    print("\nFinding related cases for CASE-INVESTMENT-001...")
    
    try:
        response = requests.get(
            f"{base_url}/graph/case-links/CASE-INVESTMENT-001?threshold=0.2",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Found {data['count']} related cases (threshold: {data['threshold']:.1%})")
            
            print("\nRelated Cases (sorted by similarity):")
            for case in data['related_cases']:
                print(f"\n  Case: {case['case_id']}")
                print(f"    Similarity: {case['similarity']:.1%}")
                print(f"    Shared Entities: {case['intersection']}")
                print(f"    Total Unique: {case['union']}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Connection error: {e}")
        print("Make sure Graph Engine is running on port 8001")
        print("Run: uvicorn Graph_engine.main:app --reload --port 8001")


def demonstrate_case_analysis():
    """
    Demonstrate comprehensive case network analysis
    """
    
    base_url = "http://localhost:8001"
    
    print("\n" + "="*70)
    print("STEP 3: Network Analysis")
    print("="*70)
    
    print("\nAnalyzing case network for CASE-INVESTMENT-001...")
    
    try:
        response = requests.get(
            f"{base_url}/graph/case-analysis/CASE-INVESTMENT-001",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'success':
                analysis = data['data']
                
                print(f"\n✓ Analysis Complete")
                print(f"\nCase Details:")
                print(f"  Case ID: {analysis['case_id']}")
                print(f"  Risk Score: {analysis['case_risk_score']}")
                
                print(f"\nNetwork Statistics:")
                print(f"  Related Cases: {analysis['related_count']}")
                print(f"  Avg Related Risk: {analysis['avg_related_risk']:.1f}")
                print(f"  Network Risk Level: {analysis['network_risk_level']}")
                
                print(f"\nRelated Cases:")
                for case in analysis['related_cases']:
                    print(f"\n  {case['case_id']}")
                    print(f"    Score: {case['score']:.1%}")
                    print(f"    Risk: {case['risk_score']}")
            else:
                print(f"✗ Case not found")
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")


def demonstrate_threshold_comparison():
    """
    Show how different thresholds affect results
    """
    
    base_url = "http://localhost:8001"
    
    print("\n" + "="*70)
    print("STEP 4: Threshold Comparison")
    print("="*70)
    
    thresholds = [0.1, 0.2, 0.3, 0.5]
    
    print("\nComparing different similarity thresholds for CASE-INVESTMENT-001...")
    
    for threshold in thresholds:
        try:
            response = requests.get(
                f"{base_url}/graph/case-links/CASE-INVESTMENT-001?threshold={threshold}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data['count']
                print(f"\n✓ Threshold {threshold:.1%}: {count} related cases")
                
                for case in data['related_cases'][:3]:  # Show first 3
                    print(f"    - {case['case_id']}: {case['similarity']:.1%}")
                
                if len(data['related_cases']) > 3:
                    print(f"    ... and {len(data['related_cases']) - 3} more")
        except Exception as e:
            print(f"✗ Error at threshold {threshold}: {e}")


def demonstrate_isolated_case():
    """
    Show behavior for isolated case (no related cases)
    """
    
    base_url = "http://localhost:8001"
    
    print("\n" + "="*70)
    print("STEP 5: Isolated Case Analysis")
    print("="*70)
    
    print("\nAnalyzing isolated case (CASE-PHISHING-001)...")
    print("This case has different entities, so should have no related cases")
    
    try:
        response = requests.get(
            f"{base_url}/graph/case-links/CASE-PHISHING-001?threshold=0.2",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['count'] == 0:
                print(f"\n✓ Correct: No related cases found")
                print(f"  This case uses different infrastructure:")
                print(f"    - Different attacker email")
                print(f"    - Different URL")
                print(f"    - Different phone")
            else:
                print(f"\n⚠ Found {data['count']} related cases")
                print("  (Unexpected - check entity data)")
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")


def demonstrate_api_usage():
    """
    Show raw API usage examples
    """
    
    print("\n" + "="*70)
    print("STEP 6: API Usage Reference")
    print("="*70)
    
    print("\n1. Query case links with default threshold:")
    print("   GET /graph/case-links/CASE-001")
    
    print("\n2. Query case links with custom threshold:")
    print("   GET /graph/case-links/CASE-001?threshold=0.5")
    
    print("\n3. Get case network analysis:")
    print("   GET /graph/case-analysis/CASE-001")
    
    print("\n4. Example Python code:")
    print("""
    import requests
    
    # Get related cases
    response = requests.get(
        "http://localhost:8001/graph/case-links/CASE-001?threshold=0.3"
    )
    data = response.json()
    
    print(f"Found {data['count']} related cases")
    for case in data['related_cases']:
        print(f"  {case['case_id']}: {case['similarity']:.1%}")
    """)
    
    print("\n5. Example cURL:")
    print("""
    # Get related cases
    curl "http://localhost:8001/graph/case-links/CASE-001?threshold=0.2"
    
    # Get analysis
    curl "http://localhost:8001/graph/case-analysis/CASE-001"
    """)


def show_expected_results():
    """
    Show what results should look like
    """
    
    print("\n" + "="*70)
    print("EXPECTED RESULTS")
    print("="*70)
    
    print("\nFor CASE-INVESTMENT-001 (threshold=0.2):")
    print("""
    {
      "status": "success",
      "case_id": "CASE-INVESTMENT-001",
      "threshold": 0.2,
      "count": 2,
      "related_cases": [
        {
          "case_id": "CASE-INVESTMENT-002",
          "similarity": 0.75,
          "intersection": 3,
          "union": 4
        },
        {
          "case_id": "CASE-INVESTMENT-003",
          "similarity": 0.67,
          "intersection": 3,
          "union": 4
        }
      ]
    }
    """)
    
    print("\nFor CASE-INVESTMENT-001 (threshold=0.5):")
    print("""
    {
      "status": "success",
      "case_id": "CASE-INVESTMENT-001",
      "threshold": 0.5,
      "count": 2,
      "related_cases": [
        {
          "case_id": "CASE-INVESTMENT-002",
          "similarity": 0.75,
          "intersection": 3,
          "union": 4
        },
        {
          "case_id": "CASE-INVESTMENT-003",
          "similarity": 0.67,
          "intersection": 3,
          "union": 4
        }
      ]
    }
    """)
    
    print("\nFor CASE-PHISHING-001 (threshold=0.2):")
    print("""
    {
      "status": "success",
      "case_id": "CASE-PHISHING-001",
      "threshold": 0.2,
      "count": 0,
      "related_cases": []
    }
    """)


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("CASE LINKING WORKFLOW DEMONSTRATION")
    print("█" * 70)
    
    print("\nThis script demonstrates the complete case linking workflow.")
    print("Before running, ensure:")
    print("  1. Neo4j instance is online")
    print("  2. Graph Engine server is running:")
    print("     uvicorn Graph_engine.main:app --reload --port 8001")
    
    input("\n Press Enter to start demonstration...")
    
    # Run demonstrations
    demonstrate_case_linking()
    demonstrate_case_analysis()
    demonstrate_threshold_comparison()
    demonstrate_isolated_case()
    
    # Show reference
    demonstrate_api_usage()
    show_expected_results()
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Query /graph/case-links/{case_id} for any case")
    print("  2. Experiment with different thresholds")
    print("  3. Use /graph/case-analysis for network insights")
    print("  4. Monitor Neo4j browser at https://console.neo4j.io")
    print("\n" + "="*70 + "\n")
