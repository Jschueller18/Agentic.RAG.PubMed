"""
Batch Test Case Generator
Creates diverse batches of test profiles for SGD-style training

Similar to how ML models train on batches of data, this generates
diverse user profiles to test formulations against, ensuring the
optimized mixes work well across a broad population.
"""

import random
from typing import Dict, List, Any


class BatchTestGenerator:
    """
    Generates batches of diverse test cases for each use case
    
    Uses stratified sampling to ensure coverage across:
    - Age ranges
    - Sex distribution
    - Activity levels / sleep issues / health goals
    - Body weights
    """
    
    def __init__(self, batch_size: int = 12):
        """
        Args:
            batch_size: Number of test cases per batch (default 12)
        """
        self.batch_size = batch_size
    
    def generate_sleep_batch(self) -> List[Dict[str, Any]]:
        """
        Generate batch of test cases for sleep mix optimization
        
        Covers diverse profiles with various sleep issues
        """
        batch = []
        
        # Age stratification (handle small batches)
        if self.batch_size >= 8:
            # Proper stratification for larger batches
            ages_18_30 = [random.randint(18, 30) for _ in range(self.batch_size // 4)]
            ages_31_50 = [random.randint(31, 50) for _ in range(self.batch_size // 4)]
            ages_51_70 = [random.randint(51, 70) for _ in range(self.batch_size // 4)]
            ages_70plus = [random.randint(70, 85) for _ in range(self.batch_size // 4)]
            all_ages = ages_18_30 + ages_31_50 + ages_51_70 + ages_70plus
            # Fill any remaining slots
            while len(all_ages) < self.batch_size:
                all_ages.append(random.randint(18, 85))
        else:
            # Random ages for small batches
            all_ages = [random.randint(18, 85) for _ in range(self.batch_size)]
        
        # Sex distribution (50/50)
        sexes = (["male", "female"] * (self.batch_size // 2 + 1))[:self.batch_size]
        
        # Sleep issues (varied combinations)
        sleep_issue_options = [
            ["trouble_falling_asleep"],
            ["frequent_waking"],
            ["early_waking"],
            ["restless_sleep"],
            ["trouble_falling_asleep", "frequent_waking"],
            ["trouble_falling_asleep", "restless_sleep"],
            ["frequent_waking", "early_waking"],
            ["restless_sleep", "frequent_waking"],
        ]
        
        for i in range(self.batch_size):
            age = all_ages[i]
            sex = sexes[i]
            weight = random.randint(120, 220) if sex == "male" else random.randint(100, 180)
            
            test_case = {
                "age": age,
                "sex": sex,
                "weight": weight,
                "sleep_issues": random.choice(sleep_issue_options),
                "magnesium_intake": random.randint(150, 350),
                "calcium_intake": random.randint(600, 1200),
                "potassium_intake": random.randint(1500, 3000),
                "sodium_intake": random.randint(1500, 3500),
                "medications": random.choice([[], ["none"], ["diuretics"]] if age > 50 else [[]]),
                "use_case": "sleep"
            }
            batch.append(test_case)
        
        return batch
    
    def generate_active_batch(self) -> List[Dict[str, Any]]:
        """
        Generate batch of test cases for active mix optimization
        
        Covers diverse athletic profiles and activity levels
        """
        batch = []
        
        # Age stratification (skewed younger for active users, handle small batches)
        if self.batch_size >= 6:
            ages_18_30 = [random.randint(18, 30) for _ in range(self.batch_size // 2)]
            ages_31_50 = [random.randint(31, 50) for _ in range(self.batch_size // 3)]
            ages_51_plus = [random.randint(51, 70) for _ in range(self.batch_size - len(ages_18_30) - len(ages_31_50))]
            all_ages = ages_18_30 + ages_31_50 + ages_51_plus
        else:
            all_ages = [random.randint(18, 55) for _ in range(self.batch_size)]
        
        # Sex distribution
        sexes = (["male", "female"] * (self.batch_size // 2 + 1))[:self.batch_size]
        
        # Activity levels
        activity_levels = [
            "high_intensity",
            "endurance",
            "strength_training",
            "crossfit",
            "running",
            "cycling"
        ]
        
        for i in range(self.batch_size):
            age = all_ages[i]
            sex = sexes[i]
            weight = random.randint(140, 220) if sex == "male" else random.randint(110, 160)
            
            test_case = {
                "age": age,
                "sex": sex,
                "weight": weight,
                "activity_level": random.choice(activity_levels),
                "training_hours_per_week": random.randint(4, 12),
                "sweat_rate": random.choice(["moderate", "high", "very_high"]),
                "magnesium_intake": random.randint(200, 400),
                "calcium_intake": random.randint(700, 1300),
                "potassium_intake": random.randint(2000, 3500),
                "sodium_intake": random.randint(2000, 4000),
                "performance_goals": random.choice([
                    ["endurance"],
                    ["strength"],
                    ["recovery"],
                    ["endurance", "recovery"]
                ]),
                "use_case": "active"
            }
            batch.append(test_case)
        
        return batch
    
    def generate_daily_batch(self) -> List[Dict[str, Any]]:
        """
        Generate batch of test cases for daily wellness mix optimization
        
        Covers broad general population
        """
        batch = []
        
        # Age stratification (even distribution, handle small batches)
        if self.batch_size >= 8:
            ages_18_30 = [random.randint(18, 30) for _ in range(self.batch_size // 4)]
            ages_31_50 = [random.randint(31, 50) for _ in range(self.batch_size // 4)]
            ages_51_70 = [random.randint(51, 70) for _ in range(self.batch_size // 4)]
            ages_70plus = [random.randint(70, 85) for _ in range(self.batch_size // 4)]
            all_ages = ages_18_30 + ages_31_50 + ages_51_70 + ages_70plus
            while len(all_ages) < self.batch_size:
                all_ages.append(random.randint(18, 85))
        else:
            all_ages = [random.randint(18, 85) for _ in range(self.batch_size)]
        
        # Sex distribution
        sexes = (["male", "female"] * (self.batch_size // 2 + 1))[:self.batch_size]
        
        # Activity levels (skewed toward sedentary/moderate for daily mix)
        activity_levels = [
            "sedentary",
            "sedentary",
            "light",
            "light",
            "moderate",
            "moderate"
        ]
        
        for i in range(self.batch_size):
            age = all_ages[i]
            sex = sexes[i]
            weight = random.randint(130, 220) if sex == "male" else random.randint(110, 180)
            
            test_case = {
                "age": age,
                "sex": sex,
                "weight": weight,
                "activity_level": random.choice(activity_levels),
                "magnesium_intake": random.randint(150, 350),
                "calcium_intake": random.randint(600, 1200),
                "potassium_intake": random.randint(1500, 2800),
                "sodium_intake": random.randint(1800, 3500),
                "health_goals": random.choice([
                    ["general_wellness"],
                    ["energy"],
                    ["stress_support"],
                    ["cardiovascular_health"],
                    ["bone_health"]
                ]),
                "diet_quality": random.choice(["poor", "average", "good"]),
                "use_case": "daily"
            }
            batch.append(test_case)
        
        return batch
    
    def generate_batch(self, use_case: str) -> List[Dict[str, Any]]:
        """
        Generate batch for specified use case
        
        Args:
            use_case: "sleep", "active", or "daily"
            
        Returns:
            List of test case dictionaries
        """
        if use_case == "sleep":
            return self.generate_sleep_batch()
        elif use_case == "active":
            return self.generate_active_batch()
        elif use_case == "daily":
            return self.generate_daily_batch()
        else:
            raise ValueError(f"Unknown use case: {use_case}")


if __name__ == "__main__":
    # Test the generator
    generator = BatchTestGenerator(batch_size=12)
    
    print("="*80)
    print("BATCH TEST GENERATOR - Sample Output")
    print("="*80)
    
    for use_case in ["sleep", "active", "daily"]:
        batch = generator.generate_batch(use_case)
        print(f"\n{use_case.upper()} BATCH ({len(batch)} test cases):")
        print(f"  Age range: {min(tc['age'] for tc in batch)}-{max(tc['age'] for tc in batch)}")
        print(f"  Sex distribution: {sum(1 for tc in batch if tc['sex'] == 'male')}M / {sum(1 for tc in batch if tc['sex'] == 'female')}F")
        print(f"  Sample case: {batch[0]}")
    
    print("\n" + "="*80)


