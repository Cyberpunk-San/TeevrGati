import re

class TacitKnowledgeAgent:
    """
    Agent responsible for capturing unwritten rules from senior engineers
    and resolving conflicts between standard documentation and physics models.
    """
    
    def generate_interview_questions(self, conflict_details: dict) -> str:
        """
        Generate specific, contextual interview questions to resolve the conflict.
        """
        doc_hyp = conflict_details.get('document_hypothesis', 'Unknown')
        phys_diag = conflict_details.get('physics_result', 'Unknown')
        severity = conflict_details.get('severity', 'High')
        
        return f"""🔍 **Conflict Identified**

The documents suggest: **{doc_hyp}**
But the live sensor analysis shows: **{phys_diag}**

This is flagged as a **{severity}** priority discrepancy. 

**Senior Engineer Clarification Needed:**
1. Is the document outdated or is there a specific design modification not captured?
2. Are there any operational workarounds we should log as an unwritten procedure?
3. Should we override the torque, temperature, or speed guidelines?

*Please explain in your own words below.*"""

    def extract_tacit_rule(self, human_response: str) -> dict:
        """
        Extract structured rule from senior engineer's free-text response.
        """
        rule_text = human_response.strip()
        rule_type = "operational_workaround"
        confidence = 0.90
        
        # Heuristics based on text keywords
        response_lower = human_response.lower()
        if "torque" in response_lower or "nm" in response_lower or "tight" in response_lower:
            rule_type = "torque_workaround"
        elif "stabil" in response_lower or "wait" in response_lower or "start" in response_lower or "run" in response_lower:
            rule_type = "operational_stabilization"
        elif "heat" in response_lower or "cool" in response_lower or "temperature" in response_lower or "water" in response_lower:
            rule_type = "environmental_workaround"
        elif "wear" in response_lower or "tool" in response_lower or "minute" in response_lower or "bit" in response_lower:
            rule_type = "material_override"
            
        return {
            'rule_text': rule_text,
            'type': rule_type,
            'confidence': confidence,
            'status': 'verified'
        }

    def search_tacit_knowledge(self, query: str) -> list:
        """
        Lookup senior engineer overrides based on query keywords.
        """
        q = query.lower()
        if "vibrat" in q or "bearing" in q:
            return [{'note': 'Bearing inner race operates with higher tolerances (7.2 mm/s limit) during high load cycles.'}]
        if "torque" in q:
            return [{'note': 'Torque limit increased to 45Nm for structural stability on flange connectors.'}]
        return []
