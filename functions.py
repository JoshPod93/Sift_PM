'''

functions.py

This module provides helper functions used in the `ref_generator` script,
which automates PubMed-based systematic or scoping review workflows.

It handles:
- Reference retrieval via Entrez API
- Citation filtering by threshold
- BibTeX merging and deduplication
- Metadata inspection (e.g., missing fields, duplicates)
- Exporting results to Excel

Optimized for use in Windows environments (UTF-8 encoding enforced).

'''

# ========== Standard Library Imports ==========
import os
import sys
import glob
import platform
import time
import re
import unicodedata
import subprocess
import urllib.error
import http.client
from xml.etree import ElementTree as ET
from collections import Counter
from pprint import pprint
from tqdm import tqdm

# ========== Third-Party Imports ==========
import requests
import pandas as pd
from Bio import Entrez
import bibtexparser

def setup_encoding():
    """
    Configure UTF-8 encoding for standard I/O streams based on the operating system.

    This ensures consistent handling of international characters across platforms:
    - On **Windows**, forces UTF-8 mode using PYTHONUTF8 and reconfigures all streams.
    - On **macOS**, sets relevant locale variables and reconfigures streams if supported.
    - On **Linux**, sets fallback UTF-8 locales and reconfigures if the current encoding is not UTF-8.
    - On **other systems**, applies a generic UTF-8 configuration.

    Notes:
        - Uses `sys.stdout.reconfigure()` (Python 3.7+) where available.
        - Falls back silently if the Python version does not support reconfiguration.
    """    system = platform.system().lower()
    
    if system == 'windows':
        # Windows: Force UTF-8 to handle international characters properly
        print("🪟 Detected Windows - Enforcing UTF-8 encoding")
        os.environ["PYTHONUTF8"] = "1"
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        sys.stdin.reconfigure(encoding='utf-8')
        
    elif system == 'darwin':  # macOS
        # macOS: Usually UTF-8 by default, but ensure consistency
        print("🍎 Detected macOS - Setting UTF-8 encoding")
        os.environ["LC_ALL"] = "en_US.UTF-8"
        os.environ["LANG"] = "en_US.UTF-8"
        # macOS typically handles UTF-8 well, but we can still reconfigure if needed
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            sys.stdin.reconfigure(encoding='utf-8')
        except AttributeError:
            # Older Python versions might not have reconfigure
            pass
            
    elif system == 'linux':
        # Linux: Check current locale and set UTF-8 if not already
        print("🐧 Detected Linux - Configuring UTF-8 encoding")
        current_encoding = sys.stdout.encoding
        print(f"   Current encoding: {current_encoding}")
        
        # Set environment variables for UTF-8
        os.environ["LC_ALL"] = "C.UTF-8"  # Fallback locale
        os.environ["LANG"] = "C.UTF-8"
        
        # Try to reconfigure streams
        try:
            if current_encoding.lower() != 'utf-8':
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
                sys.stdin.reconfigure(encoding='utf-8')
                print("   ✓ Reconfigured to UTF-8")
            else:
                print("   ✓ UTF-8 already configured")
        except AttributeError:
            # Older Python versions
            print("   ⚠️ Cannot reconfigure streams (older Python version)")
            
    else:
        # Other Unix-like systems
        print(f"🖥️ Detected {system} - Applying generic UTF-8 configuration")
        os.environ["LC_ALL"] = "C.UTF-8"
        os.environ["LANG"] = "C.UTF-8"
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            sys.stdin.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    
    # Verify final encoding
    print(f"   Final stdout encoding: {sys.stdout.encoding}")
    print(f"   System default encoding: {sys.getdefaultencoding()}")

def validate_ncbi_credentials(entrez):
    """
    Validates that the Entrez.email and Entrez.api_key are not left as placeholders.

    Parameters:
        entrez (module): The Bio.Entrez module with user-defined email and API key.

    Raises:
        SystemExit: If either the email or API key is still set to the default placeholder,
                    prints an error and terminates the script.
    """
    if entrez.email == "placeholder@change.com" or entrez.api_key == "8e7f2a9b4c1d6e3f9g2h5i8j1k4l7m0n9p2q":
        print("\n❌ ERROR: You must replace the placeholder email and API key in the script.")
        print("   Both are required for accessing NCBI Entrez utilities.")
        print("   The setup is completely FREE and takes about 1 minute.")
        print("   ➤ Sign up for an NCBI account and generate your API key here:")
        print("     https://www.ncbi.nlm.nih.gov/account/\n")
        print("   For detailed instructions, refer to 'detailed_guide.md'.\n")
        sys.exit(1)

