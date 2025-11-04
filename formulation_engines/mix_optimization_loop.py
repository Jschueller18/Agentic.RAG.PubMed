"""
Mix Optimization Loop (SGD-Style)
Optimizes single-mix formulations using batch gradient descent

Similar to ML training:
1. Generate batch of diverse test cases (12+)
2. Evaluate formulation on entire batch
3. Calculate averaged gradients (adjustments)
4. Apply updates to formulation
5. Repeat until convergence
"""

import json
import copy
import os
from datetime import datetime
from typing import Dict, List, Any
from sleep_mix_optimizer import SleepMixOptimizer
from active_mix_optimizer import ActiveMixOptimizer
from daily_mix_optimizer import DailyMixOptimizer
from parallel_evaluator import ParallelEvaluator
from reasoning_reflector import ReasoningReflector
from targeted_research_downloader import TargetedResearchDownloader
from batch_test_generator import BatchTestGenerator


class MixOptimizationLoop:
    """
    SGD-style optimization for single-mix formulations
    
    Key differences from improvement_loop.py:
    - Works with batch of test cases (12+) instead of single cases
    - Averages feedback/adjustments across batch (like SGD)
    - Optimizes one fixed formulation, not personalization weights
    - Simpler convergence criteria
    """
    
    def __init__(self, use_case: str, batch_size: int = 12):
        """
        Args:
            use_case: "sleep", "active", or "daily"
            batch_size: Number of test cases per batch (default 12)
        """
        self.use_case = use_case
        self.batch_size = batch_size
        
        # Initialize components with shared Qdrant client to avoid DB locks
        from qdrant_client import QdrantClient
        shared_qdrant = QdrantClient(path="./bestmove_vector_db")
        
        self.optimizer = self._get_optimizer(use_case)
        self.evaluator = ParallelEvaluator(qdrant_client=shared_qdrant)
        self.reflector = ReasoningReflector()
        self.downloader = TargetedResearchDownloader(qdrant_client=shared_qdrant)
        self.generator = BatchTestGenerator(batch_size=batch_size)
        
        # Training history
        self.history = {
            "iterations": [],
            "avg_scores": [],
            "best_scores": [],
            "formulations": []
        }
    
    def _get_optimizer(self, use_case: str):
        """Get the appropriate optimizer for the use case"""
        if use_case == "sleep":
            return SleepMixOptimizer()
        elif use_case == "active":
            return ActiveMixOptimizer()
        elif use_case == "daily":
            return DailyMixOptimizer()
        else:
            raise ValueError(f"Unknown use case: {use_case}")
    
    def run(self, iterations: int = 20, learning_rate: float = 0.3):
        """
        Run optimization loop
        
        Args:
            iterations: Number of training iterations
            learning_rate: How aggressively to apply adjustments (0-1)
        """
        print("\n" + "="*80)
        print(f"STARTING {self.use_case.upper()} MIX OPTIMIZATION")
        print(f"Batch size: {self.batch_size} | Iterations: {iterations} | Learning rate: {learning_rate}")
        print("="*80 + "\n")
        
        best_score = 0
        best_formulation = None
        no_improvement_count = 0
        
        for iteration in range(1, iterations + 1):
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration}/{iterations}")
            print(f"{'='*80}\n")
            
            # Generate fresh batch of test cases
            batch = self.generator.generate_batch(self.use_case)
            print(f"✅ Generated batch of {len(batch)} diverse test cases")
            
            # Evaluate current formulation on entire batch
            batch_scores = []
            batch_evaluations = []
            
            for i, test_case in enumerate(batch, 1):
                print(f"\n  Evaluating test case {i}/{len(batch)}...")
                
                # Get recommendation (same for all, but evaluated in context)
                recommendation = self.optimizer.calculate(test_case)
                
                # Evaluate with RAG
                evaluation = self.evaluator.evaluate_recommendation(test_case, recommendation)
                batch_evaluations.append(evaluation)
                batch_scores.append(evaluation["overall_score"])
                
                print(f"    Overall Score: {evaluation['overall_score']}/100")
                print(f"\n    Mineral Grades:")
                for mineral, grade_data in evaluation.get('mineral_grades', {}).items():
                    score = grade_data.get('score', 0)
                    suggestion = grade_data.get('suggestion', 'N/A')
                    print(f"      {mineral.capitalize()}: {score}/100")
                    print(f"        → {suggestion}")
                print()
            
            # Calculate batch statistics
            avg_score = sum(batch_scores) / len(batch_scores)
            min_score = min(batch_scores)
            max_score = max(batch_scores)
            
            print(f"\n📊 BATCH RESULTS:")
            print(f"   Average Score: {avg_score:.1f}/100")
            print(f"   Min Score: {min_score}/100")
            print(f"   Max Score: {max_score}/100")
            
            # Update training metrics
            self.optimizer.update_training_metrics(iteration, max_score, avg_score)
            
            # Check for improvement
            if avg_score > best_score:
                best_score = avg_score
                best_formulation = copy.deepcopy(self.optimizer.weights["formulation"])
                no_improvement_count = 0
                print(f"   🎉 NEW BEST! (previous: {best_score:.1f})")
            else:
                no_improvement_count += 1
                print(f"   No improvement ({no_improvement_count} iterations)")
            
            # Save history
            self.history["iterations"].append(iteration)
            self.history["avg_scores"].append(avg_score)
            self.history["best_scores"].append(best_score)
            self.history["formulations"].append(copy.deepcopy(self.optimizer.weights["formulation"]))
            
            # Early stopping if converged
            if no_improvement_count >= 5:
                print(f"\n✋ EARLY STOPPING: No improvement for 5 iterations")
                break
            
            # Reflection phase - aggregate knowledge gaps
            print(f"\n🤔 REFLECTION PHASE:")
            all_semantic_queries = []
            all_pmc_queries = []
            
            # Reflect on a sample of evaluations (not all 12, too expensive)
            sample_size = min(3, len(batch_evaluations))
            for eval_data in batch_evaluations[:sample_size]:
                test_case = batch[batch_evaluations.index(eval_data)]
                reflection = self.reflector.reflect(
                    test_case=test_case,
                    baseline_recommendation=self.optimizer.calculate(test_case),
                    evaluation_data=eval_data,
                    adjustments_made=[],
                    final_recommendation=self.optimizer.calculate(test_case),
                    final_score=eval_data["overall_score"]
                )
                
                all_semantic_queries.extend(reflection.get("knowledge_gap_queries", []))
                all_pmc_queries.extend(reflection.get("pmc_search_queries", []))
            
            # Deduplicate queries
            unique_semantic = list(set(all_semantic_queries))[:5]
            unique_pmc = list(set(all_pmc_queries))[:5]
            
            print(f"   Found {len(unique_semantic)} semantic queries, {len(unique_pmc)} PMC queries")
            
            # Download new research
            if unique_semantic or unique_pmc:
                print(f"\n📥 DOWNLOADING NEW RESEARCH:")
                download_stats = self.downloader.fill_knowledge_gaps(
                    semantic_queries=unique_semantic,
                    pmc_queries=unique_pmc,
                    max_papers_per_gap=2
                )
                print(f"   Papers downloaded: {download_stats['papers_downloaded']}")
                print(f"   Chunks added: {download_stats['chunks_added']}")
            
            # Calculate averaged gradients (adjustments) across batch
            print(f"\n📐 CALCULATING BATCH GRADIENTS:")
            averaged_adjustments = self._calculate_averaged_adjustments(
                batch, 
                batch_evaluations,
                learning_rate
            )
            
            print(f"   Averaged adjustments:")
            for mineral, delta in averaged_adjustments.items():
                sign = "+" if delta >= 0 else ""
                print(f"     {mineral}: {sign}{delta:.1f}mg")
            
            # Apply adjustments
            if any(abs(delta) > 1 for delta in averaged_adjustments.values()):
                print(f"\n🔧 APPLYING ADJUSTMENTS...")
                self.optimizer.adjust_weights(averaged_adjustments)
                
                # Show updated formulation
                new_form = self.optimizer.weights["formulation"]
                print(f"   Updated formulation:")
                print(f"     Mg: {new_form['magnesium']}mg")
                print(f"     Ca: {new_form['calcium']}mg")
                print(f"     K:  {new_form['potassium']}mg")
                print(f"     Na: {new_form['sodium']}mg")
            else:
                print(f"\n✅ CONVERGED: Adjustments too small, formulation optimized")
                break
        
        # Final summary
        print(f"\n{'='*80}")
        print(f"OPTIMIZATION COMPLETE - {self.use_case.upper()} MIX")
        print(f"{'='*80}")
        print(f"\nBest Average Score: {best_score:.1f}/100")
        print(f"Total Iterations: {iteration}")
        print(f"\nFinal Optimized Formulation:")
        final = best_formulation if best_formulation else self.optimizer.weights["formulation"]
        print(f"  Magnesium: {final['magnesium']}mg")
        print(f"  Calcium: {final['calcium']}mg")
        print(f"  Potassium: {final['potassium']}mg")
        print(f"  Sodium: {final['sodium']}mg")
        print(f"\n{'='*80}\n")
        
        # Save training history
        self._save_history()
        
        return {
            "best_score": best_score,
            "best_formulation": best_formulation,
            "iterations": iteration,
            "history": self.history
        }
    
    def _calculate_averaged_adjustments(self, batch: List[Dict], 
                                       evaluations: List[Dict],
                                       learning_rate: float) -> Dict[str, float]:
        """
        Calculate averaged adjustments across batch (like SGD)
        
        For each mineral, average the suggested changes across all evaluations,
        weighted by how far each score is from 100
        """
        # Get current doses from optimizer
        current_formulation = self.optimizer.weights["formulation"]
        
        adjustments = {
            "magnesium": [],
            "calcium": [],
            "potassium": [],
            "sodium": []
        }
        
        print(f"\n   DEBUG: Evaluating {len(evaluations)} cases")
        print(f"   Current formulation: Mg {current_formulation['magnesium']}mg, Ca {current_formulation['calcium']}mg, K {current_formulation['potassium']}mg, Na {current_formulation['sodium']}mg")
        
        for i, eval_data in enumerate(evaluations, 1):
            grades = eval_data.get("mineral_grades", {})  # Changed from "grades" to "mineral_grades"
            
            print(f"\n   Case {i} grades found: {list(grades.keys())}")
            
            for mineral in adjustments.keys():
                if mineral in grades:
                    score = grades[mineral].get("score", 50)
                    suggestion = grades[mineral].get("suggestion", "No change")
                    current_dose = current_formulation[mineral]
                    
                    # Parse suggestion for dose change (needs current dose to calculate delta)
                    delta = self._parse_dose_suggestion(suggestion, score, current_dose)
                    adjustments[mineral].append(delta)
                    
                    # DEBUG: Show ALL parsing results
                    print(f"     {mineral}: '{suggestion[:60]}...' (score {score}) → {delta:+.1f}mg")
        
        # Average across batch and apply learning rate
        averaged = {}
        for mineral, deltas in adjustments.items():
            if deltas:
                avg_delta = sum(deltas) / len(deltas)
                averaged[mineral] = round(avg_delta * learning_rate, 1)
            else:
                averaged[mineral] = 0
        
        return averaged
    
    def _parse_dose_suggestion(self, suggestion: str, score: int, current_dose: int) -> float:
        """
        Parse dose adjustment from evaluation suggestion
        
        Examples:
        - "Increase to 450mg" with current 400mg -> delta +50mg, dampened to +15mg
        - "Reduce by 50mg" -> delta -50mg, dampened to -15mg
        - "No change" -> 0
        
        Args:
            suggestion: Claude's text suggestion
            score: The grade (0-100)
            current_dose: Current dose for this mineral
            
        Returns:
            Suggested delta (positive = increase, negative = decrease)
        """
        suggestion = suggestion.lower()
        
        if "no change" in suggestion or "keep at" in suggestion:
            return 0
        
        # Error signal based on how far from perfect
        error_signal = (100 - score) / 10  # Scale: 80/100 → 2mg adjustment
        
        import re
        
        # Extract any number followed by "mg" or "mg/day"
        numbers = re.findall(r'(\d+)\s*mg', suggestion)
        
        if not numbers:
            # No specific number, use error signal for direction
            if "increase" in suggestion or "higher" in suggestion or "more" in suggestion:
                return error_signal
            elif "decrease" in suggestion or "reduce" in suggestion or "lower" in suggestion:
                return -error_signal
            else:
                return 0
        
        # Parse the first number as the target dose
        target = int(numbers[0])
        
        # Determine direction and calculate delta
        delta = target - current_dose
        
        if "increase" in suggestion or "raise" in suggestion or "higher" in suggestion:
            # Sanity check: if they said "increase" but target is lower, use error signal
            return delta if delta > 0 else error_signal
        elif "decrease" in suggestion or "reduce" in suggestion or "lower" in suggestion:
            # Sanity check: if they said "decrease" but target is higher, use the delta anyway
            # (Claude might be confused about wording but the number is what matters)
            return delta
        elif "maintain" in suggestion or "keep" in suggestion or "continue" in suggestion:
            # They're saying keep it, but specified a number - check if it matches current
            if abs(target - current_dose) < 5:  # Within 5mg tolerance
                return 0
            else:
                # They said "maintain" but gave different number - use it
                return target - current_dose
        else:
            # Just a number with no clear direction - assume it's the target
            return target - current_dose
    
    def _save_history(self):
        """Save training history to file"""
        filename = f"{self.use_case}_mix_training_history.json"
        with open(filename, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"💾 Training history saved to {filename}")


if __name__ == "__main__":
    # Quick test
    import sys
    
    use_case = sys.argv[1] if len(sys.argv) > 1 else "sleep"
    iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    loop = MixOptimizationLoop(use_case=use_case, batch_size=12)
    results = loop.run(iterations=iterations, learning_rate=0.3)
    
    print(f"\n✅ Optimization complete!")
    print(f"Best score: {results['best_score']:.1f}/100")

