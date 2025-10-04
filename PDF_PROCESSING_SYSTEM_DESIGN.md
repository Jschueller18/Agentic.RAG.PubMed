# Automated PDF Processing System for BestMove Research

## System Architecture

```
[1. Paper Discovery]
    ↓
[2. PDF Download]
    ↓
[3. PDF Parsing & Extraction]
    ↓
[4. Markdown Conversion]
    ↓
[5. Database Storage]
    ↓
[6. RAG System Integration]
```

---

## Component 1: Paper Discovery & Prioritization

**Input:** Research queries (from BESTMOVE_CONTEXT.md use cases)
**Output:** Ranked list of papers to acquire

### Features:
```python
def discover_papers(query, max_results=100):
    """
    Search PubMed/Semantic Scholar for relevant papers
    """
    # 1. Search with BestMove-specific queries
    # 2. Filter by:
    #    - Has quantitative data (look for keywords: "dose", "mg", "n=", "p<", "RCT")
    #    - Recent (last 10 years preferred)
    #    - High citations (quality indicator)
    # 3. Rank by relevance using cross-encoder
    # 4. Return top N papers with metadata
    
    return ranked_papers
```

**Technology:**
- PubMed API (free abstracts)
- Semantic Scholar API (better metadata)
- Cross-encoder for re-ranking (already have this!)

---

## Component 2: PDF Download Manager

**Input:** List of papers with DOI/PMID/PMC ID
**Output:** Downloaded PDFs in organized structure

### Features:
```python
def download_paper_pdf(paper_id, access_method='institutional'):
    """
    Attempts multiple download strategies
    """
    strategies = [
        check_pmc_open_access(),      # Free if available
        check_publisher_link(),        # Direct if open access
        use_institutional_access(),    # Your temporary subscription
        check_author_repository(),     # ResearchGate, etc.
    ]
    
    # Try each strategy until success
    for strategy in strategies:
        pdf_path = strategy(paper_id)
        if pdf_path:
            return save_to_organized_folder(pdf_path, paper_id)
    
    return mark_for_manual_acquisition(paper_id)
```

**File Organization:**
```
research_papers/
├── raw_pdfs/
│   ├── PMID_12345678.pdf
│   ├── PMID_23456789.pdf
│   └── ...
├── parsed_content/
│   ├── PMID_12345678.md
│   ├── PMID_12345678_metadata.json
│   └── ...
└── extraction_logs/
    └── processing_log.json
```

---

## Component 3: PDF Parsing & Table Extraction

**Input:** PDF files
**Output:** Structured content with tables, sections, figures

### Features (using `unstructured` library - already installed!):
```python
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

def parse_pdf_with_structure(pdf_path):
    """
    Parse PDF preserving structure: titles, sections, tables, figures
    """
    # 1. Parse PDF into elements
    elements = partition_pdf(
        filename=pdf_path,
        infer_table_structure=True,     # Extract tables!
        extract_images_in_pdf=True,      # Get figures
        strategy='hi_res'                # Best quality
    )
    
    # 2. Categorize elements
    sections = {
        'title': None,
        'abstract': [],
        'introduction': [],
        'methods': [],
        'results': [],         # THIS IS WHERE THE GOLD IS!
        'discussion': [],
        'tables': [],          # Quantitative data!
        'figures': []          # Dose-response curves!
    }
    
    # 3. Identify sections using section headers
    current_section = 'abstract'
    for element in elements:
        if element.type == 'Title':
            # Detect section changes
            header = element.text.lower()
            if 'method' in header:
                current_section = 'methods'
            elif 'result' in header:
                current_section = 'results'
            # ... etc
        
        elif element.type == 'Table':
            # CRITICAL: Tables contain dose-response data!
            sections['tables'].append({
                'html': element.metadata.text_as_html,
                'text': element.text,
                'context': current_section
            })
        
        elif element.type == 'Image' or element.type == 'Figure':
            sections['figures'].append({
                'path': element.metadata.image_path,
                'caption': element.text
            })
        
        else:
            sections[current_section].append(element.text)
    
    return sections
```

**Why This Works:**
- ✅ `unstructured` preserves table structure as HTML
- ✅ Keeps context (which section each table is from)
- ✅ Extracts figures (can analyze with vision models later)
- ✅ Maintains document hierarchy

---

## Component 4: Markdown Conversion

