# BestMove RAG - Notebook Integration Guide

**Status:** Vector store built ✅ | Ready for integration with code.ipynb

---

## 🎯 Goal

Integrate the BestMove electrolyte research vector store (203,174 chunks from 5,366 papers) into the existing `code.ipynb` RAG notebook.

---

## 📊 What We Have

### Vector Store
- **Location:** `./bestmove_vector_db/`
- **Collection:** `bestmove_research`
- **Size:** 203,174 chunks from 5,366 full-text papers
- **Embedding Model:** BAAI/bge-small-en-v1.5 (384 dimensions)
- **Content:** Full-text PMC Open Access papers (Methods, Results, Tables)

### Test Results
✅ Tested across all BestMove use cases  
✅ Relevance scores: 0.81-0.92 (excellent!)  
✅ Papers contain quantitative data (dose-response, coefficients)  
✅ Source attribution working (PMC IDs, titles, authors)

---

## 🔧 Integration Steps

### Step 1: Update Vector Store Connection

**Current (in code.ipynb):**
```python
# Cell 47: Librarian RAG Tool
VECTOR_STORE_PATH = "./financial_rag_db"  # OLD
COLLECTION_NAME = "sec_filings"  # OLD
```

**New:**
```python
# Cell 47: Librarian RAG Tool
VECTOR_STORE_PATH = "./bestmove_vector_db"  # ✅ NEW
COLLECTION_NAME = "bestmove_research"  # ✅ NEW
```

---

### Step 2: Update Embedding Model (if different)

**Check if notebook uses same model:**
```python
# Should already be using BAAI/bge-small-en-v1.5
# If not, update to match vector store:
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
```

---

### Step 3: Update Prompts (Already Done!)

✅ Session 1: Changed from financial → biomedical  
✅ Session 2: Specialized for BestMove electrolyte research  
✅ All tools updated: Librarian, SQL Analyst, Trend Analyst, Supervisor

**No changes needed here** - prompts already optimized for BestMove!

---

### Step 4: Test the Integration

**Add a new test cell to code.ipynb:**

```python
# Test Cell: BestMove RAG Query
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

# Configuration
VECTOR_DB_PATH = "./bestmove_vector_db"
COLLECTION_NAME = "bestmove_research"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Test query
test_query = "What is the optimal magnesium dose for improving sleep quality in adults?"

# Initialize
model = TextEmbedding(model_name=EMBEDDING_MODEL)
client = QdrantClient(path=VECTOR_DB_PATH)

# Search
query_embedding = list(model.embed([test_query]))[0]
results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_embedding.tolist(),
    limit=3
).points

# Display
for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result.score:.3f}")
    print(f"   Title: {result.payload['title']}")
    print(f"   Journal: {result.payload['journal']} ({result.payload['year']})")
    print(f"   PMC ID: {result.payload['pmcid']}")
```

**Expected output:**
- Top result: "Oral magnesium supplementation for insomnia" (Score: ~0.88)
- All results should be about magnesium and sleep

---

### Step 5: Update Metadata Extraction

**Update any code that assumes SEC filing structure:**

**OLD (financial):**
```python
company = result.payload['company']
filing_type = result.payload['filing_type']
```

**NEW (biomedical):**
```python
title = result.payload['title']
pmcid = result.payload['pmcid']
journal = result.payload['journal']
year = result.payload['year']
authors = result.payload['authors']
has_methods = result.payload['has_methods']
has_results = result.payload['has_results']
num_tables = result.payload['num_tables']
```

---

### Step 6: Update Source Attribution

**When displaying results to users, show:**

```python
def format_source(result):
    """Format a source citation for BestMove RAG."""
    payload = result.payload
    return f"""
Source: {payload['title']}
Authors: {', '.join(payload['authors'][:3])}
Journal: {payload['journal']} ({payload['year']})
PMC ID: {payload['pmcid']}
Link: https://www.ncbi.nlm.nih.gov/pmc/articles/{payload['pmcid']}/
"""
```

---

## 🧪 Test Queries

**After integration, test with these BestMove-specific queries:**

