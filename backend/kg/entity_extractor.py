import re
import spacy
from typing import List, Dict, Any

# Load spaCy model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    print("[WARNING] spaCy model not found. Downloading...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"[ERROR] Failed to load spaCy model even after download: {e}")
        nlp = None

class EntityExtractor:
    """
    Extracts equipment tags, personnel, dates, and regulatory references.
    """
    
    def __init__(self):
        self.equipment_patterns = [
            r'[A-Z]{2,4}-[0-9]{2,4}',      # P-101, VLV-302
            r'[A-Z]{2,4}/[0-9]{2,4}',      # P/101
            r'[A-Z]{2,4}\s*[0-9]{2,4}',    # P 101
        ]
        self.regulation_patterns = [
            r'OISD\s*[0-9]{1,3}',
            r'Factory Act',
            r'Section\s*[0-9]{1,3}\([0-9]{1,2}\)',
            r'ISO\s*[0-9]{4,5}',
            r'PESO\s*[A-Z0-9]+',
        ]
        self.person_patterns = [
            r'[A-Z][a-z]+ [A-Z][a-z]+',     # John Doe
            r'[A-Z]\. [A-Z][a-z]+',          # J. Doe
            r'Mr\. [A-Z][a-z]+',
            r'Ms\. [A-Z][a-z]+',
            r'Dr\. [A-Z][a-z]+',
            r'Er\. [A-Z][a-z]+',             # Engineer
            r'Sr\. [A-Z][a-z]+ [A-Z][a-z]+', # Senior
        ]
    
    def extract_equipment_tags(self, text: str) -> List[Dict]:
        """Extract equipment tags using regex and spaCy NER"""
        results = []
        for pattern in self.equipment_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                results.append({
                    'tag': match.strip(),
                    'type': 'EQUIPMENT',
                    'confidence': 0.9,
                    'source': 'regex'
                })
        
        # Also use spaCy NER for general entities if loaded
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT']:
                    results.append({
                        'tag': ent.text.strip(),
                        'type': 'EQUIPMENT',
                        'confidence': 0.7,
                        'source': 'spacy'
                    })
        
        # Deduplicate
        seen = set()
        unique_results = []
        for r in results:
            if r['tag'] not in seen:
                seen.add(r['tag'])
                unique_results.append(r)
        
        return unique_results
    
    def extract_regulations(self, text: str) -> List[Dict]:
        """Extract regulatory references"""
        results = []
        for pattern in self.regulation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                results.append({
                    'reference': match.strip(),
                    'type': 'REGULATION',
                    'confidence': 0.95,
                    'source': 'regex'
                })
        
        # Deduplicate regulations
        seen = set()
        unique_results = []
        for r in results:
            norm = r['reference'].lower().replace(" ", "")
            if norm not in seen:
                seen.add(norm)
                unique_results.append(r)
        return unique_results
    
    def extract_persons(self, text: str) -> List[Dict]:
        """Extract person names"""
        results = []
        # Regex patterns
        for pattern in self.person_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                results.append({
                    'name': match.strip(),
                    'type': 'PERSON',
                    'confidence': 0.8,
                    'source': 'regex'
                })
        
        # spaCy NER for names if loaded
        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    results.append({
                        'name': ent.text.strip(),
                        'type': 'PERSON',
                        'confidence': 0.9,
                        'source': 'spacy'
                    })
        
        # Deduplicate persons
        seen = set()
        unique_results = []
        for r in results:
            if r['name'] not in seen:
                seen.add(r['name'])
                unique_results.append(r)
        return unique_results
    
    def extract_dates(self, text: str) -> List[Dict]:
        """Extract dates"""
        # Simple date patterns
        patterns = [
            r'\d{2}/\d{2}/\d{4}',   # 01/01/2024
            r'\d{4}-\d{2}-\d{2}',   # 2024-01-01
            r'[A-Z][a-z]+ \d{1,2}, \d{4}',  # January 1, 2024
            r'\d{1,2} [A-Z][a-z]+ \d{4}',   # 1 January 2024
        ]
        
        results = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                results.append({
                    'date': match.strip(),
                    'type': 'DATE',
                    'confidence': 0.9,
                    'source': 'regex'
                })
                
        # Deduplicate dates
        seen = set()
        unique_results = []
        for r in results:
            if r['date'] not in seen:
                seen.add(r['date'])
                unique_results.append(r)
        return unique_results
    
    def extract_all(self, text: str) -> Dict:
        """Run all extractors and return structured results"""
        return {
            'equipment': self.extract_equipment_tags(text),
            'regulations': self.extract_regulations(text),
            'persons': self.extract_persons(text),
            'dates': self.extract_dates(text),
        }
    
    def extract_from_document(self, pages: List[Dict]) -> Dict:
        """Extract entities from all pages of a document"""
        full_text = " ".join([p.get('text', '') for p in pages])
        return self.extract_all(full_text)
