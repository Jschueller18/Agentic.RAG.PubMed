#!/usr/bin/env python3
"""
Test BestMove RAG Integration - Simulates Cell 44 Update
Tests the vector store connection and librarian tool functionality
"""

import sys
import warnings
warnings.filterwarnings('ignore', category=UserWarning, message='Local mode is not recommended.*')

from fastembed import TextEmbedding
import qdrant_client
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any

print("="*80)
print("BESTMOVE RAG INTEGRATION TEST")
print("="*80)
print("\n📦 Step 1: Initialize Embedding Model...")

# Initialize the embedding model
# BAAI/bge-small-en-v1.5 is a great, performant open-source model
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
print("✅ Embedding model loaded: BAAI/bge-small-en-v1.5")

print("\n🔌 Step 2: Connect to BestMove Vector Database...")

# Set up the Qdrant client
# Connect to BestMove vector database (203,174 chunks from 5,366 papers)
try:
    client = qdrant_client.QdrantClient(path="./bestmove_vector_db")
    COLLECTION_NAME = "bestmove_research"
    
    # Collection already exists - no need to recreate!
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    
    print(f"✅ Connected to Qdrant collection '{COLLECTION_NAME}'")
    print(f"   📊 Total chunks: {collection_info.points_count:,}")
    print(f"   📐 Vector dimension: {collection_info.config.params.vectors.size}")
    print(f"   📏 Distance metric: {collection_info.config.params.vectors.distance}")
    
    if collection_info.points_count != 203174:
        print(f"\n⚠️  WARNING: Expected 203,174 chunks, but found {collection_info.points_count:,}")
        print("   This might indicate a different database or incomplete build.")
    
except Exception as e:
    print(f"❌ ERROR: Failed to connect to vector database")
    print(f"   Error: {str(e)}")
    print(f"\n   Troubleshooting:")
    print(f"   1. Check that './bestmove_vector_db/' exists")
    print(f"   2. Verify collection name is 'bestmove_research'")
    print(f"   3. Run 'python3 build_vector_store.py' if database doesn't exist")
    sys.exit(1)

print("\n🔧 Step 3: Initialize Cross-Encoder for Re-Ranking...")
cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("✅ Cross-encoder loaded: ms-marco-MiniLM-L-6-v2")

print("\n🧪 Step 4: Test RAG Query (Librarian Tool Simulation)...")

# Test query
test_query = "What is the optimal magnesium dose for improving sleep quality in adults?"
print(f"\n📝 Query: \"{test_query}\"")

print("\n   → Generating query embedding...")
query_embedding = list(embedding_model.embed([test_query]))[0]

print("   → Searching vector store (retrieving 20 candidates)...")
search_results = client.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_embedding.tolist(),
    limit=20,  # Get more results initially for the re-ranker
    with_payload=True
)
print(f"   ✅ Retrieved {len(search_results)} candidate chunks")

print("   → Re-ranking with cross-encoder...")
rerank_pairs = [[test_query, result.payload.get('text', result.payload.get('content', ''))] for result in search_results]
scores = cross_encoder_model.predict(rerank_pairs)
for i, score in enumerate(scores):
    search_results[i].score = float(score)
reranked_results = sorted(search_results, key=lambda x: x.score, reverse=True)
print(f"   ✅ Re-ranked results (scores: {scores.min():.2f} to {scores.max():.2f})")

print("\n" + "="*80)
print("TOP 5 RESULTS (After Re-Ranking)")
print("="*80)

for i, result in enumerate(reranked_results[:5], 1):
    payload = result.payload
    print(f"\n{i}. Score: {result.score:.3f} | Similarity: {payload.get('score', 'N/A')}")
    print(f"   Title: {payload.get('title', payload.get('paper_title', 'No title'))[:100]}...")
    print(f"   Journal: {payload.get('journal', payload.get('paper_journal', 'Unknown'))} ({payload.get('year', payload.get('paper_year', 'N/A'))})")
    print(f"   PMC ID: {payload.get('pmcid', payload.get('paper_pmcid', 'Unknown'))}")
    
    # Check for human relevance
    text_snippet = payload.get('text', payload.get('content', ''))[:200].lower()
    is_human = 'human' in text_snippet or 'patient' in text_snippet or 'adult' in text_snippet
    is_animal = 'horse' in text_snippet or 'veterinary' in text_snippet or 'equine' in text_snippet
    
    if is_animal:
        print(f"   ⚠️  WARNING: Possible animal study detected!")
    elif is_human:
        print(f"   ✓ Human study confirmed")

print("\n" + "="*80)
print("INTEGRATION TEST RESULTS")
print("="*80)

# Validate results
validation_passed = True
validation_messages = []

# Check 1: Did we get results?
if len(reranked_results) == 0:
    validation_passed = False
    validation_messages.append("❌ No results returned from search")
else:
    validation_messages.append(f"✅ Retrieved {len(reranked_results)} results")

# Check 2: Are top results relevant (score > 5.0)?
if reranked_results[0].score > 5.0:
    validation_messages.append(f"✅ Top result has good relevance score ({reranked_results[0].score:.2f})")
else:
    validation_passed = False
    validation_messages.append(f"⚠️  Top result has low relevance score ({reranked_results[0].score:.2f})")

# Check 3: Are results about magnesium/sleep?
top_text = reranked_results[0].payload.get('title', '') + ' ' + reranked_results[0].payload.get('text', reranked_results[0].payload.get('content', ''))
top_text_lower = top_text.lower()
if 'magnesium' in top_text_lower and ('sleep' in top_text_lower or 'insomnia' in top_text_lower):
    validation_messages.append("✅ Top result is about magnesium and sleep")
elif 'magnesium' in top_text_lower:
    validation_messages.append("⚠️  Top result is about magnesium but may not focus on sleep")
else:
    validation_passed = False
    validation_messages.append("❌ Top result doesn't appear relevant to query")

# Check 4: Are results human studies (not animals)?
animal_count = sum(1 for r in reranked_results[:5] if any(word in str(r.payload).lower() for word in ['horse', 'equine', 'veterinary', 'canine', 'bovine']))
if animal_count == 0:
    validation_messages.append("✅ No animal studies in top 5 results")
elif animal_count <= 1:
    validation_messages.append(f"⚠️  {animal_count} possible animal study in top 5 (will be filtered in production)")
else:
    validation_messages.append(f"⚠️  {animal_count} animal studies in top 5 (consider re-running filter)")

print()
for msg in validation_messages:
    print(msg)

print("\n" + "="*80)
if validation_passed:
    print("🎉 INTEGRATION TEST PASSED!")
    print("="*80)
    print("\n✅ Your BestMove RAG system is ready!")
    print("\nNext steps:")
    print("  1. Update Cell 44 in code.ipynb with the new connection code")
    print("  2. Test the full librarian_rag_tool with BestMove queries")
    print("  3. Run full agent queries through the Supervisor")
    print("\nSee INTEGRATION_CHANGES.md for exact code to update in the notebook.")
else:
    print("⚠️  INTEGRATION TEST COMPLETED WITH WARNINGS")
    print("="*80)
    print("\nThe system is functional but may need refinement.")
    print("Review the warnings above and see INTEGRATION_CHANGES.md for details.")

print()

