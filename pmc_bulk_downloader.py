"""
PMC Open Access Bulk Downloader for BestMove Electrolyte Research
Downloads thousands of full-text research articles from PMC Open Access Subset

Legal: All articles are from PMC Open Access Subset - freely downloadable and reusable
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Set
from Bio import Entrez
import xml.etree.ElementTree as ET

# Configuration
OUTPUT_DIR = "pmc_open_access_papers"
XML_DIR = f"{OUTPUT_DIR}/xml_files"
METADATA_FILE = f"{OUTPUT_DIR}/download_metadata.json"
LOG_FILE = f"{OUTPUT_DIR}/download_log.txt"
PROGRESS_FILE = f"{OUTPUT_DIR}/progress.json"

# NCBI Configuration
Entrez.email = "research@bestmove.com"  # Required by NCBI
# TODO: Get free API key from https://ncbi.nlm.nih.gov/account/ to increase rate limits
# Entrez.api_key = "YOUR_API_KEY_HERE"  # Uncomment and add your key

# Rate limiting (be conservative to avoid getting blocked)
REQUEST_DELAY = 0.34  # seconds between requests (conservative without API key)
MAX_RESULTS_PER_QUERY = 10000  # PMC limit
BATCH_SIZE = 100  # Fetch metadata in batches

# Target search queries for BestMove electrolyte research
# Optimized for: bioavailability, dose-response, sleep, exercise, menstrual support
SEARCH_QUERIES = [
    # Core bioavailability & absorption (critical for formulation!)
    'magnesium AND (bioavailability OR absorption) AND (citrate OR glycinate OR oxide OR threonate) AND "open access"[filter]',
    'calcium AND (bioavailability OR absorption) AND (citrate OR carbonate OR lactate) AND "open access"[filter]',
    'potassium AND (bioavailability OR absorption) AND (citrate OR chloride) AND "open access"[filter]',
    
    # Dose-response studies (THE GOLD for algorithms!)
    'magnesium AND (dose response OR dose-response OR dosage) AND (sleep OR insomnia) AND "open access"[filter]',
    'magnesium AND (dose response OR dose-response) AND (supplementation OR intervention) AND "open access"[filter]',
    'calcium AND (dose response OR dose-response) AND supplementation AND "open access"[filter]',
    
    # Sleep quality (Sleep Support Mix use case)
    'magnesium AND sleep AND (randomized controlled trial OR RCT OR clinical trial) AND "open access"[filter]',
    'magnesium threonate AND (sleep OR cognitive) AND "open access"[filter]',
    'magnesium glycinate AND sleep AND "open access"[filter]',
    
    # Exercise & performance (Workout Performance Mix use case)
    'electrolytes AND exercise AND (sweat OR perspiration OR dehydration) AND "open access"[filter]',
    'sodium AND (exercise OR athletic performance OR endurance) AND "open access"[filter]',
    'electrolyte replacement AND athletes AND "open access"[filter]',
    'potassium AND exercise AND supplementation AND "open access"[filter]',
    
    # Menstrual support (Menstrual Support Mix use case)
    'magnesium AND (menstrual OR menstruation OR dysmenorrhea OR PMS) AND "open access"[filter]',
    'calcium AND magnesium AND (menstrual OR premenstrual) AND "open access"[filter]',
    'magnesium AND (cramps OR cramping) AND menstrual AND "open access"[filter]',
    
    # Population-specific (age, sex, body composition differences)
    'magnesium AND (age OR elderly OR aging) AND supplementation AND "open access"[filter]',
    'electrolytes AND (sex differences OR gender) AND metabolism AND "open access"[filter]',
    'magnesium AND (body composition OR BMI OR lean mass) AND "open access"[filter]',
    
    # Forms comparison (critical for choosing optimal forms!)
    'magnesium AND (citrate OR oxide OR glycinate OR threonate) AND comparison AND "open access"[filter]',
    'calcium AND (citrate OR carbonate) AND comparison AND "open access"[filter]',
    'magnesium forms AND bioavailability AND "open access"[filter]',
    
    # Timing, interactions, & safety
    'magnesium AND (timing OR chronotherapy OR circadian) AND "open access"[filter]',
    'mineral AND interaction AND (calcium OR magnesium OR zinc) AND "open access"[filter]',
    'magnesium AND safety AND (adverse effects OR side effects OR tolerance) AND "open access"[filter]',
]

# Create directories
os.makedirs(XML_DIR, exist_ok=True)


def log(message: str, also_print: bool = True):
    """Log message to file and optionally print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_message + '\n')
    
    if also_print:
        print(log_message)


