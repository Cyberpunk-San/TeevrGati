import networkx as nx
import json
from datetime import datetime
from backend.kg.entity_extractor import EntityExtractor

class KnowledgeGraph:
    """
    Uses NetworkX for simplicity (no Docker required).
    For Neo4j, swap the backend—NetworkX is fine for hackathon scale.
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.extractor = EntityExtractor()
        self.document_id_counter = 0
    
    def add_document(self, parse_result: dict) -> str:
        """
        Ingest a parsed document into the knowledge graph.
        """
        doc_id = parse_result['document_id']
        self.document_id_counter += 1
        
        # Add document node
        self.graph.add_node(
            doc_id,
            type='DOCUMENT',
            metadata=parse_result.get('metadata', {}),
            pages=len(parse_result.get('pages', [])),
            timestamp=datetime.now().isoformat()
        )
        
        # Extract entities from text
        if parse_result.get('pages'):
            entities = self.extractor.extract_from_document(parse_result['pages'])
            
            # Add equipment nodes
            for eq in entities.get('equipment', []):
                node_id = f"EQ-{eq['tag']}"
                self.graph.add_node(
                    node_id,
                    type='EQUIPMENT',
                    tag=eq['tag'],
                    confidence=eq['confidence'],
                    source=eq['source']
                )

                self.graph.add_edge(
                    doc_id,
                    node_id,
                    relation='MENTIONS',
                    timestamp=datetime.now().isoformat()
                )
            
            # Add regulation nodes
            for reg in entities.get('regulations', []):
                node_id = f"REG-{reg['reference'].replace(' ', '-')}"
                self.graph.add_node(
                    node_id,
                    type='REGULATION',
                    reference=reg['reference'],
                    confidence=reg['confidence']
                )
                self.graph.add_edge(
                    doc_id,
                    node_id,
                    relation='CITES',
                    timestamp=datetime.now().isoformat()
                )
            
            # Add person nodes
            for person in entities.get('persons', []):
                node_id = f"PERSON-{person['name'].replace(' ', '-')}"
                self.graph.add_node(
                    node_id,
                    type='PERSON',
                    name=person['name'],
                    confidence=person['confidence']
                )
                self.graph.add_edge(
                    doc_id,
                    node_id,
                    relation='AUTHORED_BY' if 'author' in parse_result.get('metadata', {}) else 'MENTIONS',
                    timestamp=datetime.now().isoformat()
                )
        
        # Build cross-document links (where same equipment appears in multiple docs)
        self._build_cross_links()
        
        return doc_id
    
    def _build_cross_links(self):
        """
        Connect equipment nodes that appear in multiple documents.
        This is where "linkage completeness" happens.
        """
        # Find equipment nodes
        eq_nodes = [n for n, data in self.graph.nodes(data=True) if data.get('type') == 'EQUIPMENT']
        
        # For each equipment node, find all documents that mention it
        for eq_node in eq_nodes:
            docs = []
            for pred, succ, data in self.graph.in_edges(eq_node, data=True):
                if self.graph.nodes[pred].get('type') == 'DOCUMENT':
                    docs.append(pred)
            
            # If mentioned in multiple docs, connect the docs via this equipment
            if len(docs) > 1:
                for i in range(len(docs)):
                    for j in range(i+1, len(docs)):
                        self.graph.add_edge(
                            docs[i],
                            docs[j],
                            relation='SHARES_EQUIPMENT',
                            equipment=eq_node,
                            timestamp=datetime.now().isoformat()
                        )
    
    def add_relationship(self, from_id: str, to_id: str, relation: str, metadata: dict = None):
        """Manually add a relationship between nodes"""
        self.graph.add_edge(
            from_id,
            to_id,
            relation=relation,
            **(metadata or {})
        )
    
    def add_tacit_rule(self, equipment_id: str, rule_text: str, person_id: str = None):
        """Add tacit knowledge to the graph"""
        rule_id = f"TACIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.graph.add_node(
            rule_id,
            type='TACIT_RULE',
            text=rule_text,
            timestamp=datetime.now().isoformat()
        )
        
        # Link to equipment
        self.graph.add_edge(
            rule_id,
            equipment_id,
            relation='APPLIES_TO',
            timestamp=datetime.now().isoformat()
        )
        
        # Link to person (if provided)
        if person_id:
            self.graph.add_edge(
                person_id,
                rule_id,
                relation='KNOWS_TACIT_RULE',
                timestamp=datetime.now().isoformat()
            )
        
        return rule_id
    
    def query_multi_hop(self, equipment_tag: str, hops: int = 3) -> dict:
        """
        Answer cross-functional queries by traversing the graph.
        Example: "Show me everything related to Pump P-101"
        """
        # Find the equipment node
        eq_node = None
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'EQUIPMENT' and data.get('tag') == equipment_tag:
                eq_node = node
                break
        
        if not eq_node:
            return {'error': f'Equipment {equipment_tag} not found'}
        
        # BFS traversal
        results = {
            'equipment': {eq_node: self.graph.nodes[eq_node]},
            'procedures': [],
            'incidents': [],
            'work_orders': [],
            'regulations': [],
            'tacit_rules': [],
            'documents': [],
            'paths': []
        }
        
        # Walk the graph
        visited = set([eq_node])
        current_level = [eq_node]
        
        for _ in range(hops):
            next_level = []
            for node in current_level:
                # Get neighbors
                neighbors = list(self.graph.predecessors(node)) + list(self.graph.successors(node))
                for neighbor in neighbors:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
                        
                        # Classify neighbor
                        node_type = self.graph.nodes[neighbor].get('type')
                        if node_type == 'PROCEDURE':
                            results['procedures'].append({neighbor: self.graph.nodes[neighbor]})
                        elif node_type == 'INCIDENT':
                            results['incidents'].append({neighbor: self.graph.nodes[neighbor]})
                        elif node_type == 'WORK_ORDER':
                            results['work_orders'].append({neighbor: self.graph.nodes[neighbor]})
                        elif node_type == 'REGULATION':
                            results['regulations'].append({neighbor: self.graph.nodes[neighbor]})
                        elif node_type == 'TACIT_RULE':
                            results['tacit_rules'].append({neighbor: self.graph.nodes[neighbor]})
                        elif node_type == 'DOCUMENT':
                            results['documents'].append({neighbor: self.graph.nodes[neighbor]})
                        
                        # Record the path
                        edge_data = self.graph.get_edge_data(node, neighbor)
                        if edge_data:
                            results['paths'].append({
                                'from': node,
                                'to': neighbor,
                                'relation': edge_data[0].get('relation') if edge_data else 'unknown'
                            })
            current_level = next_level
        
        return results
    
    def to_json(self) -> str:
        """Export graph for visualization"""
        return json.dumps({
            'nodes': [
                {
                    'id': n,
                    'label': data.get('tag') or data.get('name') or data.get('reference') or n,
                    'type': data.get('type'),
                    'metadata': {k: v for k, v in data.items() if k not in ['type']}
                }
                for n, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {
                    'from': u,
                    'to': v,
                    'label': data.get('relation'),
                    'metadata': data
                }
                for u, v, data in self.graph.edges(data=True)
            ]
        }, indent=2)
    
    def save(self, path: str = "backend/data/kg/graph.json"):
        """Save graph to file"""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    def load(self, path: str = "backend/data/kg/graph.json"):
        """Load graph from file"""
        import os
        if not os.path.exists(path):
            print(f"[WARNING] Graph file not found: {path}")
            return
        with open(path, 'r') as f:
            data = json.load(f)
        self.graph.clear()
        for node in data.get('nodes', []):
            node_id = node['id']
            node_type = node.get('type')
            node_data = {'type': node_type}
            node_data.update(node.get('metadata', {}))
            self.graph.add_node(node_id, **node_data)
        for edge in data.get('edges', []):
            u = edge['from']
            v = edge['to']
            edge_meta = edge.get('metadata', {})
            self.graph.add_edge(u, v, **edge_meta)
