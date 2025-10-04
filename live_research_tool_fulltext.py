"""
Live Research Tool V2 - PubMed API with FULL-TEXT RETRIEVAL
BestMove Internal R&D Configuration

MAJOR UPGRADE: Fetches full-text XML from PMC Open Access when available,
not just abstracts. This provides access to Results, Methods, and Tables
with the quantitative data needed for algorithm development.

Architecture:
    Query → PubMed API → Check PMC Open Access → Fetch Full-Text XML
    → Parse structured sections (Methods, Results, Tables) → Re-rank → Cache
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from pymed import PubMed
from sentence_transformers import CrossEncoder
import xml.etree.ElementTree as ET
import re

# Configuration
CACHE_DIR = "electrolyte_research_papers_fulltext"
CACHE_METADATA = "papers_cache_fulltext.json"
QUERY_HISTORY = "query_history_fulltext.json"
MAX_RESULTS = 20
TOP_K = 5

# Initialize
os.makedirs(CACHE_DIR, exist_ok=True)
pubmed = PubMed(tool="BestMoveRAG", email="research@bestmove.com")
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# PMC Open Access API endpoint
PMC_OA_API = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{}/ascii"


def get_pmc_id(pubmed_id: str) -> Optional[str]:
    """Convert PubMed ID to PMC ID using NCBI ID Converter API."""
    try:
        url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pubmed_id}&format=json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            if records and 'pmcid' in records[0]:
                return records[0]['pmcid']
    except:
        pass
    return None


def fetch_fulltext_xml(pmc_id: str) -> Optional[str]:
    """Fetch full-text XML from PMC Open Access Subset."""
    try:
        pmc_number = pmc_id.replace('PMC', '')
        url = PMC_OA_API.format(pmc_number)
        response = requests.get(url, timeout=30)
        if response.status_code == 200 and len(response.text) > 100:
            return response.text
    except:
        pass
    return None


def parse_bioc_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parse BioC XML and extract structured sections.
    Returns dict with sections and detected tables/figures.
    """
    sections = {
        'title': '',
        'abstract': '',
        'introduction': '',
        'methods': '',
        'results': '',
        'discussion': '',
        'conclusions': '',
        'tables': [],
        'figures': []
    }
    
    try:
        root = ET.fromstring(xml_content)
        
        # BioC XML structure: collection -> document -> passage
        for document in root.findall('.//document'):
            for passage in document.findall('.//passage'):
                # Get section type
                section_type = None
                section_title = None
                
                for infon in passage.findall('.//infon'):
                    key = infon.get('key', '').lower()
                    value = (infon.text or '').lower() if infon.text else None
                    
                    if key in ['type', 'section_type']:
                        section_type = value
                    elif key == 'title':
                        section_title = infon.text
                
                # Get text content
                text_elem = passage.find('.//text')
                if text_elem is not None and text_elem.text:
                    text = text_elem.text.strip()
                    
                    # Detect tables (often have "Table" in title or special formatting)
                    if section_title and ('table' in section_title.lower() or 'fig' in section_title.lower()):
                        if 'table' in section_title.lower():
                            sections['tables'].append({
                                'title': section_title,
                                'content': text
                            })
                        elif 'fig' in section_title.lower():
                            sections['figures'].append({
                                'title': section_title,
                                'caption': text
                            })
                    
                    # Categorize by section type
                    if not section_type:
                        continue
                        
                    if 'title' in section_type:
                        sections['title'] = text
                    elif 'abstract' in section_type:
                        sections['abstract'] += text + '\n\n'
                    elif 'intro' in section_type:
                        sections['introduction'] += text + '\n\n'
                    elif 'method' in section_type or 'material' in section_type:
                        sections['methods'] += text + '\n\n'
                    elif 'result' in section_type:
                        sections['results'] += text + '\n\n'
                    elif 'discuss' in section_type:
                        sections['discussion'] += text + '\n\n'
                    elif 'conclu' in section_type:
                        sections['conclusions'] += text + '\n\n'
        
        # Clean up sections
        for key in sections:
            if isinstance(sections[key], str):
                sections[key] = sections[key].strip()
                
    except Exception as e:
        print(f"      ⚠ XML parsing error: {str(e)[:100]}")
    
    return sections


