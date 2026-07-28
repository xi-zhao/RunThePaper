# arXiv:2607.02157 reproduction note

## Paper identity

- Preprint: [arXiv:2607.02157v1](https://arxiv.org/abs/2607.02157) — *Thermodynamics of Quantum Reservoir Computing*.
- No journal publication recorded at the time of reproduction.
- Reproduced from the manuscript alone: no author code or data was used.

## Scientific object

The paper treats a driven open quantum reservoir as a physical, out-of-equilibrium
computer and asks what information processing costs thermodynamically. It defines
two conditional operational states — a memory state (conditioned on the present
input) and a predictive state (conditioned on the next target) — and from them the
Holevo memory and predictive capacities, a coherence decomposition
`chi = I + C` into classical mutual information and ensemble coherence, and an
injection/relaxation work bookkeeping that yields a generalized Landauer bound.
The central result is an exact identity between the irreversible driving work and
the quantum information dissipation, `beta W^irr = chi^d` (Eq. 13), and the claim
that both peak inside quantum critical regions, where the forecasting error (NMSE)
is simultaneously minimized.

Two reservoir architectures are studied: a fully connected disordered
transverse-field Ising model (TFIM) and an augmented cluster model tuned across a
symmetry-protected topological transition.

## Reproduced results

All three numerical figures were computed independently, but their evidence
stages differ. Fig. 2 and Fig. S2 use the completed paper-scale A100 campaign
(5000 sequences per parameter point, 100 TFIM disorder realizations, and the
full `4^6-1` Pauli readout) and are final reproductions. Fig. S1 uses 400 drive
sequences, 2500 samples, and 400 TFIM realizations, so it remains exploratory.
The weighted score is **77.27/100**.

- **Fig. 2 (cluster row):** near-quantitative. Memory-capacity peak 2.19 at
  alpha = 0.5 (paper ~2.25), endpoints 1.68 / 1.10, generalized Landauer peak
  0.499 (paper ~0.52), predictive coherence exceeding memory coherence at the
  peak.
- **Fig. 2 (TFIM row):** the single-peak capacity shape (peak 1.80 ± 0.11 over
  100 disorder realizations near J ~ 2), the left plateau 1.335, and the b1
  signature — the widening gray gap where `beta W^irr` plateaus while `chi^d`
  collapses in the deep paramagnet.
- **Central identity:** `beta W^irr = chi^d` holds at machine precision
  (max residual ≤ 5.7e-14) across all ~3000 production runs — the strongest
  internal check the framework admits.
- **NMSE:** the forecasting-error minimum sits at the capacity peak for both
  models (cluster minimum 6.5e-4 at alpha = 0.45; TFIM minimum at J = 2.37).
- **Fig. S1 (exploratory):** the resonance peak at 0.355 agrees with the
  paper's ~0.36 and the cluster spectral fingerprints match, but its statistical
  ensembles are smaller than the paper's.
- **Retained diagnostic mismatch:** the TFIM irreversible-work peak in
  Fig. 2b1 is 0.396 versus a visual paper reading near 0.49. Its location,
  Landauer bound, and large-J plateau pass, so the amplitude difference is
  recorded rather than hidden by widening the tolerance.

**Difference reason (TFIM peak, ~1.80 vs ~2.0):** an aggregation-convention
question the manuscript leaves open. We adjudicated it directly at the peak:
computing capacities per disorder realization and then averaging gives 2.08
(consistent with the paper), while pooling all realizations into one mixed
ensemble before taking entropies gives 15.6 — physically absurd. The paper did
not pool; the per-realization convention we used is correct, and the residual
peak difference is within sampling and figure-reading uncertainty.

**Observation beyond the published resolution:** in the deep-MBL tail (J ≳ 10),
where the published curves are visually degenerate, the multi-step memory
capacity *grows* with delay rather than decaying, and ~28% of disorder
realizations fully decouple from the drive. This persists at the paper's full
ensemble size, so it is not a small-sample artifact.

## Run the public package

```bash
# reproduce the Fig. 2 scans (both models), then the figures
python code/scripts/run_scan.py --model cluster --n-seq 5000 --n-points 21
python code/scripts/run_scan.py --model tfim --n-seq 5000 --n-points 25 --realizations 100
python code/scripts/plot_figures.py

# verify the formula/identity checks
python code/scripts/verify_formulas.py

# adjudicate the disorder-ensemble aggregation convention
python code/scripts/adjudicate_pooling.py
```

The paper-exact Fig. 2/Fig. S2 ensembles were produced on a single A100-class
GPU (`qrc_gpu.py --cupy-eig`) in about two days; Fig. S1 was not part of that
campaign. Promoting it requires 5000 x 5000 drive statistics and 10000 TFIM
disorder realizations.

## Reproduction boundary

- Scoring is capped at 80 (feature-level): the paper publishes no numerical
  data, so agreement is verified against the published panels rather than
  author data, and we decline to digitize the figures (pixel-derived agreement
  is not scientific reproduction).
- Fig. S1 remains exploratory and must not be presented as a final
  paper-scale result alongside Fig. 2 and Fig. S2.
- Three conventions the manuscript leaves unspecified were resolved and are
  documented as questions for the authors: the Mackey–Glass affine
  normalization, the open vs. periodic boundary of the augmented cluster chain
  (open boundaries are required to match the asymmetric Fig. 2), and the
  `F(omega)` spectral normalization in Fig. S1a.
- The source paper PDF and any digitized reference curves are intentionally not
  redistributed here.
