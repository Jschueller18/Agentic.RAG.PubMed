"""
Sleep Mix Optimizer
Creates ONE optimal electrolyte formulation for sleep support

Unlike sleep_support_engine.py (which personalizes), this creates a single
research-backed formulation optimized across diverse test cases using
batch gradient descent.
"""

import json
from typing import Dict, Any, List


class SleepMixOptimizer:
    """
    Optimizes a single sleep support formulation
    
    Goal: Find the ONE best electrolyte mix for sleep across diverse users
    Uses RAG-powered research to iteratively improve the formulation
    """
    
    def __init__(self, weights_file: str = "sleep_mix_final.json"):
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
        Initial formulation based on sleep research
        These will be refined through RAG-powered training
        """
        return {
            "version": "1.0",
            "use_case": "sleep",
            "last_updated": "2025-10-29",
            "description": "Optimized for sleep onset, maintenance, and quality",
            
            # Single formulation (not personalized)
            "formulation": {
                "magnesium": 400,      # mg - primary sleep mineral
                "calcium": 200,        # mg - supports Mg, GABA production
                "potassium": 250,      # mg - muscle relaxation
                "sodium": 150          # mg - minimal for bedtime
            },
            
            # Mineral forms
            "forms": {
                "magnesium": "glycinate",  # Crosses BBB, calming
                "calcium": "citrate",      # Good absorption
                "potassium": "citrate",    # Well tolerated
                "sodium": "citrate"        # Alkalizing
            },
            
            # Target ratios (adjustable during training)
            "ratios": {
                "mg_ca": 2.0,    # Mg:Ca ratio
                "k_na": 1.67     # K:Na ratio
            },
            
            # Adjustable parameters (fine-tuned via gradient descent)
            "adjustable_params": [
                "formulation.magnesium",
                "formulation.calcium", 
                "formulation.potassium",
                "formulation.sodium"
            ],
            
            # Research citations (populated during training)
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
        
        Note: survey_data is used for evaluation context, but the 
        formulation itself doesn't change per person
        """
        return {
            "magnesium": self.weights["formulation"]["magnesium"],
            "calcium": self.weights["formulation"]["calcium"],
            "potassium": self.weights["formulation"]["potassium"],
            "sodium": self.weights["formulation"]["sodium"],
            "forms": self.weights["forms"],
            "use_case": "sleep",
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
            f"Magnesium glycinate {mg}mg - primary sleep mineral for GABA production and muscle relaxation",
            f"Calcium citrate {ca}mg - supports magnesium function, Mg:Ca ratio {self._get_ratio('magnesium', 'calcium')}:1",
            f"Potassium citrate {k}mg - muscle relaxation and nervous system support",
            f"Sodium citrate {na}mg - minimal amount to avoid water retention at bedtime",
            f"K:Na ratio {self._get_ratio('potassium', 'sodium')}:1 optimized for cellular function"
        ]
    
    def adjust_weights(self, adjustments: Dict[str, float]):
        """
        Apply gradient descent adjustments to formulation
        
        Args:
            adjustments: Dict of mineral -> delta (e.g. {"magnesium": +10, "calcium": -5})
        """
        for mineral, delta in adjustments.items():
            if mineral in self.weights["formulation"]:
                current = self.weights["formulation"][mineral]
                new_value = max(0, current + delta)  # Don't go negative
                
                # Apply safety caps
                max_doses = {"magnesium": 500, "calcium": 400, "potassium": 400, "sodium": 300}
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
    # Test the optimizer
    optimizer = SleepMixOptimizer()
    
    test_case = {
        "age": 35,
        "sex": "female",
        "sleep_issues": ["trouble_falling_asleep"]
    }
    
    result = optimizer.calculate(test_case)
    
    print("="*80)
    print("SLEEP MIX (Single Optimized Formulation)")
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


