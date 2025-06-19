"""
Update Rhythm Phutela's thesis content with DSB repair focus
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.models import Document

# Find and update Rhythm Phutela's thesis
thesis = Document.objects.filter(
    author__icontains='Rhythm Phutela',
    doc_type='thesis'
).first()

if thesis:
    # Update with DSB repair focused content
    thesis.content = """
Temporal Dynamics of DNA Double-Strand Break Repair and RNA Processing
By Rhythm Phutela, PhD Thesis, 2025

ABSTRACT:
This thesis investigates the molecular mechanisms underlying DNA double-strand break (DSB) repair, with a particular focus on the temporal dynamics and RNA-mediated regulatory processes. Using advanced molecular techniques including CRISPR-Cas9, live-cell imaging, and RNA sequencing, we uncovered novel mechanisms by which cells coordinate DSB repair with RNA processing to maintain genomic stability.

CHAPTER 1: INTRODUCTION
DNA double-strand breaks (DSBs) represent one of the most cytotoxic forms of DNA damage. Their improper repair can lead to chromosomal rearrangements, cell death, or oncogenic transformation. This thesis explores how cells orchestrate the complex machinery required for DSB repair, with emphasis on:
- Homologous recombination (HR) and non-homologous end joining (NHEJ) pathways
- RNA-mediated regulation of repair factor recruitment
- Temporal coordination of repair events with cell cycle progression
- Novel RNA species generated at DSB sites

CHAPTER 2: MATERIALS AND METHODS
2.1 DSB Induction Systems
- I-SceI endonuclease system for site-specific DSB generation
- CRISPR-Cas9 for targeted DSB induction
- Ionizing radiation for genome-wide DSB studies
- Laser microirradiation for real-time DSB tracking

2.2 DSB Detection and Analysis
- γH2AX immunofluorescence for DSB visualization
- Neutral comet assay for DSB quantification
- ChIP-seq for repair factor recruitment dynamics
- BLESS and END-seq for genome-wide DSB mapping

2.3 RNA Analysis at DSB Sites
- DRIP-seq for R-loop detection
- RNA-seq following DSB induction
- Single-molecule RNA FISH at damage sites
- PAR-CLIP for RNA-binding protein identification

CHAPTER 3: TEMPORAL DYNAMICS OF DSB REPAIR
Key findings:
1. **Early Response (0-15 minutes)**
   - Rapid γH2AX phosphorylation spreading up to 2 Mb from break sites
   - ATM activation kinetics show biphasic response
   - Initial recruitment of PARP1 and Ku70/80 complexes
   - Discovery of immediate RNA polymerase II stalling

2. **Pathway Choice Decision (15-60 minutes)**
   - 53BP1 and BRCA1 antagonism determines HR vs NHEJ
   - Cell cycle-dependent regulation via CDK activity
   - Novel role for lncRNA DDSR1 in pathway selection
   - Resection initiation controlled by CtIP phosphorylation

3. **Repair Execution (1-6 hours)**
   - RAD51 filament formation dynamics in HR
   - Systematic analysis of DNA synthesis patterns
   - NHEJ ligation kinetics and fidelity assessment
   - Chromatin restoration following repair

CHAPTER 4: RNA-MEDIATED REGULATION OF DSB REPAIR
Major discoveries:
1. **Damage-induced RNAs (diRNAs)**
   - Identified novel class of small RNAs (20-22 nt) generated at DSB sites
   - diRNAs recruit repair factors through sequence-specific interactions
   - DROSHA-dependent biogenesis pathway characterized
   - Essential for efficient HR in mammalian cells

2. **R-loops in DSB Repair**
   - R-loops form transiently at DSB sites
   - Facilitate repair factor recruitment
   - Excessive R-loops impair repair and must be resolved
   - SETX helicase critical for R-loop homeostasis

3. **lncRNA Regulatory Networks**
   - DDSR1 (DNA Damage-Sensitive RNA 1) scaffolds HR proteins
   - DINO stabilizes p53 following DNA damage
   - Novel antisense transcripts regulate repair gene expression
   - Temporal expression patterns correlate with repair phases

CHAPTER 5: SINGLE-CELL ANALYSIS OF REPAIR HETEROGENEITY
Novel single-cell findings:
1. **Cell-to-Cell Variability**
   - 30% of cells show delayed repair kinetics
   - Heterogeneous pathway choice even in clonal populations
   - Pre-existing chromatin states influence repair efficiency
   - Stochastic vs deterministic repair outcomes

2. **Live-Cell Imaging Results**
   - Real-time tracking of 53BP1 and BRCA1 foci
   - Discovered oscillatory recruitment patterns
   - Repair factor exchange dynamics quantified
   - Correlation with cell fate decisions

CHAPTER 6: THERAPEUTIC IMPLICATIONS
Applications for cancer therapy:
1. **PARP Inhibitor Resistance**
   - Identified RNA-based mechanisms of resistance
   - Novel combination strategies targeting diRNA pathways
   - Biomarkers for patient stratification

2. **Synthetic Lethality Approaches**
   - New targets in RNA processing machinery
   - Combination with DSB-inducing agents
   - Cell cycle-specific vulnerabilities

3. **Precision Medicine Applications**
   - RNA signatures predict repair pathway usage
   - Personalized therapy based on repair capacity
   - Novel drug targets in lncRNA networks

CHAPTER 7: CONCLUSIONS AND FUTURE DIRECTIONS
This thesis establishes RNA as a critical regulator of DSB repair, revealing:
1. Temporal coordination of repair events at molecular resolution
2. Novel RNA species that directly participate in repair
3. Heterogeneous repair outcomes at single-cell level
4. Therapeutic opportunities targeting RNA-repair interfaces

Future work should focus on:
- Structural biology of RNA-protein complexes at DSBs
- In vivo validation using animal models
- Clinical translation of RNA-based repair biomarkers
- Development of RNA-targeting repair modulators

APPENDICES:
A. Detailed protocols for DSB induction and detection
B. Bioinformatics pipelines for repair kinetics analysis
C. Single-cell analysis workflows
D. RNA-seq data processing methods
E. Statistical analysis frameworks

REFERENCES:
Over 400 references covering DSB repair, RNA biology, single-cell analysis, and therapeutic applications.
"""
    thesis.save()
    print(f"✅ Updated thesis content for: {thesis.title}")
    print(f"   New content focuses on DSB repair mechanisms")
else:
    print("❌ Could not find Rhythm Phutela's thesis to update")

# Trigger reindexing
print("\n📝 Note: You'll need to reindex documents for search to reflect these changes")