"""
BestMove Sleep Support Formula Engine
Calculates optimal electrolyte doses for sleep quality improvement

All weights are research-backed and continuously refined through RAG system
"""

import json
from typing import Dict, Any


class SleepSupportEngine:
    """
    Calculates personalized electrolyte formulation for sleep support
    
    Key factors:
    - Age, sex, weight, BMI
    - Sleep issues (onset, maintenance, quality)
    - Current mineral intake (diet + supplements)
    - Activity level and sweat rate
    - Medications that affect electrolytes
    """
    
    def __init__(self, weights_file: str = "sleep_weights.json"):
        """Load adjustable weights from file"""
        self.weights_file = weights_file
        self.load_weights()
        
    def load_weights(self):
        """Load current weight configuration"""
        try:
            with open(self.weights_file, 'r') as f:
                self.weights = json.load(f)
        except FileNotFoundError:
            # Initialize with research-backed defaults
            self.weights = self.get_default_weights()
            self.save_weights()
    
    def save_weights(self):
        """Save updated weights"""
        with open(self.weights_file, 'w') as f:
            json.dump(self.weights, f, indent=2)
    
    def get_default_weights(self) -> Dict:
        """Default weights based on initial research review"""
        return {
            "version": "1.0",
            "last_updated": "2025-10-07",
            "research_citations": [],
            
            # Magnesium weights (primary sleep mineral)
            "magnesium": {
                "base_dose": 300,  # mg - baseline for average adult
                "age_multipliers": {
                    "18-30": 1.0,
                    "31-50": 1.1,
                    "51-70": 1.2,
                    "70+": 1.25
                },
                "sex_multipliers": {
                    "male": 1.0,
                    "female": 1.15  # Women often need more for sleep
                },
                "weight_factor": 1.5,  # mg per kg above 70kg
                "sleep_issue_adjustments": {
                    "trouble_falling_asleep": 100,  # mg
                    "frequent_waking": 75,
                    "early_waking": 50,
                    "restless_sleep": 75,
                    "none": 0
                },
                "current_intake_gap_multiplier": 0.7,  # Fill 70% of RDA gap
                "max_dose": 500,  # mg - safety limit for single dose
                "form": "glycinate"  # Best for sleep (crosses BBB)
            },
            
            # Calcium weights (supports Mg, but can interfere if too high)
            "calcium": {
                "base_dose": 200,
                "age_multipliers": {
                    "18-30": 1.0,
                    "31-50": 1.1,
                    "51-70": 1.3,
                    "70+": 1.4
                },
                "sex_multipliers": {
                    "male": 1.0,
                    "female": 1.2
                },
                "mg_ratio_target": 0.5,  # Ca should be ~50% of Mg for sleep
                "current_intake_gap_multiplier": 0.3,  # Less aggressive fill
                "max_dose": 400,
                "form": "citrate"
            },
            
            # Potassium weights (supports muscle relaxation)
            "potassium": {
                "base_dose": 200,
                "age_multipliers": {
                    "18-30": 1.0,
                    "31-50": 1.0,
                    "51-70": 1.1,
                    "70+": 1.15
                },
                "sex_multipliers": {
                    "male": 1.1,
                    "female": 1.0
                },
                "sleep_quality_boost": 50,  # For restless sleep
                "current_intake_gap_multiplier": 0.4,
                "max_dose": 300,
                "form": "citrate"
            },
            
            # Sodium weights (minimal for bedtime - can cause water retention)
            "sodium": {
                "base_dose": 100,
                "age_multipliers": {
                    "18-30": 1.0,
                    "31-50": 0.9,
                    "51-70": 0.8,
                    "70+": 0.7
                },
                "sex_multipliers": {
                    "male": 1.0,
                    "female": 0.9
                },
                "activity_adjustment": 0.5,  # Minimal increase for active users
                "max_dose": 200,
                "form": "citrate"
            },
            
            # Interaction adjustments
            "interactions": {
                "mg_ca_ratio_optimal": 2.0,  # Mg:Ca should be ~2:1 for sleep
                "k_na_ratio_optimal": 2.5   # K:Na should be ~2.5:1
            },
            
            # Medication interactions
            "medication_adjustments": {
                "diuretics": {"magnesium": 1.2, "potassium": 1.3},
                "blood_pressure_meds": {"sodium": 0.7},
                "thyroid_meds": {"calcium": 0.8}  # Ca interferes with absorption
            }
        }
    
    def calculate(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate personalized sleep support formulation
        
        Args:
            survey_data: Complete survey responses
            
        Returns:
            Dict with doses for each mineral and reasoning
        """
        # Extract relevant variables
        age = survey_data.get("age", 35)
        sex = survey_data.get("sex", "female").lower()
        weight_lbs = survey_data.get("weight", 150)
        weight_kg = weight_lbs * 0.453592
        
        sleep_issues = survey_data.get("sleep_issues", [])
        
        current_intake = {
            "magnesium": survey_data.get("magnesium_intake", 250),
            "calcium": survey_data.get("calcium_intake", 900),
            "potassium": survey_data.get("potassium_intake", 2000),
            "sodium": survey_data.get("sodium_intake", 2000)
        }
        
        medications = survey_data.get("medications", [])
        
        # Calculate each mineral
        magnesium = self._calculate_magnesium(age, sex, weight_kg, sleep_issues, current_intake["magnesium"], medications)
        calcium = self._calculate_calcium(age, sex, weight_kg, current_intake["calcium"], magnesium, medications)
        potassium = self._calculate_potassium(age, sex, weight_kg, sleep_issues, current_intake["potassium"])
        sodium = self._calculate_sodium(age, sex, current_intake["sodium"])
        
        # Adjust for interactions
        calcium, magnesium = self._adjust_mg_ca_ratio(magnesium, calcium)
        potassium, sodium = self._adjust_k_na_ratio(potassium, sodium)
        
        return {
            "magnesium": round(magnesium),
            "calcium": round(calcium),
            "potassium": round(potassium),
            "sodium": round(sodium),
            "forms": {
                "magnesium": self.weights["magnesium"]["form"],
                "calcium": self.weights["calcium"]["form"],
                "potassium": self.weights["potassium"]["form"],
                "sodium": self.weights["sodium"]["form"]
            },
            "reasoning": self._generate_reasoning(survey_data, magnesium, calcium, potassium, sodium),
            "weights_version": self.weights["version"]
        }
    
    def _calculate_magnesium(self, age, sex, weight_kg, sleep_issues, current_intake, medications):
        """Calculate optimal magnesium dose"""
        w = self.weights["magnesium"]
        
        # Start with base dose
        dose = w["base_dose"]
        
        # Age adjustment
        age_group = self._get_age_group(age)
        dose *= w["age_multipliers"][age_group]
        
        # Sex adjustment
        dose *= w["sex_multipliers"][sex]
        
        # Weight adjustment (for people above 70kg)
        if weight_kg > 70:
            dose += (weight_kg - 70) * w["weight_factor"]
        
        # Sleep issue adjustments
        for issue in sleep_issues:
            issue_key = issue.replace(" ", "_").replace("(", "").replace(")", "").lower()
            if issue_key in w["sleep_issue_adjustments"]:
                dose += w["sleep_issue_adjustments"][issue_key]
        
        # Fill gap from current intake (RDA is ~400mg for adults)
        rda = 400 if sex == "male" else 350
        intake_gap = max(0, rda - current_intake)
        dose += intake_gap * w["current_intake_gap_multiplier"]
        
        # Medication adjustments
        for med in medications:
            if med.lower() in self.weights["medication_adjustments"]:
                dose *= self.weights["medication_adjustments"][med.lower()].get("magnesium", 1.0)
        
        # Cap at max dose
        dose = min(dose, w["max_dose"])
        
        return dose
    
    def _calculate_calcium(self, age, sex, weight_kg, current_intake, magnesium_dose, medications):
        """Calculate optimal calcium dose"""
        w = self.weights["calcium"]
        
        # Start with base
        dose = w["base_dose"]
        
        # Age adjustment
        age_group = self._get_age_group(age)
        dose *= w["age_multipliers"][age_group]
        
        # Sex adjustment
        dose *= w["sex_multipliers"][sex]
        
        # Target ratio with magnesium (Ca should be ~50% of Mg for sleep)
        ratio_based_dose = magnesium_dose * w["mg_ratio_target"]
        dose = (dose + ratio_based_dose) / 2  # Average of base and ratio
        
        # Fill gap from current intake (RDA is ~1000mg for adults)
        rda = 1000 if age < 50 else 1200
        intake_gap = max(0, rda - current_intake)
        dose += intake_gap * w["current_intake_gap_multiplier"]
        
        # Medication adjustments
        for med in medications:
            if med.lower() in self.weights["medication_adjustments"]:
                dose *= self.weights["medication_adjustments"][med.lower()].get("calcium", 1.0)
        
        # Cap at max
        dose = min(dose, w["max_dose"])
        
        return dose
    
    def _calculate_potassium(self, age, sex, weight_kg, sleep_issues, current_intake):
        """Calculate optimal potassium dose"""
        w = self.weights["potassium"]
        
        # Start with base
        dose = w["base_dose"]
        
        # Age adjustment
        age_group = self._get_age_group(age)
        dose *= w["age_multipliers"][age_group]
        
        # Sex adjustment
        dose *= w["sex_multipliers"][sex]
        
        # Boost for sleep quality issues
        if "restless_sleep" in [i.lower().replace(" ", "_") for i in sleep_issues]:
            dose += w["sleep_quality_boost"]
        
        # Fill gap (RDA is ~2600-3400mg - we only fill small portion)
        rda = 3400 if sex == "male" else 2600
        intake_gap = max(0, rda - current_intake)
        dose += intake_gap * w["current_intake_gap_multiplier"]
        
        # Cap at max
        dose = min(dose, w["max_dose"])
        
        return dose
    
    def _calculate_sodium(self, age, sex, current_intake):
        """Calculate optimal sodium dose (minimal for bedtime)"""
        w = self.weights["sodium"]
        
        # Start with base
        dose = w["base_dose"]
        
        # Age adjustment (less as we age - blood pressure concerns)
        age_group = self._get_age_group(age)
        dose *= w["age_multipliers"][age_group]
        
        # Sex adjustment
        dose *= w["sex_multipliers"][sex]
        
        # Cap at max
        dose = min(dose, w["max_dose"])
        
        return dose
    
    def _adjust_mg_ca_ratio(self, mg, ca):
        """Adjust Mg:Ca ratio to optimal for sleep"""
        target_ratio = self.weights["interactions"]["mg_ca_ratio_optimal"]
        current_ratio = mg / ca if ca > 0 else 999
        
        # If ratio is off, adjust calcium (Mg is primary for sleep)
        if current_ratio < target_ratio * 0.8:  # Ca too high
            ca = mg / target_ratio
        elif current_ratio > target_ratio * 1.2:  # Ca too low
            ca = mg / target_ratio
        
        return ca, mg
    
    def _adjust_k_na_ratio(self, k, na):
        """Adjust K:Na ratio to optimal"""
        target_ratio = self.weights["interactions"]["k_na_ratio_optimal"]
        current_ratio = k / na if na > 0 else 999
        
        # Adjust sodium if ratio is off
        if current_ratio < target_ratio * 0.8:  # Na too high
            na = k / target_ratio
        
        return k, na
    
    def _get_age_group(self, age):
        """Get age group bucket"""
        if age < 31:
            return "18-30"
        elif age < 51:
            return "31-50"
        elif age < 71:
            return "51-70"
        else:
            return "70+"
    
    def _generate_reasoning(self, survey_data, mg, ca, k, na):
        """Generate human-readable reasoning for the recommendation"""
        reasons = []
        
        age = survey_data.get("age", 35)
        sex = survey_data.get("sex", "female")
        sleep_issues = survey_data.get("sleep_issues", [])
        
        # Magnesium reasoning
        if mg >= 400:
            reasons.append(f"High magnesium ({mg}mg) for sleep support due to {', '.join(sleep_issues) if sleep_issues else 'general sleep enhancement'}")
        
        # Age-based
        if age > 50:
            reasons.append(f"Increased doses for age {age} - higher mineral needs for sleep")
        
        # Sex-based
        if sex.lower() == "female":
            reasons.append("Female-specific adjustments for hormonal influence on sleep")
        
        # Ratio explanations
        mg_ca_ratio = mg / ca if ca > 0 else 0
        reasons.append(f"Mg:Ca ratio of {mg_ca_ratio:.1f}:1 optimized for GABA production and sleep")
        
        return reasons


if __name__ == "__main__":
    # Test the engine
    engine = SleepSupportEngine()
    
    test_case = {
        "age": 35,
        "sex": "female",
        "weight": 140,
        "sleep_issues": ["Trouble falling asleep", "Frequent nighttime waking"],
        "magnesium_intake": 200,
        "calcium_intake": 800,
        "potassium_intake": 2000,
        "sodium_intake": 2200,
        "medications": []
    }
    
    result = engine.calculate(test_case)
    
    print("="*80)
    print("SLEEP SUPPORT FORMULATION")
    print("="*80)
    print(f"\nMagnesium ({result['forms']['magnesium']}): {result['magnesium']}mg")
    print(f"Calcium ({result['forms']['calcium']}): {result['calcium']}mg")
    print(f"Potassium ({result['forms']['potassium']}): {result['potassium']}mg")
    print(f"Sodium ({result['forms']['sodium']}): {result['sodium']}mg")
    print(f"\nReasoning:")
    for reason in result['reasoning']:
        print(f"  • {reason}")
    print("\n" + "="*80)


