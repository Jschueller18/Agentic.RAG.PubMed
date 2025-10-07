#!/usr/bin/env python3
"""
PMC Corpus Processing Pipeline - BestMove Electrolyte Research
Filters, parses, and chunks 27,212 research papers for RAG system

Pipeline:
1. Parse XML → Extract title + abstract
2. Apply relevance filter (keyword-based)
3. For relevant papers → Full parse + structure-aware chunking
4. Save chunks ready for vector embedding

Estimated runtime: 2-3 hours for 27,212 papers
Expected output: ~5,000-8,000 relevant papers
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import os
import json
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# Import unstructured for chunking
from unstructured.documents.elements import (
    Element, Title, NarrativeText, Table, Text
)
from unstructured.chunking.title import chunk_by_title


# ============================================================
# RELEVANCE FILTER
# ============================================================

def is_relevant_to_bestmove(title: str, abstract: str, strict: bool = False) -> tuple[bool, str]:
    """
    Keyword-based relevance filter for BestMove electrolyte research.
    
    Returns:
        (is_relevant: bool, reason: str)
    """
    text = (title + " " + abstract).lower()
    
    # MUST have at least one target mineral
    target_minerals = ['magnesium', 'calcium', 'potassium', 'sodium', 'electrolyte', 'mineral']
    has_mineral = any(m in text for m in target_minerals)
    
    if not has_mineral:
        return False, "No target minerals mentioned"
    
    # MUST have human/clinical context
    human_indicators = [
        'human', 'adult', 'patient', 'participant', 'subject', 'volunteer',
        'men', 'women', 'male', 'female', 'elderly', 'athlete',
        'supplement', 'supplementation', 'intake', 'diet', 'dietary',
        'deficiency', 'serum', 'plasma', 'blood', 'urine',
        'bioavailability', 'absorption', 'dose', 'dosage',
        'clinical trial', 'randomized', 'placebo', 'rct'
    ]
    has_human_context = any(h in text for h in human_indicators)
    
    # EXCLUDE plant/animal/environmental studies
    exclusion_keywords = [
        'soil', 'crop', 'plant growth', 'agricultural', 'agriculture',
        'livestock', 'poultry', 'swine', 'cattle', 'pig', 'chicken',
        'amaranth', 'wheat', 'rice', 'corn', 'maize', 'soybean',
        'fertilizer', 'irrigation', 'cultivation',
        'in vitro', 'cell culture', 'tissue culture',
        'nanoparticle', 'nanotechnology', 'biosynthesis',
        'veterinary', 'equine', 'horse', 'horses', 'canine', 'dog', 
        'feline', 'cat', 'animal model', 'rat', 'mice', 'mouse'
    ]
    is_excluded = any(e in text for e in exclusion_keywords)
    
    # Strong indicators (bonus points for highly relevant papers)
    strong_indicators = [
        'bioavailability', 'absorption', 'dose-response', 'dose response',
        'clinical trial', 'randomized controlled', 'rct', 'double-blind',
        'supplementation', 'deficiency', 'serum level', 'plasma level',
        'sleep quality', 'insomnia', 'exercise performance', 'athletic',
        'menstrual', 'premenstrual', 'pms', 'dysmenorrhea',
        'hypomagnesemia', 'hypocalcemia', 'hypokalemia', 'hyponatremia'
    ]
    has_strong_indicator = any(s in text for s in strong_indicators)
    
    # Decision logic
    if is_excluded:
        return False, "Excluded topic (plant/animal/environmental)"
    
    if strict:
        # Strict mode: require human context AND strong indicator
        if has_human_context and has_strong_indicator:
            return True, "Highly relevant (human + strong indicator)"
        else:
            return False, "Not strict enough (missing human context or strong indicator)"
    else:
        # Permissive mode: just require human context OR strong indicator
        if has_human_context or has_strong_indicator:
            reason = []
            if has_human_context:
                reason.append("human context")
            if has_strong_indicator:
                reason.append("strong indicator")
            return True, f"Relevant ({', '.join(reason)})"
        else:
            return False, "No human context or strong indicators"


# ============================================================
# QUICK METADATA EXTRACTION (for filtering)
# ============================================================

def extract_quick_metadata(xml_path: str) -> Dict[str, str]:
    """
    Quickly extract just title and abstract for filtering.
    Much faster than full parse.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Title
        title_elem = root.find('.//article-title')
        title = ''.join(title_elem.itertext()).strip() if title_elem is not None else ""
        
        # Abstract
        abstract_elem = root.find('.//abstract')
        abstract = ''.join(abstract_elem.itertext()).strip() if abstract_elem is not None else ""
        
        # PMC ID
        pmc_id = root.find('.//article-id[@pub-id-type="pmc"]')
        if pmc_id is not None and pmc_id.text:
            pmcid = f"PMC{pmc_id.text}"
        else:
            filename = os.path.basename(xml_path)
            pmcid = filename.replace('PMC_', 'PMC').replace('.xml', '')
        
        return {
            'pmcid': pmcid,
            'title': title,
            'abstract': abstract
        }
    except Exception as e:
        return {
            'pmcid': 'unknown',
            'title': '',
            'abstract': '',
            'error': str(e)
        }


