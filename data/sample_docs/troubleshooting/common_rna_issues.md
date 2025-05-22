# Common RNA-Workflow Issues & Quick Fixes

| Symptom | Probable Cause | Quick Check | Recommended Fix |
|---------|---------------|-------------|-----------------|
| **A260/230 < 1.5 after extraction** | Phenol or guanidine carry-over | Verify Trizol phase separation timing | Repeat chloroform extraction; add additional 70 % EtOH wash |
| **RNA smearing on agarose gel** | Degradation by RNase | RNase-free tips? Gloves? | Use RNase-Zap on bench; add RNase inhibitor (40 U/mL) to lysis buffer |
| **Low IVT yield (< 1 µg/µL)** | Mg²⁺ depleted or NTPs old | Check MgCl₂ pH; run control reaction | Titrate MgCl₂ 6–10 mM; prepare fresh 25 mM NTP mix |
| **Cas13 knock-down efficiency < 40 %** | Mis-folded crRNA | Heat-shock refold protocol applied? | Denature crRNA 65 °C 5 min → snap-cool on ice; test new guide design |
| **qPCR ΔCt very high (> 3)** | Reverse-transcription inefficient | cDNA synthesis temp/time | Increase RT to 50 °C 15 min; switch to SuperScript IV |
| **Unexpected bands in PCR of sgRNA template** | Primer-dimer or genomic DNA | No-template control result? | Add DMSO 3 %; treat template with DNase I |
| **Nanodrop ratio OK but Bioanalyzer RIN < 7** | Shearing during vortex | Vortex step in protocol? | Use gentle flick instead of vortex; chill all tubes |
| **Colony PCR negative for insert** | sgRNA cassette unstable in bacteria | Strain used? | Transform into E. coli Stbl3; incubate at 30 °C |
| **Capillary electrophoresis shows double-peak crRNA** | Incomplete CIP treatment | CIP batch age? | Repeat with fresh CIP 37 °C 30 min; verify dephosphorylation |
| **RNA pellet invisible after isopropanol precip.** | Low starting material | Glycogen added? | Add 1 µL GlycoBlue; extend −20 °C precipitation to 2 h |
