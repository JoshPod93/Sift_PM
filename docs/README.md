\# 🔎 SIFT-PM: Systematic Incorporation and Filtering Tool for PubMed

SIFT-PM is a Python-based automation toolkit designed to streamline and enhance the literature review process. Optimized for use with NCBI's PubMed API, it enables researchers to efficiently seek, sift, and select high-quality papers for systematic or scoping reviews.

See the /docs quick_setup.md or detailed_guide.md for more info.

\---

\## 🧠 What It Does

\- 📥 Ingests PMIDs directly from PubMed search results or automated queries.

\- 🔄 Supports overlapping conjunctive keyword strategies to ensure targeted and exhaustive topic coverage.

\- ⚖️ Applies a citation threshold to prioritize high-impact research based on citation counts.

\- 🧹 Automatically deduplicates entries across multiple result sets — no need for Zotero, Mendeley, or manual pruning.

\- 📊 Exports a finalized Excel spreadsheet with:

\- Entry counts before and after filtering and deduplication.

\- Metadata compatible with PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) documentation.

\---

\## 🎯 Purpose

SIFT-PM is intended for:

\- 🧪 Researchers and evidence synthesis teams conducting systematic or scoping reviews.

\- ✅ Those seeking quality control over included studies.

\- 🕒 Anyone aiming to minimize manual workload and avoid redundancy.

\- 🔁 Users who value reproducibility and transparent documentation of the filtering process.

\---

\## 💡 Optimized for Windows

🪟 This script is Windows-optimized, with UTF-8 encoding compatibility built-in. It explicitly reconfigures \`sys.stdin\`, \`sys.stdout\`, and \`sys.stderr\` to avoid encoding errors commonly encountered in Windows terminals — particularly important when working with international characters in BibTeX.

\---

\## 📄 License

This project is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.

✅ You are free to share, remix, adapt, and build upon this work — even for commercial purposes — as long as appropriate credit is given.

\---

\## 📄 BibTeX Citation

You can copy the following and save it as a \`.bib\` file (e.g., \`siftpm.bib\`):

\`\`\`bibtex

@misc{siftpm2025,

author = {Joshua J. Podmore and Moein Radman and Silke Paulmann and Riccardo Poli and Ian Daly},

title = {SIFT-PM: Systematic Incorporation and Filtering Tool for PubMed},

year = {2025},

howpublished = {\\url{<https://github.com/JoshPod93/Sift-PM}}>,

note = {Python-based toolkit for efficient PubMed citation aggregation, filtering, and deduplication for systematic reviews},

}

\## 📄 Vancouver Citation

Podmore JJ, Radman M, Paulmann S, Poli R, Daly I.

SIFT-PM: Systematic Incorporation and Filtering Tool for PubMed \[Internet\]. 2025. Available from: <https://github.com/JoshPod93/Sift-PM>

## Credits

This project uses and depends on several excellent open-source tools and libraries. Special thanks to the developers and maintainers of these projects:

- **pubmed-bib** by [Zhucheng Huang](https://github.com/zhuchcn/pubmed-bib)  
  A handy tool for retrieving BibTeX citations from PubMed IDs.  
  🔗 https://github.com/zhuchcn/pubmed-bib

- Other dependencies are listed in the [requirements.txt](./requirements.txt) file.

We appreciate the open-source community for providing these valuable resources!