**Input:** Structured sections from parsing
**Output:** Clean markdown with preserved tables

### Features:
```python
def convert_to_markdown(sections, paper_metadata):
    """
    Convert structured content to markdown
    """
    markdown = f"""# {sections['title']}

**Authors:** {paper_metadata['authors']}
**Year:** {paper_metadata['year']}
**PMID:** {paper_metadata['pmid']}
**DOI:** {paper_metadata['doi']}

---

## Abstract

{' '.join(sections['abstract'])}

---

## Methods

{' '.join(sections['methods'])}

---

## Results

{' '.join(sections['results'])}

---

## Tables

"""
    
    # Add tables with proper markdown formatting
    for i, table in enumerate(sections['tables'], 1):
        markdown += f"\n### Table {i}\n\n"
        
        # Convert HTML table to markdown table
        markdown += convert_html_table_to_markdown(table['html'])
        markdown += f"\n*Context: {table['context']} section*\n\n"
    
    # Add discussion
    markdown += f"\n---\n\n## Discussion\n\n{' '.join(sections['discussion'])}\n"
    
    return markdown
```

**Example Output:**
```markdown
# Effects of Magnesium Supplementation on Sleep Quality: A Randomized Controlled Trial

**Authors:** Smith et al.
**Year:** 2023
**PMID:** 12345678

---

## Results

A total of 120 participants completed the study. Sleep onset latency was significantly reduced in the magnesium group compared to placebo...

---

## Tables

### Table 2: Dose-Response Effects on Sleep Latency

| Dose (mg) | n | Baseline SOL (min) | Post SOL (min) | Change | p-value |
|-----------|---|-------------------|----------------|--------|---------|
| 100       | 30| 42.3 ± 8.2        | 38.1 ± 7.5     | -4.2   | 0.08    |
| 200       | 30| 41.8 ± 9.1        | 32.5 ± 6.8     | -9.3   | 0.002   |
| 300       | 30| 43.1 ± 7.9        | 28.2 ± 5.4     | -14.9  | <0.001  |

*Context: Results section*

---
```

**This is EXACTLY what you need for BestMove!**

---

## Component 5: Database Storage

**Input:** Markdown files + metadata
**Output:** Searchable database + vector store

### Features:
```python
def store_in_database(markdown_content, metadata, sections):
    """
    Store in multiple formats for different use cases
    """
    
    # 1. File storage (markdown files)
    save_markdown_file(markdown_content, metadata['pmid'])
    
    # 2. Structured database (SQLite/Postgres)
    db.papers.insert({
        'pmid': metadata['pmid'],
        'title': metadata['title'],
        'year': metadata['year'],
        'authors': metadata['authors'],
        'num_tables': len(sections['tables']),
        'has_dose_response': detect_dose_response_data(sections),
        'markdown_path': f"parsed_content/PMID_{metadata['pmid']}.md",
        'relevance_score': calculate_relevance_to_bestmove(sections)
    })
    
    # 3. Extract quantitative data to structured format
    for table in sections['tables']:
        extracted_data = extract_quantitative_values(table)
        db.quantitative_data.insert({
            'pmid': metadata['pmid'],
            'table_number': table['number'],
            'mineral': extracted_data['mineral'],  # e.g., "magnesium"
            'doses': extracted_data['doses'],      # [100, 200, 300]
            'outcomes': extracted_data['outcomes'], # sleep latency values
            'effect_sizes': extracted_data['effects']
        })
    
    # 4. Vector embeddings for RAG
    chunks = chunk_by_title(sections)  # Already have this function!
    for chunk in chunks:
        embedding = embedding_model.embed(chunk.text)
        vector_store.add(chunk, embedding, metadata)
```

**Database Schema:**
```sql
-- Papers table
CREATE TABLE papers (
    pmid TEXT PRIMARY KEY,
    title TEXT,
    year INTEGER,
    authors TEXT,
    abstract TEXT,
    markdown_path TEXT,
    has_quantitative_data BOOLEAN,
    relevance_score FLOAT
);

-- Quantitative data table (THE GOLD!)
CREATE TABLE quantitative_data (
    id INTEGER PRIMARY KEY,
    pmid TEXT,
    mineral TEXT,              -- magnesium, sodium, potassium, calcium
    form TEXT,                 -- citrate, oxide, glycinate, etc.
    dose_mg FLOAT,
    outcome_measure TEXT,      -- sleep latency, absorption, etc.
    outcome_value FLOAT,
    effect_size FLOAT,
    p_value FLOAT,
    population TEXT,           -- age group, health status
    FOREIGN KEY (pmid) REFERENCES papers(pmid)
);
```

