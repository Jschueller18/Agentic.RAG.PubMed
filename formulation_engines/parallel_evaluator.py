"""
Parallel RAG Evaluator
Runs multiple research queries simultaneously to validate and grade formulation recommendations
"""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from fastembed import TextEmbedding
import qdrant_client
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
            self.client = qdrant_client.QdrantClient(path="./bestmove_vector_db")
        self.collection_name = "bestmove_research"
        
        # Claude for reasoning
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
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
        """Generate all evaluation queries"""
        age = survey_data.get("age", 35)
        sex = survey_data.get("sex", "female")
        sleep_issues = survey_data.get("sleep_issues", [])
        
        mg = recommendation["magnesium"]
        ca = recommendation["calcium"]
        k = recommendation["potassium"]
        na = recommendation["sodium"]
        
        queries = {
            # Mineral-specific queries
            "magnesium_dose": f"Is {mg}mg magnesium optimal dose for sleep quality in {age} year old {sex}?",
            "calcium_dose": f"Is {ca}mg calcium appropriate for bedtime sleep support?",
            "potassium_dose": f"Does {k}mg potassium affect sleep quality and muscle relaxation?",
            "sodium_dose": f"Should sodium be {na}mg for evening electrolyte support?",
            
            # Interaction queries
            "mg_ca_ratio": f"What is optimal magnesium to calcium ratio for sleep? Current: {mg}mg Mg, {ca}mg Ca",
            "k_na_balance": f"What is optimal potassium to sodium balance for nighttime? Current: {k}mg K, {na}mg Na",
            
            # Demographic query
            "demographic": f"Optimal electrolyte doses for sleep in {age} year old {sex} with {', '.join(sleep_issues) if sleep_issues else 'general sleep support'}",
            
            # Condition-specific query
            "sleep_type": self._generate_sleep_query(sleep_issues, sex, age)
        }
        
        return queries
    
    def _generate_sleep_query(self, sleep_issues: List[str], sex: str, age: int) -> str:
        """Generate sleep-type specific query"""
        if not sleep_issues:
            return f"General electrolyte support for sleep quality in {age} year old {sex}"
        
        # Map sleep issues to research queries
        issue_map = {
            "trouble falling asleep": "sleep onset latency reduction",
            "frequent nighttime waking": "sleep maintenance and reducing wake episodes",
            "early morning waking": "preventing early awakening",
            "restless sleep": "improving sleep quality and reducing movement"
        }
        
        primary_issue = sleep_issues[0].lower() if sleep_issues else "general sleep"
        research_term = issue_map.get(primary_issue, "sleep quality improvement")
        
        return f"Magnesium and calcium doses for {research_term} in {sex} adults age {age}"
    
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
        
        # Search vector store
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=top_k
        ).points
        
        # Format results
        formatted = []
        for result in search_results:
            payload = result.payload
            formatted.append({
                "title": payload.get("title", "Unknown"),
                "text": payload.get("text", "")[:1000],  # First 1000 chars
                "pmcid": payload.get("pmcid", "Unknown"),
                "score": result.score,
                "journal": payload.get("journal", "Unknown"),
                "year": payload.get("year", "Unknown")
            })
        
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
            
            # Ask Claude to grade
            prompt = f"""You are an expert nutritionist evaluating an electrolyte formulation.

Customer Profile:
- Age: {survey_data.get('age')}
- Sex: {survey_data.get('sex')}
- Sleep Issues: {', '.join(survey_data.get('sleep_issues', ['none']))}
- Current {mineral} intake: {survey_data.get(f'{mineral}_intake', 'unknown')}mg/day

Recommended Dose: {dose}mg {mineral}

Research Context:
{context}

Grade this {mineral} dose from 0-100 based on:
1. Safety (is it within safe limits?)
2. Efficacy (will it help their sleep issues?)
3. Research backing (does research support this dose?)
4. Individual fit (right for their age/sex/needs?)

Respond in this exact format:
SCORE: [0-100]
FEEDBACK: [2-3 sentences explaining the score]
SUGGESTION: [specific dose adjustment if needed, or "No change needed"]"""

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


