import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
import hashlib
import json
import os
from typing import Optional, Dict, Any, List, Union

class VectorIndex:
    """
    Handles embedding and retrieval of document chunks.
    """
    
    def __init__(self, persist_directory: str = "backend/data/chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use configurable embedding model
        embedding_model_name = os.getenv(
            "EMBEDDING_MODEL",
            "all-MiniLM-L6-v2"
        )
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="industrial_docs",
            embedding_function=self.embedding_model
        )
        
        # Initialize text splitter for better chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function=len,
        )
    
    def chunk_document(self, pages: list, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> list:
        """
        Split document into overlapping chunks for RAG using recursive character splitting.
        """
        full_text = " ".join([p.get('text', '') for p in pages])
        
        if not full_text.strip():
            return []
        
        # Use custom chunk size if provided, otherwise use default
        if chunk_size or overlap:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size or 500,
                chunk_overlap=overlap or 100,
                separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
                length_function=len,
            )
            chunks_text = splitter.split_text(full_text)
        else:
            chunks_text = self.text_splitter.split_text(full_text)
        
        # Format chunks with metadata
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            if chunk_text.strip():
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': hashlib.md5(chunk_text.encode()).hexdigest()[:8],
                    'word_count': len(chunk_text.split()),
                    'chunk_index': i,
                    'total_chunks': len(chunks_text)
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
        """Add document chunks to the vector index using upsert for duplicate protection"""
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
                'chunk_index': chunk['chunk_index'],
                'total_chunks': chunk['total_chunks'],
                **base_metadata
            }
            for chunk in chunks
        ]
        
        try:
            # Use upsert to avoid duplicates
            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            print(f"[SUCCESS] Added/Updated {len(chunks)} chunks from {document_id}")
        except Exception as e:
            print(f"[ERROR] Failed to add document to index: {e}")
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the index for relevant chunks with optional metadata filtering.
        
        Args:
            query: The search query
            top_k: Number of results to return
            where: Optional metadata filter (e.g., {"asset": "P-201"})
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where
            )
            
            # Format results with similarity scores
            formatted_results = []
            if results['ids'] and results['documents']:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results.get('distances') else None
                    similarity = 1 - distance if distance is not None else None
                    
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': distance,
                        'similarity': similarity
                    })
            
            return formatted_results
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []
    
    def query_with_context(
        self, 
        query: str, 
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Search and return both raw chunks and the full context with optional filtering.
        """
        results = self.search(query, top_k, where)
        
        # Combine chunks into one context
        context = "\n\n".join([r['text'] for r in results])
        
        # Calculate average similarity if results exist
        avg_similarity = None
        if results:
            similarities = [r.get('similarity') for r in results if r.get('similarity') is not None]
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
        
        return {
            'results': results,
            'context': context,
            'source_count': len(results),
            'query': query,
            'avg_similarity': avg_similarity
        }
    
    def delete_document(self, document_id: str):
        """Delete all chunks for a specific document"""
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"[SUCCESS] Deleted {len(results['ids'])} chunks for {document_id}")
            else:
                print(f"[INFO] No chunks found for {document_id}")
        except Exception as e:
            print(f"[ERROR] Failed to delete document: {e}")
    
    def get_stats(self) -> dict:
        """Get statistics about the index"""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'persist_directory': self.persist_directory,
                'embedding_model': os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                'collection_name': "industrial_docs"
            }
        except Exception as e:
            print(f"[ERROR] Failed to get stats: {e}")
            return {}
    
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
        print("[SUCCESS] Index reset")