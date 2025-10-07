#!/usr/bin/env python3
"""
BestMove RAG System - Quick Test
Tests the vector store with BestMove-specific queries
"""

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from datetime import datetime

# Configuration
VECTOR_DB_PATH = "./bestmove_vector_db"
COLLECTION_NAME = "bestmove_research"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def search_bestmove_rag(query: str, top_k: int = 5, show_full_text: bool = False):
    """
    Search the BestMove RAG system with a query.
    
    Args:
        query: Search query (natural language)
        top_k: Number of results to return
        show_full_text: Whether to show full chunk text or just preview
    """
    print("="*80)
    print("BESTMOVE RAG SYSTEM - QUERY TEST")
    print("="*80)
    print(f"\n🔍 Query: '{query}'")
    print(f"📊 Returning top {top_k} results\n")
    
    # Initialize
    print("Loading embedding model...")
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    
    print("Connecting to vector database...")
    client = QdrantClient(path=VECTOR_DB_PATH)
    
    # Generate query embedding
    print("Generating query embedding...")
    query_embedding = list(model.embed([query]))[0]
    
    # Search
    print("Searching vector store...\n")
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k
    ).points
    
    # Display results
    print("="*80)
    print("SEARCH RESULTS")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*80}")
        print(f"RESULT #{i} - Similarity Score: {result.score:.3f}")
        print(f"{'='*80}")
        
        payload = result.payload
        
        print(f"\n📄 Paper Information:")
        print(f"   Title: {payload['title']}")
        print(f"   Journal: {payload['journal']} ({payload['year']})")
        print(f"   PMC ID: {payload['pmcid']}")
        print(f"   Authors: {', '.join(payload['authors'][:3])}")
        if len(payload['authors']) > 3:
            print(f"            ... and {len(payload['authors'])-3} more")
        
        print(f"\n📊 Content Quality:")
        print(f"   Has Methods: {'✓' if payload['has_methods'] else '✗'}")
        print(f"   Has Results: {'✓' if payload['has_results'] else '✗'}")
        print(f"   Number of Tables: {payload['num_tables']}")
        print(f"   Chunk: {payload['chunk_id']+1} of {payload['total_chunks']}")
        
        print(f"\n📝 Content:")
        if show_full_text:
            print(payload['text'])
        else:
            # Show first 500 characters
            text_preview = payload['text'][:500]
            print(f"   {text_preview}...")
            print(f"\n   [Showing first 500 characters. Total length: {len(payload['text'])} characters]")
    
    print("\n" + "="*80)
    print("✅ Search Complete!")
    print("="*80)


def test_bestmove_queries():
    """
    Run a series of BestMove-specific test queries.
    """
    print("\n" + "="*80)
    print("BESTMOVE RAG SYSTEM - COMPREHENSIVE TEST")
    print("="*80)
    print(f"Testing multiple use cases: Sleep, Exercise, Menstrual, Bioavailability")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    test_queries = [
        {
            "category": "Sleep Support Mix",
            "query": "What is the optimal magnesium dose for improving sleep quality and reducing insomnia?",
        },
        {
            "category": "Workout Performance Mix",
            "query": "How do electrolytes affect exercise performance and what are optimal sodium and potassium levels for athletes?",
        },
        {
            "category": "Menstrual Support Mix",
            "query": "What minerals help reduce menstrual cramps and PMS symptoms? What are effective dosages?",
        },
        {
            "category": "Bioavailability",
            "query": "What is the bioavailability difference between magnesium citrate and magnesium oxide?",
        },
        {
            "category": "Population Differences",
            "query": "How do age and gender affect magnesium and calcium requirements?",
        },
    ]
    
    for test in test_queries:
        print("\n" + "🎯"*40)
        print(f"USE CASE: {test['category']}")
        print("🎯"*40 + "\n")
        
        search_bestmove_rag(test['query'], top_k=3, show_full_text=False)
        
        input("\nPress Enter to continue to next query...")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE!")
    print("="*80)
    print("\nThe BestMove RAG system is ready for:")
    print("  ✓ Sleep Support queries")
    print("  ✓ Workout Performance queries")
    print("  ✓ Menstrual Support queries")
    print("  ✓ Bioavailability questions")
    print("  ✓ Population-specific dosing")
    print("  ✓ Dose-response relationships")
    print("  ✓ Mineral interactions")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single query mode
        if sys.argv[1] == "test":
            # Run comprehensive test suite
            test_bestmove_queries()
        else:
            # Custom query
            query = " ".join(sys.argv[1:])
            search_bestmove_rag(query, top_k=5, show_full_text=False)
    else:
        # Default: Quick test
        print("\nRunning quick test with Sleep Support query...\n")
        search_bestmove_rag(
            "What is the optimal magnesium dose for improving sleep quality in adults?",
            top_k=3,
            show_full_text=False
        )
        
        print("\n\n" + "="*80)
        print("HOW TO USE THIS SCRIPT")
        print("="*80)
        print("\n1. Single Query:")
        print("   python3 test_bestmove_rag.py your query here")
        print("\n2. Comprehensive Test (all use cases):")
        print("   python3 test_bestmove_rag.py test")
        print("\n3. Default (quick test):")
        print("   python3 test_bestmove_rag.py")
        print("\n" + "="*80 + "\n")

