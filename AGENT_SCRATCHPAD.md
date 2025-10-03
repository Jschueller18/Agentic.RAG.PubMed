# Agentic RAG - Electrolyte Research System - Project Scratchpad

**Project:** Converting Financial RAG System → Electrolyte Research RAG System  
**Date Started:** October 2, 2025  
**Last Updated:** October 2, 2025  
**Status:** Phase 0-2 Complete, Agent Tools Updated ✅

---

## 📝 Latest Session Summary (October 2, 2025)

**Completed:** Phase 1-2 Complete + BestMove Contextualization

**Key Accomplishments - Session 1:**
- ✅ Updated all metadata enrichment prompts (Cell 30) from financial → biomedical research analyst
- ✅ Updated query optimizer (Cell 45) for biomedical literature search
- ✅ Converted Librarian RAG tool (Cell 47) from SEC filings → PubMed research papers
- ✅ Updated Analyst SQL tool (Cell 50) from revenue data → electrolyte properties
- ✅ Adapted Analyst Trend tool (Cell 53) from time-series → property comparisons
- ✅ Updated Supervisor/Planner prompt (Cell 66) to research analyst role
- ✅ Revised all discussion cells (46, 48, 51, 54, 67) to reflect research context

**Key Accomplishments - Session 2 (BestMove Specific):**
- ✅ Re-specialized ALL prompts for **personalized electrolyte formulation research**
- ✅ Updated focus to support **algorithm development** for customized supplements
- ✅ Optimized for **four use cases**: Daily Wellness, Workout Performance, Sleep Quality, Menstrual Support
- ✅ Enhanced query optimizer to handle highly technical R&D questions (dose-response curves, interaction coefficients, time constants, etc.)
- ✅ Updated Librarian tool for quantitative data extraction (sweat loss coefficients, acclimatization time constants, population-specific requirements)
- ✅ Refined all tool descriptions to emphasize individual variability factors (age, sex, body composition, genetics, diet, exercise)

**Business Context:** BestMove creates personalized electrolyte supplements tailored to individual body, lifestyle, and goals. System supports two configurations:
1. **Internal R&D**: Highly technical queries for algorithm development
2. **Customer Chatbot**: Accessible explanations with source citations

**Impact:** System now optimized for extracting quantitative research data needed to calculate optimal sodium, potassium, magnesium, and calcium amounts per serving based on survey variables.

**Next Priority:** Download full set of electrolyte research papers from PMC and build vector store.

### **Session 3 Progress (October 3, 2025)**

**PMC API Test Results:**
```
✓ All tests passed successfully!
- Found 15 papers across 3 test queries
- 0 duplicates (100% unique)
- Average file size: ~2,143 bytes per paper
- API response time: Fast (< 5 seconds)
```

**Test Queries that worked:**
- 'magnesium absorption bioavailability': 5 papers
- 'sodium supplementation metabolism': 5 papers  
- 'potassium citrate bioavailability': 5 papers

**Status:** PMC API verified working. Ready to download full dataset (~100-120 papers).

### **Architecture Decision: Live API + Auto-Caching (Oct 3, 2025)**

**Problem:** Generic pre-downloaded papers (e.g., "calcium citrate vs carbonate") not optimal for BestMove's hyper-specific technical queries.

**Solution:** Live API retrieval with automatic corpus building

**Architecture:**
```
Query → PubMed API (live) → Fetch 20 candidates → Re-rank (cross-encoder) 
  → Top 5 results → Auto-save to electrolyte_research_papers/ → Return
```

**Key Benefits:**
- ✅ Access to millions of papers (not just 100 pre-downloaded)
- ✅ Queries like "magnesium dose-response sleep latency age groups" find exact studies needed
- ✅ Papers automatically cached for future customer chatbot corpus
- ✅ Organic corpus building: only papers actually used in formulation research
- ✅ RAG architecture preserved: Still uses cross-encoder re-ranking (Cell 47 logic)
- ✅ Latency: 15-30 seconds (acceptable for R&D, not customer-facing)

**Implementation Plan:**
1. Create `live_research_tool` as separate tool (test independently)
2. Keep existing `librarian_rag_tool` untouched initially
3. Add paper cache manager (`papers_cache.json`, `query_history.json`)
4. Test with BestMove technical queries
5. Once validated, optionally replace Cell 47 implementation