### Sleep Support Mix
```
"What is the optimal magnesium dose for improving sleep quality?"
"Does magnesium threonate improve sleep better than citrate?"
"What is the relationship between magnesium levels and insomnia?"
```

### Workout Performance Mix
```
"How much sodium do athletes lose during exercise?"
"What electrolytes improve athletic performance?"
"What is the optimal potassium intake for endurance athletes?"
```

### Menstrual Support Mix
```
"What magnesium dose reduces menstrual cramps?"
"Do calcium and magnesium help with PMS symptoms?"
"What minerals affect menstrual pain?"
```

### Bioavailability (R&D Focus)
```
"What is the bioavailability of magnesium citrate vs oxide?"
"Which calcium form has the highest absorption rate?"
"How does vitamin D affect magnesium absorption?"
```

---

## 📈 Expected Performance

### Retrieval Quality
- **Top-3 accuracy:** ~90% (based on test results)
- **Relevance scores:** 0.75+ for good matches, 0.85+ for excellent
- **Source diversity:** Multiple papers per query

### Response Time
- **Search:** <100ms (local Qdrant)
- **Embedding generation:** ~50ms per query
- **Total:** <200ms for retrieval

### Coverage
- ✅ All BestMove product lines covered
- ✅ Dose-response data available
- ✅ Population-specific requirements
- ✅ Form comparisons (citrate, oxide, glycinate, etc.)
- ✅ Timing & interactions

---

## 🎯 Next Steps After Integration

### 1. Agent Testing
Run full agent queries through the notebook to ensure:
- Supervisor routes queries correctly
- Librarian tool retrieves relevant papers
- Final responses cite sources properly

### 2. Prompt Refinement
Fine-tune prompts based on actual query results:
- Adjust re-ranking thresholds
- Optimize chunk selection
- Improve source synthesis

### 3. Customer Chatbot Version
Create simplified version for customer-facing chatbot:
- Same vector store
- Simpler language in responses
- Focus on practical advice vs technical data

### 4. Continuous Corpus Updates
Set up pipeline to add new papers:
- Run `pmc_bulk_downloader.py` monthly with new queries
- Process new XMLs with `process_pmc_corpus.py`
- Rebuild vector store with `build_vector_store.py`

---

## 🚀 Quick Start Commands

```bash
# Activate environment
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# Test vector store
python3 test_bestmove_rag.py "your query here"

# Run comprehensive test
python3 test_bestmove_rag_auto.py

# Open notebook
jupyter notebook code.ipynb
```

---

## 📝 Checklist

Integration complete when:
- [ ] Vector store path updated in code.ipynb
- [ ] Collection name updated to 'bestmove_research'
- [ ] Test cell runs successfully
- [ ] Source attribution shows PMC IDs and paper titles
- [ ] All BestMove test queries return relevant results
- [ ] Agent successfully answers technical R&D questions

---

## 🆘 Troubleshooting

### "Collection not found"
- Check `VECTOR_DB_PATH` is `./bestmove_vector_db`
- Check `COLLECTION_NAME` is `bestmove_research`
- Verify database exists: `ls -lh bestmove_vector_db/`

### Low relevance scores (<0.7)
- Check embedding model matches: `BAAI/bge-small-en-v1.5`
- Verify query is BestMove-relevant (electrolytes, minerals)
- Try more specific queries with mineral names

### Slow search (>1 second)
- Consider upgrading to Qdrant Docker (recommended for 200K+ points)
- Current warning: "Local mode not recommended for >20K points"
- Performance still acceptable, but Docker will be faster

---

## 📚 Additional Resources

- `test_bestmove_rag.py` - Interactive query testing
- `test_bestmove_rag_auto.py` - Automated comprehensive tests
- `VECTOR_STORE_GUIDE.md` - How vector store was built
- `CORPUS_PROCESSING_GUIDE.md` - How papers were processed
- `AGENT_SCRATCHPAD.md` - Full project history

---

**🎉 Ready to integrate! Your BestMove RAG system has 203,174 chunks of electrolyte research ready to query!**