def format_paper_content(sections: Dict[str, Any], for_ranking: bool = False) -> str:
    """
    Format parsed sections into readable text.
    If for_ranking=True, prioritize Results/Methods for re-ranking.
    """
    if for_ranking:
        # For re-ranking: prioritize quantitative sections
        content_parts = []
        
        if sections.get('results'):
            content_parts.append("RESULTS:\n" + sections['results'])
        
        if sections.get('methods'):
            content_parts.append("METHODS:\n" + sections['methods'])
        
        if sections.get('tables'):
            for i, table in enumerate(sections['tables'], 1):
                content_parts.append(f"TABLE {i} - {table['title']}:\n{table['content']}")
        
        if sections.get('abstract'):
            content_parts.append("ABSTRACT:\n" + sections['abstract'])
        
        return '\n\n'.join(content_parts)
    
    else:
        # For display/storage: full structured format
        output = []
        
        if sections.get('abstract'):
            output.append("=" * 80)
            output.append("ABSTRACT")
            output.append("=" * 80)
            output.append(sections['abstract'])
            output.append("")
        
        if sections.get('introduction'):
            output.append("=" * 80)
            output.append("INTRODUCTION")
            output.append("=" * 80)
            output.append(sections['introduction'])
            output.append("")
        
        if sections.get('methods'):
            output.append("=" * 80)
            output.append("METHODS")
            output.append("=" * 80)
            output.append(sections['methods'])
            output.append("")
        
        if sections.get('results'):
            output.append("=" * 80)
            output.append("RESULTS")
            output.append("=" * 80)
            output.append(sections['results'])
            output.append("")
        
        if sections.get('tables'):
            output.append("=" * 80)
            output.append(f"TABLES ({len(sections['tables'])})")
            output.append("=" * 80)
            for i, table in enumerate(sections['tables'], 1):
                output.append(f"\n--- Table {i}: {table['title']} ---")
                output.append(table['content'])
            output.append("")
        
        if sections.get('discussion'):
            output.append("=" * 80)
            output.append("DISCUSSION")
            output.append("=" * 80)
            output.append(sections['discussion'])
            output.append("")
        
        if sections.get('conclusions'):
            output.append("=" * 80)
            output.append("CONCLUSIONS")
            output.append("=" * 80)
            output.append(sections['conclusions'])
            output.append("")
        
        return '\n'.join(output)


def cache_paper_fulltext(paper, pubmed_id: str, sections: Optional[Dict] = None) -> str:
    """Save paper to cache with full-text structure if available."""
    filepath = f"{CACHE_DIR}/PMC_{pubmed_id}.txt"
    
    if os.path.exists(filepath):
        return filepath
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Title: {paper.title or 'No title'}\n")
        f.write(f"PubMed ID: {pubmed_id}\n")
        
        authors = ', '.join([f"{a.get('firstname', '')} {a.get('lastname', '')}" 
                            for a in (paper.authors or [])])
        f.write(f"Authors: {authors or 'No authors listed'}\n")
        f.write(f"Publication Date: {paper.publication_date or 'Unknown'}\n\n")
        
        if sections and (sections.get('results') or sections.get('methods')):
            f.write(format_paper_content(sections, for_ranking=False))
            f.write("\n\n[Full-text retrieved from PMC Open Access]\n")
        else:
            f.write(f"Abstract:\n{paper.abstract or 'No abstract available'}\n")
            f.write("\n[Note: Full-text not available in PMC Open Access]\n")
    
    return filepath


def load_cache_metadata() -> Dict:
    """Load cached papers metadata."""
    if os.path.exists(CACHE_METADATA):
        with open(CACHE_METADATA, 'r') as f:
            return json.load(f)
    return {
        "papers": {}, 
        "stats": {
            "total_papers": 0,
            "total_queries": 0,
            "fulltext_papers": 0,
            "abstract_only_papers": 0
        }
    }


def save_cache_metadata(metadata: Dict):
    """Save updated cache metadata."""
    with open(CACHE_METADATA, 'w') as f:
        json.dump(metadata, f, indent=2)


def log_query(query: str, paper_ids: List[str]):
    """Log which query found which papers."""
    history = []
    if os.path.exists(QUERY_HISTORY):
        with open(QUERY_HISTORY, 'r') as f:
            history = json.load(f)
    
    history.append({
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "paper_ids": paper_ids,
        "num_papers": len(paper_ids)
    })
    
    with open(QUERY_HISTORY, 'w') as f:
        json.dump(history, f, indent=2)


