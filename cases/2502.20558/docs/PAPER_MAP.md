# Paper Map

## Identity

- Paper ID: `2502.20558`
- Preprint: Gefen Baranes *et al.*, “Leveraging Qubit Loss Detection in
  Fault-Tolerant Quantum Algorithms,” arXiv:2502.20558v3 (2026), 26 pages,
  27 figures.
- Formal publication: *Physical Review X* **16**, 011002 (2026).
- DOI: `10.1103/ycwc-3myc`.
- Local publisher PDF: `raw/paper.pdf`.
- Local arXiv source: `paper-source/main.tex` plus 27 vector figure assets.
- Data/code status: the source archive contains no simulation code or raw
  numerical data; the paper states that data are available from the authors
  on reasonable request.

## Reproduction Goal

Reconstruct the paper's causal chain from detected loss to decoding and logical
performance. The case independently recomputes every result determined by
printed equations or combinatorial counting, runs a transparent distance-five
repetition-code analogue of delayed-erasure decoding as a mechanism test, and
records the current clean-room system-capability boundary for every
circuit-level surface-code panel that the bounded implementation campaign did
not reproduce.

Source figure renders are comparison references only. They never feed generated
data and never count as scientific reproduction.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Problem and contribution | Loss becomes a delayed erasure; deep logical circuits amplify lifecycle effects. |
| Detecting and decoding delayed erasures | Core decoder | Rebuild the detector-error hypergraph for each possible loss time, then combine lifecycle contributions. |
| Loss-detecting SE techniques | Architecture comparison | Conventional, SWAP, teleportation-based, and direct-conversion SE. |
| Predicting performance by error counting | Reduced model | Threshold axes are linked to lifecycle length and entangling-gate count. |
| Deep logical algorithms | Algorithm-level consequence | Studies optimal SE frequency and native loss detection through gate teleportation. |
| Appendices A-B | Syndrome and MLE details | Exact and approximate decoding constructions; combination-weight test. |
| Appendices C-F | SE circuits and noise models | Lifecycle counting, Table I, and circuit-level simulation definitions. |
| Appendix G | Algorithm procedures | Explicit lifecycle counts for GHZ, 15-to-1 distillation, H/T synthesis, and adders. |
| Appendix H | Extra numerical results | Threshold, effective-distance, bias, and deep-memory sweeps. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main text after Fig. 2; Appendix B | Approximate delayed-erasure decoding hypergraph | verified |
| EQ002 | Main text Sec. III | Loss fraction definition | verified |
| EQ003 | Appendix F, Error Model A | Normalized loss/biased-Pauli channel | verified |
| EQ004 | Main text below Fig. 4 | Loss-Pauli phase-boundary interpolation | verified |
| EQ005 | Main text below Fig. 3(f) | Effective-distance power law | verified |
| EQ006 | Appendix C and Fig. 14/16 | Surface-code lifecycle counting | reconstructed and checked |
| EQ007 | Appendix G | Algorithmic lifecycle counts | independently rederived and verified |
| EQ008 | Appendix C | Accumulated SWAP movement error | verified |
| EQ009 | Appendix F, Error Model B | Error-channel normalization | normalization verified; publication definition externally blocked by mutually inconsistent source statements |
| EQ010 | Appendix A | Maximum logical-error bound | verified |
| METHOD001 | Main text/Appendix B | Exact MLE conditioning on syndrome and loss events | traced; bounded clean-room implementation campaign did not reproduce the paper-scale result |
| METHOD002 | Main text/Appendix B | Independent-lifecycle approximate MLE | traced; method-level implementation plus proxy test, but paper-scale result not reproduced |
| METHOD003 | Main text/Appendix F | Surface-code threshold/effective-distance estimation | traced; bounded clean-room implementation campaign reached the current system-capability limit |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Fig. 1 | Loss errors in logical circuits | schematic_context | Context only. |
| Fig. 2(a,b) | Delayed-erasure decoder and memory benchmark | mixed | Panel (b) is numeric; distance 5, 1% loss. |
| Fig. 3(a-g) | SE methods and performance | mixed | Panels (d-g) are numeric. |
| Fig. 4(a,b) | Threshold phase diagram and lifecycle relation | numeric_reproduction | Panel (b)'s printed analytic trend is reproducible. |
| Fig. 5(a-c) | Random Clifford circuit SE frequency | mixed | Panels (b,c) are numeric. |
| Fig. 6(a,b) | Teleportation and algorithm lifecycles | mixed | Panel (b) follows explicit Appendix-G counts. |
| Fig. 7(a,b) | Teleported-gate circuit benchmark | mixed | Panel (b) is numeric. |
| Figs. 8-9 | Loss syndrome and approximate decoder | algorithm_trace | No numeric target. |
| Figs. 10-12 | Combination weight and biased-noise thresholds | numeric_reproduction | Raw sweeps unavailable. |
| Fig. 13 | SWAP SE identity | schematic_context | No numeric target. |
| Fig. 14(a-c) | SWAP period lifecycle analysis | mixed | Panel (c) has an independently countable invariant. |
| Figs. 15-16 | SWAP period and conventional comparison | numeric_reproduction | Fig. 16(a) has an analytic lifecycle component. |
| Figs. 17-21 | Cluster/Steane relations, noise sphere, algorithms | schematic_context | Fig. 21 supports Fig. 6(b)'s counting. |
| Table I | SE lifecycle, overhead, thresholds, effective distance | mixed | Analytic rows are exact; simulation rows were attempted independently and not reproduced at the current system-capability boundary. |
| Figs. 22-26 | Additional memory/threshold/effective-distance data | numeric_reproduction | Independently attempted; not reproduced at the current system-capability boundary. |
| Fig. 27 | Random circuit scheduling illustration | schematic_context | No numeric target. |

## Assumptions

- “Lifecycle length” counts noisy entangling-gate locations from initialization
  to loss-detecting measurement; noiseless boundary operations are excluded.
- The rotated planar surface-code interaction count is
  `N_CZ = 4 d (d-1)` per full stabilizer round.
- The local proxy uses the paper's distance and per-opportunity loss probability
  but is a classical repetition-code analogue, not a surface-code replacement.
- The paper's plotted vectors are used for visual comparison only; no curve is
  digitized into generated outputs.
