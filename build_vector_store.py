#!/usr/bin/env python3
"""
Vector Store Builder - BestMove Electrolyte Research
Generates embeddings and stores 203,174 chunks in Qdrant vector database

Pipeline:
1. Load processed chunks from JSON files
2. Generate embeddings using fastembed (fast, local, no API costs!)
3. Store in Qdrant with metadata for filtering
4. Create optimized indexes for fast retrieval

Estimated runtime: 30-60 minutes for 203,174 chunks
Output: Qdrant database ready for RAG queries
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from datetime import datetime
import numpy as np

# Embeddings and Vector DB
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)


# ============================================================
# CONFIGURATION
# ============================================================

CHUNKS_DIR = Path("processed_corpus/chunks")
VECTOR_DB_PATH = "./bestmove_vector_db"
COLLECTION_NAME = "bestmove_research"

# Embedding model (BAAI/bge-small-en-v1.5 - fast, good quality, 384 dimensions)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384  # Dimension of the model

# Processing batch size (for memory management)
BATCH_SIZE = 100  # Process 100 chunks at a time


# ============================================================
# LOAD CHUNKS
# ============================================================

def load_all_chunks() -> List[Dict[str, Any]]:
    """
    Load all chunks from processed JSON files.
    Returns list of chunks with metadata.
    """
    print("Loading chunks from JSON files...")
    
    chunk_files = sorted(CHUNKS_DIR.glob("*_chunks.json"))
    
    if not chunk_files:
        raise FileNotFoundError(f"No chunk files found in {CHUNKS_DIR}")
    
    print(f"Found {len(chunk_files):,} chunk files")
    
    all_chunks = []
    papers_loaded = 0
    
    for chunk_file in tqdm(chunk_files, desc="Loading chunks"):
        try:
            with open(chunk_file, 'r') as f:
                data = json.load(f)
            
            paper_info = data['paper']
            chunks = data['chunks']
            
            # Add paper metadata to each chunk
            for i, chunk in enumerate(chunks):
                chunk_with_metadata = {
                    'text': chunk['text'],
                    'pmcid': paper_info['pmcid'],
                    'title': paper_info['title'],
                    'authors': paper_info.get('authors', []),
                    'journal': paper_info.get('journal', ''),
                    'year': paper_info.get('year', ''),
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'has_methods': paper_info['statistics'].get('has_methods', False),
                    'has_results': paper_info['statistics'].get('has_results', False),
                    'num_tables': paper_info['statistics'].get('total_tables', 0)
                }
                all_chunks.append(chunk_with_metadata)
            
            papers_loaded += 1
            
        except Exception as e:
            print(f"\nError loading {chunk_file.name}: {e}")
            continue
    
    print(f"\n✅ Loaded {len(all_chunks):,} chunks from {papers_loaded:,} papers")
    return all_chunks


# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

def generate_embeddings(chunks: List[Dict[str, Any]], model: TextEmbedding) -> List[np.ndarray]:
    """
    Generate embeddings for chunks in batches.
    Returns list of embedding vectors.
    """
    print(f"\nGenerating embeddings for {len(chunks):,} chunks...")
    print(f"Model: {EMBEDDING_MODEL} (dimension: {EMBEDDING_DIM})")
    
    embeddings = []
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Generating embeddings"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [chunk['text'] for chunk in batch]
        
        # Generate embeddings for batch
        batch_embeddings = list(model.embed(texts))
        embeddings.extend(batch_embeddings)
    
    print(f"✅ Generated {len(embeddings):,} embeddings")
    return embeddings


# ============================================================
# CREATE VECTOR DATABASE
# ============================================================

def create_vector_collection(client: QdrantClient):
    """
    Create Qdrant collection with proper schema.
    """
    print(f"\nCreating Qdrant collection: {COLLECTION_NAME}")
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print("  Deleted existing collection")
    except:
        pass
    
    # Create new collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE  # Cosine similarity for semantic search
        )
    )
    
    print(f"✅ Collection created: {COLLECTION_NAME}")


def store_chunks_in_qdrant(
    client: QdrantClient,
    chunks: List[Dict[str, Any]],
    embeddings: List[np.ndarray]
):
    """
    Store chunks and embeddings in Qdrant with metadata.
    """
    print(f"\nStoring {len(chunks):,} chunks in Qdrant...")
    
    points = []
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        # Create point with vector and payload (metadata)
        point = PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={
                'text': chunk['text'],
                'pmcid': chunk['pmcid'],
                'title': chunk['title'],
                'authors': chunk['authors'][:5],  # Limit to first 5 authors
                'journal': chunk['journal'],
                'year': chunk['year'],
                'chunk_id': chunk['chunk_id'],
                'total_chunks': chunk['total_chunks'],
                'has_methods': chunk['has_methods'],
                'has_results': chunk['has_results'],
                'num_tables': chunk['num_tables']
            }
        )
        points.append(point)
        
        # Upload in batches
        if len(points) >= BATCH_SIZE:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            points = []
    
    # Upload remaining points
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    
    print(f"✅ Stored {len(chunks):,} chunks in Qdrant")


# ============================================================
# VERIFICATION & STATS
# ============================================================

def verify_vector_store(client: QdrantClient, chunks: List[Dict[str, Any]]):
    """
    Verify the vector store was created correctly and show statistics.
    """
    print("\n" + "="*80)
    print("VECTOR STORE VERIFICATION")
    print("="*80)
    
    # Get collection info
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    
    print(f"\n📊 Collection Stats:")
    print(f"  Name: {COLLECTION_NAME}")
    print(f"  Total vectors: {collection_info.points_count:,}")
    print(f"  Vector dimension: {EMBEDDING_DIM}")
    print(f"  Distance metric: Cosine similarity")
    
    # Calculate metadata stats
    years = [c['year'] for c in chunks if c['year']]
    journals = [c['journal'] for c in chunks if c['journal']]
    papers_with_methods = sum(1 for c in chunks if c['has_methods'])
    papers_with_results = sum(1 for c in chunks if c['has_results'])
    papers_with_tables = sum(1 for c in chunks if c['num_tables'] > 0)
    
    print(f"\n📄 Content Stats:")
    print(f"  Unique papers: {len(set(c['pmcid'] for c in chunks)):,}")
    print(f"  Year range: {min(years) if years else 'N/A'} - {max(years) if years else 'N/A'}")
    print(f"  Unique journals: {len(set(journals)):,}")
    print(f"  Chunks with Methods: {papers_with_methods:,} ({papers_with_methods/len(chunks)*100:.1f}%)")
    print(f"  Chunks with Results: {papers_with_results:,} ({papers_with_results/len(chunks)*100:.1f}%)")
    print(f"  Papers with Tables: {papers_with_tables:,} ({papers_with_tables/len(chunks)*100:.1f}%)")
    
    # Test search
    print(f"\n🔍 Test Search: 'magnesium supplementation sleep quality'")
    test_query = "magnesium supplementation sleep quality dose response"
    
    # Generate embedding for test query
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    query_embedding = list(model.embed([test_query]))[0]
    
    # Search
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=3
    )
    
    print(f"\n  Top 3 results:")
    for i, result in enumerate(search_results, 1):
        print(f"\n  {i}. Score: {result.score:.3f}")
        print(f"     Paper: {result.payload['title'][:80]}...")
        print(f"     Journal: {result.payload['journal']} ({result.payload['year']})")
        print(f"     PMC ID: {result.payload['pmcid']}")
        print(f"     Text: {result.payload['text'][:150]}...")
    
    print("\n" + "="*80)
    print("✅ VECTOR STORE READY FOR RAG!")
    print("="*80)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """
    Main pipeline: Load chunks → Generate embeddings → Store in Qdrant
    """
    print("\n" + "="*80)
    print("VECTOR STORE BUILDER - BestMove Electrolyte Research")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Chunks directory: {CHUNKS_DIR}")
    print(f"Vector DB path: {VECTOR_DB_PATH}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print("="*80 + "\n")
    
    start_time = datetime.now()
    
    # Step 1: Load all chunks
    chunks = load_all_chunks()
    
    if not chunks:
        print("❌ No chunks found! Exiting.")
        return
    
    # Step 2: Initialize embedding model
    print("\nInitializing embedding model...")
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    print("✅ Model loaded")
    
    # Step 3: Generate embeddings
    embeddings = generate_embeddings(chunks, model)
    
    # Step 4: Initialize Qdrant client
    print("\nInitializing Qdrant client...")
    client = QdrantClient(path=VECTOR_DB_PATH)
    print(f"✅ Client initialized (path: {VECTOR_DB_PATH})")
    
    # Step 5: Create collection
    create_vector_collection(client)
    
    # Step 6: Store chunks with embeddings
    store_chunks_in_qdrant(client, chunks, embeddings)
    
    # Step 7: Verify and show stats
    verify_vector_store(client, chunks)
    
    # Final summary
    elapsed = datetime.now() - start_time
    print(f"\n⏱️  Total time: {elapsed}")
    print(f"📁 Vector database saved to: {VECTOR_DB_PATH}/")
    print(f"🎯 Collection name: {COLLECTION_NAME}")
    print(f"\n✅ Vector store ready for integration with code.ipynb!")
    print("\nNext steps:")
    print("  1. Open code.ipynb")
    print("  2. Update vector store path to './bestmove_vector_db'")
    print("  3. Update collection name to 'bestmove_research'")
    print("  4. Test with BestMove queries!")
    print("="*80 + "\n")


# ============================================================
# QUICK SEARCH FUNCTION (for testing)
# ============================================================

def search_vector_store(query: str, top_k: int = 5):
    """
    Quick search function for testing the vector store.
    
    Usage:
        python3 build_vector_store.py search "magnesium sleep"
    """
    print(f"\n🔍 Searching for: '{query}'")
    print(f"   Top {top_k} results\n")
    
    # Initialize
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    client = QdrantClient(path=VECTOR_DB_PATH)
    
    # Generate query embedding
    query_embedding = list(model.embed([query]))[0]
    
    # Search
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=top_k
    )
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.score:.3f}")
        print(f"   Paper: {result.payload['title']}")
        print(f"   Journal: {result.payload['journal']} ({result.payload['year']})")
        print(f"   PMC ID: {result.payload['pmcid']}")
        print(f"   Text: {result.payload['text'][:200]}...")
        print()


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        # Search mode
        if len(sys.argv) < 3:
            print("Usage: python3 build_vector_store.py search 'your query here'")
            sys.exit(1)
        
        query = " ".join(sys.argv[2:])
        search_vector_store(query)
    else:
        # Build mode
        main()

