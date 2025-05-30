'''

Prerequisites:
Perform your literature searches directly on the PubMed website using its search interface. From each search, export the list of PMIDs by selecting "Send to" → "File" → "PMID list" to save a plain text file (e.g., named 'pubmed_general', 'pubmed_needs', 'pubmed_performance'). Place these .txt files in your working directory before running this script. Set your NCBI API key for Entrez access to enable API queries.

Script workflow:
1) Set a citation count threshold to filter out low-citation entries.  
2) Clear old files in the './output/' folder.  
3) For each PMID list file:  
   - Fetch citation details from the NCBI API.  
   - Discard entries below the citation threshold.  
   - Generate a corresponding BibTeX (.bib) file.  
4) If multiple .bib files are generated, combine them into a single unified .bib file.  
5) Analyze the combined or single .bib file for missing key fields and duplicate entries.  
6) Remove duplicates by grouping entries by PMID and matching article titles retrieved via Biopython queries to keep the most accurate record.  
7) Re-check the finalized .bib file for completeness and duplicates.  
8) Print counts of entries before and after duplicate removal.  
9) Export the cleaned BibTeX entries to an Excel spreadsheet for review.  
10) The finalized .bib file is ready for manual import into reference managers like Mendeley or Zotero.

Notes:  
This script does not perform PubMed searches or save PMIDs; those must be done manually via the PubMed website search tool.  
Duplicate removal prioritizes entries matching the official article title fetched from NCBI.  
Error files (e.g., due to non-ASCII characters) are generated externally and should be checked manually if present.

'''

'''

        IMPORTS

'''

import os
import sys
import time
import glob
import platform
from Bio import Entrez
import bibtexparser
import functions as f

# ----------------------------------------
# Cross-Platform Encoding Configuration
# ----------------------------------------
f.setup_encoding()

# ----------------------------------------
# Set up Entrez API credentials
# ----------------------------------------
Entrez.email = "joshpodmore@hotmail.co.uk"  # Replace with your email
Entrez.api_key = "24c53e643b4cdb5719a09d9d29bcaa5d4809"  # Replace with your NCBI API key

# User configuration
# Entrez.email = "placeholder@change.com"  # Replace with your email
# Entrez.api_key = "8e7f2a9b4c1d6e3f9g2h5i8j1k4l7m0n9p2q"  # Replace with your NCBI API key

f.validate_ncbi_credentials(Entrez)
    
# ----------------------------------------
# Parameters and Target Directory
# ----------------------------------------
targ_dir = './output'
threshold = 10
print(f'\n>>> Enforcing Citation Threshold: {threshold}\n')

# ----------------------------------------
# Clear Previous Output Files
# ----------------------------------------
print(f"🧹 Clearing old files in: {targ_dir}")
for fpath in glob.glob(os.path.join(targ_dir, '*')):
    try:
        os.remove(fpath)
        print(f"  - Deleted: {fpath}")
    except Exception as e:
        print(f"  ⚠️ Could not delete {fpath}: {e}")

# ----------------------------------------
# Run Search for Each Spec
# ----------------------------------------
pmid_dir = './pmid_lists'
spec_list = [f[:-4] for f in os.listdir(pmid_dir) if f.endswith('.txt')]
file_paths = []

for search_spec in spec_list:
    print(f'\n🔍 Processing: {search_spec}')
    file_path = f.ref_gen(search_spec, pmid_dir, targ_dir, threshold)
    file_paths.append(file_path)
    print(f"  ➕ Output saved: {file_path}")

print(f"\n📦 Collected BibTeX files:\n{file_paths}")
time.sleep(2)

# ----------------------------------------
# Combine BibTeX Files if Needed
# ----------------------------------------
if len(file_paths) > 1:
    print("🧬 Combining BibTeX files...")
    combined_path = f.combine_bib_files(file_paths, targ_dir)
else:
    combined_path = file_paths[0]

print(f"📦 Combined file path: {combined_path}")

# ----------------------------------------
# Check for Duplicates (Pre-removal)
# ----------------------------------------
print("\n📋 Checking for duplicates before removal...")
f.check_info_check_duplicates(combined_path, save_txt=True, save_folder=targ_dir)

# ----------------------------------------
# Remove Duplicates and Save Finalized File
# ----------------------------------------
print("\n✂️ Removing duplicates and saving finalized version...")
f.remove_duplicates(combined_path, targ_dir)

# ----------------------------------------
# Re-check for Duplicates (Post-removal)
# ----------------------------------------
finalized_path = os.path.join(targ_dir, 'finalized.bib')
print("\n📋 Re-checking for duplicates after removal...")
f.check_info_check_duplicates(finalized_path, save_txt=False, save_folder=None)

# ----------------------------------------
# Count BibTeX Entries Before and After
# ----------------------------------------
print("\n🔢 Counting BibTeX entries...")
f.count_entries_and_print(combined_path)
f.count_entries_and_print(finalized_path)

# ----------------------------------------
# Export to Excel
# ----------------------------------------
print("\n📤 Exporting finalized BibTeX to Excel...")
f.bib_to_excel(targ_dir)

# ----------------------------------------
# Done
# ----------------------------------------
print('\n✅ --- PROCESSING COMPLETE --- ✅')