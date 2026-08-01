# Reproduction note

We independently reproduced every theory-numerical panel of *Enhancing
Nonreciprocity through Squeezing-Induced Symmetry Breaking* (PRL 136, 253602,
2026): 23 panels grouped into ten executable targets. The implementation starts
from the paper's Bogoliubov coupling, closed Gaussian moment equations,
steady-state energies, passive-energy invariant, and scattering matrix. It does
not digitize or reuse source curves.

Four scientific claims are verified. The symmetry-breaking enhancement,
battery energy and ergotropy growth, optimal-coupling structure, and
unidirectional transmission all follow from independent calculations. Eight
target bundles are fully reproduced. Figure 4 remains partial because the open
Zenodo transmission arrays belong to an earlier manuscript and peak near 10.07,
whereas the final formula peaks at 27.31.

We also found a semantics error in Figure S3. Its axis is printed as absolute
energy `E_i^ss/omega_b`, yet all nine curves start at one. EQ002 gives absolute
baselines 1.5242, 1.0412, and 0.1176 at the three couplings, so they cannot all
produce that intercept. Normalizing by each formula-derived nonsqueezed
baseline gives `E_i^ss/E^ss` curves whose unit intercepts and visible endpoints
agree. The public figure therefore corrects the label and the NPZ retains both
observables. The source image was used only for post-generation adjudication.

The most important result is a negative one. The printed model is quadratic
with linear jumps, so its Gaussian dynamics are exact. For Supplementary Figure
S1(d), that solution peaks at 59.97. A finite Fock cutoff of 10 peaks at 3.75
and visually matches the published scale near 4, but it imposes an occupation
ceiling of 9. The supplement does not disclose its cutoff or convergence study.
We therefore reproduce the qualitative detuning regime while rejecting the
published panel as a converged quantitative result.

The public author arrays are CC BY 4.0 comparison evidence. They are loaded only
after generated curves exist. Scientific visual fidelity is 90.31; the separate
presentation diagnostic is 66.23 and contributes no scientific credit.
Completion is based on derivations, independent execution, invariants, and
explicit discrepancy attribution rather than layout resemblance.