**File Structure After Implementation:**
```
electrolyte_research_papers/     # Auto-growing corpus
├── PMC_12345.txt               # Each paper saved on first fetch
├── PMC_67890.txt
└── ...
papers_cache.json                # Metadata: all cached papers
query_history.json               # Which queries found which papers
```

**Status:** Live research tool created (`live_research_tool.py`). Ready for testing.

**Next Steps:**
1. Install sentence-transformers: `pip install sentence-transformers`
2. Test tool: `python3 live_research_tool.py`
3. Verify papers auto-cache to `electrolyte_research_papers/`
4. Check metadata files: `papers_cache.json`, `query_history.json`
5. Once validated, integrate into notebook as tool option

**Files Created:**
- `live_research_tool.py` - Standalone live API tool with auto-caching
- Architecture documented above

---

## 🎯 BestMove Use Cases & Example R&D Queries

### **Sleep Support Mix**
Technical queries for algorithm development:
1. "What is the exact dose-response relationship for magnesium on sleep onset latency across different age groups (18-30, 31-50, 51-65, 65+), controlling for baseline magnesium status?"
2. "How does body composition (lean mass vs. fat mass) affect magnesium distribution volume and optimal dosing for sleep, beyond simple weight-based scaling?"
3. "What genetic polymorphisms (TRPM6, TRPM7, CNNM2) affect magnesium absorption efficiency, and what are their prevalence rates across populations?"

### **Workout Performance Mix**
Technical queries for algorithm development:
1. "In controlled studies measuring whole-body sweat losses, what is the actual multiplicative interaction coefficient between exercise intensity (measured as %VO2max) and duration for sodium losses? Specifically, does a 2-hour run at 75% VO2max produce 2.0x the sodium loss of a 1-hour run, or does the coefficient deviate from linearity (e.g., 1.8x or 2.3x)?"
2. "Across longitudinal studies tracking the same individuals during heat acclimatization protocols, what are the specific time constants (τ in days) for: (a) sweat rate increases, (b) sweat sodium concentration decreases, and (c) plasma volume expansion? How do these three adaptations interact to affect total sodium loss recommendations over a 14-day acclimatization period?"
3. "In studies where the same athletes undergo repeated sweat testing under identical conditions, what is the within-individual coefficient of variation for sweat sodium concentration? And how does this compare to between-individual variation? At what sample size (n sessions) does the standard error of an individual's mean stabilize to within ±10% of their true value?"

### **Daily Wellness Mix**
Technical queries for algorithm development:
1. "What does recent research (last 5 years) say about age-specific variations in electrolyte absorption efficiency and requirements for adults aged 30-65 in non-exercise contexts? Specifically, should our Daily Support Mix algorithm apply different scaling factors beyond the current kidney function adjustment (0.98^(age-30)) to account for gut absorption changes, hormonal shifts, or metabolic differences across decades?"
2. "What evidence exists for how different dietary patterns (Mediterranean, ketogenic, plant-based, intermittent fasting, Standard American Diet) affect baseline electrolyte status and supplementation needs in sedentary to lightly active adults? Are our current diet-type multipliers (plant-based: 0.8x, keto: 1.2x sodium) adequately capturing the electrolyte demands and deficiencies associated with each pattern, or should we be applying more nuanced adjustments by individual mineral?"
3. "Beyond the baseline DRI differences and the 1.15x fluid multiplier for males, what does current research indicate about gender-specific electrolyte metabolism, utilization, and requirements for non-pregnant, non-menstruating adults in daily life contexts? Should our Daily Support Mix algorithm incorporate additional gender-based adjustments for factors like muscle mass differences, hormonal influences on mineral retention, or sex-specific chronic disease risk profiles?"

### **Menstrual Support Mix**
Technical queries for algorithm development:
1. "What are the exact dose-response curves for magnesium supplementation and menstrual cramp severity across different age groups (18-25, 26-35, 36-45)? Retrieve RCTs measuring pain scores (VAS/NRS) at different magnesium doses (100mg, 200mg, 300mg, 400mg) and calculate the marginal benefit per 50mg increment."
2. "For women on combination oral contraceptives, analyze studies measuring serum magnesium and zinc levels at months 3, 6, 12, 18, and 24+ of continuous use. What is the mathematical relationship between duration and depletion rate? Does depletion plateau or continue linearly?"
3. "In studies where both calcium and magnesium were supplemented for menstrual symptoms, what Ca:Mg ratios (1:1, 2:1, 3:1, 4:1) showed optimal efficacy? Are there interaction effects where the ratio matters more than absolute doses?"

