"""
PMC Query Optimizer - Transform research needs into effective PubMed Central searches

Uses Claude Haiku to intelligently convert specific research gaps into broad,
flexible Boolean queries optimized for PubMed Central's keyword-based search.
"""

import os
from typing import List
from langchain_anthropic import ChatAnthropic


class PMCQueryOptimizer:
    """
    Transform specific research needs into broad, effective PMC searches
    
    Takes highly specific queries like:
    "magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35"
    
    And converts them to effective PMC Boolean queries like:
    "(magnesium supplementation OR magnesium intake) AND (sleep latency OR sleep onset) 
     AND (women OR female) AND (clinical trial OR randomized)"
    """
    
    def __init__(self):
        """Initialize Claude Haiku for query optimization"""
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.2,  # Low temperature for consistent query formatting
            max_tokens=500,   # Queries are short
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
    
    def optimize_for_pmc(self, research_need: str) -> str:
        """
        Transform a research need into an effective PMC Boolean query
        
        Args:
            research_need: Specific research gap (e.g., from ReasoningReflector)
            
        Returns:
            Optimized Boolean query for PubMed Central
        """
        
        prompt = f"""You are a research librarian optimizing a PubMed Central search query.

## INPUT QUERY:
{research_need}

## TASK:
Transform this into an effective PubMed Central Boolean search query by:

1. **Extract Core Concepts**: Identify the main research concepts (mineral, outcome, population, study type)
2. **Remove Specifics**: Remove specific dosages, brand names, and exact age ranges
3. **Add Synonyms**: Use OR operators to include research synonyms
4. **Create Boolean Query**: Combine concepts with AND operators

## GUIDELINES:
- Remove: specific dosages (300mg, 400-500mg), brand names (glycinate, citrate), exact ages (25-35)
- Keep: general concepts (magnesium, sleep latency, women, randomized controlled trial)
- Use OR for synonyms: (magnesium supplementation OR magnesium intake OR magnesium therapy)
- Use AND to connect different concepts
- Focus on research language, not product language
- Add "open access" filter at the end

## EXAMPLES:

Input: "magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35"
Output: (magnesium supplementation OR magnesium intake OR magnesium therapy) AND (sleep latency OR sleep onset latency OR sleep initiation) AND (women OR female OR premenopausal) AND (randomized controlled trial OR clinical trial OR RCT) AND "open access"[filter]

Input: "calcium citrate 200mg sleep quality postmenopausal women"
Output: (calcium supplementation OR calcium intake) AND (sleep quality OR sleep efficiency OR subjective sleep) AND (postmenopausal women OR postmenopausal female) AND "open access"[filter]

Input: "potassium sleep maintenance diabetes RCT"
Output: (potassium supplementation OR potassium intake) AND (sleep maintenance OR sleep continuity OR wake after sleep onset) AND (diabetes OR diabetic OR type 2 diabetes) AND (randomized controlled trial OR clinical trial) AND "open access"[filter]

## OUTPUT:
Provide ONLY the optimized Boolean query, no explanations."""

        try:
            response = self.llm.invoke(prompt)
            optimized_query = response.content.strip()
            
            # Clean up the response (remove quotes if LLM added them)
            if optimized_query.startswith('"') and optimized_query.endswith('"'):
                optimized_query = optimized_query[1:-1]
            
            return optimized_query
            
        except Exception as e:
            print(f"   ⚠️  Query optimization failed: {e}")
            # Fallback: simple extraction of core terms
            return self._simple_fallback(research_need)
    
    def optimize_batch(self, research_needs: List[str]) -> List[str]:
        """
        Optimize multiple queries at once
        
        Args:
            research_needs: List of specific research gaps
            
        Returns:
            List of optimized Boolean queries
        """
        optimized = []
        for need in research_needs:
            optimized.append(self.optimize_for_pmc(need))
        return optimized
    
    def _simple_fallback(self, research_need: str) -> str:
        """
        Simple fallback if LLM optimization fails
        Just extracts key terms and creates basic Boolean query
        """
        import re
        
        # Remove dosages
        clean = re.sub(r'\d+\s*-?\s*\d*\s*mg', '', research_need)
        
        # Remove specific forms
        clean = re.sub(r'\b(glycinate|citrate|malate|oxide|chloride)\b', '', clean, flags=re.IGNORECASE)
        
        # Remove age ranges
        clean = re.sub(r'age\s*\d+\s*-?\s*\d*', '', clean, flags=re.IGNORECASE)
        
        # Extract key terms
        terms = []
        if 'magnesium' in clean.lower():
            terms.append('(magnesium supplementation OR magnesium intake)')
        if 'calcium' in clean.lower():
            terms.append('(calcium supplementation OR calcium intake)')
        if 'potassium' in clean.lower():
            terms.append('(potassium supplementation OR potassium intake)')
        if 'sodium' in clean.lower():
            terms.append('(sodium intake OR salt intake)')
        
        if 'sleep' in clean.lower():
            terms.append('(sleep quality OR sleep latency OR sleep efficiency)')
        
        if 'women' in clean.lower() or 'female' in clean.lower():
            terms.append('(women OR female)')
        
        if 'rct' in clean.lower() or 'trial' in clean.lower() or 'randomized' in clean.lower():
            terms.append('(randomized controlled trial OR clinical trial)')
        
        if not terms:
            # Very broad fallback
            return '(magnesium OR calcium OR potassium OR sodium) AND sleep AND "open access"[filter]'
        
        return ' AND '.join(terms) + ' AND "open access"[filter]'