---

## Component 6: RAG Integration

Once processed, integrate with existing notebook:

```python
# Option A: Replace librarian_rag_tool with local corpus
@tool
def librarian_local_corpus(query: str) -> List[Dict[str, Any]]:
    """
    Search curated BestMove research corpus
    """
    # Vector search on your markdown files
    results = vector_store.search(query, limit=20)
    
    # Re-rank (already have cross-encoder!)
    reranked = cross_encoder_rerank(query, results)
    
    # Return with full context including tables
    return format_results_with_tables(reranked[:5])
```

**Benefits:**
- ✅ Fast (<2 seconds vs 15-30 for live API)
- ✅ Complete control over corpus quality
- ✅ Tables included in context!
- ✅ Quantitative data extracted to structured DB

---

## Full Automation Script

```python
# automated_paper_processor.py

def process_bestmove_research_corpus():
    """
    End-to-end automation
    """
    
    # 1. Discover papers
    queries = load_bestmove_queries()  # From BESTMOVE_CONTEXT.md
    all_papers = []
    for query in queries:
        papers = discover_papers(query, max_results=20)
        all_papers.extend(papers)
    
    # Deduplicate and rank
    unique_papers = deduplicate_by_pmid(all_papers)
    prioritized = rank_by_data_richness(unique_papers)
    
    print(f"Found {len(prioritized)} unique papers to process")
    
    # 2. Download PDFs (with your institutional access)
    print("\nDownloading PDFs...")
    for paper in prioritized[:100]:  # Top 100 papers
        pdf_path = download_paper_pdf(paper.pmid)
        if pdf_path:
            paper.pdf_path = pdf_path
            print(f"  ✓ {paper.pmid}")
        else:
            print(f"  ✗ {paper.pmid} - manual acquisition needed")
    
    # 3. Parse all PDFs
    print("\nParsing PDFs...")
    for paper in prioritized:
        if not paper.pdf_path:
            continue
        
        try:
            sections = parse_pdf_with_structure(paper.pdf_path)
            markdown = convert_to_markdown(sections, paper.metadata)
            store_in_database(markdown, paper.metadata, sections)
            print(f"  ✓ Processed {paper.pmid}")
        except Exception as e:
            print(f"  ✗ Error processing {paper.pmid}: {e}")
    
    # 4. Build vector store
    print("\nBuilding vector store...")
    build_vector_store_from_markdown()
    
    # 5. Generate summary report
    generate_corpus_report()
    
    print("\n✅ BestMove research corpus ready!")
    print(f"   - {count_papers()} papers processed")
    print(f"   - {count_tables()} tables extracted")
    print(f"   - {count_quantitative_datapoints()} quantitative data points")
```

---

## Timeline & Effort

**Week 1: Setup & Discovery**
- Set up institutional access (DeepDyve or alumni)
- Run paper discovery scripts
- Identify top 100 papers
- **Effort:** 4-6 hours

**Week 2-3: Acquisition**
- Download PDFs (mostly automated)
- Manual requests for unavailable papers
- **Effort:** 8-10 hours (mostly waiting)

**Week 4: Processing**
- Run automated parsing
- Quality check extracted tables
- Fix any parsing errors
- **Effort:** 6-8 hours

**Week 5: Integration**
- Build vector store
- Integrate with notebook
- Test queries
- **Effort:** 4-6 hours

**Total:** ~25-30 hours over 5 weeks
**Result:** Permanent, high-quality research corpus with quantitative data!

---

## Cost-Benefit Analysis

**Costs:**
- Institutional access: $100-200
- Your time: ~30 hours
- **Total: $100-200 + time**

**Benefits:**
- ✅ Own the corpus forever (no ongoing API costs)
- ✅ Actual quantitative data (not just abstracts!)
- ✅ Tables with dose-response curves
- ✅ Fast queries (<2s vs 15-30s)
- ✅ Complete control over quality
- ✅ Legal and ethical
- ✅ Can extend/update anytime

**ROI:** Massive! This is your competitive moat.

