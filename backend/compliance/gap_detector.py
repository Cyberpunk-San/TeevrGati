class ComplianceGapDetector:
    """
    Evaluates maintenance procedures and RAG context documentation 
    against standard OISD, OSHA, and Factory Act safety compliance protocols.
    """
    
    def check_safety_compliance(self, procedure_text: str) -> list:
        gaps = []
        # Keyword checks mapped to industrial safety standards
        safety_checks = {
            'lockout': ('LOTO (Lockout-Tagout) isolation procedure', 'OSHA 1910.147 / OISD-105'),
            'grounding': ('Electrostatic grounding / bonding checklist', 'OISD-GDN-180'),
            'ppe': ('Personal Protective Equipment (PPE) specification', 'OSHA 1910.132'),
            'ventilation': ('Confined space gas testing & ventilation clearance', 'OSHA 1910.146'),
            'tagout': ('Tagout warning flag registration', 'OSHA 1910.147')
        }
        
        proc_lower = procedure_text.lower()
        for keyword, (description, standard) in safety_checks.items():
            if keyword not in proc_lower:
                gaps.append({
                    'clause': keyword.upper(),
                    'description': description,
                    'status': 'MISSING',
                    'standard': standard,
                    'severity': 'HIGH' if keyword in ['lockout', 'grounding'] else 'MEDIUM'
                })
                
        return gaps