---

## 🎯 Project Goal (Original)

Adapt an existing Agentic RAG pipeline (originally designed for Microsoft SEC filings analysis) to work with electrolyte research papers from PubMed Central.

---

## ✅ Completed Work

### **Phase 0: Setup & Data Acquisition**

#### 1. **Requirements Updated** (`requirements.txt`)
- ✅ Removed: `sec-edgar-downloader`
- ✅ Added: `pymed`, `biopython`, `requests`
- ✅ Kept: All RAG infrastructure (langchain, langgraph, qdrant, etc.)

#### 2. **Notebook Updates** (`code.ipynb`)

**Cell 0 (Title):**
- Changed from "Archon: Financial Analyst" → "Electrolyte Research Intelligence System"
- Updated description to focus on biomedical research instead of financial filings

**Cell 3 (Install Packages):**
- Replaced `sec-edgar-downloader` with `pymed` and `biopython`

**Cell 6 (Imports):**
- Added: `from pymed import PubMed`
- Added: `from Bio import Entrez`
- Added: `from unstructured.partition.pdf import partition_pdf`

**Cell 11 (Data Acquisition Description):**
- Updated to describe PubMed Central API instead of SEC EDGAR
- Lists 6 electrolyte research topics to search

**Cell 12 (Download Code):**
- Replaced SEC filing download with PMC API queries
- Searches 6 topics: electrolyte absorption, sodium metabolism, potassium bioavailability, magnesium forms, calcium comparison, exercise performance
- Max 20 papers per query = ~120 total papers

**Cell 15 (File Verification):**
- Creates `electrolyte_research_papers/` directory
- Saves papers as text files with format: `PMC_{pubmed_id}.txt`
- Each file contains: Title, PubMed ID, Authors, Publication Date, Abstract
- Implements deduplication by PubMed ID

**Cell 18 (Structured Database):**
- Replaced revenue data with `electrolyte_properties.csv`
- 10 electrolyte forms with properties:
  - `electrolyte_name`, `element`, `supplement_form`
  - `bioavailability_percent` (4% - 98%)
  - `elemental_content_percent`
  - `rda_mg` (Recommended Daily Allowance)
  - `absorption_site` (Small Intestine, Duodenum)
  - `common_dosage_mg`
  - `timing_recommendation` (With meals, Anytime, Bedtime)

**Cell 21-23 (Parsing Section):**
- Created `parse_research_paper()` function for text files
- Extracts structured sections: Title, Metadata, Abstract
- Simpler than HTML parsing (research papers have clearer structure)

#### 3. **Test Infrastructure**

**Created:** `test_pmc_connection.py`
- 7 comprehensive tests for PMC API connection
- Validates: imports, API connection, search, file save, deduplication, database creation
- **Result:** All tests PASSED ✅

**Test Results (Actual Data):**
```
Query: "magnesium absorption bioavailability" → 3 papers found
Query: "electrolyte absorption bioavailability" → 5 papers found
Query: "sodium supplementation metabolism" → 5 papers found
Query: "potassium citrate bioavailability" → 5 papers found
Total: 15 unique papers retrieved
File size: ~2,143 bytes per paper (includes full abstract)
```

#### 4. **Environment Setup**

**Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install pymed biopython pandas requests
```

**Status:** ✅ Working and tested

### **Phase 1: Knowledge Core (COMPLETED ✅)**

#### 1. **Metadata Enrichment Prompts Updated** (Cell 30)
- ✅ Changed from "expert financial analyst" → "expert biomedical research analyst"
- ✅ Updated focus from financial documents → research papers on electrolytes
- ✅ Changed table example from revenue trends → bioavailability comparisons

#### 2. **Query Optimizer Updated** (Cell 45)
- ✅ Changed from "corporate financial documents (10-Ks, 10-Qs)" → "biomedical research papers"
- ✅ Updated focus from financial terms → scientific terms, compounds, mechanisms

### **Phase 2: Specialist Agents (COMPLETED ✅)**

#### 1. **Librarian RAG Tool** (Cell 47)
- ✅ Updated from "Microsoft's financial documents" → "electrolyte research papers from PubMed Central"
- ✅ Changed focus from financial performance → bioavailability, absorption mechanisms, clinical findings

#### 2. **Analyst SQL Tool** (Cell 50)
- ✅ Updated from "Microsoft's revenue and net income data" → "electrolyte properties and bioavailability data"
- ✅ Changed examples from financial queries → electrolyte property queries

#### 3. **Analyst Trend Tool** (Cell 53)
- ✅ Updated from "financial data over time" → "compare electrolyte properties across forms"
- ✅ Changed examples from revenue trends → bioavailability comparisons

#### 4. **Supervisor/Planner** (Cell 66)
- ✅ Updated from "master financial analyst agent" → "master biomedical research analyst agent"
- ✅ Changed plan example from revenue analysis → magnesium form comparison

#### 5. **Discussion Text Updates** (Cells 46, 48, 51, 54, 67)
- ✅ Updated all discussion text to reflect research context
- ✅ Changed references from SEC filings → research papers
- ✅ Updated terminology from financial → biochemical

---

## 📋 Remaining Tasks

### **Phase 3: Reasoning Engine & Graph Orchestration**

**Status:** Ready for testing (minimal changes needed)
- The cognitive architecture (Gatekeeper, Planner, Auditor, Tool Executor) operates on abstracted tool layer
- Main changes needed: Update example queries in test cells to use electrolyte research questions
- Update Gatekeeper ambiguity examples (currently use Microsoft financial queries)

### **Phase 4: Advanced Evaluation**

**Status:** Requires update of test queries and evaluation criteria
- Replace financial query examples with electrolyte research queries
- Update evaluation criteria from financial accuracy → scientific accuracy
- RAGAS framework works the same, just needs domain-appropriate questions

### **Phase 5: Red Teaming**

**Status:** Ready (auto-generated, minimal changes)
- Red team prompts are auto-generated from user queries
- May need to test with electrolyte-specific edge cases

### **Phase 6: Advanced Features**

**Status:** Ready (Memory, Monitoring, Vision work on any domain)
- The Scribe (Memory): Domain-agnostic
- The Watchtower (Monitoring): Works with PubMed queries
- The Oracle (Vision): Can analyze charts from any papers

---

## 🔧 Technical Details

### **Data Sources**

**PubMed Central API:**
- **Endpoint:** Via `pymed` Python library
- **Authentication:** Email address (for courtesy identification)
- **Rate Limits:** Generous free tier, no API key required
- **Data Format:** Structured objects with title, abstract, authors, pubmed_id, publication_date
- **Coverage:** Millions of open-access biomedical research papers

**Search Strategy:**
```python
SEARCH_QUERIES = [
    "electrolyte absorption bioavailability",
    "sodium supplementation metabolism",
    "potassium citrate bioavailability",
    "magnesium absorption forms",
    "calcium citrate vs carbonate",
    "electrolyte timing exercise performance"
]
MAX_RESULTS_PER_QUERY = 20
```

### **File Structure**

```
Agentic.RAG/
├── venv/                          # Virtual environment
├── electrolyte_research_papers/   # Downloaded papers
│   └── PMC_{pubmed_id}.txt       # Format: Title, Authors, Abstract
├── electrolyte_properties.csv     # Structured database
├── code.ipynb                     # Main notebook (partially updated)
├── requirements.txt               # Updated dependencies
├── test_pmc_connection.py         # Test script
└── AGENT_SCRATCHPAD.md           # This file
```

### **Key Architecture Decisions**

1. **Text-based storage** instead of PDF parsing
   - Rationale: PMC provides structured abstracts, no need for complex PDF parsing
   - Benefit: Faster, more reliable, simpler to chunk

2. **Kept vector store approach** (Qdrant + embeddings)
   - Works identically for research papers as for financial docs
   - No changes needed to Phase 1 embedding logic

3. **Structured database for properties**
   - Similar to original financial metrics
   - Allows SQL agent to answer factual queries about electrolyte forms

4. **Preserved all cognitive architecture**
   - Gatekeeper, Planner, Auditor, Strategist all remain
   - Only prompt content needs updating, not logic

---

## 🚀 How to Continue

### **Current Status: Phase 1-2 Complete! ✅**

All core prompts and agent tool descriptions have been successfully updated from financial domain to electrolyte research domain.

### **Next Steps (Phase 3-4):**

1. **Test the updated pipeline**
   - Run cells to verify prompts work correctly with new domain
   - Test each agent tool individually with electrolyte queries
   - Sample test query: "What is the bioavailability of magnesium citrate vs magnesium oxide?"

2. **Update Gatekeeper examples** (Cell 62-64)
   - Replace "How is Microsoft doing?" with electrolyte research examples
   - Update ambiguous vs specific query tests

3. **Update evaluation queries** (Phase 4)
   - Replace financial test queries with electrolyte research questions
   - Verify RAGAS evaluation framework works with new domain

4. **End-to-end validation**
   - Run full pipeline with representative electrolyte research queries
   - Verify vector store retrieval, SQL queries, and agent responses

### **Commands to Resume Work:**

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# If you need to reinstall packages:
pip install pymed biopython pandas requests

# To test connection again:
python3 test_pmc_connection.py

# To run full notebook (requires more packages):
pip install langchain langgraph langchain-openai langchain-google-genai \
    qdrant-client fastembed sentence-transformers langsmith ragas \
    tavily-python python-dotenv tqdm unstructured
```

