#!/usr/bin/env python3
"""
Test Claude + BestMove RAG Integration
Quick test to verify Anthropic API key and vector database work together
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

print("="*80)
print("CLAUDE + BESTMOVE RAG - INTEGRATION TEST")
print("="*80)

# Check API key
print("\n📋 Step 1: Checking API Key...")
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    print("❌ ERROR: ANTHROPIC_API_KEY not found in environment!")
    print("   Run: source ~/.bashrc")
    sys.exit(1)
print(f"✅ API Key found: {api_key[:15]}...{api_key[-10:]}")

# Import dependencies
print("\n📦 Step 2: Loading dependencies...")
try:
    from langchain_anthropic import ChatAnthropic
    from fastembed import TextEmbedding
    import qdrant_client
    print("✅ All packages loaded successfully")
except ImportError as e:
    print(f"❌ ERROR: Missing package: {e}")
    print("   Run: pip install langchain-anthropic fastembed qdrant-client")
    sys.exit(1)

# Initialize Claude
print("\n🤖 Step 3: Initializing Claude...")
try:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0,
        max_tokens=1024,
        api_key=api_key
    )
    print("✅ Claude initialized (claude-3-5-sonnet-20241022)")
except Exception as e:
    print(f"❌ ERROR: Failed to initialize Claude: {e}")
    sys.exit(1)

# Test Claude with simple query
print("\n💬 Step 4: Testing Claude...")
try:
    response = llm.invoke("Say 'Hello from Claude!' in exactly 4 words.")
    print(f"✅ Claude response: {response.content}")
except Exception as e:
    print(f"❌ ERROR: Claude API call failed: {e}")
    sys.exit(1)

# Connect to vector database
print("\n🗄️  Step 5: Connecting to Vector Database...")
try:
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = qdrant_client.QdrantClient(path="./bestmove_vector_db")
    COLLECTION_NAME = "bestmove_research"
    
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"✅ Connected to '{COLLECTION_NAME}' with {collection_info.points_count:,} chunks")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to vector database: {e}")
    sys.exit(1)

# Test RAG query
print("\n🔍 Step 6: Testing RAG Query...")
test_query = "What is magnesium good for?"
print(f"   Query: '{test_query}'")

try:
    # Generate embedding
    query_embedding = list(embedding_model.embed([test_query]))[0]
    
    # Search vector store
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=3
    ).points
    
    print(f"✅ Retrieved {len(results)} results from vector store")
    
    # Format context from top results
    context_parts = []
    for i, result in enumerate(results[:3], 1):
        payload = result.payload
        title = payload.get('title', payload.get('paper_title', 'Unknown'))
        text = payload.get('text', payload.get('content', ''))[:500]
        context_parts.append(f"[Source {i}] {title}\n{text}")
    
    context = "\n\n".join(context_parts)
    
    print("\n🤖 Step 7: Asking Claude to synthesize answer...")
    
    # Create prompt for Claude
    prompt = f"""Based on the following research excerpts, answer the question: {test_query}

Research Context:
{context}

Provide a concise answer (2-3 sentences) citing which sources support your answer."""
    
    # Get Claude's response
    response = llm.invoke(prompt)
    answer = response.content
    
    print("\n" + "="*80)
    print("CLAUDE'S ANSWER:")
    print("="*80)
    print(answer)
    print("="*80)
    
except Exception as e:
    print(f"❌ ERROR: RAG query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Success!
print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80)
print("\n🎉 Your BestMove RAG system is working with Claude!")
print("\nNext steps:")
print("  1. Open code.ipynb in Jupyter")
print("  2. Update Cell 6 to use Anthropic instead of OpenAI")
print("  3. Run the full agent pipeline!")
print("\n" + "="*80)

