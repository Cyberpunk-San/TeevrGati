import json
from datetime import datetime
import uuid
import os
from typing import Dict, List, Optional

class WorkOrderGenerator:
    """
    Generates work orders from diagnostic results.
    """
    
    def __init__(self, inventory_path: str = "backend/data/inventory.csv"):
        self.inventory_path = inventory_path
        self.work_order_counter = 0
    
    def create_work_order(self, asset_id: str, fault_type: str, severity: str, context: str) -> Dict:
        """
        Generate a complete work order.
        """
        self.work_order_counter += 1
        wo_id = f"WO-{datetime.now().strftime('%y')}-{self.work_order_counter:04d}"
        
        # Check spare parts
        spare_parts = self._check_inventory(fault_type)
        
        work_order = {
            'id': wo_id,
            'asset_id': asset_id,
            'fault_type': fault_type,
            'severity': severity,
            'created_at': datetime.now().isoformat(),
            'status': 'Open',
            'priority': self._get_priority(severity),
            'description': f"Diagnosed {fault_type} on {asset_id}",
            'context': context,
            'spare_parts_required': spare_parts,
            'labor_estimate_hours': self._estimate_labor(fault_type),
            'safety_requirements': self._get_safety_requirements(fault_type),
            'instructions': [
                "1. Lockout-tagout equipment",
                "2. Disassemble affected area",
                f"3. Inspect/replace {fault_type}",
                "4. Reassemble and test",
                "5. Document findings"
            ],
            'generated_by': 'Industrial Cortex AI'
        }
        
        # Save to file (for demo)
        self._save_work_order(work_order)
        
        return work_order
    
    def _check_inventory(self, fault_type: str) -> List[str]:
        """
        Check if required spare parts are in stock from local inventory database.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        inv_path = os.path.join(base_dir, "backend", "data", "inventory.csv")
        
        if os.path.exists(inv_path):
            try:
                import csv
                parts_to_request = []
                fault_lower = fault_type.lower()
                
                with open(inv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        category = row.get('category', '').lower()
                        part = row.get('part', '')
                        qty = int(row.get('quantity', 0))
                        
                        # Match fault terms with part categories
                        if category in fault_lower or (category == 'bearing' and 'bearing' in fault_lower):
                            if qty > 0:
                                parts_to_request.append(part)
                                
                if parts_to_request:
                    return parts_to_request
            except Exception as e:
                print(f"[ERROR] Failed to load inventory database: {e}")
                
        # Default fallback categories
        inventory = {
            'bearing inner race': ['Bearing SKF-6205', 'Bearing SKF-6306'],
            'bearing outer race': ['Bearing SKF-6205', 'Bearing SKF-6306'],
            'misalignment': ['Coupling CM-101', 'Alignment tool'],
            'unbalance': ['Balance weights', 'Fixing screws']
        }
        
        # Find matching parts
        for key, parts in inventory.items():
            if key in fault_type.lower():
                return [parts[0]]
                
        return ['General service kit']
    
    PRIORITY_MAPPING = {
        'Critical': 'Emergency',
        'Alert': 'High',
        'Warning': 'Medium',
        'Normal': 'Low'
    }
    
    LABOR_HOURS_ESTIMATES = {
        'bearing': int(os.getenv('TEEVRGATI_LABOR_BEARING', '4')),
        'misalignment': int(os.getenv('TEEVRGATI_LABOR_MISALIGNMENT', '2')),
        'unbalance': int(os.getenv('TEEVRGATI_LABOR_UNBALANCE', '3')),
        'default': int(os.getenv('TEEVRGATI_LABOR_DEFAULT', '2'))
    }

    def _get_priority(self, severity: str) -> str:
        """Map severity to priority"""
        return self.PRIORITY_MAPPING.get(severity, 'Medium')
    
    def _estimate_labor(self, fault_type: str) -> int:
        """Estimate labor hours"""
        fault_lower = fault_type.lower()
        for key, hours in self.LABOR_HOURS_ESTIMATES.items():
            if key in fault_lower:
                return hours
        return self.LABOR_HOURS_ESTIMATES['default']
    
    def _get_safety_requirements(self, fault_type: str) -> List[str]:
        """Get safety requirements"""
        safety = [
            'Lockout-tagout (LOTO) required',
            'Safety glasses required',
            'Steel-toed boots required'
        ]
        
        if 'bearing' in fault_type.lower():
            safety.append('Heavy lifting may be required')
        
        return safety
    
    def _save_work_order(self, work_order: Dict):
        """Save work order to file"""
        output_dir = "backend/data/work_orders/"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{work_order['id']}.json")
        with open(filepath, 'w') as f:
            json.dump(work_order, f, indent=2)
    
    def get_work_order(self, wo_id: str) -> Optional[Dict]:
        """Retrieve a work order by ID"""
        filepath = f"backend/data/work_orders/{wo_id}.json"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
