"""
Self-Improvement Loop
Continuously refines formulation algorithms using RAG-powered feedback

Process:
1. Generate test case
2. Calculate recommendation
3. Evaluate with parallel RAG queries (8+)
4. Grade (0-100)
5. Adjust weights
6. Re-test
7. Keep if improved, revert if worse
"""

import json
import copy
import os
import glob
from datetime import datetime
from typing import Dict, List
from sleep_support_engine import SleepSupportEngine
from parallel_evaluator import ParallelEvaluator
from reasoning_reflector import ReasoningReflector
from targeted_research_downloader import TargetedResearchDownloader


class ImprovementLoop:
    """
    Self-improving algorithm system
    
    Iterates through test cases, evaluates performance, and automatically
    adjusts algorithm weights to improve recommendations
    """
    
    def __init__(self, engine_type: str = "sleep_support"):
        """Initialize improvement loop"""
        print("="*80)
        print("BESTMOVE SELF-IMPROVING ALGORITHM SYSTEM")
        print("="*80)
        
        self.engine_type = engine_type
        
        # Load engine
        print(f"\n📦 Loading {engine_type} engine...")
        if engine_type == "sleep_support":
            self.engine = SleepSupportEngine()
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
        
        # Load shared vector database client
        import qdrant_client
        vector_db_path = "./bestmove_vector_db"
        self.qdrant_client = qdrant_client.QdrantClient(path=vector_db_path)

        # Load evaluator (pass shared client)
        self.evaluator = ParallelEvaluator(qdrant_client=self.qdrant_client)

        # Load reasoning reflector
        print("📋 Loading reasoning reflector (Claude Sonnet 4.5)...")
        self.reflector = ReasoningReflector()
        
        # Track improvements
        self.iteration_history = []
        self.best_score = 0
        self.improvement_count = 0
        
        print("✅ System ready for self-improvement with metacognitive reflection")
    
    def run_improvement_cycle(self, test_cases: List[Dict], max_iterations: int = 5):
        """
        Run complete improvement cycle
        
        Args:
            test_cases: List of test customer profiles
            max_iterations: Max times to try improving each case
        """
        print("\n" + "="*80)
        print(f"STARTING IMPROVEMENT CYCLE")
        print(f"Test Cases: {len(test_cases)}")
        print(f"Max Iterations: {max_iterations}")
        print("="*80)
        
        for case_idx, test_case in enumerate(test_cases, 1):
            print(f"\n\n{'='*80}")
            print(f"TEST CASE {case_idx}/{len(test_cases)}")
            print(f"Age: {test_case.get('age')}, Sex: {test_case.get('sex')}, "
                  f"Issues: {', '.join(test_case.get('sleep_issues', []))}")
            print("="*80)
            
            self._improve_for_test_case(test_case, max_iterations)
        
        # Print final summary
        self._print_improvement_summary()
        
        # Offer to fill knowledge gaps
        self._offer_knowledge_gap_filling()
    
    def _improve_for_test_case(self, test_case: Dict, max_iterations: int):
        """Improve algorithm for a specific test case"""
        
        # Initial evaluation
        print("\n🧪 ITERATION 0 (Baseline)")
        print("-" * 80)
        
        recommendation = self.engine.calculate(test_case)
        evaluation = self.evaluator.evaluate_recommendation(test_case, recommendation)
        
        baseline_score = evaluation["overall_score"]
        current_score = baseline_score
        
        print(f"\n📊 Baseline Score: {baseline_score}/100")
        self._print_recommendation(recommendation)
        
        # Save baseline weights and recommendation for reflection
        baseline_weights = copy.deepcopy(self.engine.weights)
        best_weights = copy.deepcopy(baseline_weights)
        baseline_recommendation = copy.deepcopy(recommendation)
        
        # Improvement iterations
        for iteration in range(1, max_iterations + 1):
            print(f"\n\n🔄 ITERATION {iteration}")
            print("-" * 80)
            
            # Adjust weights based on feedback
            improvements_made = self._adjust_weights(evaluation, test_case, recommendation)
            
            if not improvements_made:
                print("ℹ️  No improvements to make - algorithm is optimal for this case")
                break
            
            # Re-calculate with new weights
            new_recommendation = self.engine.calculate(test_case)
            new_evaluation = self.evaluator.evaluate_recommendation(test_case, new_recommendation)
            new_score = new_evaluation["overall_score"]
            
            print(f"\n📊 New Score: {new_score}/100 (was {current_score}/100)")
            self._print_recommendation(new_recommendation)
            
            # Decide: keep or revert?
            if new_score > current_score:
                improvement = new_score - current_score
                print(f"\n✅ IMPROVEMENT! (+{improvement} points) - Keeping changes")
                current_score = new_score
                best_weights = copy.deepcopy(self.engine.weights)
                self.improvement_count += 1
                
                # Update for next iteration
                evaluation = new_evaluation
                recommendation = new_recommendation
            else:
                decline = current_score - new_score
                print(f"\n❌ DECLINED (-{decline} points) - Reverting changes")
                self.engine.weights = copy.deepcopy(best_weights)
                # Don't update evaluation/recommendation - keep trying from best state
        
        # Generate metacognitive reflection
        reflection = self.reflector.reflect(
            test_case=test_case,
            baseline_recommendation=baseline_recommendation,
            evaluation_data=evaluation,
            adjustments_made=evaluation.get("improvements", []),
            final_recommendation=recommendation,
            final_score=current_score
        )
        
        # Record this test case's results
        self.iteration_history.append({
            "test_case": test_case,
            "baseline_score": baseline_score,
            "final_score": current_score,
            "improvement": current_score - baseline_score,
            "iterations": iteration,
            "reflection": reflection
        })
        
        # Save if we improved
        if current_score > baseline_score:
            print(f"\n💾 Saving improved weights (score: {baseline_score} → {current_score})")
            self.engine.save_weights()
    
    def _adjust_weights(self, evaluation: Dict, test_case: Dict, 
                       current_recommendation: Dict) -> bool:
        """
        Adjust algorithm weights based on evaluation feedback
        
        Returns: True if adjustments were made, False if no improvements needed
        """
        improvements = evaluation["improvements"]
        
        if not improvements:
            return False
        
        print(f"\n🔧 Applying {len(improvements)} adjustments:")
        
        for improvement in improvements:
            mineral = improvement["mineral"]
            current_dose = improvement["current_dose"]
            suggestion = improvement.get("suggested_change", "No specific suggestion")
            
            print(f"\n  {mineral.upper()}:")
            print(f"    Current: {current_dose}mg")
            print(f"    Feedback: {suggestion}")
            
            # Parse suggestion and adjust weights
            adjustment = self._parse_and_apply_suggestion(
                mineral, suggestion, test_case, current_dose
            )
            
            if adjustment:
                print(f"    Applied: {adjustment}")
        
        return True
    
    def _parse_and_apply_suggestion(self, mineral: str, suggestion: str, 
                                    test_case: Dict, current_dose: float) -> str:
        """
        Parse Claude's suggestion and adjust weights accordingly
        
        Examples of suggestions:
        - "Increase to 450mg for better sleep onset support"
        - "Reduce calcium to 200mg to improve Mg:Ca ratio"
        - "Add 50mg for frequent waking"
        """
        suggestion_lower = suggestion.lower()
        
        # Extract target dose if mentioned
        import re
        dose_match = re.search(r'(\d+)\s*mg', suggestion_lower)
        target_dose = int(dose_match.group(1)) if dose_match else None
        
        if target_dose:
            # Calculate needed adjustment
            change_pct = (target_dose - current_dose) / current_dose
            
            # Determine which weight to adjust
            age = test_case.get("age", 35)
            sex = test_case.get("sex", "female")
            sleep_issues = test_case.get("sleep_issues", [])
            
            weights = self.engine.weights[mineral]
            
            # Adjust the most relevant weight
            if "age" in suggestion_lower or age > 50:
                # Adjust age multiplier
                age_group = self.engine._get_age_group(age)
                old_mult = weights["age_multipliers"][age_group]
                new_mult = old_mult * (1 + change_pct * 0.5)  # 50% of needed change
                weights["age_multipliers"][age_group] = round(new_mult, 2)
                return f"Age mult {age_group}: {old_mult} → {new_mult:.2f}"
            
            elif "sex" in suggestion_lower or ("female" in suggestion_lower and sex == "female"):
                # Adjust sex multiplier
                old_mult = weights["sex_multipliers"][sex.lower()]
                new_mult = old_mult * (1 + change_pct * 0.5)
                weights["sex_multipliers"][sex.lower()] = round(new_mult, 2)
                return f"Sex mult: {old_mult} → {new_mult:.2f}"
            
            elif any(issue_word in suggestion_lower for issue_word in ["onset", "waking", "restless"]):
                # Adjust sleep issue weights
                if mineral == "magnesium" and "sleep_issue_adjustments" in weights:
                    for issue in sleep_issues:
                        issue_key = issue.lower().replace(" ", "_")
                        if issue_key in weights["sleep_issue_adjustments"]:
                            old_adj = weights["sleep_issue_adjustments"][issue_key]
                            change_amt = (target_dose - current_dose) * 0.7  # 70% of gap
                            new_adj = old_adj + change_amt
                            weights["sleep_issue_adjustments"][issue_key] = round(new_adj)
                            return f"Sleep issue '{issue}' adjustment: {old_adj}mg → {new_adj:.0f}mg"
            
            else:
                # Adjust base dose
                old_base = weights["base_dose"]
                new_base = old_base * (1 + change_pct * 0.3)  # 30% of needed change
                weights["base_dose"] = round(new_base)
                return f"Base dose: {old_base}mg → {new_base:.0f}mg"
        
        return "Unable to parse specific adjustment"
    
    def _print_recommendation(self, rec: Dict):
        """Print recommendation in readable format"""
        print(f"  Mg: {rec['magnesium']}mg | Ca: {rec['calcium']}mg | "
              f"K: {rec['potassium']}mg | Na: {rec['sodium']}mg")
    
    def _print_improvement_summary(self):
        """Print summary of all improvements"""
        print("\n\n" + "="*80)
        print("IMPROVEMENT SUMMARY")
        print("="*80)
        
        total_cases = len(self.iteration_history)
        total_improvements = sum(1 for h in self.iteration_history if h["improvement"] > 0)
        avg_improvement = sum(h["improvement"] for h in self.iteration_history) / total_cases if total_cases > 0 else 0
        
        print(f"\nTest Cases: {total_cases}")
        print(f"Cases Improved: {total_improvements}/{total_cases}")
        print(f"Average Improvement: +{avg_improvement:.1f} points")
        print(f"Total Weight Adjustments: {self.improvement_count}")
        
        print("\n" + "-"*80)
        print("Per-Case Results (with Confidence Scores):")
        print("-"*80)
        
        for i, history in enumerate(self.iteration_history, 1):
            improvement = history["improvement"]
            symbol = "✅" if improvement > 0 else "➖"
            confidence = history.get("reflection", {}).get("confidence_score", 0)
            conf_symbol = "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
            
            print(f"{symbol} Case {i}: {history['baseline_score']} → {history['final_score']} "
                  f"({'+' if improvement >= 0 else ''}{improvement} pts, {history['iterations']} iterations) "
                  f"{conf_symbol} Confidence: {confidence}%")
            
            # Print key gap query if any
            gap_queries = history.get("reflection", {}).get("knowledge_gap_queries", [])
            if gap_queries and len(gap_queries) > 0:
                print(f"   🔍 Gap: {gap_queries[0][:70]}..." if len(gap_queries[0]) > 70 else f"   🔍 Gap: {gap_queries[0]}")
        
        print("\n" + "="*80)
    
    def _offer_knowledge_gap_filling(self):
        """Collect all knowledge gap queries and automatically download research"""
        # Collect all unique gap queries
        all_gap_queries = []
        for history in self.iteration_history:
            reflection = history.get("reflection", {})
            queries = reflection.get("knowledge_gap_queries", [])
            all_gap_queries.extend(queries)

        # Remove duplicates while preserving order
        unique_queries = []
        seen = set()
        for query in all_gap_queries:
            if query.lower() not in seen:
                unique_queries.append(query)
                seen.add(query.lower())

        if not unique_queries:
            print("\n✅ No knowledge gaps identified - research coverage is complete!")
            return

        print("\n" + "="*80)
        print("KNOWLEDGE GAPS IDENTIFIED")
        print("="*80)
        print(f"\nThe AI identified {len(unique_queries)} research gaps that could improve recommendations:")
        print()

        for i, query in enumerate(unique_queries, 1):
            print(f"{i}. {query}")

        print("\n" + "-"*80)
        print("AUTOMATIC RESEARCH DOWNLOAD")
        print("-"*80)
        print("The system will automatically:")
        print("  • Search PubMed Central for these specific papers")
        print("  • Download only NEW papers (no duplicates)")
        print("  • Evaluate research quality and relevance")
        print("  • Process and add good research to vector database")
        print("  • Log insufficient research for manual review")
        print()

        # Automatically download and evaluate research
        print("\n🚀 Starting targeted research download and evaluation...")
        downloader = TargetedResearchDownloader(qdrant_client=self.qdrant_client)
        evaluator = ResearchQualityEvaluator()

        # Download research
        download_stats = downloader.fill_knowledge_gaps(unique_queries, max_papers_per_gap=3)

        if download_stats["papers_downloaded"] > 0:
            print(f"\n✅ Downloaded {download_stats['papers_downloaded']} new papers!")

            # Evaluate research quality
            quality_results = evaluator.evaluate_research_quality(unique_queries, download_stats)

            # Process results
            self._process_research_evaluation(quality_results, unique_queries)

        else:
            print("\nℹ️  No new papers found - existing database covers these topics")

    def _process_research_evaluation(self, quality_results: Dict, original_queries: List[str]):
        """Process research quality evaluation results and decide what to do"""
        good_research = quality_results.get("good_research", {})
        bad_research = quality_results.get("bad_research", {})

        print("\n" + "="*80)
        print("RESEARCH QUALITY EVALUATION RESULTS")
        print("="*80)

        # Process good research
        if good_research:
            print(f"\n✅ GOOD RESEARCH ({len(good_research)} queries with quality matches)")
            for query, papers in good_research.items():
                print(f"  • '{query}' → {len(papers)} relevant papers")
                print("    → Research integrated successfully")

            print("\n💡 Running improvement cycle again to leverage new research...")
            # Re-run improvement cycle with new research
            test_cases = generate_test_cases()
            self.run_improvement_cycle(test_cases, max_iterations=2)

        # Process bad research
        if bad_research:
            print(f"\n❌ INSUFFICIENT RESEARCH ({len(bad_research)} queries need manual attention)")

            # Delete bad research files
            self._delete_bad_research(bad_research)

            # Create research needs document
            self._create_research_needs_document(bad_research)

            print("   → Logged to research_needs.md for manual review")
        if not good_research and not bad_research:
            print("\n⚠️  No research evaluation results - nothing to process")

    def _create_research_needs_document(self, bad_research: Dict):
        """Create a document tracking research gaps that need manual attention"""
        research_needs_file = "/home/jschu/projects/Agentic.RAG/research_needs.md"

        # Create or append to research needs document
        with open(research_needs_file, "a") as f:
            f.write(f"\n\n## Research Gaps Requiring Manual Attention - {datetime.now().isoformat()}\n")
            f.write("="*80 + "\n\n")

            for query, issues in bad_research.items():
                f.write(f"### Query: {query}\n")
                f.write(f"Issues: {', '.join(issues)}\n")
                f.write("**Recommended Actions:**\n")
                f.write("- Manual literature search in academic databases\n")
                f.write("- Contact domain experts for insights\n")
                f.write("- Commission targeted research if gap is critical\n\n")
                f.write("-" * 60 + "\n")

        print(f"📋 Research needs documented in: {research_needs_file}")

    def _delete_bad_research(self, bad_research: Dict):
        """Delete research files that don't meet quality standards"""
        deleted_count = 0

        # Get all downloaded papers
        xml_files = glob.glob("/home/jschu/projects/Agentic.RAG/downloaded_papers/*.xml")

        for xml_file in xml_files:
            try:
                filename = os.path.basename(xml_file)
                # Extract PMC ID from filename (e.g., PMC123456.xml -> 123456)
                pmc_id_num = filename.replace("PMC", "").replace(".xml", "")

                # Check if this paper should be deleted
                should_delete = False
                for query, issues in bad_research.items():
                    # If this paper was downloaded for a bad query, delete it
                    if any(pmc_id_num in issue for issue in issues):
                        should_delete = True
                        break

                if should_delete:
                    os.remove(xml_file)
                    deleted_count += 1
                    print(f"   🗑️  Deleted poor quality research: {filename}")

            except Exception as e:
                print(f"   ⚠️  Could not process file {xml_file}: {e}")

        if deleted_count > 0:
            print(f"\n🗑️  Deleted {deleted_count} poor quality research files")


