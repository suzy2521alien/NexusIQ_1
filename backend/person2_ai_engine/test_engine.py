#!/usr/bin/env python3
"""
Testing script for Person 2 AI Engine
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from pipeline.intelligence_processor import IntelligenceProcessor
from utils.similarity import SimilarityFinder
import json

def test_intelligence_engine():
    # Sample ingestion outputs
    sample1 = {
        "case_id": "CASE-20260502-1234",
        "source_file": "chat1.txt",
        "entities": {
            "wallets": ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"],
            "emails": ["support@example.com"],
            "phones": ["5551234567"],
            "urls": ["https://fakeinvestment.com"],
            "names": ["John Doe"]
        },
        "raw_text": "Invest 5000 now and get 20000 return immediately. Send to wallet 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 or contact support@example.com",
        "timestamp": "2026-05-02T10:30:00Z",
        "hash": "abc123..."
    }

    sample2 = {
        "case_id": "CASE-20260502-5678",
        "source_file": "chat2.txt",
        "entities": {
            "wallets": [],
            "emails": ["love@romance.com"],
            "phones": ["8001234567"],
            "urls": [],
            "names": ["Sarah"]
        },
        "raw_text": "Hi darling, I need money urgently for my mother's surgery. Please send to my account.",
        "timestamp": "2026-05-02T11:00:00Z",
        "hash": "def456..."
    }

    # Initialize processor
    processor = IntelligenceProcessor()

    # Process samples
    result1 = processor.process_intelligence(sample1)
    result2 = processor.process_intelligence(sample2)

    print("=== Sample 1 Results ===")
    print(f"Intent: {result1['intent']}")
    print(f"Risk: {result1['risk_assessment']}")
    print(f"Embedding shape: {len(result1['embedding'])}")
    print(f"Entity insights: {len(result1['entity_insights'])}")
    print()

    print("=== Sample 2 Results ===")
    print(f"Intent: {result2['intent']}")
    print(f"Risk: {result2['risk_assessment']}")
    print(f"Embedding shape: {len(result2['embedding'])}")
    print(f"Entity insights: {len(result2['entity_insights'])}")
    print()

    # Test similarity
    stored_embeddings = {
        result1['case_id']: result1['embedding'],
        result2['case_id']: result2['embedding']
    }

    similarity_finder = SimilarityFinder()
    query = "Send money for investment returns"
    similar = similarity_finder.find_similar_cases(query, stored_embeddings, top_k=2)

    print("=== Similarity Test ===")
    print(f"Query: '{query}'")
    print("Similar cases:")
    for case_id, score in similar:
        print(f"  {case_id}: {score:.3f}")

    # Save sample output
    with open('sample_output.json', 'w') as f:
        json.dump(result1, f, indent=2)

    print("\nSample output saved to sample_output.json")

if __name__ == "__main__":
    test_intelligence_engine()