def load_progress() -> Dict:
    """Load progress from previous run if exists"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'downloaded_pmcids': [],
        'failed_pmcids': [],
        'queries_completed': [],
        'total_downloaded': 0
    }


def save_progress(progress: Dict):
    """Save progress to allow resuming"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def search_pmc(query: str, retmax: int = MAX_RESULTS_PER_QUERY) -> List[str]:
    """
    Search PMC for articles matching query
    Returns list of PMC IDs
    """
    try:
        log(f"Searching PMC: {query}")
        
        # Search PMC database
        handle = Entrez.esearch(
            db="pmc",
            term=query,
            retmax=retmax,
            sort="relevance"
        )
        
        results = Entrez.read(handle)
        handle.close()
        
        pmc_ids = results['IdList']
        count = results['Count']
        
        log(f"  Found {count} articles, retrieved {len(pmc_ids)} IDs")
        
        time.sleep(REQUEST_DELAY)
        return pmc_ids
        
    except Exception as e:
        log(f"  ERROR in search: {e}")
        return []


def fetch_article_metadata(pmc_ids: List[str]) -> List[Dict]:
    """
    Fetch metadata for articles in batches
    Returns list of article metadata dicts
    """
    articles = []
    
    for i in range(0, len(pmc_ids), BATCH_SIZE):
        batch = pmc_ids[i:i + BATCH_SIZE]
        
        try:
            log(f"  Fetching metadata for {len(batch)} articles (batch {i//BATCH_SIZE + 1})")
            
            # Fetch summaries
            handle = Entrez.esummary(
                db="pmc",
                id=','.join(batch)
            )
            
            summaries = Entrez.read(handle)
            handle.close()
            
            # Extract key metadata
            for doc in summaries:
                if isinstance(doc, dict):
                    articles.append({
                        'pmcid': doc.get('Id', ''),
                        'title': doc.get('Title', 'No title'),
                        'authors': doc.get('AuthorList', []),
                        'journal': doc.get('FullJournalName', ''),
                        'pub_date': doc.get('PubDate', ''),
                        'doi': doc.get('DOI', '')
                    })
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            log(f"  ERROR fetching metadata batch: {e}")
            continue
    
    return articles


def download_full_text_xml(pmcid: str) -> bool:
    """
    Download full-text XML for a single article
    Returns True if successful
    """
    xml_path = f"{XML_DIR}/PMC_{pmcid}.xml"
    
    # Skip if already downloaded
    if os.path.exists(xml_path):
        return True
    
    try:
        # Fetch full-text XML
        handle = Entrez.efetch(
            db="pmc",
            id=pmcid,
            rettype="xml",
            retmode="xml"
        )
        
        xml_content = handle.read()
        handle.close()
        
        # Verify it's valid XML
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8')
        
        # Quick validation
        ET.fromstring(xml_content)
        
        # Save XML file
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        time.sleep(REQUEST_DELAY)
        return True
        
    except Exception as e:
        log(f"  ERROR downloading PMC{pmcid}: {e}", also_print=False)
        return False


def download_articles(articles: List[Dict], progress: Dict) -> int:
    """
    Download full-text XMLs for list of articles
    Returns count of successful downloads
    """
    downloaded_set = set(progress['downloaded_pmcids'])
    failed_set = set(progress['failed_pmcids'])
    
    new_downloads = 0
    
    for i, article in enumerate(articles, 1):
        pmcid = article['pmcid']
        
        # Skip if already processed
        if pmcid in downloaded_set or pmcid in failed_set:
            continue
        
        if i % 10 == 0:
            log(f"  Progress: {i}/{len(articles)} articles processed, {new_downloads} new downloads")
        
        success = download_full_text_xml(pmcid)
        
        if success:
            downloaded_set.add(pmcid)
            new_downloads += 1
            
            # Update progress periodically
            if new_downloads % 50 == 0:
                progress['downloaded_pmcids'] = list(downloaded_set)
                progress['total_downloaded'] = len(downloaded_set)
                save_progress(progress)
        else:
            failed_set.add(pmcid)
    
    # Final progress update
    progress['downloaded_pmcids'] = list(downloaded_set)
    progress['failed_pmcids'] = list(failed_set)
    progress['total_downloaded'] = len(downloaded_set)
    save_progress(progress)
    
    return new_downloads