# ============================================================
# FULL PARSE (for relevant papers only)
# ============================================================

def parse_full_paper(xml_path: str) -> Optional[Dict[str, Any]]:
    """
    Full parse of JATS XML - only called for relevant papers.
    Returns structured sections ready for chunking.
    """
    try:
        from test_jats_xml_parser import parse_jats_xml
        return parse_jats_xml(xml_path)
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None


# ============================================================
# CONVERT TO UNSTRUCTURED ELEMENTS
# ============================================================

def convert_to_unstructured_elements(parsed: Dict[str, Any]) -> List[Element]:
    """
    Convert parsed sections to unstructured Element objects.
    This allows us to use chunk_by_title for intelligent chunking.
    """
    from unstructured.documents.elements import ElementMetadata
    
    elements = []
    
    # Add title as Title element
    if parsed['metadata'].get('title'):
        title_meta = ElementMetadata(filename=parsed['metadata'].get('pmcid', 'unknown'))
        elements.append(Title(text=parsed['metadata']['title'], metadata=title_meta))
    
    # Add each section
    for i, section in enumerate(parsed['sections']):
        section_meta = ElementMetadata(
            filename=parsed['metadata'].get('pmcid', 'unknown'),
            page_number=i+1
        )
        
        # Section heading as Title
        elements.append(Title(text=section.title, metadata=section_meta))
        
        # Section content as NarrativeText
        elements.append(NarrativeText(text=section.content, metadata=section_meta))
    
    # Add tables as Table elements
    for i, table in enumerate(parsed['tables']):
        table_text = f"{table['label']}: {table['caption']}\n\n"
        if table['html']:
            table_text += table['html']
        
        table_meta = ElementMetadata(
            filename=parsed['metadata'].get('pmcid', 'unknown'),
            text_as_html=table['html']
        )
        
        elements.append(Table(text=table_text, metadata=table_meta))
    
    return elements


# ============================================================
# CHUNK WITH STRUCTURE-AWARENESS
# ============================================================

def chunk_paper(elements: List[Element], max_chunk_size: int = 2048) -> List[Dict[str, Any]]:
    """
    Apply chunk_by_title strategy to preserve structure.
    Tables are kept atomic (not split).
    """
    try:
        chunks = chunk_by_title(
            elements,
            max_characters=max_chunk_size,
            combine_text_under_n_chars=256,
            new_after_n_chars=int(max_chunk_size * 0.9)
        )
        
        # Convert chunks to simple dicts for JSON serialization
        chunk_dicts = []
        for chunk in chunks:
            chunk_dict = {
                'text': chunk.text,
                'metadata': chunk.metadata.to_dict() if hasattr(chunk.metadata, 'to_dict') else {}
            }
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts
    except Exception as e:
        print(f"Error chunking: {e}")
        return []


# ============================================================
# MAIN PROCESSING PIPELINE
# ============================================================