def live_research_tool_fulltext(query: str, verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Search PubMed API, fetch full-text when available, parse structure, and cache results.
    
    Returns papers with full Results/Methods/Tables sections when available.
    """
    if verbose:
        print(f"\n{'='*80}")
        print(f"LIVE RESEARCH TOOL V2 - PubMed + PMC Full-Text")
        print(f"{'='*80}")
        print(f"Query: {query}")
    
    # Step 1: Fetch papers from PubMed
    if verbose:
        print(f"\n[1/5] Fetching papers from PubMed (max {MAX_RESULTS})...")
    
    try:
        results = pubmed.query(query, max_results=MAX_RESULTS)
        papers = list(results)
        if verbose:
            print(f"      ✓ Found {len(papers)} papers")
    except Exception as e:
        print(f"      ✗ Error: {e}")
        return []
    
    if not papers:
        if verbose:
            print("      ⚠ No papers found for this query")
        return []
    
    # Step 2: Fetch full-text from PMC
    if verbose:
        print(f"\n[2/5] Checking PMC Open Access for full-text...")
    
    cached_papers = []
    fulltext_count = 0
    
    for paper in papers:
        try:
            pubmed_id = paper.pubmed_id.split('\n')[0] if paper.pubmed_id else None
            if not pubmed_id:
                continue
            
            content_for_ranking = paper.abstract or ''
            sections = None
            has_fulltext = False
            
            # Try to get full-text from PMC
            pmc_id = get_pmc_id(pubmed_id)
            if pmc_id:
                if verbose:
                    print(f"      → PMID {pubmed_id} → {pmc_id}...", end=' ')
                
                xml_content = fetch_fulltext_xml(pmc_id)
                if xml_content:
                    sections = parse_bioc_xml(xml_content)
                    if sections.get('results') or sections.get('methods'):
                        content_for_ranking = format_paper_content(sections, for_ranking=True)
                        has_fulltext = True
                        fulltext_count += 1
                        table_count = len(sections.get('tables', []))
                        if verbose:
                            print(f"✓ Full-text! ({table_count} tables)")
                    else:
                        if verbose:
                            print("⚠ XML but no Results/Methods")
                else:
                    if verbose:
                        print("✗ Not in Open Access")
            
            if not content_for_ranking:
                continue
            
            filepath = cache_paper_fulltext(paper, pubmed_id, sections)
            
            cached_papers.append({
                'pubmed_id': pubmed_id,
                'pmc_id': pmc_id,
                'title': paper.title or '',
                'content': content_for_ranking,
                'has_fulltext': has_fulltext,
                'sections': sections,
                'filepath': filepath
            })
            
        except Exception as e:
            continue
    
    if verbose:
        print(f"\n      ✓ Processed {len(cached_papers)} papers ({fulltext_count} with full-text)")
    
    # Step 3: Re-rank
    if verbose:
        print(f"\n[3/5] Re-ranking with cross-encoder...")
    
    rerank_pairs = [[query, p['content']] for p in cached_papers]
    scores = cross_encoder.predict(rerank_pairs)
    
    for i, score in enumerate(scores):
        cached_papers[i]['rerank_score'] = float(score)
    
    reranked = sorted(cached_papers, key=lambda x: x['rerank_score'], reverse=True)
    
    if verbose:
        print(f"      ✓ Re-ranked {len(reranked)} papers")
    
    # Step 4: Select top K
    top_papers = reranked[:TOP_K]
    
    if verbose:
        print(f"\n[4/5] Top {len(top_papers)} results:")
        for i, paper in enumerate(top_papers, 1):
            icon = "📄" if paper['has_fulltext'] else "📝"
            tables = len(paper['sections'].get('tables', [])) if paper['sections'] else 0
            table_info = f" ({tables} tables)" if tables > 0 else ""
            print(f"  {i}. [{paper['rerank_score']:.2f}] {icon}{table_info} | {paper['title'][:55]}...")
    
    # Step 5: Update cache
    if verbose:
        print(f"\n[5/5] Updating metadata...")
    
    metadata = load_cache_metadata()
    metadata['stats']['total_queries'] += 1
    
    for paper in top_papers:
        if paper['pubmed_id'] not in metadata['papers']:
            metadata['papers'][paper['pubmed_id']] = {
                'title': paper['title'],
                'pmc_id': paper.get('pmc_id'),
                'has_fulltext': paper['has_fulltext'],
                'first_seen': datetime.now().isoformat(),
                'usage_count': 1
            }
            metadata['stats']['total_papers'] += 1
            if paper['has_fulltext']:
                metadata['stats']['fulltext_papers'] += 1
            else:
                metadata['stats']['abstract_only_papers'] += 1
        else:
            metadata['papers'][paper['pubmed_id']]['usage_count'] += 1
    
    save_cache_metadata(metadata)
    log_query(query, [p['pubmed_id'] for p in top_papers])
    
    # Format results
    results = []
    for paper in top_papers:
        results.append({
            'source': f"PMID_{paper['pubmed_id']}" + (" 📄FULL-TEXT" if paper['has_fulltext'] else ""),
            'content': paper['content'],
            'summary': paper['title'],
            'has_fulltext': paper['has_fulltext'],
            'pmc_id': paper.get('pmc_id'),
            'rerank_score': paper['rerank_score'],
            'sections': paper['sections']
        })
    
    if verbose:
        print(f"      ✓ Complete!\n{'='*80}\n")
    
    return results


# Test
if __name__ == "__main__":
    print("Testing Live Research Tool V2 (Full-Text)\n")
    
    test_query = "magnesium supplementation dose response sleep randomized controlled trial"
    
    results = live_research_tool_fulltext(test_query, verbose=True)
    
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Query: {test_query}")
    print(f"Papers returned: {len(results)}")
    print(f"Full-text papers: {sum(1 for r in results if r['has_fulltext'])}")
    print(f"\nCache: {CACHE_DIR}/")
    print(f"Metadata: {CACHE_METADATA}")
    
    if results and results[0]['has_fulltext']:
        print(f"\n{'='*80}")
        print("SAMPLE: First 500 chars of full-text Results section")
        print(f"{'='*80}")
        print(results[0]['content'][:500] + "...")
