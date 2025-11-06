"""
Reasoning Reflector - Metacognitive Analysis Layer

Provides transparent insight into the AI's decision-making process:
- Summary of thought process
- Confidence assessment based on research quality
- Identification of knowledge gaps
- Explanation of why adjustments were made
"""

import os
from typing import Dict, List, Any
from langchain_anthropic import ChatAnthropic


class ReasoningReflector:
    """
    Meta-reasoning layer that explains the AI's thought process
    
    Analyzes the entire evaluation cycle and provides:
    1. Thought process summary
    2. Confidence score (0-100) based on research quality
    3. Knowledge gaps identified
    4. Reasoning for each adjustment
    """
    
    def __init__(self):
        """Initialize Claude Haiku for reflection"""
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.3,  # Slightly higher for more natural explanation
            max_tokens=4096,  # Longer for detailed reflection
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
    
    def reflect(self, 
                test_case: Dict[str, Any],
                baseline_recommendation: Dict[str, Any],
                evaluation_data: Dict[str, Any],
                adjustments_made: List[Dict[str, Any]],
                final_recommendation: Dict[str, Any],
                final_score: int) -> Dict[str, Any]:
        """
        Generate metacognitive reflection on the evaluation process
        
        Args:
            test_case: Customer profile
            baseline_recommendation: Initial doses calculated
            evaluation_data: All RAG queries and research results
            adjustments_made: Weight changes applied
            final_recommendation: Adjusted doses
            final_score: Final grade (0-100)
            
        Returns:
            Dict with thought_process, confidence, gaps, and reasoning
        """
        
        print("\n🧠 REASONING REFLECTION (Claude Haiku)")
        print("-" * 80)
        
        # Build comprehensive context
        context = self._build_context(
            test_case,
            baseline_recommendation,
            evaluation_data,
            adjustments_made,
            final_recommendation,
            final_score
        )
        
        # Prompt for reflection
        prompt = f"""You are a metacognitive AI analyzing an electrolyte formulation recommendation.

## IMPORTANT: RAG stands for "Retrieval-Augmented Generation" - a technique where we search a research database (retrieval) and use those findings to inform AI reasoning (augmented generation). When you see "RAG Evaluation" or "RAG queries", it refers to this database search process, NOT a red-amber-green rating system.

## CONTEXT:
{context}

## TASK:
Provide a concise structured reflection:

### CONFIDENCE SCORE
Rate 0-100 based on research quality, consistency, and specificity.
Format: CONFIDENCE SCORE: [number]

### KEY REASONING (2-3 sentences max)
Summarize why this recommendation was made based on the Retrieval-Augmented Generation (RAG) evaluation of research papers.

### KNOWLEDGE GAPS - SEMANTIC (max 5 items)
List SPECIFIC knowledge gaps for semantic vector database search. These should be detailed and precise.
Example: "magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35"

Use this format:
SEMANTIC_GAP 1: [specific detailed query]
SEMANTIC_GAP 2: [specific detailed query]
SEMANTIC_GAP 3: [specific detailed query]

### KNOWLEDGE GAPS - PMC (max 5 items)
List BROADER research concepts for external PubMed Central search. Focus on core research questions without specific dosages or brand names.
Example: "magnesium supplementation AND sleep latency AND women AND randomized controlled trial"

Use this format:
PMC_GAP 1: [broad research concept]
PMC_GAP 2: [broad research concept]
PMC_GAP 3: [broad research concept]

### ADJUSTMENT SUMMARY (if any)
One sentence per adjustment explaining what changed and why.

Be concise and actionable. Focus on what research would directly improve this specific recommendation."""

        try:
            response = self.llm.invoke(prompt)
            reflection_text = response.content
            
            # Parse the reflection
            parsed = self._parse_reflection(reflection_text)
            
            # Print summary
            self._print_summary(parsed)
            
            return parsed
            
        except Exception as e:
            print(f"❌ Error during reflection: {e}")
            return {
                "thought_process": f"Error during reflection: {e}",
                "confidence_score": 0,
                "knowledge_gaps": ["Reflection system error"],
                "adjustment_reasoning": [],
                "future_recommendations": []
            }
    
    def _build_context(self, test_case, baseline_rec, eval_data, adjustments, final_rec, score):
        """Build comprehensive context for reflection"""
        
        # Customer profile
        context = f"""### CUSTOMER PROFILE:
- Age: {test_case.get('age')}
- Sex: {test_case.get('sex')}
- Weight: {test_case.get('weight')} lbs
- Sleep Issues: {', '.join(test_case.get('sleep_issues', ['none']))}
- Current Magnesium Intake: {test_case.get('magnesium_intake', 'unknown')}mg/day
- Current Calcium Intake: {test_case.get('calcium_intake', 'unknown')}mg/day
- Current Potassium Intake: {test_case.get('potassium_intake', 'unknown')}mg/day
- Current Sodium Intake: {test_case.get('sodium_intake', 'unknown')}mg/day
- Medications: {', '.join(test_case.get('medications', ['none']))}

### BASELINE RECOMMENDATION (Before RAG Evaluation):
Note: RAG = Retrieval-Augmented Generation - searching research database for relevant studies

- Magnesium: {baseline_rec['magnesium']}mg ({baseline_rec.get('forms', {}).get('magnesium', 'unknown form')})
- Calcium: {baseline_rec['calcium']}mg ({baseline_rec.get('forms', {}).get('calcium', 'unknown form')})
- Potassium: {baseline_rec['potassium']}mg ({baseline_rec.get('forms', {}).get('potassium', 'unknown form')})
- Sodium: {baseline_rec['sodium']}mg ({baseline_rec.get('forms', {}).get('sodium', 'unknown form')})

### RAG EVALUATION RESULTS (Retrieval-Augmented Generation):
We searched the research database for relevant studies and evaluated the recommendation against those findings.

"""
        
        # Add research summary for each query
        queries_run = eval_data.get('queries_run', [])
        mineral_grades = eval_data.get('mineral_grades', {})
        
        context += "**Queries Run and Research Found:**\n\n"
        
        for query_type in queries_run:
            research_count = eval_data.get('research_count', {}).get(query_type, 0)
            context += f"- {query_type}: {research_count} research papers found\n"
        
        context += "\n**Mineral Grades:**\n\n"
        
        for mineral, grade_data in mineral_grades.items():
            context += f"**{mineral.upper()}:** {grade_data['score']}/100\n"
            context += f"  Feedback: {grade_data['feedback']}\n"
            if grade_data.get('suggestion'):
                context += f"  Suggestion: {grade_data['suggestion']}\n"
            context += "\n"
        
        # Add adjustments made
        if adjustments:
            context += "### ADJUSTMENTS MADE:\n\n"
            for adj in adjustments:
                context += f"**{adj['mineral'].upper()}:**\n"
                context += f"  - Current dose: {adj['current_dose']}mg\n"
                context += f"  - Issue identified: {adj['issue']}\n"
                context += f"  - Change applied: {adj['suggested_change']}\n"
                context += f"  - Priority: {adj['priority']}\n\n"
        else:
            context += "### ADJUSTMENTS MADE:\nNone - recommendation was already optimal\n\n"
        
        # Add final results
        context += f"""### FINAL RECOMMENDATION (After Adjustments):
- Magnesium: {final_rec['magnesium']}mg
- Calcium: {final_rec['calcium']}mg
- Potassium: {final_rec['potassium']}mg
- Sodium: {final_rec['sodium']}mg

### FINAL SCORE: {score}/100
"""
        
        return context
    
    def _parse_reflection(self, reflection_text: str) -> Dict[str, Any]:
        """Parse Claude's reflection response (handles both structured and unstructured formats)"""
        sections = {
            "key_reasoning": "",
            "confidence_score": 0,
            "knowledge_gap_queries": [],  # Semantic queries (specific)
            "pmc_search_queries": [],      # PMC queries (broad)
            "adjustment_summary": ""
        }

        import re

        # Extract confidence score from anywhere in the text
        score_pattern = re.compile(r'CONFIDENCE SCORE[:\s]*(\d+)', re.IGNORECASE)
        score_match = score_pattern.search(reflection_text)
        if score_match:
            sections['confidence_score'] = int(score_match.group(1))

        # Extract key reasoning
        reasoning_pattern = re.compile(r'KEY REASONING[:\s]*(.+?)(?=\n\n|\n[A-Z]|$)', re.DOTALL | re.IGNORECASE)
        reasoning_match = reasoning_pattern.search(reflection_text)
        if reasoning_match:
            sections['key_reasoning'] = reasoning_match.group(1).strip()

        # Extract SEMANTIC knowledge gap queries
        semantic_queries = []
        semantic_pattern = re.compile(r'SEMANTIC_GAP\s+\d+:\s*(.+)', re.IGNORECASE)
        for match in semantic_pattern.finditer(reflection_text):
            query = match.group(1).strip()
            if query and len(query) > 10:  # Valid query
                semantic_queries.append(query)

        if semantic_queries:
            sections['knowledge_gap_queries'] = semantic_queries

        # Extract PMC knowledge gap queries
        pmc_queries = []
        pmc_pattern = re.compile(r'PMC_GAP\s+\d+:\s*(.+)', re.IGNORECASE)
        for match in pmc_pattern.finditer(reflection_text):
            query = match.group(1).strip()
            if query and len(query) > 10:  # Valid query
                pmc_queries.append(query)

        if pmc_queries:
            sections['pmc_search_queries'] = pmc_queries

        # Fallback: Look for old GAP format for backwards compatibility
        if not semantic_queries and not pmc_queries:
            gap_queries = []
            gap_pattern = re.compile(r'GAP\s+\d+:\s*(.+)', re.IGNORECASE)
            for match in gap_pattern.finditer(reflection_text):
                query = match.group(1).strip()
                if query and len(query) > 10:  # Valid query
                    gap_queries.append(query)

            if gap_queries:
                sections['knowledge_gap_queries'] = gap_queries
                sections['pmc_search_queries'] = gap_queries  # Use same for both as fallback

        # Extract adjustment summary
        adjustment_pattern = re.compile(r'ADJUSTMENT SUMMARY[:\s]*(.+?)(?=\n\n|\n[A-Z]|$)', re.DOTALL | re.IGNORECASE)
        adjustment_match = adjustment_pattern.search(reflection_text)
        if adjustment_match:
            sections['adjustment_summary'] = adjustment_match.group(1).strip()

        # If we still don't have content, try to extract from the whole text
        if not sections['key_reasoning'] and not sections['knowledge_gap_queries']:
            # Look for any content that might be reasoning or gaps
            lines = reflection_text.split('\n')
            for line in lines:
                if len(line.strip()) > 20 and not line.strip().startswith('CONFIDENCE') and not line.strip().startswith('GAP'):
                    if not sections['key_reasoning']:
                        sections['key_reasoning'] = line.strip()
                    elif not sections['knowledge_gap_queries']:
                        sections['knowledge_gap_queries'] = [line.strip()]

        return sections
    
    def _map_section_name(self, old_name: str) -> str:
        """Map old section names to new structure"""
        mapping = {
            'knowledge_gaps': 'knowledge_gap_queries',
            'key_reasoning': 'key_reasoning',
            'adjustment_summary': 'adjustment_summary',
            'confidence_score': 'confidence_score'
        }
        return mapping.get(old_name, old_name)
    
    def _print_summary(self, reflection: Dict[str, Any]):
        """Print formatted summary of reflection"""
        
        print("\n" + "="*80)
        print("METACOGNITIVE REFLECTION")
        print("="*80)
        
        confidence = reflection.get('confidence_score', 0)
        # Ensure confidence is an int
        if isinstance(confidence, str):
            try:
                confidence = int(confidence)
            except:
                confidence = 0
        
        print(f"\n📊 CONFIDENCE: {confidence}/100", end=" ")
        
        if confidence >= 80:
            print("✅ High confidence")
        elif confidence >= 60:
            print("⚠️  Moderate confidence")
        else:
            print("❌ Low confidence")
        
        print("\n💭 KEY REASONING:")
        print("-" * 80)
        reasoning = reflection.get('key_reasoning', 'No reasoning provided')
        print(reasoning)
        
        print("\n🔍 KNOWLEDGE GAPS - SEMANTIC (for vector database):")
        print("-" * 80)
        semantic_queries = reflection.get('knowledge_gap_queries', [])
        if semantic_queries:
            for i, query in enumerate(semantic_queries, 1):
                print(f"  {i}. {query}")
        else:
            print("  • None - research coverage is complete")
        
        print("\n🌐 KNOWLEDGE GAPS - PMC (for external search):")
        print("-" * 80)
        pmc_queries = reflection.get('pmc_search_queries', [])
        if pmc_queries:
            for i, query in enumerate(pmc_queries, 1):
                print(f"  {i}. {query}")
        else:
            print("  • None - research coverage is complete")
        
        adjustment = reflection.get('adjustment_summary', '')
        if adjustment:
            print("\n🔧 ADJUSTMENTS:")
            print("-" * 80)
            print(adjustment)
        
        print("\n" + "="*80)


