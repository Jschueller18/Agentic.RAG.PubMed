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
    
    def fill_knowledge_gaps(self, gap_queries: List[str], max_papers_per_gap: int = 5) -> Dict:
        """
        Download papers to fill specific knowledge gaps
        
        Args:
            gap_queries: List of specific research queries from AI reflection
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
        
        for i, query in enumerate(gap_queries, 1):
            print(f"\n📋 Gap {i}/{len(gap_queries)}: {query}")
            print("-" * 80)
            
            # Search PMC
            pmcids = self._search_pmc(query, max_results=max_papers_per_gap * 2)
            stats["papers_found"] += len(pmcids)
            
            # Filter out duplicates
            new_pmcids = [pid for pid in pmcids if pid not in self.downloaded_pmcids]
            duplicates = len(pmcids) - len(new_pmcids)
            stats["papers_skipped_duplicate"] += duplicates
            
            print(f"   Found: {len(pmcids)} papers ({duplicates} duplicates)")
            
            # Download and process new papers
            if new_pmcids:
                downloaded = self._download_and_process(new_pmcids[:max_papers_per_gap], query)
                stats["papers_downloaded"] += downloaded["papers"]
                stats["chunks_added"] += downloaded["chunks"]
            
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
        """Search PMC for papers matching query"""
        try:
            # Add filters for open access and relevance
            search_query = f'{query} AND "open access"[filter]'
            
            # Search
            handle = Entrez.esearch(
                db="pmc",
                term=search_query,
                retmax=max_results,
                sort="relevance"
            )
            results = Entrez.read(handle)
            handle.close()
            
            pmcids = [f"PMC{pid}" if not pid.startswith("PMC") else pid 
                     for pid in results.get("IdList", [])]
            
            return pmcids
            
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return []
    
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
        
        # Metadata
        metadata = {
            "title": parsed_paper.get("title", "Unknown"),
            "journal": parsed_paper.get("journal", "Unknown"),
            "year": parsed_paper.get("year", "Unknown"),
            "pmcid": parsed_paper.get("pmcid", "Unknown"),
            "authors": ", ".join(parsed_paper.get("authors", [])[:3])
        }
        
        # Abstract as first chunk
        if parsed_paper.get("abstract"):
            chunks.append({
                "text": f"Title: {metadata['title']}\n\nAbstract: {parsed_paper['abstract']}",
                "metadata": {**metadata, "section": "Abstract"}
            })
        
        # Sections
        for section in parsed_paper.get("sections", []):
            title = section.get("title", "")
            content = section.get("content", "")
            
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

