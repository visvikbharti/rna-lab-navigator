# Week 22, 2025 Progress Report
## May 26 - June 1, 2025

### RNA Lab Navigator Project
**Goal:** Complete implementation of RAG system for Dr. Chakraborty's RNA biology lab

**Progress:**
- **Completed full RAG System implementation** with multi-model AI platform vision
- **Fixed critical frontend issues** - resolved blank page rendering and navigation problems
- **Documented session context** for project continuity and next steps
- System architecture includes Django backend, React frontend, Weaviate vector DB, and OpenAI GPT-4o integration
- Current status: Core functionality ready, pending final deployment and user testing

**Technical Achievements:**
- Implemented hybrid search (vector + BM25) with HNSW indexing
- Configured chunking strategy (400±50 words with 100-word overlap)
- Set up Celery for async document processing
- Created comprehensive documentation for deployment readiness

### Research Proposal Rebuttal Preparation
**Context:** Prepared rebuttal for BFI proposal by Prof. Souvik Maiti on Class IIB CRISPR systems

**Work Completed:**
- Reviewed original proposal: "Proposal_ClassIIB CRISPR_SM.docx"
- Analyzed reviewer comments from "BFI_IGIB_3_25 _ Prof Souvik Maiti.pdf"
- Drafted comprehensive rebuttal addressing reviewer concerns
- Created final version: "Final_Rebuttle_BFI_Prof_Souvik_Maiti.docx"
- Key focus areas: Technical feasibility, experimental design clarifications, and budget justifications

### CRISPR Nuclease Comparative Analysis
**Objective:** Systematic comparison of SpCas9, FnCas9, and FnCas12a nucleases

**Bioinformatics Pipeline Development:**
- Created Snakemake workflows for automated pairwise comparisons
- Implemented comprehensive analysis covering:
  - PAM sequence preferences
  - Cutting efficiency profiles
  - Off-target prediction algorithms
  - Structural alignment and comparison
- Generated comparison matrices for all three nuclease pairs:
  - SpCas9 vs FnCas9
  - SpCas9 vs FnCas12a  
  - FnCas9 vs FnCas12a
- Prepared PyMOL visualization commands for structural presentations

**Key Outputs:**
- Analysis summary documents for each comparison
- Technical Q&A documentation for presentation preparation
- Comprehensive results interpretation guide

### Time Allocation Summary
- RNA Lab Navigator: 45%
- Rebuttal Preparation: 25%
- CRISPR Analysis: 25%
- Documentation/Reporting: 5%

### Challenges Encountered
1. Frontend routing issues in RNA Lab Navigator required deep debugging
2. Balancing multiple deadlines across different projects
3. Ensuring comprehensive analysis coverage for CRISPR comparison

### Next Week's Priorities
1. Deploy RNA Lab Navigator to production environment
2. Submit finalized rebuttal document
3. Present CRISPR nuclease comparison findings
4. Begin user onboarding for RNA Lab Navigator system

### PI Feedback Section
[To be filled during weekly meeting]

---
*Report prepared: June 2, 2025*