def process_corpus(
    xml_dir: str = "pmc_open_access_papers/xml_files",
    output_dir: str = "processed_corpus",
    strict_mode: bool = False,
    sample_size: Optional[int] = None
):
    """
    Main processing pipeline:
    1. Filter for relevance
    2. Parse relevant papers
    3. Chunk intelligently
    4. Save results
    """
    
    # Setup
    xml_dir = Path(xml_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)
    
    # Get all XML files
    xml_files = sorted(xml_dir.glob("*.xml"))
    if sample_size:
        xml_files = xml_files[:sample_size]
    
    print(f"\n{'='*80}")
    print(f"PMC CORPUS PROCESSING PIPELINE - BestMove Electrolyte Research")
    print(f"{'='*80}")
    print(f"Total papers to process: {len(xml_files):,}")
    print(f"Relevance filter: {'STRICT' if strict_mode else 'PERMISSIVE'}")
    print(f"Output directory: {output_dir}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Statistics
    stats = {
        'total_papers': len(xml_files),
        'relevant_papers': 0,
        'filtered_out': 0,
        'parsing_errors': 0,
        'total_chunks': 0,
        'filter_reasons': {},
        'started_at': datetime.now().isoformat()
    }
    
    # Metadata for all papers
    all_metadata = []
    
    # Phase 1: Filter for relevance
    print("PHASE 1: Filtering for relevance...")
    relevant_files = []
    
    for xml_file in tqdm(xml_files, desc="Filtering"):
        quick_meta = extract_quick_metadata(str(xml_file))
        
        is_relevant, reason = is_relevant_to_bestmove(
            quick_meta['title'],
            quick_meta['abstract'],
            strict=strict_mode
        )
        
        # Track filter reasons
        stats['filter_reasons'][reason] = stats['filter_reasons'].get(reason, 0) + 1
        
        # Save metadata
        metadata_entry = {
            'pmcid': quick_meta['pmcid'],
            'title': quick_meta['title'],
            'relevant': is_relevant,
            'filter_reason': reason,
            'file': xml_file.name
        }
        all_metadata.append(metadata_entry)
        
        if is_relevant:
            relevant_files.append(xml_file)
            stats['relevant_papers'] += 1
        else:
            stats['filtered_out'] += 1
    
    print(f"\n✅ Filtering complete!")
    print(f"   Relevant papers: {stats['relevant_papers']:,} ({stats['relevant_papers']/len(xml_files)*100:.1f}%)")
    print(f"   Filtered out: {stats['filtered_out']:,}")
    print(f"\nTop filter reasons:")
    for reason, count in sorted(stats['filter_reasons'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   - {reason}: {count:,}")
    
    # Phase 2: Parse and chunk relevant papers
    print(f"\nPHASE 2: Parsing and chunking {len(relevant_files):,} relevant papers...")
    
    processed_papers = []
    
    for xml_file in tqdm(relevant_files, desc="Processing"):
        try:
            # Full parse
            parsed = parse_full_paper(str(xml_file))
            if not parsed:
                stats['parsing_errors'] += 1
                continue
            
            # Convert to unstructured Elements
            elements = convert_to_unstructured_elements(parsed)
            
            # Chunk
            chunks = chunk_paper(elements)
            
            # Save paper info
            paper_info = {
                'pmcid': parsed['metadata'].get('pmcid', 'unknown'),
                'title': parsed['metadata'].get('title', ''),
                'authors': parsed['metadata'].get('authors', []),
                'journal': parsed['metadata'].get('journal', ''),
                'year': parsed['metadata'].get('year', ''),
                'num_chunks': len(chunks),
                'statistics': parsed['statistics']
            }
            processed_papers.append(paper_info)
            
            # Save chunks for this paper
            chunks_file = chunks_dir / f"{paper_info['pmcid']}_chunks.json"
            with open(chunks_file, 'w') as f:
                json.dump({
                    'paper': paper_info,
                    'chunks': chunks
                }, f, indent=2)
            
            stats['total_chunks'] += len(chunks)
            
        except Exception as e:
            print(f"\nError processing {xml_file.name}: {e}")
            stats['parsing_errors'] += 1
    
    # Save final statistics and metadata
    stats['completed_at'] = datetime.now().isoformat()
    stats['processed_papers'] = len(processed_papers)
    
    with open(output_dir / "processing_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    with open(output_dir / "all_papers_metadata.json", 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    with open(output_dir / "processed_papers_metadata.json", 'w') as f:
        json.dump(processed_papers, f, indent=2)
    
    # Final report
    print(f"\n{'='*80}")
    print(f"PROCESSING COMPLETE!")
    print(f"{'='*80}")
    print(f"Total papers processed: {len(xml_files):,}")
    print(f"Relevant papers found: {stats['relevant_papers']:,}")
    print(f"Successfully processed: {len(processed_papers):,}")
    print(f"Parsing errors: {stats['parsing_errors']}")
    print(f"Total chunks created: {stats['total_chunks']:,}")
    print(f"Average chunks per paper: {stats['total_chunks']/len(processed_papers):.1f}")
    print(f"\nOutput saved to: {output_dir}/")
    print(f"  - chunks/ (individual paper chunks)")
    print(f"  - processing_stats.json (statistics)")
    print(f"  - all_papers_metadata.json (all papers with filter results)")
    print(f"  - processed_papers_metadata.json (processed papers only)")
    print(f"{'='*80}\n")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process PMC corpus for BestMove RAG system")
    parser.add_argument('--strict', action='store_true', help='Use strict filtering (more restrictive)')
    parser.add_argument('--sample', type=int, help='Process only N papers (for testing)')
    
    args = parser.parse_args()
    
    process_corpus(
        strict_mode=args.strict,
        sample_size=args.sample
    )