def get_bibtex_for_pmid(pmid):
    """
    Retrieve BibTeX citation data for a given PubMed ID (PMID) using the `pubmed-bib` command-line tool.

    This function requires the `pubmed-bib` utility to be installed and available in your system's PATH.
    It runs the tool via subprocess and captures the BibTeX-formatted citation.

    Setup:
        You only need to install `pubmed-bib` once using the following method:

        - Clone and install from the official GitHub repository:
            git clone https://github.com/zhuchcn/pubmed-bib.git
            cd pubmed-bib
            pip install -e .
            cd ..

    Parameters:
        pmid (str or int): The PubMed ID for which to retrieve the BibTeX entry.

    Returns:
        str or None: The BibTeX entry as a UTF-8 string if successful; otherwise, None.
    """
    try:
        result = subprocess.run(
            ['pubmed-bib', '--id', str(pmid)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode('utf-8', errors='replace')  # Robust to encoding issues
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PMID {pmid}: {e.stderr.decode('utf-8', errors='replace')}")
        return None

def count_entries_and_print(bib_file):
    """
    Count and print the number of entries in a given BibTeX (.bib) file.

    Parameters:
        bib_file (str): Path to the .bib file to be read.

    Returns:
        None: Prints the number of entries to the console.
    """
    # Load the BibTeX file
    with open(bib_file, 'r', encoding='utf-8') as bibfile:
        bib_database = bibtexparser.load(bibfile)
    
    # Count the number of entries
    num_entries = len(bib_database.entries)

    print(f"\nNumber of entries in '{bib_file}': {num_entries}")

def get_citations(pmid, max_retries=3):
    """
    Fetch the number of citations for a given PubMed ID (PMID) using the Entrez E-utilities API.

    This function queries the PubMed database to find how many other PubMed articles cite the given PMID.
    It includes basic error handling and a retry mechanism for robustness.

    Parameters:
        pmid (str): The PubMed ID to look up.
        max_retries (int): Number of times to retry the request if an HTTP error occurs (default: 3).

    Returns:
        int: Number of citations if found.
        0: If the article has no citations or input is invalid.
        None: If an error occurs after all retries or unexpected issues prevent retrieval.
    """
    if not pmid or not isinstance(pmid, str):
        print(f"Invalid PMID format: {pmid}")
        return 0
    
    for retry in range(max_retries):
        try:
            # Entrez.elink expects pmid as a list or string; convert if needed
            handle = Entrez.elink(dbfrom="pubmed", id=str(pmid), linkname="pubmed_pubmed_citedin")
            record = Entrez.read(handle)
            handle.close()

            if not record or 'LinkSetDb' not in record[0]:
                # No citations found
                return 0

            link_set_db = record[0]['LinkSetDb']

            if not link_set_db or 'Link' not in link_set_db[0]:
                return 0

            citation_count = len(link_set_db[0]['Link'])
            return citation_count

        except urllib.error.HTTPError as e:
            print(f"\nHTTP Error fetching citations for PMID {pmid}: {e}")
            if retry < max_retries - 1:
                print("Retrying after 2 seconds...")
                time.sleep(2)
            else:
                print("Max retries reached. Returning None.")
                return None
        except (IndexError, KeyError) as e:
            print(f"Parsing error for PMID {pmid}: {e} (assuming 0 citations)")
            return 0
        except Exception as e:
            print(f"\nUnexpected error for PMID {pmid}: {e}")
            return None
            
def sanitize_bibtex(bibtex_entry):
    """
    Sanitize a BibTeX entry by removing or replacing non-ASCII characters.

    This is useful for ensuring compatibility with BibTeX parsers and tools 
    that may not handle Unicode characters well. The function uses Unicode 
    normalization (NFKD) to decompose characters and then encodes to ASCII, 
    ignoring characters that can't be represented.

    Parameters:
        bibtex_entry (str): The raw BibTeX entry string potentially containing non-ASCII characters.

    Returns:
        str: A sanitized BibTeX entry string containing only ASCII characters.
    """
    sanitized_entry = unicodedata.normalize('NFKD', bibtex_entry).encode('ascii', 'ignore').decode('ascii')
    return sanitized_entry

def pmid_to_doi(pmid, email, api_key):
    """
    Retrieve the DOI for a given PubMed ID (PMID) using the NCBI E-utilities API.

    This function sends a request to the NCBI efetch endpoint to retrieve article 
    metadata in XML format. It then parses the XML to extract the DOI (Digital 
    Object Identifier) associated with the article, if available.

    Parameters:
        pmid (str): The PubMed ID of the article.
        email (str): Email address to include in the request, as recommended by NCBI.
        api_key (str): NCBI API key to authenticate and increase request rate limits.

    Returns:
        tuple:
            - str or None: The DOI URL (e.g., 'https://doi.org/10.xxxx/xxxx') if found; otherwise, None.
            - str or None: The PMID if successfully processed; otherwise, None.

    Notes:
        - If the XML response is malformed or DOI is not found, the function returns (None, pmid).
        - If the HTTP request fails, it returns (None, None).
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'email': email,
        'api_key': api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        try:
            root = ET.fromstring(response.text)
            for article_id in root.findall('.//ArticleId'):
                if article_id.attrib.get('IdType') == 'doi':
                    doi = "https://doi.org/" + article_id.text
                    return doi, pmid
            return None, pmid
        except ET.ParseError:
            print("Error parsing the XML response.")
    else:
        print(f"HTTP Error: {response.status_code}")
    return None, None

def pmid_to_doi_via_crossref(pmid):
    """
    Retrieve the DOI for a given PubMed ID (PMID) by querying the CrossRef API.

    This function queries CrossRef's works endpoint filtered by the PubMed ID,
    parses the JSON response, and extracts the DOI if available.

    Parameters:
        pmid (str or int): The PubMed ID of the article.

    Returns:
        tuple:
            - str or None: The DOI URL (e.g., 'https://doi.org/10.xxxx/xxxx') if found; otherwise, None.
            - str or int: The original PMID provided.

    Notes:
        - Returns (None, pmid) if no DOI is found or in case of any errors.
        - A timeout of 10 seconds is used for the API request.
        - Any exceptions during the request or parsing are caught and logged.
    """
    url = f"https://api.crossref.org/works?filter=pubmed-id:{pmid}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'message' in data and 'items' in data['message']:
                items = data['message']['items']
                if items:
                    doi = items[0].get('DOI')
                    if doi:
                        return "https://doi.org/" + doi, pmid
        return None, pmid
    except Exception as e:
        print(f"CrossRef fetch failed for PMID {pmid}: {e}")
        return None, pmid

def append_doi_pmid_to_entry(bibtex_entry, pmid, email, api_key):
    """
    Append DOI and PMID fields to a BibTeX entry string.

    This function attempts to retrieve the DOI for a given PubMed ID (PMID) 
    using Entrez first, then falls back to CrossRef if Entrez fails. It then
    adds the DOI (uppercase key) and PMID (lowercase key) fields to the BibTeX
    entry if they are not already present.

    Parameters:
        bibtex_entry (str): The raw BibTeX entry as a string.
        pmid (str or int): The PubMed ID to query for DOI and ensure inclusion.
        email (str): Email address required by Entrez API.
        api_key (str): API key required by Entrez API.

    Returns:
        str: The updated BibTeX entry with DOI and/or PMID fields appended,
             maintaining proper BibTeX syntax.

    Notes:
        - Checks for existing PMID field (case-insensitive) before adding.
        - Inserts new fields before the closing brace '}' of the entry.
        - Ensures proper comma placement to maintain valid BibTeX formatting.
        - If neither DOI nor PMID is found or needed, returns the original entry unchanged.
    """
    doi, pmid_out = pmid_to_doi(pmid, email, api_key)

    if doi is None:
        print(f"\nEntrez failed for PMID {pmid}, trying Crossref...")
        doi, pmid_out = pmid_to_doi_via_crossref(pmid)

    # Check if pmid already in bibtex (case-insensitive)
    if re.search(r'\bpmid\s*=\s*{.*?}', bibtex_entry, re.IGNORECASE):
        pmid_exists = True
    else:
        pmid_exists = False

    # Prepare lines to insert
    lines_to_add = []
    if doi:
        lines_to_add.append(f'    DOI = {{{doi}}},\n')  # uppercase DOI
    if pmid_out and not pmid_exists:
        lines_to_add.append(f'    pmid = {{{pmid_out}}},\n')

    if not lines_to_add:
        return bibtex_entry  # nothing to add

    # Find last closing brace '}' of entry
    last_brace_pos = bibtex_entry.rfind('}')
    if last_brace_pos == -1:
        # Malformed BibTeX, just append at end
        return bibtex_entry + ''.join(lines_to_add)

    # Insert before last brace, but check for trailing commas
    before = bibtex_entry[:last_brace_pos].rstrip()
    after = bibtex_entry[last_brace_pos:]

    # Add a comma before if not already present at end of entry body (to avoid syntax errors)
    if not before.endswith(','):
        before += ','

    updated_entry = before + '\n' + ''.join(lines_to_add) + after
    return updated_entry
    
def fetch_title_from_biopython(pmid):
    """
    Retrieve the article title for a given PMID using Biopython Entrez.

    Args:
        pmid (str): PubMed ID of the article.

    Returns:
        str or None: Article title if found, else None.
    """
    # Fetch the article title associated with the PMID using Biopython
    # Entrez.email = "your_email@example.com"  # Set your email
    handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
    record = Entrez.read(handle)
    title = record['PubmedArticle'][0]['MedlineCitation']['Article']['ArticleTitle']
    return title if title else None

def remove_duplicates(bib_file, targ_dir):
    """
    Remove duplicate BibTeX entries by grouping on PMID and resolving conflicts using title match or year.
    Saves the cleaned entries to 'output/finalized.bib' in targ_dir.

    Args:
        bib_file (str): Path to the input .bib file.
        targ_dir (str): Directory where the output is saved.

    Returns:
        str: Path to the cleaned, combined .bib file.
    """
    # Load the BibTeX file
    with open(bib_file, 'r', encoding='utf-8') as bibfile:
        bib_database = bibtexparser.load(bibfile)

    # Group entries by PMID
    groups = {}
    for entry in bib_database.entries:
        pmid = entry.get('pmid')
        if pmid not in groups:
            groups[pmid] = []
        groups[pmid].append(entry)

    # Resolve duplicates based on title matching
    unique_entries = []
    for pmid, entries in groups.items():
        if len(entries) == 1:
            unique_entries.append(entries[0])
        else:
            title_from_biopython = fetch_title_from_biopython(pmid)
            if title_from_biopython:
                matching_entries = [entry for entry in entries if entry.get('title') == title_from_biopython]
                if matching_entries:
                    unique_entries.append(matching_entries[0])
                else:
                    sorted_entries = sorted(entries, key=lambda x: x.get('year'))
                    unique_entries.append(sorted_entries[0])
            else:
                sorted_entries = sorted(entries, key=lambda x: x.get('year'))
                unique_entries.append(sorted_entries[0])

    # Properly join path with 'output' folder and filename
    output_file = os.path.join(targ_dir, 'finalized.bib')

    # Make sure the Output directory exists before writing
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the unique entries to the new .bib file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        unique_database = bibtexparser.bibdatabase.BibDatabase()
        unique_database.entries = unique_entries
        bibtexparser.dump(unique_database, outfile)

    # Return the path to the finalized .bib file
    return output_file

def combine_bib_files(file_paths, targ_dir):
    """
    Merge multiple .bib files into one and save as 'combined_bib_file.bib' 
    inside the 'output' targ_dir folder.
    
    Args:
        file_paths (list of str): Paths to input .bib files.
        targ_dir (str): Target directory containing output.
        
    Returns:
        str: Path to the combined .bib output file.
    """
    combined_entries = []

    # Read entries from each file and append to combined list
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as bibfile:
            bib_database = bibtexparser.load(bibfile)
            combined_entries.extend(bib_database.entries)

    # Create combined database
    combined_database = bibtexparser.bibdatabase.BibDatabase()
    combined_database.entries = combined_entries

    # Define output path inside Finalized subdirectory
    output_path = os.path.join(targ_dir, 'combined_bib_file.bib')

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write combined BibTeX file
    with open(output_path, 'w', encoding='utf-8') as outfile:
        bibtexparser.dump(combined_database, outfile)

    print(f"Combined .bib file written to: {output_path}")
    return output_path

def check_info_check_duplicates(file_path, save_txt=False, save_folder=None):
    with open(file_path, 'r', encoding='utf-8') as bibfile:
        bib_database = bibtexparser.load(bibfile)

    entries = bib_database.entries
    original_total = len(entries)
    removed_ids = set()
    removed_pmids = set()
    removed_dois = set()

    # Helper: remove duplicates based on key
    def remove_duplicates(entries, key):
        seen = set()
        new_entries = []
        removed_keys = set()
        for entry in entries:
            val = entry.get(key)
            if not val:
                new_entries.append(entry)
                continue
            if val in seen:
                removed_keys.add(val)
            else:
                seen.add(val)
                new_entries.append(entry)
        return new_entries, removed_keys

    # First pass: remove by ID
    entries, dup_ids = remove_duplicates(entries, 'ID')
    removed_ids.update(dup_ids)

    # Second pass: remove by PMID
    entries, dup_pmids = remove_duplicates(entries, 'pmid')
    removed_pmids.update(dup_pmids)

    # Third pass: remove by DOI
    entries, dup_dois = remove_duplicates(entries, 'doi')
    removed_dois.update(dup_dois)

    # Summary info
    ids = [e.get('ID') for e in entries]
    pmids = [e.get('pmid') for e in entries]
    dois = [e.get('doi') for e in entries]

    missing_fields_counts = {
        'journal': sum(1 for e in entries if not e.get('journal')),
        'volume': sum(1 for e in entries if not e.get('volume')),
        'pages': sum(1 for e in entries if not e.get('pages')),
        'pmid': sum(1 for e in entries if not e.get('pmid')),
        'doi': sum(1 for e in entries if not e.get('doi')),
    }

    lines = []
    if removed_ids or removed_pmids or removed_dois:
        lines.append("⚠️ WARNING: DUPLICATES DETECTED ⚠️\n")
    else:
        lines.append("✅ NO duplicates present in input list ✅\n")

    lines.append("Summary Info:")
    lines.append(f"Original total entries: {original_total}")
    lines.append(f"Remaining entries after deduplication: {len(entries)}")
    lines.append(f"First ID: {ids[0] if ids else 'N/A'}")
    lines.append(f"First few PMIDs: {pmids[:3]}")
    lines.append(f"First few DOIs: {dois[:3]}\n")

    lines.append("Missing Fields Counts:")
    for field, count in missing_fields_counts.items():
        lines.append(f"  {field}: {count}")

    lines.append("\n---------------")
    lines.append(f"Duplicate IDs removed ({len(removed_ids)}):")
    for d in sorted(removed_ids):
        lines.append(f"  {d}")

    lines.append("\n---------------")
    lines.append(f"Duplicate PMIDs removed ({len(removed_pmids)}):")
    for d in sorted(removed_pmids):
        lines.append(f"  {d}")

    lines.append("\n---------------")
    lines.append(f"Duplicate DOIs removed ({len(removed_dois)}):")
    for d in sorted(removed_dois):
        lines.append(f"  {d}")

    lines.append(f"\nTotal unique entries removed: {original_total - len(entries)}")

    report = '\n'.join(lines)
    print(report)

    if save_txt:
        if not save_folder:
            raise ValueError("If save_txt is True, save_folder must be provided.")
        output_path = os.path.join(save_folder, 'duplicate_check_summary.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 Summary saved to: {output_path}")
        
def bib_to_excel(targ_dir):
    """
    Convert 'finalized.bib' in the 'output' folder to an Excel file in the same folder.
    
    Args:
        targ_dir (str): Base directory 'output' subfolder.
    """
    finalized_bib = os.path.join(targ_dir, 'finalized.bib')
    output_excel = os.path.join(targ_dir, 'finalized_entries.xlsx')

    with open(finalized_bib, 'r', encoding='utf-8') as f:
        bib_db = bibtexparser.load(f)

    df = pd.DataFrame(bib_db.entries)
    df.to_excel(output_excel, index=False)

def ref_gen(search_spec, pmid_dir, targ_dir, threshold):
    """
    Process a list of PubMed IDs from a text file, filter by citation count, 
    and generate a BibTeX file with entries for PMIDs above the specified citation threshold.

    (Docstring omitted here for brevity, same as before)
    """

        # Input/output file paths
    file_path = os.path.join(pmid_dir, search_spec + '.txt')
    sub_threshold_file_path = os.path.join(targ_dir, search_spec + '_sub_threshold.txt')
    pmids_in_threshold = os.path.join(targ_dir, search_spec + '_in_threshold.txt')
    bib_output_path = os.path.join(targ_dir, search_spec + '_thresh.bib')
    error_file_path = os.path.join(targ_dir, search_spec + '_error.txt')

    # Read PMIDs
    pmids = []
    with open(file_path, 'r') as file:
        for line in tqdm(file, desc="Reading PMIDs"):
            pmid = line.strip()
            pmids.append(str(pmid))

    print('Total PMID IDs:', len(pmids))

    # Filter by citation count
    pmids_with_at_least_X_citations = []
    pmids_sub_threshold = []

    for pmid in tqdm(pmids, desc="Checking citations"):
        citation_count = get_citations(pmid)

        if citation_count is None:
            print(f"Skipping PMID {pmid} due to failed citation fetch.")
            pmids_sub_threshold.append(pmid)
        elif citation_count >= threshold:
            pmids_with_at_least_X_citations.append(pmid)
        else:
            pmids_sub_threshold.append(pmid)

        time.sleep(3.0)

    # Save PMIDs below threshold
    with open(sub_threshold_file_path, 'w') as f:
        for pmid in pmids_sub_threshold:
            f.write(pmid + '\n')

    print('Total PMIDs above threshold:', len(pmids_with_at_least_X_citations))
    print('Total PMIDs below threshold:', len(pmids_sub_threshold))

    # Setup counters for failures
    entrez_fail_count = 0
    crossref_fail_count = 0
    errors = []

    initial_wait_time = 3
    wait_time_increment = 0.5
    max_retries = 5

    with open(bib_output_path, "a", encoding='utf-8') as bib_file, \
         open(pmids_in_threshold, "w", encoding='utf-8') as pmid_file:

        with tqdm(pmids_with_at_least_X_citations, desc="Converting to .bib") as pbar:
            for pmid in pbar:
                pmid_file.write(str(pmid) + '\n')
                wait_time = initial_wait_time
                attempt = 0
                bibtex_entry = None

                # Try Entrez first with retries
                while attempt < max_retries:
                    bibtex_entry = get_bibtex_for_pmid(pmid)
                    if bibtex_entry:
                        pbar.set_postfix(method='Entrez success', pmid=pmid)
                        break
                    else:
                        pbar.set_postfix(method=f'Entrez retry {attempt + 1}', pmid=pmid)
                        time.sleep(wait_time)
                        wait_time += wait_time_increment
                        attempt += 1

                if not bibtex_entry:
                    entrez_fail_count += 1
                    print(f"Entrez failed for PMID {pmid}, trying Crossref...")

                    # Try Crossref once
                    bibtex_entry = get_bibtex_via_crossref(pmid)
                    if bibtex_entry:
                        pbar.set_postfix(method='Crossref success', pmid=pmid)
                        print(f"Crossref succeeded for PMID {pmid}.")
                    else:
                        crossref_fail_count += 1
                        print(f"Crossref failed for PMID {pmid} as well.")
                        pbar.set_postfix(method='Failed both', pmid=pmid)
                        errors.append(f"Failed to retrieve bibtex entry for PMID {pmid} via Entrez and Crossref.")
                        continue

                # Try writing the entry, handle Unicode errors with sanitization fallback
                try:
                    bibtex_entry = append_doi_pmid_to_entry(bibtex_entry, pmid, Entrez.email, Entrez.api_key)
                    bib_file.write(bibtex_entry + '\n\n')
                    pbar.set_postfix(status='Written', pmid=pmid)
                except UnicodeEncodeError:
                    try:
                        sanitized = sanitize_bibtex(bibtex_entry)
                        sanitized = append_doi_pmid_to_entry(sanitized, pmid, Entrez.email, Entrez.api_key)
                        bib_file.write(sanitized + '\n\n')
                        pbar.set_postfix(status='Sanitized & Written', pmid=pmid)
                    except UnicodeEncodeError as e:
                        error_msg = f"Failed to write sanitized BibTeX entry for PMID {pmid}. Error: {str(e)}"
                        pbar.set_postfix(status='Write failed', pmid=pmid)
                        errors.append(error_msg)

    # Write error log if any
    if errors:
        with open(error_file_path, 'w', encoding='utf-8') as error_file:
            for error in errors:
                error_file.write(error + '\n')

    # Final summary
    og = len(pmids)
    nw = len(pmids_with_at_least_X_citations)
    er = len(errors)

    print('Original Number of PMIDs:', og)
    print('Rejected by Thresholding:', og - nw)
    print(f"BibTeX entries attempted: {nw}")
    print(f"Entrez failures: {entrez_fail_count}")
    print(f"Crossref failures: {crossref_fail_count}")
    print(f"Errors during BibTeX fetch/write: {er}")
    print('Successfully written entries:', nw - er)

    return bib_output_path
