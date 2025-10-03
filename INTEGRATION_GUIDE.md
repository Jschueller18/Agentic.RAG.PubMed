# Live Research Tool Integration Guide

## ✅ Status: Live Tool Tested & Ready

**Tool Location:** `live_research_tool.py`  
**Test Results:** ✅ Working perfectly
- 20 papers fetched from PubMed API
- 19 papers cached successfully
- Cross-encoder re-ranking operational
- Auto-caching creates files + metadata

## Integration Options

### Option 1: Add as New Tool (Recommended for Testing)

**Approach:** Add `live_research_tool` as a 5th tool alongside existing `librarian_rag_tool`

**Advantages:**
- ✅ Preserves existing architecture (Fareed Khan's design intact)
- ✅ Allows A/B testing: vector store vs live API
- ✅ Agent can choose based on query type
- ✅ Easy to rollback if issues arise

**Implementation:**
1. Import `live_research_tool` function into notebook (Cell after imports)
2. Wrap it with `@tool` decorator
3. Add to `tools` list in Cell 60
4. Update Supervisor prompt to explain when to use each tool

**Differentiation:**
- `librarian_rag_tool`: Fast, pre-built corpus (good for customer chatbot)
- `live_research_tool`: Live API, hyper-specific queries (good for R&D)

---

### Option 2: Replace Existing Tool (Direct Approach)

**Approach:** Swap vector store search with live API in existing `librarian_rag_tool`

**Advantages:**
- ✅ Simpler - only one RAG tool
- ✅ Cleaner tool architecture
- ✅ Follows original design pattern

**Disadvantages:**
- ⚠️ Loses fast vector store retrieval
- ⚠️ 15-30 second latency per query (live API calls)

**Implementation:**
1. Modify Cell 47 (librarian_rag_tool definition)
2. Replace vector store search logic with `live_research_tool()` call
3. Keep query optimization and formatting logic
4. Remove vector store dependencies if not needed elsewhere

---

## Recommended Path: Option 1 (Dual Tools)

### Step-by-Step Integration

#### 1. Import Live Tool (Add new cell after Cell 6 - Imports)

```python
# Import Live Research Tool
from live_research_tool import live_research_tool as live_api_search

print("✓ Live Research Tool imported")
```

#### 2. Wrap as LangChain Tool (Add new cell after Cell 47)

```python
@tool
def live_api_research_tool(query: str) -> List[Dict[str, Any]]:
    """
    This tool performs LIVE searches of PubMed Central's full database (millions of papers).
    Use it for hyper-specific R&D queries that require the most current research or very specific dose-response data, population studies, or technical coefficients not likely in a pre-built corpus.
    Best for internal algorithm development requiring exact quantitative relationships.
    The input should be a specific technical research question.
    Returns top 5 papers after re-ranking.
    Note: Takes 15-30 seconds per query (live API + re-ranking).
    """
    print(f"\n-- Live API Research Tool Called with query: '{query}' --")
    
    # Call the live research function (it handles optimization internally)
    results = live_api_search(query, verbose=True)
    
    return results

print("✓ live_api_research_tool defined")
```

#### 3. Add to Tools List (Modify Cell 60)

**Current:**
```python
tools = [librarian_rag_tool, analyst_sql_tool, analyst_trend_tool, scout_web_search_tool]
```

**Updated:**
```python
tools = [
    librarian_rag_tool,        # Fast pre-built corpus (if you build vector store)
    live_api_research_tool,    # Live PubMed API for hyper-specific queries
    analyst_sql_tool,          # Electrolyte properties database
    analyst_trend_tool,        # Property comparisons
    scout_web_search_tool      # General web search
]
```

#### 4. Update Supervisor Prompt (Cell 66 - Planner)

Add guidance about when to use each research tool:

```python
# In create_planner_prompt() function, add to instructions:
"""
**Research Tool Selection:**
- Use librarian_rag_tool for: General electrolyte questions, customer-facing queries, fast retrieval
- Use live_api_research_tool for: Hyper-specific R&D queries requiring exact dose-response curves, 
  population-specific data, recent papers, or technical coefficients unlikely in pre-built corpus.
  Note: live_api_research_tool is slower (15-30s) but searches millions of papers.
"""
```

---

## Testing Strategy

### Test Query 1: General (Should use librarian_rag_tool if corpus exists)
```
"What are the bioavailability differences between magnesium citrate and magnesium oxide?"
```

### Test Query 2: Hyper-Specific (Should use live_api_research_tool)
```
"What is the exact dose-response relationship for magnesium supplementation on sleep 
onset latency in adults aged 30-50 with baseline magnesium deficiency?"
```

### Test Query 3: Quantitative R&D (Should use live_api_research_tool)
```
"In controlled studies, what is the multiplicative interaction coefficient between 
exercise intensity (%VO2max) and duration for sodium losses during endurance exercise?"
```

---

## Cache Management

The live tool automatically builds a corpus in `electrolyte_research_papers/`:
- Each paper cached on first retrieval
- `papers_cache.json` tracks all papers with usage stats
- `query_history.json` logs which queries found which papers

**Over time, this creates an organic corpus optimized for BestMove's actual queries.**

**Later optimization:** Build vector store from cached papers for faster retrieval of frequently accessed papers.

---

## Configuration Options

### For R&D Mode (Current Setup)
- Keep `verbose=True` in live_api_research_tool
- Shows detailed progress for researchers
- 15-30 second latency acceptable

### For Customer Chatbot (Future)
- Build vector store from cached papers
- Use `librarian_rag_tool` for fast retrieval (<2s)
- Only use live API for queries with no good local matches

---

## Next Steps

1. ✅ **Completed:** Live tool tested and working
2. ⏳ **Next:** Integrate into notebook (Option 1 - add as new tool)
3. ⏳ **Test:** Run test queries through full agent system
4. ⏳ **Validate:** Verify Supervisor chooses correct tool for query types
5. ⏳ **Optimize:** Build vector store from cached papers (optional future step)

---

## Files Modified

When you integrate, you'll modify these notebook cells:
- **New Cell after Cell 6**: Import live_research_tool
- **New Cell after Cell 47**: Define live_api_research_tool with @tool decorator
- **Cell 60**: Add live_api_research_tool to tools list
- **Cell 66**: Update Supervisor prompt with tool selection guidance

---

## Rollback Plan

If issues arise:
1. Remove live_api_research_tool from tools list
2. Revert Supervisor prompt changes
3. Continue using vector store approach
4. Cached papers remain available for future use

