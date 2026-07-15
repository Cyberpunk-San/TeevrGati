"""
Industrial Knowledge Graph Ontology
Defines the relationships that connect all your documents.
"""

# Node Types
NODE_TYPES = {
    'EQUIPMENT': 'Equipment',           # Pump P-101, Compressor C-202
    'COMPONENT': 'Component',           # Bearing, Seal, Motor
    'PROCEDURE': 'Procedure',           # SOP-2023, Lockout-Tagout
    'INCIDENT': 'Incident',             # Near-miss #42, Failure Report
    'WORK_ORDER': 'WorkOrder',          # WO-9821
    'REGULATION': 'Regulation',         # OISD Section 4.2, Factory Act
    'PERSON': 'Person',                 # Sr. Engineer Rao
    'TACIT_RULE': 'TacitRule',          # Unwritten knowledge
    'DOCUMENT': 'Document',             # Any source document
    'DEPARTMENT': 'Department',         # Maintenance, Safety, Engineering
}

# Relationship Types (The "Dots" You Connect)
RELATIONSHIP_TYPES = {
    'HAS_PART': 'HAS_PART',                     # Equipment → Component
    'GOVERNED_BY': 'GOVERNED_BY',               # Equipment → Procedure
    'CITES_CLAUSE': 'CITES_CLAUSE',             # Procedure → Regulation
    'INVOLVES': 'INVOLVES',                     # Incident → Equipment
    'REVEALED_GAP_IN': 'REVEALED_GAP_IN',       # Incident → Procedure
    'CREATED_WORK_ORDER': 'CREATED_WORK_ORDER', # Person → WorkOrder
    'ADDRESSES': 'ADDRESSES',                   # WorkOrder → Incident
    'KNOWS_TACIT_RULE': 'KNOWS_TACIT_RULE',     # Person → TacitRule
    'APPLIES_TO': 'APPLIES_TO',                 # TacitRule → Equipment
    'AUTHORED_BY': 'AUTHORED_BY',               # Document → Person
    'BELONGS_TO': 'BELONGS_TO',                 # Person → Department
    'UPDATED_BY': 'UPDATED_BY',                 # Document → Person (versioning)
}
