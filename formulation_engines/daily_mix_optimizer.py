"""
Daily Mix Optimizer
Creates ONE optimal electrolyte formulation for daily wellness

Optimized for: general health maintenance, baseline electrolyte support
"""

import json
from typing import Dict, Any, List


class DailyMixOptimizer:
    """
    Optimizes a single daily wellness formulation
    
    Goal: Find the ONE best electrolyte mix for daily maintenance across diverse users
    Focus: Balanced baseline support, preventive health, no specific condition targeting
    """
    
    def __init__(self, weights_file: str = "daily_mix_final.json"):
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
        Initial formulation based on daily wellness research
        Moderate, balanced doses for general health
        """
        return {
            "version": "1.0",
            "use_case": "daily",
            "last_updated": "2025-10-29",
            "description": "Optimized for daily wellness and maintenance",
            
            # Single balanced formulation
            "formulation": {
                "magnesium": 300,      # mg - general health, stress support
                "calcium": 200,        # mg - bone health, cellular function
                "potassium": 300,      # mg - cardiovascular, cellular balance
                "sodium": 200          # mg - moderate for general hydration
            },
            
            # Mineral forms
            "forms": {
                "magnesium": "glycinate",  # Well tolerated, calming
                "calcium": "citrate",      # Good absorption
                "potassium": "citrate",    # Gentle, well absorbed
                "sodium": "citrate"        # Alkalizing, gentle
            },
            
            # Target ratios
            "ratios": {
                "mg_ca": 1.5,    # Mg:Ca ratio (balanced)
                "k_na": 1.5      # K:Na ratio (balanced)
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
            "use_case": "daily",
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
            f"Magnesium glycinate {mg}mg - stress support, muscle function, cardiovascular health",
            f"Calcium citrate {ca}mg - bone health, cellular signaling, enzyme function",
            f"Potassium citrate {k}mg - cardiovascular support, blood pressure regulation",
            f"Sodium citrate {na}mg - electrolyte balance, cellular hydration",
            f"Balanced ratios (Mg:Ca {self._get_ratio('magnesium', 'calcium')}:1, K:Na {self._get_ratio('potassium', 'sodium')}:1) for optimal daily wellness"
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
                
                # Safety caps (moderate for daily use)
                max_doses = {"magnesium": 450, "calcium": 400, "potassium": 500, "sodium": 400}
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
    optimizer = DailyMixOptimizer()
    
    test_case = {
        "age": 40,
        "sex": "female",
        "activity_level": "moderate",
        "health_goals": ["general_wellness"]
    }
    
    result = optimizer.calculate(test_case)
    
    print("="*80)
    print("DAILY MIX (Single Optimized Formulation)")
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


