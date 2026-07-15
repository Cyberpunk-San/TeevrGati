from backend.kg.knowledge_graph import KnowledgeGraph
from backend.rag.vector_index import VectorIndex
from backend.kg.entity_extractor import EntityExtractor
import re
import os

class UnifiedBrain:
    """
    The "Historian" module.
    Answers questions using Knowledge Graph + RAG.
    """
    
    def __init__(self, kg_path: str = None, db_path: str = None):
        self.kg_path = kg_path or os.getenv('TEEVRGATI_KG_PATH', "backend/data/kg/graph.json")
        self.kg = KnowledgeGraph()
        self.vector = VectorIndex(persist_directory=db_path or os.getenv('TEEVRGATI_CHROMA_DB_PATH', "backend/data/chroma_db"))
        self.extractor = EntityExtractor()
        
        # Try to load existing graph
        if os.path.exists(self.kg_path):
            try:
                self.kg.load(self.kg_path)
                print(f"[SUCCESS] Loaded existing knowledge graph from {self.kg_path}")
            except Exception as e:
                print(f"[WARNING] Failed to load existing graph from {self.kg_path}: {e}. Starting fresh.")
        else:
            print("[WARNING] No existing graph found—starting fresh")
    
    def ingest_document(self, parse_result: dict) -> str:
        """Add a document to both KG and RAG index"""
        doc_id = self.kg.add_document(parse_result)
        self.vector.add_document(doc_id, parse_result.get('pages', []), parse_result.get('metadata', {}))
        self.kg.save(self.kg_path)
        return doc_id
    
    def query(self, user_query: str) -> dict:
        """
        Answer a user question using both KG and RAG.
        Returns structured results for the orchestrator.
        """
        result = {
            'query': user_query,
            'kg_results': None,
            'rag_results': None,
            'entities_found': [],
            'confidence': 0.0,
            'sources': []
        }
        
        # Step 1: Extract entities from the query
        entities = self.extractor.extract_all(user_query)
        result['entities_found'] = entities
        
        # Step 2: If equipment mentioned, query the KG
        equipment_tags = [eq['tag'] for eq in entities.get('equipment', [])]
        kg_results = {}
        
        for tag in equipment_tags:
            kg_result = self.kg.query_multi_hop(tag, hops=3)
            if kg_result and 'error' not in kg_result:
                kg_results[tag] = kg_result
                result['sources'].extend(kg_result.get('documents', []))
                result['sources'].extend(kg_result.get('procedures', []))
                result['sources'].extend(kg_result.get('incidents', []))
        
        result['kg_results'] = kg_results if kg_results else None
        
        # Step 3: Always run RAG for context
        rag_context = self.vector.query_with_context(user_query, top_k=5)
        result['rag_results'] = rag_context
        result['sources'].extend(rag_context.get('results', []))
        
        # Step 4: Calculate confidence based on source richness
        source_count = len(result['sources'])
        thresh_high = int(os.getenv('TEEVRGATI_RAG_SOURCE_THRESH_HIGH', '10'))
        thresh_med = int(os.getenv('TEEVRGATI_RAG_SOURCE_THRESH_MED', '5'))
        thresh_low = int(os.getenv('TEEVRGATI_RAG_SOURCE_THRESH_LOW', '2'))
        
        conf_high = float(os.getenv('TEEVRGATI_RAG_CONF_HIGH', '0.9'))
        conf_med = float(os.getenv('TEEVRGATI_RAG_CONF_MED', '0.7'))
        conf_low = float(os.getenv('TEEVRGATI_RAG_CONF_LOW', '0.5'))
        conf_default = float(os.getenv('TEEVRGATI_RAG_CONF_DEFAULT', '0.3'))
        
        if source_count > thresh_high:
            result['confidence'] = conf_high
        elif source_count > thresh_med:
            result['confidence'] = conf_med
        elif source_count > thresh_low:
            result['confidence'] = conf_low
        else:
            result['confidence'] = conf_default

        
        return result
    
    def get_equipment_context(self, equipment_tag: str) -> dict:
        """Specialized query for a single piece of equipment"""
        return self.kg.query_multi_hop(equipment_tag, hops=3)
    
    def save(self):
        """Save the KG state"""
        self.kg.save(self.kg_path)