def main():
    """Main download orchestration"""
    
    log("="*80)
    log("PMC OPEN ACCESS BULK DOWNLOADER - BestMove Electrolyte Research")
    log("="*80)
    
    # Load previous progress
    progress = load_progress()
    log(f"\nResuming from previous session:")
    log(f"  Previously downloaded: {progress['total_downloaded']} articles")
    log(f"  Failed downloads: {len(progress['failed_pmcids'])}")
    log(f"  Queries completed: {len(progress['queries_completed'])}")
    
    # Store all metadata
    all_metadata = []
    
    # Process each search query
    for query_idx, query in enumerate(SEARCH_QUERIES, 1):
        
        # Skip if already completed
        if query in progress['queries_completed']:
            log(f"\n[Query {query_idx}/{len(SEARCH_QUERIES)}] SKIPPED (already completed): {query}")
            continue
        
        log(f"\n{'='*80}")
        log(f"[Query {query_idx}/{len(SEARCH_QUERIES)}] Processing: {query}")
        log(f"{'='*80}")
        
        # Search for articles
        pmc_ids = search_pmc(query)
        
        if not pmc_ids:
            log("  No articles found, moving to next query")
            progress['queries_completed'].append(query)
            save_progress(progress)
            continue
        
        # Fetch metadata
        articles = fetch_article_metadata(pmc_ids)
        log(f"  Retrieved metadata for {len(articles)} articles")
        all_metadata.extend(articles)
        
        # Download full-text XMLs
        log(f"  Starting download of full-text XMLs...")
        new_downloads = download_articles(articles, progress)
        log(f"  Downloaded {new_downloads} new articles from this query")
        
        # Mark query as completed
        progress['queries_completed'].append(query)
        save_progress(progress)
        
        log(f"  Query complete! Total corpus: {progress['total_downloaded']} articles")
    
    # Save final metadata
    log(f"\n{'='*80}")
    log("DOWNLOAD COMPLETE!")
    log(f"{'='*80}")
    log(f"Total articles downloaded: {progress['total_downloaded']}")
    log(f"Failed downloads: {len(progress['failed_pmcids'])}")
    log(f"XML files saved to: {XML_DIR}/")
    
    # Save comprehensive metadata
    metadata_summary = {
        'download_date': datetime.now().isoformat(),
        'total_articles': progress['total_downloaded'],
        'failed_downloads': len(progress['failed_pmcids']),
        'queries_used': SEARCH_QUERIES,
        'articles': all_metadata[:1000]  # Save first 1000 for reference
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata_summary, f, indent=2)
    
    log(f"Metadata saved to: {METADATA_FILE}")
    log(f"\nNext steps:")
    log(f"  1. XML files are ready for parsing")
    log(f"  2. Use your existing XML parser to extract sections")
    log(f"  3. Build vector store from parsed content")
    
    # Summary statistics
    log(f"\n{'='*80}")
    log("SUMMARY STATISTICS")
    log(f"{'='*80}")
    
    xml_files = [f for f in os.listdir(XML_DIR) if f.endswith('.xml')]
    total_size_mb = sum(os.path.getsize(os.path.join(XML_DIR, f)) for f in xml_files) / (1024*1024)
    
    log(f"XML files: {len(xml_files)}")
    log(f"Total size: {total_size_mb:.2f} MB")
    log(f"Average size: {total_size_mb/len(xml_files):.2f} MB per file")
    log(f"Storage location: {os.path.abspath(XML_DIR)}")


if __name__ == "__main__":
    try:
        start_time = time.time()
        main()
        elapsed = (time.time() - start_time) / 60
        log(f"\nTotal runtime: {elapsed:.1f} minutes")
    except KeyboardInterrupt:
        log("\n\nDownload interrupted by user. Progress has been saved.")
        log("Run script again to resume from where you left off.")
    except Exception as e:
        log(f"\n\nFATAL ERROR: {e}")
        raise
