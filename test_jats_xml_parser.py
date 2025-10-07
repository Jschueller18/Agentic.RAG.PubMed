#!/usr/bin/env python3
"""
JATS XML Parser Test - BestMove Electrolyte Research
Tests parsing of PMC Open Access papers into structured format
Compatible with unstructured library's chunk_by_title workflow
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import os
from pathlib import Path

# These will be converted to unstructured Elements later
class ParsedSection:
    def __init__(self, section_type: str, title: str, content: str, metadata: dict = None):
        self.section_type = section_type  # 'title', 'abstract', 'methods', 'results', etc.
        self.title = title
        self.content = content
        self.metadata = metadata or {}
    
    def __repr__(self):
        return f"<{self.section_type}: {self.title[:50]}...>"


def parse_jats_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parse JATS XML file and extract structured sections.
    
    Returns:
        dict with:
            - metadata: title, authors, journal, year
            - sections: list of ParsedSection objects
            - tables: list of table data
            - statistics: parsing stats
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    result = {
        'metadata': {},
        'sections': [],
        'tables': [],
        'statistics': {}
    }
    
    # ============================================================
    # METADATA EXTRACTION
    # ============================================================
    
    # Title
    title_elem = root.find('.//article-title')
    if title_elem is not None:
        result['metadata']['title'] = ''.join(title_elem.itertext()).strip()
    
    # Authors
    authors = []
    for contrib in root.findall('.//contrib[@contrib-type="author"]')[:10]:  # Limit to first 10
        given = contrib.find('.//given-names')
        surname = contrib.find('.//surname')
        if given is not None and surname is not None:
            authors.append(f"{given.text} {surname.text}")
    result['metadata']['authors'] = authors
    
    # Journal
    journal = root.find('.//journal-title')
    if journal is not None:
        result['metadata']['journal'] = journal.text
    
    # Year
    year = root.find('.//pub-date[@pub-type="epub"]/year')
    if year is None:
        year = root.find('.//pub-date/year')
    if year is not None:
        result['metadata']['year'] = year.text
    
    # PMC ID - try multiple sources
    pmc_id = root.find('.//article-id[@pub-id-type="pmc"]')
    if pmc_id is not None and pmc_id.text:
        result['metadata']['pmcid'] = f"PMC{pmc_id.text}"
    else:
        # Try to extract from filename if not in XML
        import os
        filename = os.path.basename(xml_path)
        if filename.startswith('PMC_'):
            result['metadata']['pmcid'] = filename.replace('PMC_', 'PMC').replace('.xml', '')
    
    # ============================================================
    # ABSTRACT EXTRACTION
    # ============================================================
    
    abstract_elem = root.find('.//abstract')
    if abstract_elem is not None:
        abstract_text = ''.join(abstract_elem.itertext()).strip()
        # Remove "Abstract" heading if it's redundant
        abstract_text = abstract_text.replace('Abstract', '', 1).strip()
        result['sections'].append(
            ParsedSection('abstract', 'Abstract', abstract_text)
        )
    
    # ============================================================
    # BODY SECTIONS EXTRACTION (Methods, Results, Discussion, etc.)
    # ============================================================
    
    body = root.find('.//body')
    if body is not None:
        for sec in body.findall('.//sec'):
            # Get section title
            title_elem = sec.find('./title')
            section_title = title_elem.text if title_elem is not None else "Untitled Section"
            
            # Get all text content (excluding nested sections)
            paragraphs = []
            for p in sec.findall('./p'):
                p_text = ''.join(p.itertext()).strip()
                if p_text:
                    paragraphs.append(p_text)
            
            section_content = '\n\n'.join(paragraphs)
            
            if section_content:
                # Classify section type (improved detection)
                title_lower = section_title.lower()
                content_lower = section_content[:500].lower()  # Check first 500 chars
                
                if 'method' in title_lower or 'material' in title_lower or 'procedure' in title_lower:
                    section_type = 'methods'
                elif 'result' in title_lower or 'finding' in title_lower:
                    section_type = 'results'
                elif 'discussion' in title_lower:
                    section_type = 'discussion'
                elif 'introduction' in title_lower or 'background' in title_lower:
                    section_type = 'introduction'
                elif 'conclusion' in title_lower or 'summary' in title_lower:
                    section_type = 'conclusion'
                # Detect Results from content patterns
                elif any(pattern in content_lower for pattern in ['table 1', 'table 2', 'figure 1', 'as shown in', 'p <', 'p=']):
                    section_type = 'results'
                # Detect Methods from content patterns
                elif any(pattern in content_lower for pattern in ['participants', 'samples were', 'conducted', 'measured', 'analyzed using']):
                    section_type = 'methods'
                else:
                    section_type = 'body'
                
                result['sections'].append(
                    ParsedSection(section_type, section_title, section_content)
                )
    
    # ============================================================
    # TABLE EXTRACTION
    # ============================================================
    
    for table_wrap in root.findall('.//table-wrap'):
        table_data = {
            'id': table_wrap.get('id', 'unknown'),
            'label': None,
            'caption': None,
            'html': None
        }
        
        # Table label (e.g., "Table 1")
        label = table_wrap.find('.//label')
        if label is not None:
            table_data['label'] = label.text
        
        # Table caption
        caption = table_wrap.find('.//caption')
        if caption is not None:
            table_data['caption'] = ''.join(caption.itertext()).strip()
        
        # Table HTML (for rendering)
        table_elem = table_wrap.find('.//table')
        if table_elem is not None:
            # Convert XML table to simple representation
            table_data['html'] = ET.tostring(table_elem, encoding='unicode', method='html')
        
        result['tables'].append(table_data)
    
    # ============================================================
    # STATISTICS
    # ============================================================
    
    result['statistics'] = {
        'total_sections': len(result['sections']),
        'total_tables': len(result['tables']),
        'has_methods': any(s.section_type == 'methods' for s in result['sections']),
        'has_results': any(s.section_type == 'results' for s in result['sections']),
        'total_text_length': sum(len(s.content) for s in result['sections'])
    }
    
    return result


def print_parsed_summary(parsed: Dict[str, Any]):
    """Print a human-readable summary of parsed paper."""
    print("=" * 80)
    print("PARSED PAPER SUMMARY")
    print("=" * 80)
    
    # Metadata
    meta = parsed['metadata']
    print(f"\n📄 TITLE: {meta.get('title', 'N/A')}")
    print(f"👥 AUTHORS: {', '.join(meta.get('authors', [])[:3])}")
    if len(meta.get('authors', [])) > 3:
        print(f"            ... and {len(meta['authors'])-3} more")
    print(f"📚 JOURNAL: {meta.get('journal', 'N/A')}")
    print(f"📅 YEAR: {meta.get('year', 'N/A')}")
    print(f"🆔 PMC ID: {meta.get('pmcid', 'N/A')}")
    
    # Sections
    print(f"\n📝 SECTIONS FOUND: {parsed['statistics']['total_sections']}")
    for section in parsed['sections']:
        preview = section.content[:100].replace('\n', ' ')
        print(f"  • {section.section_type.upper()}: {section.title}")
        print(f"    Preview: {preview}...")
        print(f"    Length: {len(section.content)} characters\n")
    
    # Tables
    print(f"📊 TABLES FOUND: {parsed['statistics']['total_tables']}")
    for table in parsed['tables']:
        print(f"  • {table['label']}: {table['caption'][:100] if table['caption'] else 'No caption'}...")
    
    # Statistics
    stats = parsed['statistics']
    print(f"\n✅ QUALITY CHECKS:")
    print(f"  • Has Methods section: {'✓' if stats['has_methods'] else '✗'}")
    print(f"  • Has Results section: {'✓' if stats['has_results'] else '✗'}")
    print(f"  • Total text extracted: {stats['total_text_length']:,} characters")
    print(f"  • Tables preserved: {stats['total_tables']}")
    
    print("=" * 80)


def test_sample_papers(num_samples=3, random_sample=False):
    """Test parser on sample papers from the corpus."""
    xml_dir = Path("pmc_open_access_papers/xml_files")
    
    if not xml_dir.exists():
        print(f"❌ Error: Directory {xml_dir} not found!")
        return
    
    # Get sample XML files
    all_files = list(xml_dir.glob("*.xml"))
    
    if random_sample:
        import random
        random.seed(42)
        xml_files = random.sample(all_files, min(num_samples, len(all_files)))
    else:
        xml_files = sorted(all_files)[:num_samples]
    
    if not xml_files:
        print(f"❌ Error: No XML files found in {xml_dir}")
        return
    
    print(f"\n🧪 TESTING JATS XML PARSER ON {len(xml_files)} SAMPLE PAPERS\n")
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*80}")
        print(f"SAMPLE {i}/{len(xml_files)}: {xml_file.name}")
        print(f"{'='*80}")
        
        try:
            parsed = parse_jats_xml(str(xml_file))
            print_parsed_summary(parsed)
            
            # Check if this paper is relevant to BestMove
            title = parsed['metadata'].get('title', '').lower()
            abstract_text = ''
            for section in parsed['sections']:
                if section.section_type == 'abstract':
                    abstract_text = section.content.lower()
                    break
            
            relevance_keywords = [
                'magnesium', 'calcium', 'potassium', 'sodium',
                'electrolyte', 'mineral', 'supplementation',
                'bioavailability', 'absorption', 'dose'
            ]
            
            found_keywords = [kw for kw in relevance_keywords if kw in title or kw in abstract_text]
            if found_keywords:
                print(f"\n🎯 RELEVANCE: Found keywords: {', '.join(found_keywords)}")
            
        except Exception as e:
            print(f"❌ ERROR parsing {xml_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ PARSER TEST COMPLETE!")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review the extracted sections - do they look complete?")
    print("2. Check if tables are preserved (not split)")
    print("3. Verify Methods and Results sections are captured")
    print("4. If quality looks good, we'll convert to unstructured Elements")
    print("5. Then integrate with the existing chunk_by_title pipeline")


if __name__ == "__main__":
    # Test with random sampling for better coverage of the corpus
    test_sample_papers(num_samples=5, random_sample=True)

