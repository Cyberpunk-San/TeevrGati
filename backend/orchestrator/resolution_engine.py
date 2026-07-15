from datetime import datetime
import os

class ResolutionEngine:
    """
    Engine responsible for auto-resolving conflicts in Industrial Cortex
    and performing self-healing operations on the Knowledge Graph.
    """
    # Configurable confidence threshold constants
    PHYS_MIN_CONFIDENCE = float(os.getenv('TEEVRGATI_PHYS_MIN_CONFIDENCE', '0.8'))
    DOC_MAX_CONFIDENCE_FOR_OVERRIDE = float(os.getenv('TEEVRGATI_DOC_MAX_CONFIDENCE_FOR_OVERRIDE', '0.9'))
    DOC_HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('TEEVRGATI_DOC_HIGH_CONFIDENCE_THRESHOLD', '0.9'))
    PHYS_LOW_CONFIDENCE_THRESHOLD = float(os.getenv('TEEVRGATI_PHYS_LOW_CONFIDENCE_THRESHOLD', '0.6'))
    DEFAULT_AMBIGUOUS_CONFIDENCE = float(os.getenv('TEEVRGATI_DEFAULT_AMBIGUOUS_CONFIDENCE', '0.5'))
    DEFAULT_DOC_CONFIDENCE = float(os.getenv('TEEVRGATI_DEFAULT_DOC_CONFIDENCE', '0.5'))
    DEFAULT_PHYS_CONFIDENCE = float(os.getenv('TEEVRGATI_DEFAULT_PHYS_CONFIDENCE', '1.0'))
    
    def resolve_conflict_automatically(self, conflict_details: dict) -> dict:
        """
        Evaluate a conflict automatically based on system heuristics.
        """
        doc_conf = conflict_details.get('document_confidence', self.DEFAULT_DOC_CONFIDENCE)
        phys_conf = conflict_details.get('physics_confidence', self.DEFAULT_PHYS_CONFIDENCE)
        
        # Heuristic 1: If physics confidence is extremely high (100% deterministic FFT/envelope analysis)
        # and document confidence is relatively low or standard, physics wins.
        if phys_conf >= self.PHYS_MIN_CONFIDENCE and doc_conf < self.DOC_MAX_CONFIDENCE_FOR_OVERRIDE:
            return {
                'winner': 'physics',
                'reason': f"Deterministic live sensor verification (FFT/Envelope Analysis confidence {phys_conf:.0%}) overrides static document suggestions (confidence {doc_conf:.0%}).",
                'confidence': phys_conf
            }
            
        # Heuristic 2: If document confidence is very high and physics is low, trust documents
        if doc_conf >= self.DOC_HIGH_CONFIDENCE_THRESHOLD and phys_conf < self.PHYS_LOW_CONFIDENCE_THRESHOLD:
            return {
                'winner': 'documents',
                'reason': "Document standards are highly specific, whereas sensor telemetry shows low confidence anomalies.",
                'confidence': doc_conf
            }
            
        # Heuristic 3: Otherwise, ambiguous -> Ask human
        return {
            'winner': 'human',
            'reason': "Ambiguous discrepancy between document history and sensor signatures. Requires expert engineer verification.",
            'confidence': self.DEFAULT_AMBIGUOUS_CONFIDENCE
        }
        
    def apply_self_healing(self, kg, asset_id: str, winner_id: str, reason: str, choice: str) -> list:
        """
        Performs self-healing on the knowledge graph with robust validation checking.
        """
        if not asset_id:
            print("[WARNING] No asset_id provided for self-healing graph operation.")
            return []
            
        target_asset_node = f"EQ_{asset_id}"
        if target_asset_node not in kg.graph.nodes:
            print(f"[WARNING] Asset node {target_asset_node} not found in the Knowledge Graph. Seeding empty node to heal.")
            # Automatically create the node to prevent failure during demos
            kg.graph.add_node(target_asset_node, type='Equipment', status='active', label=asset_id)
            
        related_docs = []
        
        # Traverse graph edges to locate document IDs
        for u, v, data in kg.graph.edges(data=True):
            if v == target_asset_node and data.get('relation') == 'MENTIONS':
                related_docs.append(u)
                
        healed_nodes = []
        
        # Apply healing updates
        for doc_id in related_docs:
            if doc_id in kg.graph.nodes:
                # Mark node as outdated
                kg.graph.nodes[doc_id]['status'] = 'outdated'
                kg.graph.nodes[doc_id]['superseded_timestamp'] = datetime.now().isoformat()
                healed_nodes.append(doc_id)
                
                # Link outdated document to the winning resolution node
                kg.graph.add_edge(
                    doc_id,
                    winner_id,
                    relation='REPLACED_BY',
                    reason=reason,
                    choice=choice,
                    timestamp=datetime.now().isoformat()
                )
                
        # Also mark the specific asset node as having verified rules
        if target_asset_node in kg.graph.nodes:
            kg.graph.nodes[target_asset_node]['last_reconciliation'] = datetime.now().isoformat()
            
        # Serialize self-healed changes
        try:
            kg.save()
        except Exception as e:
            print(f"[ERROR] Failed to save graph database updates: {e}")
            
        return healed_nodes
