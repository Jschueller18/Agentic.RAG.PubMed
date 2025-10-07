# PMC Corpus Processing Guide

## Overview
This pipeline filters 27,212 research papers for BestMove relevance, then chunks the relevant ones using structure-aware chunking.

**Expected Results:**
- ~5,000-8,000 relevant papers (from 27,212 total)
- ~50,000-150,000 chunks ready for vector embedding
- Runtime: 2-3 hours for full corpus

---

## Quick Start

### 1. Test on Small Sample First (Recommended!)
```bash
cd /home/jschu/projects/Agentic.RAG
python3 process_pmc_corpus.py --sample 100
```
This processes only 100 papers to verify everything works (~2 minutes).

### 2. Run Full Corpus (Permissive Filter)
```bash
python3 process_pmc_corpus.py
```
This processes all 27,212 papers with permissive filtering (~2-3 hours).

### 3. Run Full Corpus (Strict Filter)
```bash
python3 process_pmc_corpus.py --strict
```
Uses stricter criteria - only papers with both human context AND strong indicators.

---

## Output Structure

```
processed_corpus/
├── chunks/                              # Individual paper chunks
│   ├── PMC10051332_chunks.json
│   ├── PMC7648400_chunks.json
│   └── ... (5,000-8,000 files)
│
├── processing_stats.json                # Overall statistics
├── all_papers_metadata.json             # All 27K papers with filter results  
└── processed_papers_metadata.json       # Only processed papers
```

---

## Filtering Criteria

### What Gets INCLUDED:

**Target Minerals (MUST have):**
- Magnesium, Calcium, Potassium, Sodium, Electrolyte, Mineral

**Human/Clinical Context (MUST have one):**
- Human studies, patients, participants
- Supplementation, intake, dietary
- Deficiency, serum levels, plasma
- Bioavailability, absorption, dose
- Clinical trials, RCT, placebo

**Strong Indicators (BONUS - high priority):**
- Dose-response studies
- Randomized controlled trials
- Sleep quality, exercise performance
- Menstrual support, PMS
- Electrolyte disorders (hypokalemia, etc.)

### What Gets EXCLUDED:

- ❌ Plant studies (soil, crops, agriculture)
- ❌ Animal studies (livestock, poultry)
- ❌ In vitro / cell culture
- ❌ Nanotechnology
- ❌ Environmental science

---

## Understanding the Output

### processing_stats.json
```json
{
  "total_papers": 27212,
  "relevant_papers": 6543,
  "filtered_out": 20669,
  "processed_papers": 6521,
  "parsing_errors": 22,
  "total_chunks": 89234,
  "filter_reasons": {
    "Relevant (human context, strong indicator)": 3245,
    "Relevant (human context)": 2198,
    "No target minerals mentioned": 15432,
    ...
  }
}
```

### Individual Chunk Files (PMC10051332_chunks.json)
```json
{
  "paper": {
    "pmcid": "PMC10051332",
    "title": "Chronic Organic Magnesium Supplementation...",
    "authors": ["John Doe", "Jane Smith"],
    "journal": "Nutrients",
    "year": "2023",
    "num_chunks": 12
  },
  "chunks": [
    {
      "text": "Abstract\n\nBackground: Magnesium deficiency...",
      "metadata": {
        "filetype": "text/xml",
        "page_number": 1
      }
    },
    ...
  ]
}
```

---

## Monitoring Progress

The script shows real-time progress:

```
PHASE 1: Filtering for relevance...
Filtering: 100%|████████████| 27212/27212 [10:23<00:00, 43.7 papers/s]

✅ Filtering complete!
   Relevant papers: 6,543 (24.0%)
   Filtered out: 20,669

Top filter reasons:
   - Relevant (human context, strong indicator): 3,245
   - No target minerals mentioned: 15,432
   - Excluded topic (plant/animal/environmental): 4,872

PHASE 2: Parsing and chunking 6,543 relevant papers...
Processing: 100%|████████████| 6543/6543 [1:45:32<00:00, 1.04 papers/s]
```

---

## Next Steps After Processing

Once you have the chunks, you'll:

1. **Generate Embeddings** (using `sentence-transformers` or OpenAI)
   ```python
   from fastembed import TextEmbedding
   model = TextEmbedding()
   
   for chunk_file in chunk_files:
       chunks = load_chunks(chunk_file)
       embeddings = model.embed([c['text'] for c in chunks])
   ```

2. **Store in Vector Database** (Qdrant already in notebook)
   ```python
   from qdrant_client import QdrantClient
   client = QdrantClient(path="./qdrant_db")
   
   client.upsert(
       collection_name="bestmove_research",
       points=[...]
   )
   ```

3. **Integrate with RAG System** (existing code.ipynb)
   - Replace SEC filings data source
   - Use same chunk_by_title workflow (already done!)
   - Same vector search + cross-encoder re-ranking

---

## Troubleshooting

### "ImportError: No module named 'test_jats_xml_parser'"
Make sure you're in the project directory:
```bash
cd /home/jschu/projects/Agentic.RAG
```

### Processing too slow?
Try reducing chunk size:
```python
# In process_pmc_corpus.py, line ~195
max_chunk_size=1024  # Instead of 2048
```

### Want different filtering?
Edit `is_relevant_to_bestmove()` function in `process_pmc_corpus.py`:
- Add keywords to `human_indicators`
- Add exclusions to `exclusion_keywords`
- Adjust `strong_indicators` for priority topics

---

## Estimated Resource Usage

- **Disk Space:** ~500 MB for 6,000 papers (chunks as JSON)
- **Memory:** ~2 GB peak
- **CPU:** Single-threaded (could parallelize if needed)
- **Time:** 
  - Filtering: ~10 minutes
  - Parsing+Chunking: ~2 hours
  - Total: ~2h 10min

---

## Questions?

Check the code comments in `process_pmc_corpus.py` or adjust the filtering criteria to match your needs!