### **Quick Reference: Component Status**

| Component | Status | Priority | Cells |
|-----------|--------|----------|-------|
| Metadata enrichment prompts | ✅ Complete | HIGH | 27-30 |
| Agent tool descriptions | ✅ Complete | HIGH | 46, 47, 48, 50, 51, 53, 54 |
| Supervisor/Planner prompt | ✅ Complete | HIGH | 66, 67 |
| Gatekeeper examples | ⏳ Pending | MEDIUM | 62-64 |
| Query examples in tests | ⏳ Pending | MEDIUM | Throughout Phase 3-5 |
| Chunking strategy validation | ⏳ Pending | LOW | 24-25 |
| End-to-end testing | ⏳ Pending | HIGH | Full pipeline |

---

## 📊 Performance Baselines

**Test Run (Oct 2, 2025):**
- Papers retrieved: 15 unique papers
- Average abstract length: ~2,143 bytes
- Search queries: 3 different topics
- API response time: Fast (< 5 seconds per query)
- Deduplication: 100% effective (0 duplicates in test)

**Expected Production Scale:**
- Total papers: 100-120 (6 queries × 20 papers)
- After deduplication: ~80-100 unique papers
- Vector DB size: ~200-300 chunks (after chunking abstracts)
- Structured DB: 10 electrolyte forms

---

## 🎓 Key Learnings

1. **PMC API is robust**: No authentication needed, generous rate limits
2. **Text format simpler than PDF**: Abstracts are well-structured, easier to parse
3. **Virtual env essential**: PEP 668 protection on modern Ubuntu requires venv
4. **Architecture is domain-agnostic**: Most of the RAG pipeline needs no logic changes
5. **Prompt updates are the main work**: Converting financial → research terminology

---

## 🔗 Important Links

- **Original Project**: Based on Uber's Enhanced Agentic RAG blog post
- **PubMed Central API**: https://www.ncbi.nlm.nih.gov/pmc/tools/developers/
- **PyMed Library**: https://github.com/gijswobben/pymed
- **Test Results**: See `test_papers/` directory for sample output

---

## ⚠️ Known Issues / Notes

1. **Virtual Environment**: Must activate before running any Python scripts
2. **pip not installed by default**: Required `apt install python3-pip` and `python3-venv`
3. **Sample paper content**: Test retrieval included some non-electrolyte papers (like ritonavir) - may need more specific queries for production
4. **Metadata quality**: Depends on abstract availability in PMC (most have full abstracts)

---

## 💡 Future Enhancements (Optional)

1. **Full-text PDF retrieval**: Some PMC papers have full PDFs available
2. **Citation network analysis**: PMC provides citation links
3. **Temporal analysis**: Track research trends over time
4. **Multi-modal vision**: Extract data from charts/tables in papers (Phase 6 feature)
5. **Semantic Scholar integration**: Additional paper source for broader coverage

---

**End of Scratchpad**

*This document should be updated at the start of each new session to track progress and context.*

