"""
Active Mix Optimizer
Creates ONE optimal electrolyte formulation for active/athletic use

Optimized for: exercise performance, recovery, hydration, muscle function
"""

import json
from typing import Dict, Any, List


class ActiveMixOptimizer:
    """
    Optimizes a single active/performance formulation
    
    Goal: Find the ONE best electrolyte mix for active users across diverse profiles
    Focus: Higher sodium/potassium for sweat loss, magnesium for muscle recovery
    """
    
    def __init__(self, weights_file: str = "active_mix_final.json"):
        """Initialize with default or saved weights"""
        self.weights_file = weights_file
        self.load_weights()
    
    def load_weights(self):
        """Load current mix formulation"""
        try:
            with open(self.weights_file, 'r') as f:
                self.weights = json.load(f)
        except FileNotFoundError:
            self.weights = self.get_default_weights()
            self.save_weights()
    
    def save_weights(self):
        """Save updated mix formulation"""
        with open(self.weights_file, 'w') as f:
            json.dump(self.weights, f, indent=2)
    
    def get_default_weights(self) -> Dict:
        """
        Initial formulation based on exercise/performance research
        Higher electrolyte levels for sweat loss replacement
        """
        return {
            "version": "1.0",
            "use_case": "active",
            "last_updated": "2025-10-29",
            "description": "Optimized for exercise performance, recovery, and hydration",
            
            # Single formulation for active users
            "formulation": {
                "magnesium": 350,      # mg - muscle function, ATP production
                "calcium": 250,        # mg - muscle contraction, bone health
                "potassium": 500,      # mg - major sweat loss, muscle function
                "sodium": 300          # mg - major sweat loss, hydration
            },
            
            # Mineral forms
            "forms": {
                "magnesium": "glycinate",  # Well absorbed, gentle
                "calcium": "citrate",      # Good bioavailability
                "potassium": "citrate",    # Rapid absorption
                "sodium": "citrate"        # Fast hydration
            },
            
            # Target ratios
            "ratios": {
                "mg_ca": 1.4,    # Mg:Ca ratio (less emphasis than sleep)
                "k_na": 1.67     # K:Na ratio (electrolyte balance)
            },
            
            # Adjustable parameters
            "adjustable_params": [
                "formulation.magnesium",
                "formulation.calcium", 
                "formulation.potassium",
                "formulation.sodium"
            ],
            
            # Research citations
            "research_support": [],
            
            # Training metrics
            "training_history": {
                "iterations": 0,
                "best_score": 0,
                "avg_score": 0
            }
        }
    
    def calculate(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return the single optimized formulation
        
        survey_data used for evaluation context only
        """
        return {
            "magnesium": self.weights["formulation"]["magnesium"],
            "calcium": self.weights["formulation"]["calcium"],
            "potassium": self.weights["formulation"]["potassium"],
            "sodium": self.weights["formulation"]["sodium"],
            "forms": self.weights["forms"],
            "use_case": "active",
            "ratios": {
                "mg_ca": self._get_ratio("magnesium", "calcium"),
                "k_na": self._get_ratio("potassium", "sodium")
            },
            "reasoning": self._generate_reasoning(),
            "version": self.weights["version"]
        }
    
    def _get_ratio(self, mineral1: str, mineral2: str) -> float:
        """Calculate current ratio between two minerals"""
        val1 = self.weights["formulation"][mineral1]
        val2 = self.weights["formulation"][mineral2]
        return round(val1 / val2, 2) if val2 > 0 else 0
    
    def _generate_reasoning(self) -> List[str]:
        """Generate explanation for this formulation"""
        mg = self.weights["formulation"]["magnesium"]
        ca = self.weights["formulation"]["calcium"]
        k = self.weights["formulation"]["potassium"]
        na = self.weights["formulation"]["sodium"]
        
        return [
            f"Magnesium glycinate {mg}mg - ATP production, muscle recovery, reduces cramping",
            f"Calcium citrate {ca}mg - muscle contraction, bone health under stress",
            f"Potassium citrate {k}mg - primary sweat electrolyte, muscle function, prevents cramping",
            f"Sodium citrate {na}mg - primary sweat electrolyte, rapid hydration, performance",
            f"K:Na ratio {self._get_ratio('potassium', 'sodium')}:1 for optimal hydration and performance"
        ]
    
    def adjust_weights(self, adjustments: Dict[str, float]):
        """
        Apply gradient descent adjustments to formulation
        
        Args:
            adjustments: Dict of mineral -> delta
        """
        for mineral, delta in adjustments.items():
            if mineral in self.weights["formulation"]:
                current = self.weights["formulation"][mineral]
                new_value = max(0, current + delta)
                
                # Safety caps (higher for active use)
                max_doses = {"magnesium": 500, "calcium": 500, "potassium": 700, "sodium": 500}
                new_value = min(new_value, max_doses.get(mineral, 1000))
                
                self.weights["formulation"][mineral] = round(new_value)
        
        # Update ratios
        self.weights["ratios"]["mg_ca"] = self._get_ratio("magnesium", "calcium")
        self.weights["ratios"]["k_na"] = self._get_ratio("potassium", "sodium")
        
        self.save_weights()
    
    def update_training_metrics(self, iteration: int, score: float, avg_score: float):
        """Update training history"""
        self.weights["training_history"]["iterations"] = iteration
        self.weights["training_history"]["best_score"] = max(
            self.weights["training_history"]["best_score"], 
            score
        )
        self.weights["training_history"]["avg_score"] = avg_score
        self.save_weights()


if __name__ == "__main__":
    optimizer = ActiveMixOptimizer()
    
    test_case = {
        "age": 28,
        "sex": "male",
        "activity_level": "high_intensity",
        "training_hours": 6
    }
    
    result = optimizer.calculate(test_case)
    
    print("="*80)
    print("ACTIVE MIX (Single Optimized Formulation)")
    print("="*80)
    print(f"\nMagnesium ({result['forms']['magnesium']}): {result['magnesium']}mg")
    print(f"Calcium ({result['forms']['calcium']}): {result['calcium']}mg")
    print(f"Potassium ({result['forms']['potassium']}): {result['potassium']}mg")
    print(f"Sodium ({result['forms']['sodium']}): {result['sodium']}mg")
    print(f"\nRatios: Mg:Ca = {result['ratios']['mg_ca']}:1, K:Na = {result['ratios']['k_na']}:1")
    print(f"\nReasoning:")
    for reason in result['reasoning']:
        print(f"  • {reason}")
    print("\n" + "="*80)


