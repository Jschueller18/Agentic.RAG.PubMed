#!/usr/bin/env python3
"""
Update Cell 44 in code.ipynb to connect to BestMove vector database
"""

import json
import sys

NOTEBOOK_PATH = "code.ipynb"

print("Reading notebook...")
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"Found {len(notebook['cells'])} cells")

# Find the cell with id "index-qdrant-setup"
target_cell_idx = None
for i, cell in enumerate(notebook['cells']):
    if cell.get('id') == 'index-qdrant-setup':
        target_cell_idx = i
        print(f"Found target cell at index {i}")
        break

if target_cell_idx is None:
    print("ERROR: Could not find cell with id 'index-qdrant-setup'")
    sys.exit(1)

# Update the cell source
old_source = notebook['cells'][target_cell_idx]['source']
print(f"\nOld cell has {len(old_source)} lines")

new_source = [
    "# Initialize the embedding model\n",
    "# BAAI/bge-small-en-v1.5 is a great, performant open-source model\n",
    "embedding_model = TextEmbedding(model_name=\"BAAI/bge-small-en-v1.5\")\n",
    "\n",
    "# Set up the Qdrant client\n",
    "# Connect to BestMove vector database (203,174 chunks from 5,366 papers)\n",
    "client = qdrant_client.QdrantClient(path=\"./bestmove_vector_db\")\n",
    "COLLECTION_NAME = \"bestmove_research\"\n",
    "\n",
    "# Collection already exists - no need to recreate!\n",
    "collection_info = client.get_collection(collection_name=COLLECTION_NAME)\n",
    "print(f\"✅ Connected to Qdrant collection '{COLLECTION_NAME}' with {collection_info.points_count:,} chunks.\")\n",
    "print(f\"📊 Vector dimension: {collection_info.config.params.vectors.size}\")\n",
    "print(f\"🔍 Ready for BestMove electrolyte research queries!\")"
]

notebook['cells'][target_cell_idx]['source'] = new_source

# Clear the output since it will be outdated
notebook['cells'][target_cell_idx]['outputs'] = []
notebook['cells'][target_cell_idx]['execution_count'] = None

print(f"New cell has {len(new_source)} lines")
print("\nWriting updated notebook...")

with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print("✅ Notebook updated successfully!")
print("\nChanges made:")
print("  • Updated client from ':memory:' to './bestmove_vector_db'")
print("  • Changed COLLECTION_NAME from 'financial_docs_v3' to 'bestmove_research'")
print("  • Removed client.recreate_collection() (would delete data!)")
print("  • Added connection confirmation with chunk count")
print("\nNext: Open code.ipynb and run Cell 13 to verify the connection!")

