# Lessons Learned — 10.1007-s11433-024-2478-8

## What worked well

- **Self-validating reproduction via the paper's own claim.** The paper gives
  fully-specified waveform coefficients *and* a quantitative claim (gate error
  < 10⁻⁴). Plugging the coefficients into an independently-built Hamiltonian and
  checking the claim is a falsifiable test: a wrong model cannot hit < 10⁻⁴ from
  the paper's own numbers. This turned "did we get the physics right?" into a
  one-number check.
- **Product basis instead of transcribing a reduced Hamiltonian.** The paper's
  three-body H (eq. a4) is written in an OCR-hostile Morris–Shore reduced form.
  Building the full product-basis Hamiltonian from local driving rules + Förster
  couplings was less error-prone, and its equivalence was then *proved* two ways:
  symbolically (√2 symmetric couplings, antisymmetric dark states) and
  numerically (a verbatim 6-state transcription agrees to < 1e-8). That
  cross-check is what let the formula gate move from `reconstructed` to `verified`.
- **Axis-tick digitization for pixel-level scoring.** Detecting axis frames and
  tick pixel positions, then calibrating pixel→data linearly, gave clean
  curve digitization (waveform plateaus and known minima matched to < 0.6% of
  axis range), which upgraded the comparison from `visual_feature_contract` to
  `digitized_curve` and the case to complete reproduction.

## Pitfalls / pain points

- **`cd` inside a compound Bash command moved the persistent working directory**
  and later `agent/...` paths failed. Use absolute paths or avoid `cd` in
  compound commands.
- **Figure numbering mismatch in the source text.** The prose says "Fig. 3(c)"
  for what the figure caption labels panel (d). Recorded the mapping in PAPER_MAP
  rather than trusting either verbatim.
- **Phase-panel digitization blows up at 2π wraps.** Circular pointwise error
  spikes to ~π at the single column where the paper curve jumps; report RMS with
  the jump columns flagged rather than treating it as a physics mismatch.
- **Twin-axis panels need separate calibration** for the left (Rabi) and right
  (detuning) axes; using one axis for both curve families corrupts the detuning
  digitization.

## For future reproductions

- For any paper that publishes explicit control waveforms + a scalar
  fidelity/error claim, treat the claim as the primary acceptance gate before
  worrying about figure matching.
- When a Hamiltonian is given in a symmetry-reduced form, reconstruct in the full
  product basis and cross-validate against the reduced form; keep both.

## New Failure Modes

- **Digitizing a wrapped-phase curve at its 2π discontinuity** produces a
  spurious ~π pointwise error at the single jump column; treat it as a
  digitization artifact, not a physics mismatch, and report RMS with jump columns
  flagged.
- **`cd` inside a compound Bash command** silently moved the persistent working
  directory and broke later relative `agent/...` paths.

## Reusable Checks Or Tools

- `src/digitize.py` — raster-figure digitizer: axis-frame + tick detection ->
  linear pixel→data calibration -> colour-segmentation curve extraction, with
  twin-axis support. Domain-neutral core is proposed for promotion into
  `PRAgent-workflow/` (see HARNESS_BACKLOG).
- Product-basis vs verbatim Morris–Shore cross-validation
  (`tests/test_product_and_bright_sector11_agree`) as a pattern for verifying a
  symmetry-reduced Hamiltonian.

## Two-photon extension (Fig. 4/5/6) — what worked and what didn't

- **Reduced-form + ladder replacement is the clean way to build a two-photon
  many-body model.** Appendix eqs. (a5)/(a6) state the two-photon Hamiltonian is
  the single-photon (a4) with every |1><->|r> coupling replaced by a |1><->|e><->|r|
  ladder. Building a per-atom {|1>,|e>,|r>,|q>} tensor product with the (a4)
  interaction reproduced Fig. 4 hybrid populations to <0.4% RMS.
- **Adiabatic elimination was worse than the full model here** (1.9e-2 vs 1.3e-3)
  because Omega_p/2Delta_0 ~ 0.32 is not small — the intermediate state is
  transiently populated. Do not shortcut a two-photon gate with an effective
  two-level model when this ratio is not << 1; simulate the full ladder.
- **Honest error gap:** the paper reports <1e-4 for the two-photon gates but the
  faithful full-3-level model gives ~1e-3 with the published waveforms. The most
  likely explanation is that the waveforms were optimised in the paper's own
  (reduced/effective) model. Reproduce the figure (curves) and report the
  full-model error as the honest number rather than forcing <1e-4.
- **Doppler dual-pulse cancellation is cheap to demonstrate rigorously:** apply
  the pulse twice with the Doppler detuning sign flipped and compare the
  end-of-gate phase deviation to the un-flipped (single-direction) pulse; the
  ratio (~1e-4) IS the first-order cancellation.
- **Know when to stop:** Fig. 6 (three-qubit Toffoli) needs a multi-qubit buffer
  geometry the paper does not specify; the best-guess star geometry gave 11%
  leakage in the 256-state sector. With a 175 s/run feedback loop and no ground
  truth but the figure, guessing geometries is not worth it — report it as
  underspecified rather than force a match. Figs. a6-a8 have no listed
  coefficients and are simply not reproducible.