class ResearchQualityEvaluator:
    """
    Evaluates the quality and relevance of downloaded research papers
    Uses LLM to assess how well papers match the original search queries
    """

    def __init__(self):
        # We'll use the same Anthropic client as the reasoning reflector
        import os
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            # Try to load from bashrc
            try:
                import subprocess
                result = subprocess.run(['bash', '-c', 'source ~/.bashrc && echo $ANTHROPIC_API_KEY'],
                                      capture_output=True, text=True)
                self.anthropic_api_key = result.stdout.strip()
            except:
                self.anthropic_api_key = None

        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

    def evaluate_research_quality(self, queries: List[str], download_stats: Dict) -> Dict:
        """
        Evaluate if downloaded papers actually address the knowledge gaps

        Returns:
        {
            "good_research": {query: [paper_ids]},
            "bad_research": {query: [issues]}
        }
        """
        from anthropic import Anthropic
        import glob

        client = Anthropic(api_key=self.anthropic_api_key)

        # Get recently downloaded papers
        recent_papers = self._get_recently_downloaded_papers()

        good_research = {}
        bad_research = {}

        print("\n🔍 Evaluating research quality using Claude Sonnet 4.5...")
        print(f"   Found {len(recent_papers)} recent papers to evaluate")

        for query in queries:
            print(f"\n   Evaluating query: '{query[:60]}...'")

            # Sample a few papers for this query
            sample_papers = recent_papers[:3]  # Evaluate first 3 papers

            if not sample_papers:
                bad_research[query] = ["No papers found for this query"]
                continue

            # Prepare evaluation prompt
            prompt = self._create_evaluation_prompt(query, sample_papers)

            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.1,
                    system="You are a research quality evaluator. Be precise and factual.",
                    messages=[{"role": "user", "content": prompt}]
                )

                result = self._parse_evaluation_response(response.content[0].text)

                if result["quality_score"] >= 7:  # Good enough quality
                    good_research[query] = [p["pmc_id"] for p in sample_papers]
                    print(f"     ✅ Quality score: {result['quality_score']}/10")
                else:
                    bad_research[query] = result["issues"]
                    print(f"     ❌ Quality score: {result['quality_score']}/10 - {', '.join(result['issues'][:2])}")

            except Exception as e:
                print(f"     ⚠️  Evaluation failed: {str(e)}")
                bad_research[query] = [f"Evaluation error: {str(e)}"]

        return {
            "good_research": good_research,
            "bad_research": bad_research
        }

    def _get_recently_downloaded_papers(self) -> List[Dict]:
        """Get list of recently downloaded papers"""
        papers = []
        try:
            # Look for recently downloaded XML files
            xml_files = glob.glob("/home/jschu/projects/Agentic.RAG/downloaded_papers/*.xml")
            xml_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first

            for xml_file in xml_files[:10]:  # Check last 10 downloads
                try:
                    # Extract PMC ID from filename
                    filename = os.path.basename(xml_file)
                    pmc_id = filename.replace("PMC", "").replace(".xml", "")

                    papers.append({
                        "pmc_id": f"PMC{pmc_id}",
                        "file_path": xml_file,
                        "filename": filename
                    })
                except:
                    continue

        except Exception as e:
            print(f"Warning: Could not find recent papers: {e}")

        return papers

    def _create_evaluation_prompt(self, query: str, papers: List[Dict]) -> str:
        """Create prompt for evaluating research quality"""
        papers_text = ""
        for i, paper in enumerate(papers, 1):
            papers_text += f"\nPAPER {i}:\n"
            papers_text += f"PMC ID: {paper['pmc_id']}\n"
            papers_text += f"Filename: {paper['filename']}\n"

            # Try to extract title and abstract from XML
            try:
                # Simple XML parsing to get title and abstract
                import xml.etree.ElementTree as ET
                tree = ET.parse(paper['file_path'])
                root = tree.getroot()

                # Try to find title
                title_elem = root.find(".//article-title")
                if title_elem is not None and title_elem.text:
                    papers_text += f"Title: {title_elem.text.strip()}\n"

                # Try to find abstract
                abstract_elem = root.find(".//abstract")
                if abstract_elem is not None:
                    abstract_text = ""
                    for p in abstract_elem.findall(".//p"):
                        if p.text:
                            abstract_text += p.text.strip() + " "
                    if abstract_text.strip():
                        papers_text += f"Abstract: {abstract_text.strip()[:300]}...\n"
            except:
                papers_text += "Content: Could not extract from XML\n"

        prompt = f"""
        Please evaluate how well these research papers address the following knowledge gap:

        QUERY: "{query}"

        {papers_text}

        Please rate the overall quality and relevance on a scale of 1-10 (where 10 is perfect match for the query).

        Also identify any specific issues or limitations:

        RESPONSE FORMAT:
        QUALITY_SCORE: [1-10]
        ISSUES: [comma-separated list of specific issues, or "none" if no issues]
        RELEVANCE_ASSESSMENT: [brief explanation of how well papers address the query]
        """
        return prompt

    def _parse_evaluation_response(self, response: str) -> Dict:
        """Parse Claude's evaluation response"""
        result = {
            "quality_score": 5,  # default
            "issues": ["Could not parse response"],
            "assessment": "Unknown"
        }

        try:
            # Extract quality score
            import re
            score_match = re.search(r'QUALITY_SCORE:\s*(\d+)', response, re.IGNORECASE)
            if score_match:
                result["quality_score"] = int(score_match.group(1))

            # Extract issues
            issues_match = re.search(r'ISSUES:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if issues_match:
                issues_text = issues_match.group(1).strip()
                if issues_text.lower() != "none":
                    result["issues"] = [issue.strip() for issue in issues_text.split(",") if issue.strip()]
                else:
                    result["issues"] = []

            # Extract assessment
            assessment_match = re.search(r'RELEVANCE_ASSESSMENT:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if assessment_match:
                result["assessment"] = assessment_match.group(1).strip()

        except Exception as e:
            print(f"Warning: Could not parse evaluation: {e}")

        return result


def generate_test_cases() -> List[Dict]:
    """Generate diverse test cases for algorithm improvement"""
    return [
        # Case 1: Young woman with sleep onset issues
        {
            "age": 28,
            "sex": "female",
            "weight": 135,
            "sleep_issues": ["Trouble falling asleep"],
            "magnesium_intake": 180,
            "calcium_intake": 750,
            "potassium_intake": 1900,
            "sodium_intake": 2100,
            "medications": []
        },
        
        # Case 2: Middle-aged man with frequent waking
        {
            "age": 45,
            "sex": "male",
            "weight": 185,
            "sleep_issues": ["Frequent nighttime waking", "Restless sleep"],
            "magnesium_intake": 250,
            "calcium_intake": 900,
            "potassium_intake": 2300,
            "sodium_intake": 2400,
            "medications": []
        },
        
        # Case 3: Older woman, low mineral intake
        {
            "age": 62,
            "sex": "female",
            "weight": 145,
            "sleep_issues": ["Trouble falling asleep", "Early morning waking"],
            "magnesium_intake": 150,
            "calcium_intake": 650,
            "potassium_intake": 1600,
            "sodium_intake": 1800,
            "medications": ["blood_pressure_meds"]
        },
    ]


if __name__ == "__main__":
    # Run improvement cycle
    loop = ImprovementLoop("sleep_support")
    
    test_cases = generate_test_cases()
    
    loop.run_improvement_cycle(test_cases, max_iterations=3)
    
    print("\n✅ Self-improvement cycle complete!")
    print("Algorithm weights have been updated based on research findings.")

