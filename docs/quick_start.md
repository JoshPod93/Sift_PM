## Quick Setup

- **Clone the repository**

git clone <https://github.com/JoshPod93/Sift-PM.git>

cd Sift-PM

- **Install requirements**

pip install -r requirements.txt

- **Prepare PMID lists**  
    Save .txt files containing newline-separated PMIDs in the ./pmid_lists/ folder.
- **Configure settings**
    1. Navigate to ref_generator/
    2. Open ref_generator.py and:
        - Set your email and API key (lines 53–54)
        - Set your citation threshold (line 60)
- **Run the script**

python ref_generator.py

- **View results**  
    Navigate to ./output/ and open finalized_entries.xlsx

**Note:** For detailed guidance, see the detailed_guide.md

## Credits

This project uses and depends on several excellent open-source tools and libraries. Special thanks to the developers and maintainers of these projects:

- **pubmed-bib** by [Zhucheng Huang](https://github.com/zhuchcn/pubmed-bib)  
  A handy tool for retrieving BibTeX citations from PubMed IDs.  
  🔗 https://github.com/zhuchcn/pubmed-bib

- Other dependencies are listed in the [requirements.txt](./requirements.txt) file.

We appreciate the open-source community for providing these valuable resources!