# PMC Open Access Bulk Download - Instructions

## ✅ Status: Ready to Run!

**What this will do:**
- Download 5,000-10,000 full-text research papers from PMC Open Access
- All legally downloadable (Open Access Subset)
- Focus on electrolyte research for BestMove
- Takes 30-60 minutes
- Can be paused and resumed anytime

---

## Before You Start (Optional but Recommended)

### Get a Free NCBI API Key (increases speed 3x)

1. Go to: https://ncbi.nlm.nih.gov/account/
2. Create free account (takes 2 minutes)
3. Go to Settings → API Key Management
4. Generate API key
5. Copy the key
6. Edit `pmc_bulk_downloader.py`:
   - Find line: `# Entrez.api_key = "YOUR_API_KEY_HERE"`
   - Uncomment and add your key: `Entrez.api_key = "abc123xyz"`

**Benefits:**
- Without key: 3 requests/second = ~2 hours for 10,000 papers
- With key: 10 requests/second = ~40 minutes for 10,000 papers

**It's optional** - script works fine without it, just slower.

---

## Running the Download

### Simple Version (Just Run It):

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate
python3 pmc_bulk_downloader.py
```

That's it! The script will:
1. Search PMC for electrolyte research
2. Download full-text XMLs
3. Save progress as it goes
4. Create logs

### If You Need to Stop

Press `Ctrl+C` to stop anytime. Progress is saved automatically.

To resume later, just run the same command again - it picks up where it left off!

---

## What You'll Get

### Directory Structure:
```
pmc_open_access_papers/
├── xml_files/
│   ├── PMC_12345678.xml
│   ├── PMC_23456789.xml
│   └── ... (5,000-10,000 files)
├── download_metadata.json
├── download_log.txt
└── progress.json
```

### File Sizes:
- Each XML: ~50-500 KB
- Total corpus: 500 MB - 2 GB
- Make sure you have 3-5 GB free space

---

## Search Queries Being Used

The script searches for:
1. Electrolytes + hydration/rehydration
2. Electrolyte replacement + athletes/exercise
3. Sodium + balance/homeostasis  
4. Potassium + balance/homeostasis
5. Magnesium + supplementation/bioavailability
6. Oral rehydration solutions
7. Hyponatremia OR hypernatremia
8. Electrolyte disorders
9. Magnesium + sleep
10. Sodium + exercise

All with "open access" filter = completely legal!

---

## Progress Monitoring

### Watch the output:
```
[2025-10-04 15:30:00] Searching PMC: electrolytes AND hydration...
[2025-10-04 15:30:02]   Found 5432 articles, retrieved 5432 IDs
[2025-10-04 15:30:05]   Fetching metadata for 100 articles (batch 1)
[2025-10-04 15:31:00]   Progress: 100/5432 articles processed, 98 new downloads
...
```

### Check files downloaded:
```bash
ls pmc_open_access_papers/xml_files/ | wc -l
```

### Check log file:
```bash
tail -f pmc_open_access_papers/download_log.txt
```

---

## Estimated Timeline

**Without API key (3 req/sec):**
- 5,000 papers: ~60 minutes
- 10,000 papers: ~2 hours

**With API key (10 req/sec):**
- 5,000 papers: ~20 minutes  
- 10,000 papers: ~40 minutes

Plus time for the initial searches (~5-10 min total).

---

## Troubleshooting

### "Too many requests" error
- You're being rate-limited
- Wait 5 minutes, then restart
- Get an API key (see above)

### Script stops/crashes
- Check download_log.txt for errors
- Progress is saved in progress.json
- Just run script again to resume

### Not enough disk space
- Each paper is ~100-200 KB
- 10,000 papers = ~2 GB
- Clear space and resume

### No papers downloading
- Check internet connection
- Try running test again (see below)
- Check if NCBI services are up: https://www.ncbi.nlm.nih.gov/

---

## Quick Test (Before Full Run)

Test with just 10 papers:

```bash
cd /home/jschu/projects/Agentic.RAG
source venv/bin/activate

# Edit pmc_bulk_downloader.py temporarily:
# Change line: SEARCH_QUERIES = [
# To just one query for testing:
# SEARCH_QUERIES = [
#     'magnesium supplementation AND "open access"[filter]',
# ]
# And change: MAX_RESULTS_PER_QUERY = 10

python3 pmc_bulk_downloader.py
```

Should take ~1 minute and download 10 papers.

---

## After Download Completes

### Verify Success:
```bash
cd pmc_open_access_papers

# Count XMLs
ls xml_files/*.xml | wc -l

# Check metadata
cat download_metadata.json | head -30

# See summary
tail -20 download_log.txt
```

### Next Steps:
1. ✅ You'll have thousands of full-text papers
2. ✅ All in XML format with structured sections
3. ✅ Ready for parsing (Methods, Results, Tables)
4. ✅ Build vector store from parsed content
5. ✅ Integrate with notebook

---

## Legal Note

**This is 100% legal:**
- PMC Open Access Subset = explicitly free to download and reuse
- NCBI provides these APIs specifically for bulk downloads
- All papers have Creative Commons or similar licenses
- Perfect for commercial use (BestMove)

Source: https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/

---

## Ready to Start?

Run this command:

```bash
cd /home/jschu/projects/Agentic.RAG && source venv/bin/activate && python3 pmc_bulk_downloader.py
```

Then go get coffee! ☕

The script will handle everything and show progress as it goes.
