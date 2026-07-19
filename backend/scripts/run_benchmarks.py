import os
import time
import json
import requests

API_URL = "http://localhost:8000/api/query"

# 10 Expert Benchmark Questions mapping to our synthetic dataset
BENCHMARK_SET = [
    {
        "query": "What is the correct torque spec for Pump P-201 coupling bolts?",
        "expected_entity": "95",
        "category": "conflict_detection"
    },
    {
        "query": "What is the lockout sequence for P-201 according to the 2024 SOP?",
        "expected_entity": "step b",
        "category": "procedural"
    },
    {
        "query": "Which asset has a bearing replacement interval of 12,000 hours?",
        "expected_entity": "p-202",
        "category": "entity_extraction"
    },
    {
        "query": "What is the inner race frequency for the crude oil transfer pump?",
        "expected_entity": "103",
        "category": "physics_telemetry"
    },
    {
        "query": "Who reported the BRG-WEAR failure on P-202?",
        "expected_entity": "sharma",
        "category": "work_order_history"
    },
    {
        "query": "What is the maximum allowed vibration for Pump P-201 before it hits ISO Zone C?",
        "expected_entity": "7.1",
        "category": "compliance"
    },
    {
        "query": "What is the root cause for the SEAL-FAIL incident on C-101?",
        "expected_entity": "dry running",
        "category": "rca_analysis"
    },
    {
        "query": "Which pump was serviced for cavitation by R. Verma?",
        "expected_entity": "p-202",
        "category": "work_order_history"
    },
    {
        "query": "What safety equipment is required for C-101 maintenance according to OISD-105?",
        "expected_entity": "ppe",
        "category": "safety_compliance"
    },
    {
        "query": "What was the previous torque spec for P-201 before the 2024 update?",
        "expected_entity": "80",
        "category": "conflict_detection"
    }
]

def run_benchmark():
    print("Starting TeevrGati Benchmark Run...")
    results = {
        "timestamp": time.time(),
        "total_queries": len(BENCHMARK_SET),
        "successful_queries": 0,
        "average_time_ms": 0,
        "entity_extraction_accuracy": 0.0,
        "details": []
    }

    total_time = 0
    correct_entities = 0

    for i, item in enumerate(BENCHMARK_SET):
        query = item["query"]
        expected = item["expected_entity"].lower()
        
        print(f"[{i+1}/{len(BENCHMARK_SET)}] Query: {query}")
        
        start_time = time.time()
        try:
            headers = {"Authorization": "Bearer dev-key"}
            resp = requests.post(API_URL, json={"query": query}, headers=headers, timeout=30)
            elapsed = (time.time() - start_time) * 1000
            total_time += elapsed
            
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("response", "").lower()
                
                # Check if expected entity is in answer
                is_correct = expected in answer
                if is_correct:
                    correct_entities += 1
                
                results["details"].append({
                    "query": query,
                    "expected": expected,
                    "is_correct": is_correct,
                    "time_ms": elapsed,
                    "error": None
                })
                print(f"  -> Time: {elapsed:.0f}ms | Correct: {is_correct}")
            else:
                print(f"  -> Failed: HTTP {resp.status_code}")
                results["details"].append({
                    "query": query,
                    "expected": expected,
                    "is_correct": False,
                    "time_ms": elapsed,
                    "error": f"HTTP {resp.status_code}"
                })
        except Exception as e:
            print(f"  -> Error: {e}")
            results["details"].append({
                "query": query,
                "expected": expected,
                "is_correct": False,
                "time_ms": 0,
                "error": str(e)
            })
            
        time.sleep(1) # Small delay to not rate limit LLM too hard

    results["average_time_ms"] = total_time / len(BENCHMARK_SET)
    results["entity_extraction_accuracy"] = (correct_entities / len(BENCHMARK_SET)) * 100
    results["successful_queries"] = correct_entities
    
    print("\n--- Benchmark Complete ---")
    print(f"Accuracy: {results['entity_extraction_accuracy']}%")
    print(f"Avg Time: {results['average_time_ms']:.0f}ms")
    
    # Save results
    os.makedirs("backend/data", exist_ok=True)
    with open("backend/data/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved to backend/data/benchmark_results.json")

if __name__ == "__main__":
    run_benchmark()
