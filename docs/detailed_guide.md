## Install

- **Clone the repository**

git clone <https://github.com/JoshPod93/Sift-PM.git>

cd Sift-PM

- **Install requirements**

pip install -r requirements.txt

## ✅ Step 1: Set Up the Python Environment

Before using this repository, you must set up a Python environment to ensure compatibility and install all necessary dependencies.

### 🐍 Required Python Version: 3.9

This codebase is tested and built to work with **Python 3.9**. Using other versions (especially Python 3.11 or newer) may cause compatibility issues with certain packages such as biopython, openpyxl, or plotting libraries.

### ⚙️ Option 1: Using Conda (Recommended)

If you use Anaconda or Miniconda, follow these steps:

1. **Create a new environment:**

conda create -n pubmed_env python=3.9

1. **Activate the environment:**

conda activate pubmed_env

1. **Install requirements:**

Once activated, install dependencies with:

pip install -r requirements.txt

### ✅ Final Check

Verify your setup by running:

python --version

You should see:

Python 3.9.x

Also check that core packages like biopython, pandas, and matplotlib are installed:

pip list

## ✅ Step 2: Generate an NCBI API Key for PubMed Access

NCBI (National Center for Biotechnology Information) provides an API key to allow increased rate limits and reliable access to PubMed and other databases using the E-utilities API.

### 🔧 Why an API Key?

Without an API key, the request limit is **3 requests per second**. With a key, this increases to **10 requests per second**, which is critical for large-scale queries.

### 📌 Instructions to Get an NCBI API Key

1. **Create an NCBI Account**
    - Visit: <https://www.ncbi.nlm.nih.gov/account/>
    - Click **Register for an NCBI account** and complete the sign-up process.
2. **Log In**
    - Go to <https://www.ncbi.nlm.nih.gov/account/> again and log in using your new credentials.
3. **Go to Your Dashboard**
    - Click your username in the top-right corner.
    - Select **Dashboard**.
4. **Generate an API Key**
    - In the **API Key Management** section:
        - Click **Create an API Key**.
        - An API key like 123abc456def789ghi will be shown.
5. **Copy and Save the Key**
    - Store it securely. You will need it in your scripts.
    - Example format for environment or scripts:

NCBI_API_KEY=123abc456def789ghi

### ✏️ Modify the Code to Use Your Key

1. Open the file:  
    ref_generator.py
2. Navigate to **lines 53–54**. You will see:

Entrez.email = "<your@email.com>"

Entrez.api_key = "your-api-key-here"

1. Replace the placeholders with:
    - The email address you registered with NCBI.
    - Your actual API key.

### ✅ Example

Entrez.email = "<my.name@university.edu>"

Entrez.api_key = "d89c1234efgh5678ijkl9012mnop3456qrst"

## ✅ Step 3: Generate and Save PubMed Search Queries

To start, create a carefully structured conjunctive search query that maximizes coverage of your literature topic while maintaining precision.

### 🔍 Generate a Search Query

You can use ChatGPT or another large language model to help craft your PubMed query. Simply describe your review topic clearly.

**Example prompt to ChatGPT:**

“Create a conjunctive PubMed query to search for papers on SSVEP-based BCI spellers.”

### ✅ Example Output

(SSVEP OR "steady state visual evoked potential") AND ("brain-computer interface" OR BCI) AND (speller OR spelling OR communication)

This query captures relevant variations of terminology likely used in the literature and can be directly copied into PubMed.

### 🔎 Run the Search on PubMed

1. Visit: <https://pubmed.ncbi.nlm.nih.gov/>
2. Paste your conjunctive search string into the search bar and hit **Search**.

### ⏳ Optional: Narrow Your Results

Use filters on the left (e.g., Publication Date) to restrict results by year or other criteria.

### 💾 Save the PMIDs

1. After results load, click the **Save** button below the search bar.
2. In the popup:
    - Under **Selection**, choose **All results** (not just “All results on page”).
    - Under **Format**, select **PMID**.
3. Click **Create File** to download a .txt file containing one PMID per line.

Example contents:

31729671

33916189

26834611

29601538

...

### 🗂 Rename and Store the File

- Rename the .txt file to something meaningful and versioned, for example:  
    query_ssvep_spellers_0001.txt
- Move this file into the project’s ./pmid_lists folder.

This file serves as input for the next processing step.

### ➕ Add Multiple Queries (Optional)

You can create and save multiple query files covering different aspects of your topic. The code will automatically detect and process **all** .txt files in the ./pmid_lists folder — no manual specification required.

## ✅ Step 4: How ref_generator.py Works

The ref_generator.py script is the core of SIFT-PM. It automates loading, filtering, and converting PubMed article metadata for systematic or scoping reviews. Here’s a step-by-step overview of its main functions:

### 1\. Citation Threshold Filtering

- At **line 60**, the script sets a citation threshold:

threshold = 5

- Articles with fewer citations than this threshold are excluded.
- This helps focus on higher-impact research by filtering out less-cited papers.

### 2\. Clearing Previous Results

- Before each run, the script removes all files in the ./output/ directory:

shutil.rmtree('./output/')

- This keeps output clean by preventing leftover files from prior runs affecting results.

### 3\. PMID-Based Article Retrieval

- For each .txt PMID file in ./pmid_lists:
  - The script queries the NCBI E-utilities API (Entrez.efetch) to fetch metadata.
  - Articles are split into two groups based on the citation threshold:
    - **Above threshold:** saved as query_0001_in_threshold.txt
    - **Below threshold:** saved as query_0001_sub_threshold.txt

### 4\. BibTeX Generation

- BibTeX entries are generated **only** for articles above the citation threshold (\*\_in_threshold.txt).
- This avoids clutter from low-impact or irrelevant studies.
- A .bib file is created for each thresholded list.

### 5\. Aggregation and Deduplication

- After processing all lists:
  - All .bib files are merged into one: combined.bib
  - Duplicates are identified (by title/DOI) and removed.
  - The clean output is saved as finalized.bib
- Filtering and deduplication steps are logged, providing summary counts compatible with PRISMA flowcharts (e.g., initial count, excluded by threshold, duplicates removed).

### 6\. Excel Export

- The script converts finalized.bib into an Excel .xlsx file.
- Each BibTeX field (author, title, journal, doi, year, etc.) becomes a column.
- This structured table is ready for review teams or import into review software.

## Credits

This project uses and depends on several excellent open-source tools and libraries. Special thanks to the developers and maintainers of these projects:

- **pubmed-bib** by [Zhucheng Huang](https://github.com/zhuchcn/pubmed-bib)  
  A handy tool for retrieving BibTeX citations from PubMed IDs.  
  🔗 https://github.com/zhuchcn/pubmed-bib

- Other dependencies are listed in the [requirements.txt](./requirements.txt) file.

We appreciate the open-source community for providing these valuable resources!
