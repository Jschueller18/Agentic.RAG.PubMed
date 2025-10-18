# PMC Search System - Quick Reference Guide

## Overview
The system now uses a **dual-query architecture** for knowledge gap filling:
- **Semantic queries** (specific) for vector database search
- **PMC queries** (broad, flexible) for external PubMed Central search

## How It Works

### 1. Reflection Phase
When the AI reflects on its recommendations, it generates two types of queries:

```
🔍 KNOWLEDGE GAPS - SEMANTIC (for vector database):
  1. magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35
  2. calcium citrate 200mg sleep quality postmenopausal women

🌐 KNOWLEDGE GAPS - PMC (for external search):
  1. magnesium supplementation AND sleep quality AND women
  2. calcium supplementation AND sleep AND postmenopausal
```

### 2. Query Optimization
If only semantic queries are provided, the `PMCQueryOptimizer` automatically converts them:

**Input (Semantic):**
```
magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35
```

**Output (PMC):**
```
(magnesium supplementation OR magnesium intake OR magnesium therapy) 
AND (sleep latency OR sleep onset latency OR sleep initiation) 
AND (women OR female OR premenopausal) 
AND (randomized controlled trial OR clinical trial OR RCT) 
AND "open access"[filter]
```

### 3. Hybrid Search
Each knowledge gap is searched in two ways:

1. **Vector Database** (Semantic Search)
   - Uses specific query
   - Finds precisely relevant papers in existing database
   - Returns top 3-5 most similar papers

2. **PubMed Central** (Keyword Search)
   - Uses broad, optimized query
   - Finds new papers from external source
   - Returns top 12 papers, filters duplicates

### 4. Results
```
📋 Gap 1/9
   🔍 Semantic: magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35...
   🌐 PMC: magnesium supplementation AND sleep quality AND women
   📄 Found 12 external papers  ✅
   📚 Found 3 database papers
   📥 Processing: 3 new external papers (9 duplicates skipped)
   ✅ PMC9941068: 41 chunks added
   ✅ PMC9331058: 33 chunks added
   ✅ PMC12158063: 64 chunks added
```

## Key Components

### PMCQueryOptimizer
**File:** `formulation_engines/pmc_query_optimizer.py`

**Purpose:** Transform specific research needs into effective PMC Boolean queries

**Method:** `optimize_for_pmc(research_need: str) -> str`

**Example Usage:**
```python
from formulation_engines.pmc_query_optimizer import PMCQueryOptimizer

optimizer = PMCQueryOptimizer()
specific_query = "magnesium glycinate 400mg sleep quality RCT women"
broad_query = optimizer.optimize_for_pmc(specific_query)
# Returns: "(magnesium supplementation OR magnesium intake) AND ..."
```

### TargetedResearchDownloader
**File:** `formulation_engines/targeted_research_downloader.py`

**Updated Method:**
```python
fill_knowledge_gaps(
    semantic_queries: List[str],  # For vector database
    pmc_queries: List[str],        # For external PMC search
    max_papers_per_gap: int = 5
)
```

**Example Usage:**
```python
from formulation_engines.targeted_research_downloader import TargetedResearchDownloader

downloader = TargetedResearchDownloader()

semantic_queries = [
    "magnesium 400mg sleep quality women age 25-35"
]
pmc_queries = [
    "magnesium supplementation AND sleep quality AND women"
]

stats = downloader.fill_knowledge_gaps(
    semantic_queries=semantic_queries,
    pmc_queries=pmc_queries,
    max_papers_per_gap=3
)

print(f"Downloaded: {stats['papers_downloaded']} papers")
print(f"Added: {stats['chunks_added']} chunks")
```

### ReasoningReflector
**File:** `formulation_engines/reasoning_reflector.py`

**Updated Output:**
```python
reflection = {
    "key_reasoning": "...",
    "confidence_score": 86,
    "knowledge_gap_queries": [      # Semantic queries
        "magnesium glycinate 300-400mg sleep onset latency RCT women age 25-35"
    ],
    "pmc_search_queries": [          # PMC queries
        "magnesium supplementation AND sleep quality AND women"
    ],
    "adjustment_summary": "..."
}
```

## Running the System

### Full Self-Improvement Cycle
```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate
python3 run_self_improvement.py
```

### Test PMC Query Optimizer Only
```bash
python3 -c "
from formulation_engines.pmc_query_optimizer import PMCQueryOptimizer
optimizer = PMCQueryOptimizer()
print(optimizer.optimize_for_pmc('magnesium 400mg sleep quality women'))
"
```

### Test Hybrid Search
```bash
python3 -c "
from formulation_engines.targeted_research_downloader import TargetedResearchDownloader
downloader = TargetedResearchDownloader()
results = downloader.search_hybrid(
    semantic_query='magnesium 400mg sleep quality',
    pmc_query='magnesium supplementation AND sleep quality',
    pmc_max_results=5,
    semantic_max_results=5
)
print(f'PMC: {len(results[\"pmc_papers\"])} papers')
print(f'Database: {len(results[\"semantic_papers\"])} papers')
"
```

## Troubleshooting

### PMC Searches Return 0 Results
**Check:**
1. Is the query too specific? (Should have OR operators for synonyms)
2. Is `open access[filter]` included?
3. Are terms spelled correctly?

**Solution:**
Let the `PMCQueryOptimizer` handle query transformation. Don't manually create PMC queries.

### Semantic Search Returns No Results
**Check:**
1. Is the vector database initialized?
2. Is the query too generic?
3. Are embeddings working?

**Solution:**
Make semantic queries more specific with dosages, populations, and study types.

### Papers Not Being Downloaded
**Check:**
1. Are papers already in `downloaded_pmcids.json`?
2. Is there a network issue?
3. Is NCBI rate limiting?

**Solution:**
- Check duplicate tracking file
- Add delay between requests (currently 0.4s)
- Set NCBI_API_KEY environment variable for higher rate limits

## Performance Metrics

**Before Implementation:**
- PMC searches: 0 papers found
- Knowledge gaps: Not being filled
- Vector database: Static, not growing

**After Implementation:**
- PMC searches: 12 papers per query
- Knowledge gaps: Automatically filled
- Vector database: Growing with new research
- Duplicate detection: Working (9/12 duplicates skipped on average)
- Chunks added: 30-90 per paper

## Best Practices

1. **Let the AI generate both query types** in the reflection phase
2. **Use PMCQueryOptimizer** for transforming semantic to PMC queries
3. **Set reasonable limits** (max_papers_per_gap=3 is good)
4. **Monitor duplicate rates** to ensure diversity
5. **Check research quality** before integration (already automated)

## Configuration

### API Keys Required
```bash
# In ~/.bashrc or environment
export ANTHROPIC_API_KEY="sk-ant-..."  # For Claude Haiku
export NCBI_API_KEY="..."              # Optional, for higher rate limits
```

### Adjustable Parameters

**In `improvement_loop.py`:**
```python
download_stats = downloader.fill_knowledge_gaps(
    semantic_queries=unique_semantic_queries,
    pmc_queries=unique_pmc_queries,
    max_papers_per_gap=3  # Adjust to download more/fewer papers
)
```

**In `pmc_query_optimizer.py`:**
```python
self.llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.2,  # Lower = more consistent, Higher = more creative
    max_tokens=500
)
```

## Summary

The dual-query architecture successfully solves the PMC search problem by:
- Generating appropriate queries for each search type
- Using LLM-powered optimization for PMC queries
- Maintaining high specificity for semantic searches
- Finding new relevant research automatically
- Integrating new papers into the knowledge base

The system is now fully operational and continuously improving its knowledge base!

