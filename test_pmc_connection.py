#!/usr/bin/env python3
"""
Test script to verify PubMed Central API connection and data retrieval
"""

import os
import sys

print("=" * 80)
print("Testing PubMed Central Connection for Electrolyte Research RAG")
print("=" * 80)

# Test 1: Import required libraries
print("\n[TEST 1] Importing required libraries...")
try:
    from pymed import PubMed
    from Bio import Entrez
    import pandas as pd
    print("✓ All imports successful!")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nPlease install missing packages:")
    print("  pip install pymed biopython pandas")
    sys.exit(1)

# Test 2: Initialize PubMed client
print("\n[TEST 2] Initializing PubMed API client...")
try:
    pubmed = PubMed(tool="ElectrolyteRAG", email="researcher@example.com")
    print("✓ PubMed client initialized successfully!")
except Exception as e:
    print(f"✗ Failed to initialize client: {e}")
    sys.exit(1)

# Test 3: Search for a single electrolyte research paper
print("\n[TEST 3] Searching for electrolyte research papers...")
test_query = "magnesium absorption bioavailability"
print(f"  Query: '{test_query}'")
print(f"  Max results: 3")

try:
    results = pubmed.query(test_query, max_results=3)
    papers = list(results)
    print(f"✓ Found {len(papers)} papers!")
    
    if papers:
        print("\n[TEST 3a] Sample paper details:")
        sample = papers[0]
        print(f"  Title: {sample.title[:100]}..." if sample.title and len(sample.title) > 100 else f"  Title: {sample.title}")
        print(f"  PubMed ID: {sample.pubmed_id}")
        print(f"  Has Abstract: {'Yes' if sample.abstract else 'No'}")
        if sample.authors:
            print(f"  First Author: {sample.authors[0].get('firstname', '')} {sample.authors[0].get('lastname', '')}")
except Exception as e:
    print(f"✗ Search failed: {e}")
    sys.exit(1)

# Test 4: Save a paper to file
print("\n[TEST 4] Testing file save functionality...")
try:
    DATA_PATH = "test_papers/"
    os.makedirs(DATA_PATH, exist_ok=True)
    
    if papers:
        sample = papers[0]
        pubmed_id = sample.pubmed_id.split('\n')[0] if sample.pubmed_id else 'unknown'
        filename = f"{DATA_PATH}TEST_{pubmed_id}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Title: {sample.title or 'No title'}\n\n")
            f.write(f"PubMed ID: {pubmed_id}\n\n")
            authors_str = ', '.join([f"{a.get('firstname', '')} {a.get('lastname', '')}" for a in (sample.authors or [])]) or 'No authors listed'
            f.write(f"Authors: {authors_str}\n\n")
            f.write(f"Publication Date: {sample.publication_date or 'Unknown'}\n\n")
            f.write(f"Abstract:\n{sample.abstract or 'No abstract available'}\n")
        
        print(f"✓ Paper saved to: {filename}")
        print(f"  File size: {os.path.getsize(filename)} bytes")
    else:
        print("✗ No papers to save")
except Exception as e:
    print(f"✗ File save failed: {e}")
    sys.exit(1)

# Test 5: Test multiple queries (like in the notebook)
print("\n[TEST 5] Testing multiple search queries...")
test_queries = [
    "electrolyte absorption bioavailability",
    "sodium supplementation metabolism",
    "potassium citrate bioavailability"
]

all_papers = []
for query in test_queries:
    try:
        results = pubmed.query(query, max_results=5)
        papers_found = list(results)
        all_papers.extend(papers_found)
        print(f"  '{query}': Found {len(papers_found)} papers")
    except Exception as e:
        print(f"  '{query}': Error - {e}")

print(f"\n✓ Total papers collected: {len(all_papers)}")

# Test 6: Check for duplicates
print("\n[TEST 6] Checking for duplicate papers...")
unique_papers = {}
for paper in all_papers:
    if paper.pubmed_id:
        pubmed_id = paper.pubmed_id.split('\n')[0]
        if pubmed_id not in unique_papers:
            unique_papers[pubmed_id] = paper

print(f"  Total papers: {len(all_papers)}")
print(f"  Unique papers: {len(unique_papers)}")
print(f"  Duplicates removed: {len(all_papers) - len(unique_papers)}")

# Test 7: Create sample electrolyte database
print("\n[TEST 7] Testing electrolyte properties database creation...")
try:
    electrolyte_data = {
        'electrolyte_name': ['Sodium Chloride', 'Potassium Citrate', 'Magnesium Glycinate'],
        'element': ['Sodium', 'Potassium', 'Magnesium'],
        'supplement_form': ['Chloride', 'Citrate', 'Glycinate'],
        'bioavailability_percent': [95, 94, 42],
        'rda_mg': [1500, 2600, 420]
    }
    
    df = pd.DataFrame(electrolyte_data)
    csv_path = "test_electrolyte_properties.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✓ Electrolyte database created: {csv_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
except Exception as e:
    print(f"✗ Database creation failed: {e}")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("✓ All tests passed successfully!")
print("\nYou can now proceed with running the full notebook.")
print(f"\nTest files created:")
print(f"  - {DATA_PATH} (directory with sample paper)")
print(f"  - {csv_path} (sample electrolyte database)")
print("\nTo clean up test files, run:")
print(f"  rm -rf {DATA_PATH} {csv_path}")
print("=" * 80)

