# Method Trace

## METHOD001 — released-data reconstruction (reference only)

- **Source:** Zenodo `10.5281/zenodo.21791682` and manuscript Figures 8–9.
- **Role:** establish the paper's exact plotted values and caption-level
  acceptance criteria before any independent calculation.
- **Inputs:** the immutable release's 67 optimizer studies.
- **Algorithm:** checksum the ZIP, parse records, recompute `1+2m+r` and the
  convert/full gap, and redraw the figures.
- **Status:** complete. This evidence is labelled `author_data_validated` and is
  retained only as the post-hoc reference.

## METHOD002 — clean-room circuit-to-tree reimplementation

- **Source:** the paper's pass/ride/merge definitions, Eq. (8), NNI move
  description, and raw qsim / structured circuit inputs in the Zenodo release.
- **Role:** test Figures 8–9 without executing or translating the authors'
  `yao-rs`, `omeinsum-rs`, or `omeco` implementation.
- **Core model:** a closed binary-index tensor hypergraph and a binary
  contraction tree. A step of volume `v` costs `v`, `2v`, or `3v` when it is a
  pass, ride, or merge. The two objectives are `V(T)=Σv` and
  `C(T)=Σ factor·v`.
- **Circuit lowering:** raw qsim text for 12 random circuits; raw circuit JSON
  plus observable text for 55 structured circuits. Diagonal circuit gates
  share wire labels; expectation operators explicitly separate ket and bra.
- **Tree initialization:** `cotengra==0.7.5`, an unrelated generic tensor-network
  package, receives only index sets and dimension 2. Ten candidate trees are
  generated and subtree-reconfigured. The same candidate pool is independently
  scored by `V` and `C`.
- **Tree optimization:** case-local Python NNI simulated annealing, 600,000
  moves at `T: 1→0.005`; low-temperature polish uses 60,000 moves at
  `T: 0.02→0.0002`; seed 42. Accepted moves update only the two affected
  internal nodes.
- **Outputs:** one JSON record per circuit, including integer volumes, `(m,r)`,
  all three pipeline values, annealing traces, and complete final tree records
  with SHA-256.
- **Checks:** 67/67 raw-lowered networks match the published network topology
  and green labels post hoc; cotengra FLOPs equal the independent skeleton
  evaluator as integers; the exact dynamic-programming oracle covers tiny
  networks; repeated seeded runs produce identical tree hashes.
- **Status:** complete. All 67 deterministic records are finalized in
  `outputs/data/independent_python_full/`; aggregate per-circuit runtime is
  1,755.996 seconds.
- **Integrity boundary:** published networks are used only in a post-hoc parser
  test. Published contraction trees, optimizer studies, and numeric results are
  never inputs to METHOD002.

### METHOD002 result

- Figure 8: passed, maximum cost-law residual `4.44e-16`.
- Figure 9: partial, 57/67 circuits below `5e-4` versus 66/67 in the paper.
- Primary input audit: 122 raw circuit/observable payloads and zero author
  result, network, plan, or study payloads.

## METHOD003 — optional A100 portability benchmark

- **Role:** measure execution portability after numerical tree validation.
- **Status:** optional extension. Figures 8–9 are CPU-side tree-cost figures and
  do not require the A100. A100 timings would not be an exact reproduction of
  the paper's Ascend 910/A800 timings.

## METHOD004 — independent optimizer-complexity audit

- **Source:** Appendix independent-audit definitions and Table 5, including
  the loop-volume convention for time, space, and read-write complexity and the
  stated `kappa` comparison.
- **Role:** generate every Table 5 row from raw circuits and independently
  optimized trees, without consuming author trees, author result arrays,
  digitized values, or source pixels.
- **Required implementation:** accumulate `tc_R`, `sc_R`, `rwc_R`,
  `Delta tc`, `Delta tc` excess, and `rwc_R-rwc_C` for all twelve random
  circuits, then verify each row with a second calculation path before the
  paper table is opened for comparison.
- **Status:** declared but not implemented. This is an internal method gap, not
  a compute or publication-input blocker; T012 remains uncovered until code,
  generated data, and checks exist.