if __name__ == "__main__":
    # Test the reflector
    reflector = ReasoningReflector()
    
    test_case = {
        "age": 28,
        "sex": "female",
        "weight": 135,
        "sleep_issues": ["Trouble falling asleep"],
        "magnesium_intake": 180,
        "calcium_intake": 750,
        "potassium_intake": 1900,
        "sodium_intake": 2100
    }
    
    baseline_rec = {
        "magnesium": 500,
        "calcium": 250,
        "potassium": 300,
        "sodium": 90,
        "forms": {
            "magnesium": "glycinate",
            "calcium": "citrate",
            "potassium": "citrate",
            "sodium": "citrate"
        }
    }
    
    eval_data = {
        "overall_score": 80,
        "mineral_grades": {
            "magnesium": {"score": 85, "feedback": "Good dose for sleep onset", "suggestion": "No change needed"},
            "calcium": {"score": 80, "feedback": "Adequate for Mg support", "suggestion": "Consider slight reduction"},
            "potassium": {"score": 75, "feedback": "Moderate support", "suggestion": "No change needed"},
            "sodium": {"score": 70, "feedback": "May be too low", "suggestion": "Increase to 200-300mg"}
        },
        "queries_run": ["magnesium_dose", "calcium_dose", "potassium_dose", "sodium_dose", 
                       "mg_ca_ratio", "k_na_balance", "demographic", "sleep_type"],
        "research_count": {
            "magnesium_dose": 3,
            "calcium_dose": 3,
            "potassium_dose": 2,
            "sodium_dose": 1,
            "mg_ca_ratio": 3,
            "k_na_balance": 2,
            "demographic": 3,
            "sleep_type": 2
        }
    }
    
    adjustments = [
        {
            "mineral": "sodium",
            "current_dose": 90,
            "issue": "May be too low for optimal sleep support",
            "suggested_change": "Increase to 200-300mg",
            "priority": "medium"
        }
    ]
    
    final_rec = {
        "magnesium": 500,
        "calcium": 250,
        "potassium": 300,
        "sodium": 120
    }
    
    reflection = reflector.reflect(
        test_case,
        baseline_rec,
        eval_data,
        adjustments,
        final_rec,
        85
    )
    
    print("\n\n📄 FULL REFLECTION:")
    print("="*80)
    import json
    print(json.dumps(reflection, indent=2))

