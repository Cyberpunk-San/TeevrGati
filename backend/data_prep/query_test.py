import os
import sys

# Ensure project root workspace is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.brain.unified_brain import UnifiedBrain

def test_query():
    brain = UnifiedBrain()
    
    query = "Tell me about the AI4I 2020 Predictive Maintenance Dataset"
    print(f"Executing Query: '{query}'\n")
    
    result = brain.query(query)
    print(f"Confidence Score: {result.get('confidence'):.1%}")
    print(f"Entities Found: {result.get('entities_found')}\n")
    
    rag_results = result.get('rag_results', {})
    results_list = rag_results.get('results', [])
    
    if results_list:
        print(f"Top Semantic Match retrieved from RAG index:")
        print("-" * 50)
        print(results_list[0])
        print("-" * 50)
    else:
        print("[WARNING] No semantic matches found in RAG index.")

if __name__ == "__main__":
    test_query()
