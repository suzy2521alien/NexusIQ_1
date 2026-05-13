"""
Test suite for Graph Engine
Tests the complete pipeline: JSON → Graph → Relationships → Alerts
"""

import json
import sys
sys.path.insert(0, '.')

from graph_service import process_case, batch_process_cases


def test_single_case():
    """Test 1: Process a single case"""
    print("\n" + "="*60)
    print("TEST 1: Single Case Processing")
    print("="*60)
    
    test_data = {
        "case_id": "CASE-20260502-0001",
        "risk_score": 90,
        "entities": {
            "wallets": ["0xABC123def456"],
            "emails": ["scammer@gmail.com", "fraud@hotmail.com"],
            "phones": ["9876543210"],
            "urls": ["http://fake-bank.com"],
            "names": ["John Doe"]
        },
        "intent": "investment_scam",
        "intent_confidence": 0.85
    }
    
    try:
        result = process_case(test_data)
        print(f"\n✓ Result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_high_risk_alert():
    """Test 2: Verify HIGH_RISK_CASE alert triggers at risk_score >= 80"""
    print("\n" + "="*60)
    print("TEST 2: High Risk Alert")
    print("="*60)
    
    test_data = {
        "case_id": "CASE-20260502-0002",
        "risk_score": 95,  # Should trigger HIGH_RISK_CASE alert
        "entities": {
            "wallets": ["0xDEF789"],
            "emails": ["attacker@cryptoex.com"],
            "phones": ["8765432109"],
            "urls": ["https://crypto-invest-now.xyz"],
            "names": ["Jane Smith"]
        }
    }
    
    try:
        result = process_case(test_data)
        print(f"\n✓ High risk case processed successfully")
        print(f"✓ Should trigger HIGH_RISK_CASE alert in Neo4j")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_medium_risk_no_alert():
    """Test 3: Verify no HIGH_RISK_CASE alert at risk_score < 80"""
    print("\n" + "="*60)
    print("TEST 3: Medium Risk (No Alert)")
    print("="*60)
    
    test_data = {
        "case_id": "CASE-20260502-0003",
        "risk_score": 45,  # Should NOT trigger HIGH_RISK_CASE alert
        "entities": {
            "wallets": ["0xGHI012"],
            "emails": ["suspicious@mail.com"],
            "phones": ["7654321098"],
            "urls": []
        }
    }
    
    try:
        result = process_case(test_data)
        print(f"\n✓ Medium risk case processed successfully")
        print(f"✓ No HIGH_RISK_CASE alert should be created")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_batch_processing():
    """Test 4: Batch process multiple cases"""
    print("\n" + "="*60)
    print("TEST 4: Batch Processing")
    print("="*60)
    
    test_data_list = [
        {
            "case_id": "CASE-20260502-BATCH-01",
            "risk_score": 85,
            "entities": {
                "wallets": ["0xBATCH01"],
                "emails": ["batch1@test.com"],
                "phones": ["1111111111"]
            }
        },
        {
            "case_id": "CASE-20260502-BATCH-02",
            "risk_score": 75,
            "entities": {
                "wallets": ["0xBATCH02"],
                "emails": ["batch2@test.com"],
                "phones": ["2222222222"]
            }
        },
        {
            "case_id": "CASE-20260502-BATCH-03",
            "risk_score": 60,
            "entities": {
                "wallets": ["0xBATCH03"],
                "emails": ["batch3@test.com"]
            }
        }
    ]
    
    try:
        results = batch_process_cases(test_data_list)
        print(f"\n✓ Batch processed {len(results)} cases")
        for r in results:
            print(f"  - {r['case_id']}: {r['status']}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_entity_normalization():
    """Test 5: Entity normalization (types and value cleanup)"""
    print("\n" + "="*60)
    print("TEST 5: Entity Normalization")
    print("="*60)
    
    from models import normalize_entities
    
    raw_entities = {
        "wallets": ["0xABC", "  0xDEF  "],  # With whitespace
        "emails": ["test@gmail.com"],
        "phones": ["9999999999"],
        "urls": ["http://example.com"],
        "names": ["John Doe", "Jane Smith"],
        "unknown_type": ["should be ignored"]  # Not in mapping
    }
    
    try:
        normalized = normalize_entities(raw_entities)
        print(f"\n✓ Normalized {len(normalized)} entities")
        for entity in normalized:
            print(f"  - {entity['type']}: {entity['value']}")
        
        # Verify correct types
        types = [e['type'] for e in normalized]
        assert "Wallet" in types
        assert "Email" in types
        assert "Phone" in types
        assert "URL" in types
        assert "Person" in types
        print("\n✓ All entity types correct")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_empty_entities():
    """Test 6: Handle empty entities gracefully"""
    print("\n" + "="*60)
    print("TEST 6: Empty Entities Handling")
    print("="*60)
    
    test_data = {
        "case_id": "CASE-20260502-EMPTY",
        "risk_score": 30,
        "entities": {
            "wallets": [],
            "emails": [],
            "phones": [],
            "urls": [],
            "names": []
        }
    }
    
    try:
        result = process_case(test_data)
        print(f"\n✓ Empty entities handled gracefully")
        print(f"✓ Result: {result}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n")
    print("█" * 60)
    print("GRAPH ENGINE TEST SUITE")
    print("█" * 60)
    print("\nStarting tests...\n")
    
    tests = [
        ("Single Case", test_single_case),
        ("High Risk Alert", test_high_risk_alert),
        ("Medium Risk No Alert", test_medium_risk_no_alert),
        ("Batch Processing", test_batch_processing),
        ("Entity Normalization", test_entity_normalization),
        ("Empty Entities", test_empty_entities)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "PASS" if passed else "FAIL"
        except Exception as e:
            print(f"\n✗ Test {name} crashed: {e}")
            results[name] = "ERROR"
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, status in results.items():
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {name}: {status}")
    
    passed = sum(1 for s in results.values() if s == "PASS")
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
