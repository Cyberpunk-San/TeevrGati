import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import hashlib
import json

class VectorIndex:
    """
    Handles embedding and retrieval of document chunks.
    """
    
    def __init__(self, persist_directory: str = "backend/data/chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a free, local embedding model
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="industrial_docs",
            embedding_function=self.embedding_model
        )
        
        # Also load sentence transformer for direct use
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def chunk_document(self, pages: list, chunk_size: int = 500, overlap: int = 100) -> list:
        """Split document into overlapping chunks for RAG"""
        chunks = []
        full_text = " ".join([p.get('text', '') for p in pages])
        
        # Simple sliding window
        words = full_text.split()
        if not words:
            return chunks
            
        step = max(1, chunk_size - overlap)
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append({
                    'text': chunk,
                    'chunk_id': hashlib.md5(chunk.encode()).hexdigest()[:8],
                    'word_count': len(chunk.split()),
                    'start_index': i
                })
        
        return chunks
    
    def _sanitize_metadata(self, metadata: dict) -> dict:
        """Sanitize metadata keys to conform to Chroma DB's support (str, int, float, bool)"""
        if not metadata:
            return {}
        sanitized = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, (list, dict)):
                sanitized[k] = json.dumps(v)
            elif v is None:
                sanitized[k] = ""
            else:
                sanitized[k] = str(v)
        return sanitized
    
    def add_document(self, document_id: str, pages: list, metadata: dict = None):
        """Add document chunks to the vector index"""
        chunks = self.chunk_document(pages)
        
        if not chunks:
            print(f"[WARNING] No text chunks extracted from {document_id}")
            return
        
        ids = [f"{document_id}_{chunk['chunk_id']}" for chunk in chunks]
        texts = [chunk['text'] for chunk in chunks]
        
        # Prepare metadata
        base_metadata = self._sanitize_metadata(metadata)
        metadatas = [
            {
                'document_id': document_id,
                'chunk_id': chunk['chunk_id'],
                'word_count': chunk['word_count'],
                'start_index': chunk['start_index'],
                **base_metadata
            }
            for chunk in chunks
        ]
        
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            print(f"[SUCCESS] Added {len(chunks)} chunks from {document_id}")
        except Exception as e:
            print(f"[ERROR] Failed to add document to index: {e}")
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Search the index for relevant chunks"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['documents']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            
            return formatted_results
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []
    
    def query_with_context(self, query: str, top_k: int = 5) -> dict:
        """Search and return both raw chunks and the full context"""
        results = self.search(query, top_k)
        
        # Combine chunks into one context
        context = "\n\n".join([r['text'] for r in results])
        
        return {
            'results': results,
            'context': context,
            'source_count': len(results)
        }
    
    def reset(self):
        """Reset the index (for testing)"""
        try:
            self.client.delete_collection("industrial_docs")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name="industrial_docs",
            embedding_function=self.embedding_model
        )
