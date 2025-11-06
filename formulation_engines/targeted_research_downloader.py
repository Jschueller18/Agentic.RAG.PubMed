"""
Targeted Research Downloader
Automatically fills knowledge gaps by downloading specific papers from PMC

Features:
- Targeted search queries from AI reflection
- Duplicate detection using PMCID tracking
- Incremental vector store updates
- Automatic processing and chunking
"""

import os
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Set
from Bio import Entrez
import sys

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

# Import the parsing function from process_pmc_corpus
import importlib.util
spec = importlib.util.spec_from_file_location("process_pmc_corpus", f"{parent_dir}/process_pmc_corpus.py")
if spec and spec.loader:
    pmc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pmc_module)
    parse_full_paper = pmc_module.parse_full_paper
else:
    raise ImportError("Could not load process_pmc_corpus module")
from fastembed import TextEmbedding
import qdrant_client
from qdrant_client.models import PointStruct, Distance, VectorParams


class TargetedResearchDownloader:
    """
    Downloads specific research papers to fill knowledge gaps
    
    Maintains a database of downloaded PMCIDs to avoid duplicates
    """
    
    def __init__(self,
                 download_dir: str = "./pmc_targeted_papers",
                 pmcid_tracker_file: str = "./downloaded_pmcids.json",
                 vector_db_path: str = "./bestmove_vector_db",
                 collection_name: str = "bestmove_research",
                 qdrant_client=None):
        """Initialize downloader"""

        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

        self.pmcid_tracker_file = Path(pmcid_tracker_file)
        self.vector_db_path = vector_db_path
        self.collection_name = collection_name

        # Load existing PMCIDs
        self.downloaded_pmcids = self._load_pmcid_tracker()

        # Setup NCBI
        Entrez.email = "bestmove.research@example.com"
        api_key = os.environ.get("NCBI_API_KEY")
        if api_key:
            Entrez.api_key = api_key

        # Setup vector store
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        if qdrant_client is not None:
            self.qdrant_client = qdrant_client
        else:
            import qdrant_client
            self.qdrant_client = qdrant_client.QdrantClient(path=vector_db_path)
        
        print(f"📚 Targeted Research Downloader initialized")
        print(f"   Already downloaded: {len(self.downloaded_pmcids)} papers")
    
    def _load_pmcid_tracker(self) -> Set[str]:
        """Load set of already downloaded PMCIDs"""
        if self.pmcid_tracker_file.exists():
            with open(self.pmcid_tracker_file, 'r') as f:
                data = json.load(f)
                return set(data.get("pmcids", []))
        return set()
    
    def _save_pmcid_tracker(self):
        """Save updated PMCID set"""
        with open(self.pmcid_tracker_file, 'w') as f:
            json.dump({
                "pmcids": list(self.downloaded_pmcids),
                "count": len(self.downloaded_pmcids),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    
    def fill_knowledge_gaps(self, 
                           semantic_queries: List[str] = None, 
                           pmc_queries: List[str] = None,
                           max_papers_per_gap: int = 5) -> Dict:
        """
        Download papers to fill specific knowledge gaps using separate query types
        
        Args:
            semantic_queries: Specific queries for vector database search
            pmc_queries: Broad queries for external PMC search (pre-optimized)
            max_papers_per_gap: Max new papers to download per query
            
        Returns:
            Dict with download statistics
        """
        print("\n" + "="*80)
        print("FILLING KNOWLEDGE GAPS")
        print("="*80)
        
        stats = {
            "queries_processed": 0,
            "papers_found": 0,
            "papers_downloaded": 0,
            "papers_skipped_duplicate": 0,
            "chunks_added": 0
        }
        
        # Handle backward compatibility (single query list)
        if semantic_queries is None and pmc_queries is None:
            print("   ⚠️  No queries provided")
            return stats
        
        # If only one type provided, use it for both
        if semantic_queries is None:
            semantic_queries = pmc_queries
        if pmc_queries is None:
            pmc_queries = semantic_queries
        
        # Process each gap (match semantic and PMC queries by index)
        num_gaps = max(len(semantic_queries), len(pmc_queries))
        
        for i in range(num_gaps):
            semantic_query = semantic_queries[i] if i < len(semantic_queries) else semantic_queries[0]
            pmc_query = pmc_queries[i] if i < len(pmc_queries) else pmc_queries[0]
            
            print(f"\n📋 Gap {i+1}/{num_gaps}")
            print(f"   🔍 Semantic: {semantic_query[:60]}...")
            print(f"   🌐 PMC: {pmc_query[:60]}...")
            print("-" * 80)
            
            # Use hybrid search with separate queries
            hybrid_results = self.search_hybrid(
                semantic_query=semantic_query,
                pmc_query=pmc_query,
                pmc_max_results=max_papers_per_gap, 
                semantic_max_results=max_papers_per_gap
            )

            # PMC papers (external)
            pmc_papers = hybrid_results['pmc_papers']
            all_pmc_count = len(pmc_papers)

            # Semantic papers (from existing database)
            semantic_papers = hybrid_results['semantic_papers']
            semantic_count = len(semantic_papers)

            # Filter PMC papers for duplicates and limit to max_papers_per_gap
            new_pmcids = [pid for pid in pmc_papers if pid not in self.downloaded_pmcids][:max_papers_per_gap]
            duplicates = all_pmc_count - len(new_pmcids)
            processed_pmc_count = len(new_pmcids)

            # Update stats
            stats["papers_found"] += all_pmc_count + semantic_count
            stats["papers_skipped_duplicate"] += duplicates

            print(f"   📊 Found: {all_pmc_count} external + {semantic_count} database papers")
            print(f"   📥 Processing: {processed_pmc_count} new external papers ({duplicates} duplicates skipped)")

            # Download and process new PMC papers only
            if new_pmcids:
                downloaded = self._download_and_process(new_pmcids, semantic_query)
                stats["papers_downloaded"] += downloaded["papers"]
                stats["chunks_added"] += downloaded["chunks"]

            # For semantic papers, they're already in our database, so just mark them as "found"
            if semantic_papers:
                print(f"   ✅ {semantic_count} relevant papers already in database")
            
            stats["queries_processed"] += 1
            
            # Rate limiting
            time.sleep(0.4)
        
        # Save updated tracker
        self._save_pmcid_tracker()
        
        print("\n" + "="*80)
        print("KNOWLEDGE GAP FILLING COMPLETE")
        print("="*80)
        print(f"Queries Processed: {stats['queries_processed']}")
        print(f"Papers Found: {stats['papers_found']}")
        print(f"New Papers Downloaded: {stats['papers_downloaded']}")
        print(f"Duplicates Skipped: {stats['papers_skipped_duplicate']}")
        print(f"Chunks Added to Vector Store: {stats['chunks_added']}")
        print("="*80)
        
        return stats
    
    def _search_pmc(self, query: str, max_results: int = 10) -> List[str]:
        """Search PMC for papers using pre-optimized query (no auto-broadening)"""
        try:
            print(f"   🌐 PMC search: {query[:80]}{'...' if len(query) > 80 else ''}")

            # Search with the query as-is (should already be optimized)
            handle = Entrez.esearch(
                db="pmc",
                term=query,
                retmax=max_results * 2,  # Get more results for filtering
                sort="relevance"
            )
            results = Entrez.read(handle)
            handle.close()

            pmcids = [f"PMC{pid}" if not pid.startswith("PMC") else pid
                     for pid in results.get("IdList", [])]

            print(f"   📄 Found {len(pmcids)} external papers")
            return pmcids

        except Exception as e:
            print(f"   ❌ PMC search error: {e}")
            return []

    def search_semantic_database(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search existing vector database for semantically similar papers"""
        try:
            from sentence_transformers import SentenceTransformer

            # Use the same embedding model as the vector store
            embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")

            # Embed the query
            query_embedding = embedder.encode(query).tolist()

            # Search vector database
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k * 2,  # Get more results for filtering
                with_payload=True
            )

            # Filter and format results
            papers = []
            for result in search_results:
                payload = result.payload
                if payload and 'pmcid' in payload:
                    papers.append({
                        'pmc_id': payload['pmcid'],  # Note: database uses 'pmcid', not 'pmc_id'
                        'title': payload.get('title', 'Unknown Title'),
                        'abstract': payload.get('text', '')[:500] + '...' if payload.get('text') else '',  # Use 'text' field as abstract
                        'score': result.score,
                        'source': 'semantic_search'
                    })

            # Remove duplicates and return top results
            seen_pmcids = set()
            unique_papers = []
            for paper in papers:
                if paper['pmc_id'] not in seen_pmcids:
                    seen_pmcids.add(paper['pmc_id'])
                    unique_papers.append(paper)

            return unique_papers[:top_k]

        except Exception as e:
            print(f"   ❌ Semantic search error: {e}")
            return []

    def search_hybrid(self, 
                     semantic_query: str = None, 
                     pmc_query: str = None,
                     pmc_max_results: int = 5, 
                     semantic_max_results: int = 5) -> Dict:
        """Combine PMC search and semantic search using separate optimized queries"""
        results = {
            'pmc_papers': [],
            'semantic_papers': [],
            'total_found': 0
        }

        # PMC search (external papers) - use pre-optimized query
        if pmc_query:
            pmc_papers = self._search_pmc(pmc_query, pmc_max_results * 2)
            if pmc_papers:
                results['pmc_papers'] = pmc_papers

        # Semantic search (existing database) - use specific query
        if semantic_query:
            print(f"   🧠 Database search: {semantic_query[:60]}...")
            semantic_papers = self.search_semantic_database(semantic_query, semantic_max_results)
            if semantic_papers:
                print(f"   📚 Found {len(semantic_papers)} relevant papers in database")
                results['semantic_papers'] = semantic_papers

        results['total_found'] = len(results['pmc_papers']) + len(results['semantic_papers'])
        return results

    def _download_and_process(self, pmcids: List[str], context_query: str) -> Dict:
        """Download XMLs and add to vector store"""
        papers_processed = 0
        total_chunks = 0
        
        for pmcid in pmcids:
            try:
                # Download XML
                xml_path = self.download_dir / f"{pmcid}.xml"
                
                if not xml_path.exists():
                    # Fetch from PMC
                    pmc_id_num = pmcid.replace("PMC", "")
                    handle = Entrez.efetch(
                        db="pmc",
                        id=pmc_id_num,
                        rettype="xml",
                        retmode="xml"
                    )
                    xml_content = handle.read()
                    handle.close()
                    
                    # Save
                    with open(xml_path, 'wb') as f:
                        f.write(xml_content)
                    
                    time.sleep(0.34)  # Rate limiting
                
                # Parse
                parsed = parse_full_paper(str(xml_path))
                
                if not parsed:
                    print(f"   ⚠️  {pmcid}: Parse failed")
                    continue
                
                # Convert to chunks (simple chunking for now)
                chunks = self._create_chunks(parsed)
                
                # Add to vector store
                chunks_added = self._add_to_vector_store(chunks, pmcid, context_query)
                
                # Mark as downloaded
                self.downloaded_pmcids.add(pmcid)
                
                papers_processed += 1
                total_chunks += chunks_added
                
                print(f"   ✅ {pmcid}: {chunks_added} chunks added")
                
            except Exception as e:
                print(f"   ❌ {pmcid}: {e}")
                continue
        
        return {"papers": papers_processed, "chunks": total_chunks}
    
    def _create_chunks(self, parsed_paper: Dict, chunk_size: int = 1000) -> List[Dict]:
        """Create chunks from parsed paper"""
        chunks = []

        # Get metadata from the correct nested structure
        metadata = parsed_paper.get('metadata', {})

        # Abstract as first chunk
        if metadata.get("title"):
            abstract_text = ""
            # Look for abstract in sections
            for section in parsed_paper.get('sections', []):
                if hasattr(section, 'section_type') and section.section_type == 'abstract':
                    abstract_text = section.content
                    break

            if abstract_text:
                chunks.append({
                    "text": f"Title: {metadata.get('title', 'Unknown')}\n\nAbstract: {abstract_text}",
                    "metadata": {**metadata, "section": "Abstract"}
                })

        # Sections
        for section in parsed_paper.get("sections", []):
            title = getattr(section, "title", "")
            content = getattr(section, "content", "")

            if content:
                # Split long sections
                if len(content) > chunk_size:
                    words = content.split()
                    for i in range(0, len(words), chunk_size // 5):  # ~200 words per chunk
                        chunk_text = " ".join(words[i:i + chunk_size // 5])
                        if chunk_text:
                            chunks.append({
                                "text": f"{title}\n\n{chunk_text}",
                                "metadata": {**metadata, "section": title}
                            })
                else:
                    chunks.append({
                        "text": f"{title}\n\n{content}",
                        "metadata": {**metadata, "section": title}
                    })
        
        # Tables
        for table in parsed_paper.get("tables", []):
            chunks.append({
                "text": f"Table: {table.get('caption', 'Data')}\n\n{table.get('content', '')}",
                "metadata": {**metadata, "section": "Table"}
            })
        
        return chunks
    
    def _add_to_vector_store(self, chunks: List[Dict], pmcid: str, context_query: str) -> int:
        """Add chunks to Qdrant vector store"""
        if not chunks:
            return 0
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = list(self.embedding_model.embed(texts))
        
        # Get current max point ID
        collection_info = self.qdrant_client.get_collection(self.collection_name)
        current_count = collection_info.points_count
        
        # Create points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = current_count + i + 1
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        **chunk["metadata"],
                        "text": chunk["text"],
                        "pmcid": pmcid,  # Add PMCID to payload for deduplication
                        "source": "targeted_download",
                        "context_query": context_query  # Track why we downloaded this
                    }
                )
            )
        
        # Upload
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return len(points)


if __name__ == "__main__":
    # Test
    downloader = TargetedResearchDownloader()
    
    test_gaps = [
        "magnesium glycinate sleep onset latency randomized controlled trial",
        "sodium electrolyte balance sleep quality women"
    ]
    
    stats = downloader.fill_knowledge_gaps(test_gaps, max_papers_per_gap=3)
    
    print(f"\n✅ Test complete: {stats['papers_downloaded']} new papers added")

