"""
Live Research Tool - PubMed API with Auto-Caching
BestMove Internal R&D Configuration

Fetches papers in real-time from PubMed Central and automatically caches them
for future customer chatbot corpus building.

Architecture:
    Query → Optimize → PubMed API → Re-rank → Cache → Return top 5
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from pymed import PubMed
from sentence_transformers import CrossEncoder

# Configuration
CACHE_DIR = "electrolyte_research_papers"
CACHE_METADATA = "papers_cache.json"
QUERY_HISTORY = "query_history.json"
MAX_RESULTS = 20  # Fetch candidates for re-ranking
TOP_K = 5  # Return only top results after re-ranking

# Initialize
os.makedirs(CACHE_DIR, exist_ok=True)
pubmed = PubMed(tool="BestMoveRAG", email="research@bestmove.com")
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')


def load_cache_metadata() -> Dict:
    """Load cached papers metadata."""
    if os.path.exists(CACHE_METADATA):
        with open(CACHE_METADATA, 'r') as f:
            return json.load(f)
    return {"papers": {}, "stats": {"total_papers": 0, "total_queries": 0}}


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


def cache_paper(paper, pubmed_id: str) -> str:
    """Save paper to cache directory. Returns filepath."""
    filepath = f"{CACHE_DIR}/PMC_{pubmed_id}.txt"
    
    # Skip if already cached
    if os.path.exists(filepath):
        return filepath
    
    # Save paper content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Title: {paper.title or 'No title'}\n\n")
        f.write(f"PubMed ID: {pubmed_id}\n\n")
        authors = ', '.join([f"{a.get('firstname', '')} {a.get('lastname', '')}" 
                            for a in (paper.authors or [])])
        f.write(f"Authors: {authors or 'No authors listed'}\n\n")
        f.write(f"Publication Date: {paper.publication_date or 'Unknown'}\n\n")
        f.write(f"Abstract:\n{paper.abstract or 'No abstract available'}\n")
    
    return filepath


def live_research_tool(query: str, verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Search PubMed API in real-time and cache results.
    
    Args:
        query: Research question (will be used as-is for PubMed search)
        verbose: Print progress messages
        
    Returns:
        List of top-ranked papers with metadata
    """
    if verbose:
        print(f"\n{'='*80}")
        print(f"LIVE RESEARCH TOOL - PubMed API")
        print(f"{'='*80}")
        print(f"Query: {query}")
    
    # Step 1: Fetch papers from PubMed
    if verbose:
        print(f"\n[1/4] Fetching papers from PubMed (max {MAX_RESULTS})...")
    
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
    
    # Step 2: Cache papers and extract abstracts
    if verbose:
        print(f"\n[2/4] Caching papers to {CACHE_DIR}/...")
    
    cached_papers = []
    paper_ids = []
    
    for paper in papers:
        try:
            pubmed_id = paper.pubmed_id.split('\n')[0] if paper.pubmed_id else None
            if not pubmed_id or not paper.abstract:
                continue
            
            filepath = cache_paper(paper, pubmed_id)
            paper_ids.append(pubmed_id)
            
            cached_papers.append({
                'pubmed_id': pubmed_id,
                'title': paper.title or '',
                'abstract': paper.abstract or '',
                'filepath': filepath
            })
        except Exception as e:
            continue
    
    if verbose:
        print(f"      ✓ Cached {len(cached_papers)} papers")
    
    # Step 3: Re-rank using cross-encoder
    if verbose:
        print(f"\n[3/4] Re-ranking with cross-encoder...")
    
    rerank_pairs = [[query, p['abstract']] for p in cached_papers]
    scores = cross_encoder.predict(rerank_pairs)
    
    for i, score in enumerate(scores):
        cached_papers[i]['rerank_score'] = float(score)
    
    reranked = sorted(cached_papers, key=lambda x: x['rerank_score'], reverse=True)
    
    if verbose:
        print(f"      ✓ Re-ranked {len(reranked)} papers")
    
    # Step 4: Select top K and format results
    top_papers = reranked[:TOP_K]
    
    if verbose:
        print(f"\n[4/4] Returning top {len(top_papers)} papers")
        print(f"\nTop Results:")
        for i, paper in enumerate(top_papers, 1):
            print(f"  {i}. [{paper['rerank_score']:.2f}] {paper['title'][:60]}...")
    
    # Update cache metadata
    metadata = load_cache_metadata()
    metadata['stats']['total_queries'] += 1
    for paper in top_papers:
        if paper['pubmed_id'] not in metadata['papers']:
            metadata['papers'][paper['pubmed_id']] = {
                'title': paper['title'],
                'first_seen': datetime.now().isoformat(),
                'usage_count': 1
            }
            metadata['stats']['total_papers'] += 1
        else:
            metadata['papers'][paper['pubmed_id']]['usage_count'] += 1
    
    save_cache_metadata(metadata)
    log_query(query, [p['pubmed_id'] for p in top_papers])
    
    # Format for compatibility with existing RAG architecture
    results = []
    for paper in top_papers:
        results.append({
            'source': f"PMC_{paper['pubmed_id']}",
            'content': paper['abstract'],
            'summary': paper['title'],  # Title as summary for now
            'rerank_score': paper['rerank_score']
        })
    
    if verbose:
        print(f"\n{'='*80}\n")
    
    return results


# Test function
if __name__ == "__main__":
    print("Testing Live Research Tool\n")
    
    # Test with a BestMove technical query
    test_query = "magnesium dose response sleep onset latency"
    
    results = live_research_tool(test_query, verbose=True)
    
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Query: {test_query}")
    print(f"Papers found: {len(results)}")
    print(f"\nCached to: {CACHE_DIR}/")
    print(f"Metadata: {CACHE_METADATA}")
    print(f"History: {QUERY_HISTORY}")

