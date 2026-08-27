# Method Trace

## Method Cards

### METHOD001 — Exact loss-aware maximum-likelihood decoding

- Source: main text after Fig. 2 and Appendix B.1.
- Role: scientific reference definition.
- Inputs: measured detector syndrome, SSR loss flags, circuit, Pauli/loss model.
- Output: most likely logical correction conditioned on syndrome and losses.
- Algorithm steps: enumerate compatible Pauli errors and all compatible loss
  locations; cancel gates after each loss; calculate the joint likelihood;
  select the most likely logical equivalence class.
- Parameters: full circuit, gate-level noise, code distance, SE schedule.
- Code pointer: no author implementation is used; the bounded clean-room
  discriminator is `src/implementation_campaign.py`.
- Checks: source trace complete; complexity grows combinatorially with multiple
  losses.
- Status: method traced and independently attempted; the paper-scale target was
  not reproduced at the current clean-room system-capability boundary.
- Open questions: exact MLE package revision, circuit-builder source, sample
  counts, seeds, and tie-breaking policy.

### METHOD002 — Independent-lifecycle approximate MLE

- Source: main text decoder equation; Appendix B.2 and Fig. 9.
- Role: method used for the paper's production results.
- Inputs: one detector-error model per observed lossy lifecycle, lossless Pauli
  model, optional first-combination model.
- Output: combined decoding hypergraph.
- Algorithm steps: trace each loss independently; enumerate its possible times;
  build and probability-weight detector hyperedges; sum lifecycle models and the
  Pauli model; decode with MLE (primarily) or MWPM.
- Parameters: main-text `omega=0`; loss-location prior derived from the circuit.
- Code pointer: `src/delayed_erasure_proxy.py` implements the same
  information hierarchy in a repetition-code analogue.
- Checks: delayed information must never perform worse than ignoring a correct
  SSR flag in the noiseless-partner limit; fixed seed makes the Monte Carlo
  reproducible.
- Status: method gate open for a proxy mechanism test; the surface-code target
  was independently attempted and not reproduced at the current capability
  boundary.
- Open questions: author Stim annotations, hyperedge merge rules, correlated MLE
  decoder version, and handling of zero-probability edges.

### METHOD003 — Threshold and effective-distance extraction

- Source: main text around Fig. 3(e-g), Appendix F/H.
- Role: turns circuit-level logical-error samples into paper observables.
- Inputs: distances 3, 5, 7, 9; physical error grid; noiseless initialization;
  `d-1` noisy checks; final noiseless transversal measurement.
- Outputs: crossing threshold, far-below-threshold exponent `d_e`, distance fit,
  and space-time overhead at `P_L=10^-12` and `p=0.5%`.
- Algorithm steps: run Monte Carlo, fit finite-size crossings, fit
  `P_L=alpha p^beta`, then fit distance dependence.
- Parameters: error Models A/B/C and each SE schedule.
- Code pointer: `src/implementation_campaign.py` records the bounded
  clean-room paper-scale discriminator; a full circuit-level implementation is
  an optional future capability expansion.
- Checks: Pauli endpoint `d_e=(d+1)/2`; erasure endpoint `d_e=d`.
- Status: traced and independently attempted; the paper-scale target was not
  reproduced at the current clean-room system-capability boundary.
- Open questions: shots per point, confidence-interval method, physical-error
  grids, excluded fit points, seeds, and decoder stopping rules.
