#!/usr/bin/env python3
"""
Integration example: Person 1 + Person 2
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'person2_ai_engine'))

from person2_ai_engine.pipeline.intelligence_processor import IntelligenceProcessor

# Mock Person 1 output (normally comes from ingestion system)
person1_output = {
    "case_id": "CASE-20260502-AB12",
    "source_file": "sample.txt",
    "entities": {
        "wallets": ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"],
        "emails": ["john@example.com"],
        "phones": ["555-123-4567"],
        "urls": ["https://fake-site.com"],
        "names": ["John Doe"]
    },
    "raw_text": "Invest 5000 now and get 20000 return immediately",
    "timestamp": "2026-05-02T10:30:00Z",
    "hash": "abc123def456"
}

def integrate_person1_person2(person1_json: dict) -> dict:
    """
    Integration function that takes Person 1 output and adds Person 2 intelligence
    """
    processor = IntelligenceProcessor()
    enhanced_output = processor.process_intelligence(person1_json)
    return enhanced_output

if __name__ == "__main__":
    # Process through Person 2
    final_output = integrate_person1_person2(person1_output)

    print("🎯 FINAL ENHANCED OUTPUT:")
    print(f"Case ID: {final_output['case_id']}")
    print(f"Intent: {final_output['intent']['labels'][0]} ({final_output['intent']['confidence']})")
    print(f"Risk Level: {final_output['risk_assessment']['level']} (Score: {final_output['risk_assessment']['score']})")
    print(f"Entity Insights: {len(final_output['entity_insights'])} entities analyzed")
    print(f"Embedding Dimension: {len(final_output['embedding'])}")
    print(f"Processing Time: {final_output['ai_metadata']['processing_time']}")

    # Save final output
    import json
    with open('final_output.json', 'w') as f:
        json.dump(final_output, f, indent=2)

    print("\n✅ Full output saved to final_output.json")