"""
Parallel RAG Evaluator
Runs multiple research queries simultaneously to validate and grade formulation recommendations
"""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from langchain_anthropic import ChatAnthropic


class ParallelEvaluator:
    """
    Evaluates formulation recommendations using parallel RAG queries
    
    For each recommendation, runs 8+ queries simultaneously:
    - 4 mineral-specific queries (Mg, Ca, K, Na)
    - 2 interaction queries (Mg:Ca ratio, K:Na balance)
    - 1 demographic query (age + sex specific)
    - 1 condition query (sleep type specific)
    """
    
    def __init__(self, qdrant_client=None):
        """Initialize RAG components"""
        print("Initializing Parallel Evaluator...")

        # Vector database
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        if qdrant_client is not None:
            self.client = qdrant_client
        else:
            self.client = QdrantClient(path="./bestmove_vector_db")
        self.collection_name = "bestmove_research"
        
        # Claude for reasoning
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=2048,
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        
        print("✅ Evaluator ready")
    
    def evaluate_recommendation(self, 
                                survey_data: Dict[str, Any],
                                recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a formulation recommendation using parallel RAG queries
        
        Args:
            survey_data: Customer survey inputs
            recommendation: Calculated doses {magnesium: 400, calcium: 250, ...}
            
        Returns:
            Dict with scores, feedback, and suggested improvements
        """
        print("\n" + "="*80)
        print("PARALLEL EVALUATION")
        print("="*80)
        
        # Generate all queries
        queries = self._generate_queries(survey_data, recommendation)
        
        print(f"\n🔍 Running {len(queries)} parallel RAG queries...")
        
        # Run queries in parallel
        results = self._run_parallel_queries(queries)
        
        print(f"✅ Retrieved {sum(len(r) for r in results.values())} research excerpts")
        
        # Grade each mineral
        print("\n📊 Grading recommendation...")
        grades = self._grade_recommendation(survey_data, recommendation, results)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(grades)
        
        # Generate improvement suggestions
        improvements = self._generate_improvements(grades, recommendation)
        
        return {
            "overall_score": overall_score,
            "mineral_grades": grades,
            "improvements": improvements,
            "research_count": {k: len(v) for k, v in results.items()},
            "queries_run": list(queries.keys())
        }
    
    def _generate_queries(self, survey_data: Dict, recommendation: Dict) -> Dict[str, str]:
        """
        Generate RAG queries using scientific terminology
        
        Key principles:
        - Use noun phrases, not questions (matches literature style)
        - Use dose ranges, not exact numbers (finds more relevant studies)
        - Use research terminology (sleep onset latency, not "trouble falling asleep")
        - Use demographic terms as adjectives (adults, women, older adults)
        """
        age = survey_data.get("age", 35)
        sex = survey_data.get("sex", "female")
        sleep_issues = survey_data.get("sleep_issues", [])
        use_case = survey_data.get("use_case", "sleep")
        
        # Convert to research-friendly terms
        age_group = "adults" if age < 65 else "older adults"
        sex_term = "women" if sex == "female" else "men"
        
        # Get dose ranges instead of exact numbers
        mg_range = self._get_dose_range(recommendation["magnesium"])
        ca_range = self._get_dose_range(recommendation["calcium"])
        k_range = self._get_dose_range(recommendation["potassium"])
        
        if use_case == "sleep":
            sleep_term = self._map_sleep_issue_to_research_term(sleep_issues)
            
            queries = {
                # Mineral-specific - phrased like RESULTS sections (past tense, effect language)
                "magnesium_dose": f"magnesium {mg_range} supplementation improved reduced {sleep_term} {sex_term} {age_group} participants treatment significant",
                
                "calcium_dose": f"calcium {ca_range} evening bedtime improved sleep architecture quality {age_group} compared placebo",
                
                "potassium_dose": f"potassium {k_range} improved reduced muscle relaxation nocturnal cramps {age_group} sleep quality significant",
                
                "sodium_dose": f"sodium intake restriction evening improved reduced water retention sleep quality participants",
                
                # Interaction queries - mechanism and effects language
                "mg_ca_ratio": f"magnesium calcium ratio GABA neurotransmitter production sleep improvements optimal dose",
                
                "k_na_balance": f"potassium sodium balance electrolyte ratio cellular function sleep effects",
                
                # Demographic - effectiveness language
                "demographic": f"{sex_term} {age_group} {sleep_term} supplementation improved sleep dose response effect significant",
                
                # Condition-specific - outcomes and comparisons
                "sleep_type": f"participants {sleep_term} magnesium calcium improved compared placebo treatment effect dose response"
            }
            
        elif use_case == "active":
            queries = {
                # Results-focused language for athletic performance
                "magnesium_dose": f"athletes magnesium {mg_range} improved exercise performance recovery muscle function cramping reduced significant",
                
                "calcium_dose": f"calcium {ca_range} athletes bone health stress fracture prevention training improved compared",
                
                "potassium_dose": f"potassium {k_range} improved exercise performance reduced muscle cramping fatigue athletes sweat loss",
                
                "sodium_dose": f"sodium replacement improved hydration performance athletes sweat loss exercise compared placebo significant",
                
                "mg_ca_ratio": f"magnesium calcium ratio athletes muscle function contraction relaxation performance improved optimal",
                
                "k_na_balance": f"potassium sodium ratio improved hydration performance athletes electrolyte balance exercise effect",
                
                "demographic": f"athletes {sex_term} {age_group} electrolyte supplementation improved performance endurance recovery significant",
                
                "performance_type": f"athletes training electrolyte replacement improved performance recovery hydration dose effect significant"
            }
            
        else:  # daily
            queries = {
                # Results-focused language for daily wellness
                "magnesium_dose": f"magnesium {mg_range} daily supplementation improved cardiovascular health stress reduction {age_group} significant effect",
                
                "calcium_dose": f"calcium {ca_range} daily supplementation improved bone density osteoporosis prevention {age_group} {sex_term} compared",
                
                "potassium_dose": f"potassium {k_range} daily supplementation reduced blood pressure cardiovascular health {age_group} significant improvement",
                
                "sodium_dose": f"sodium intake reduction daily improved blood pressure health {age_group} compared participants",
                
                "mg_ca_ratio": f"magnesium calcium ratio supplementation improved bone health mineral balance {age_group} optimal effect",
                
                "k_na_balance": f"potassium sodium ratio improved blood pressure cardiovascular health participants dietary balance effect",
                
                "demographic": f"{age_group} {sex_term} daily supplementation improved health outcomes wellness prevention significant effect",
                
                "wellness_type": f"adults daily supplementation improved health markers wellness prevention {age_group} dose response significant"
            }
        
        return queries
    
    def _get_dose_range(self, dose: int) -> str:
        """
        Convert specific dose to research-friendly range
        
        Research papers rarely use exact doses - they use ranges.
        This helps find relevant studies even if exact dose not studied.
        """
        # Define ranges that match common research protocols
        if dose <= 150:
            return "100-200mg"
        elif dose <= 250:
            return "200-300mg"
        elif dose <= 350:
            return "300-400mg"
        elif dose <= 450:
            return "400-500mg"
        elif dose <= 600:
            return "500-600mg"
        else:
            return "500-700mg"
    
    def _map_sleep_issue_to_research_term(self, sleep_issues: List[str]) -> str:
        """
        Map user-friendly sleep issues to research terminology
        
        Users say: "trouble falling asleep"
        Papers say: "sleep onset latency" or "insomnia"
        """
        if not sleep_issues:
            return "sleep quality improvement"
        
        # Research terminology mapping
        research_terms = {
            "trouble_falling_asleep": "sleep onset latency insomnia",
            "trouble falling asleep": "sleep onset latency insomnia",
            "frequent_waking": "sleep maintenance wake after sleep onset",
            "frequent_nighttime_waking": "sleep maintenance wake after sleep onset",
            "frequent nighttime waking": "sleep maintenance wake after sleep onset",
            "early_waking": "early morning awakening sleep duration",
            "early_morning_waking": "early morning awakening sleep duration",
            "early morning waking": "early morning awakening sleep duration",
            "restless_sleep": "sleep quality restless leg syndrome periodic limb movement",
            "restless sleep": "sleep quality restless leg syndrome periodic limb movement"
        }
        
        primary_issue = sleep_issues[0].lower().replace(" ", "_") if sleep_issues else ""
        return research_terms.get(primary_issue, "sleep quality improvement")
    
    def _run_parallel_queries(self, queries: Dict[str, str]) -> Dict[str, List[Dict]]:
        """Run all queries in parallel using thread pool"""
        results = {}
        
        # Use ThreadPoolExecutor for parallel queries
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all queries
            future_to_key = {
                executor.submit(self._query_rag, query): key 
                for key, query in queries.items()
            }
            
            # Collect results as they complete
            for future in future_to_key:
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                    print(f"  ✓ {key}: {len(results[key])} results")
                except Exception as e:
                    print(f"  ✗ {key}: Error - {e}")
                    results[key] = []
        
        return results
    
    def _query_rag(self, query: str, top_k: int = 3) -> List[Dict]:
        """Query the RAG system for research"""
        # Generate embedding
        query_embedding = list(self.embedding_model.embed([query]))[0]
        
        # Search vector store - request more results to allow for deduplication
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=top_k * 3  # Get more results to allow deduplication
        ).points
        
        # Format results and deduplicate by PMCID (or title for Unknown PMCIDs)
        formatted = []
        seen_pmcids = set()
        seen_titles = set()  # Fallback for "Unknown" PMCIDs
        
        for result in search_results:
            payload = result.payload
            
            # Extract PMCID - check multiple possible fields
            pmcid = payload.get("pmcid") or payload.get("pmc_id") or "Unknown"
            title = payload.get("title", "Unknown")
            
            # Deduplicate: if we have a PMCID, use it; otherwise use title
            if pmcid != "Unknown":
                if pmcid in seen_pmcids:
                    continue  # Skip duplicate paper
                seen_pmcids.add(pmcid)
            else:
                # For "Unknown" PMCIDs, use title + journal as fallback dedup key
                title_key = f"{title}_{payload.get('journal', '')}"
                if title_key in seen_titles:
                    continue  # Skip duplicate paper (same title + journal)
                seen_titles.add(title_key)
            
            formatted.append({
                "title": title,
                "text": payload.get("text", "")[:1000],  # First 1000 chars
                "pmcid": pmcid,
                "score": result.score,
                "journal": payload.get("journal", "Unknown"),
                "year": payload.get("year", "Unknown")
            })
            
            # Stop when we have enough unique results
            if len(formatted) >= top_k:
                break
        
        return formatted
    
    def _grade_recommendation(self, survey_data: Dict, recommendation: Dict, 
                             research_results: Dict) -> Dict[str, Dict]:
        """Grade each mineral using Claude + research"""
        grades = {}
        
        for mineral in ["magnesium", "calcium", "potassium", "sodium"]:
            dose = recommendation[mineral]
            
            # Get relevant research
            mineral_research = research_results.get(f"{mineral}_dose", [])
            demographic_research = research_results.get("demographic", [])
            
            # Combine research
            context = self._format_research_context(mineral_research + demographic_research[:2])
            
            # Ask Claude to grade - be OPINIONATED and PRECISE
            prompt = f"""You are an expert nutritionist evaluating the OPTIMAL {mineral.upper()} DOSE (not other minerals - ONLY {mineral}).

Customer Profile:
- Age: {survey_data.get('age')}
- Sex: {survey_data.get('sex')}
- Sleep Issues: {', '.join(survey_data.get('sleep_issues', ['none']))}
- Current {mineral} intake: {survey_data.get(f'{mineral}_intake', 'unknown')}mg/day

Recommended {mineral.upper()} Dose: {dose}mg

Research Context:
{context}

Your task: Estimate the PRECISE optimal {mineral} dose for THIS person. Don't settle for "acceptable" - push for exactness.

Think like dose-response curves:
- If research shows 300mg improved X%, and 400mg improved Y%, what maximizes benefit?
- For this age/sex/condition, where on the curve should they be?
- Make your best estimate even if uncertain - we aggregate many estimates for accuracy.

Grade 0-100 based on how close {dose}mg is to YOUR estimated optimal {mineral} dose:
- 100 = {dose}mg IS optimal
- 90-99 = Very close, small adjustment helps
- 80-89 = Good but meaningfully suboptimal
- 70-79 = Acceptable but clear room for improvement
- <70 = Significantly off optimal

Be opinionated and specific. If you think 420mg {mineral} is better than {dose}mg {mineral}, say exactly that.

CRITICAL: Your suggestion must specify {mineral} ONLY. Don't mention other minerals.

Respond in this exact format:
SCORE: [0-100]
FEEDBACK: [Why this score? What's your optimal {mineral} dose?]
SUGGESTION: [e.g., "Increase to 420mg" or "Reduce to 375mg" or "Keep at {dose}mg"]"""

            try:
                response = self.llm.invoke(prompt)
                grade_data = self._parse_grade_response(response.content)
                grades[mineral] = grade_data
            except Exception as e:
                print(f"  Error grading {mineral}: {e}")
                grades[mineral] = {
                    "score": 50,
                    "feedback": f"Error during evaluation: {e}",
                    "suggestion": "No change"
                }
        
        return grades
    
    def _format_research_context(self, research: List[Dict]) -> str:
        """Format research for Claude"""
        if not research:
            return "No specific research found."
        
        context_parts = []
        for i, paper in enumerate(research[:3], 1):
            context_parts.append(
                f"[Study {i}] {paper['title']} ({paper['journal']}, {paper['year']})\n"
                f"{paper['text'][:500]}...\n"
                f"PMC ID: {paper['pmcid']}"
            )
        
        return "\n\n".join(context_parts)
    
    def _parse_grade_response(self, response: str) -> Dict:
        """Parse Claude's grading response"""
        lines = response.strip().split("\n")
        
        score = 50  # default
        feedback = ""
        suggestion = ""
        
        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score = int(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
            elif line.startswith("SUGGESTION:"):
                suggestion = line.split(":", 1)[1].strip()
        
        return {
            "score": score,
            "feedback": feedback,
            "suggestion": suggestion
        }
    
    def _calculate_overall_score(self, grades: Dict) -> int:
        """Calculate weighted overall score"""
        # Weight: Magnesium is most important for sleep
        weights = {
            "magnesium": 0.5,  # 50%
            "calcium": 0.25,   # 25%
            "potassium": 0.15, # 15%
            "sodium": 0.10     # 10%
        }
        
        weighted_sum = 0
        for mineral, weight in weights.items():
            weighted_sum += grades[mineral]["score"] * weight
        
        return round(weighted_sum)
    
    def _generate_improvements(self, grades: Dict, current_doses: Dict) -> List[Dict]:
        """Generate actionable improvement suggestions"""
        improvements = []
        
        for mineral, grade in grades.items():
            if grade["score"] < 80 and "no change" not in grade["suggestion"].lower():
                improvements.append({
                    "mineral": mineral,
                    "current_dose": current_doses[mineral],
                    "issue": grade["feedback"],
                    "suggested_change": grade["suggestion"],
                    "priority": "high" if grade["score"] < 60 else "medium"
                })
        
        # Sort by priority
        improvements.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
        
        return improvements


if __name__ == "__main__":
    # Test the evaluator
    evaluator = ParallelEvaluator()
    
    test_survey = {
        "age": 35,
        "sex": "female",
        "weight": 140,
        "sleep_issues": ["Trouble falling asleep", "Frequent nighttime waking"],
        "magnesium_intake": 200,
        "calcium_intake": 800,
        "potassium_intake": 2000,
        "sodium_intake": 2200
    }
    
    test_recommendation = {
        "magnesium": 400,
        "calcium": 250,
        "potassium": 200,
        "sodium": 100
    }
    
    evaluation = evaluator.evaluate_recommendation(test_survey, test_recommendation)
    
    print("\n" + "="*80)
    print(f"OVERALL SCORE: {evaluation['overall_score']}/100")
    print("="*80)
    
    for mineral, grade in evaluation["mineral_grades"].items():
        print(f"\n{mineral.upper()}: {grade['score']}/100")
        print(f"  {grade['feedback']}")
        if grade['suggestion']:
            print(f"  → {grade['suggestion']}")
    
    if evaluation["improvements"]:
        print("\n" + "="*80)
        print("SUGGESTED IMPROVEMENTS:")
        print("="*80)
        for imp in evaluation["improvements"]:
            print(f"\n{imp['mineral'].upper()} ({imp['priority']} priority):")
            print(f"  Current: {imp['current_dose']}mg")
            print(f"  Issue: {imp['issue']}")
            print(f"  Change: {imp['suggested_change']}")


