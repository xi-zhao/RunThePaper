# Numerical Methods

## NUM001 — Exact-point algebra and zero-mode controls

- Targets: V001.
- Dependencies: EQC001–EQC007, EQC011; METHOD001–METHOD002.
- Calculation: compare the two-site bond with the projector identity; enumerate
  all \(w\) sectors for small even \(N\); count zero modes at
  \(\theta=\pi/4\).
- Acceptance: projector idempotency and matrix error below \(10^{-12}\);
  total nullity \(2^N+1\); only the uniform-\(-\) sector has two zero modes;
  selected MPS energy below \(10^{-11}\).

## NUM002 — Phase and product-state controls

- Target: V002.
- Dependencies: EQC002, EQC003, EQC010; METHOD001.
- Calculation: exact energies of alternating \(|x\rangle|y\rangle\) states,
  the uniform \(|z\rangle\) state, and small-\(N\) sector ground energies.
- Acceptance: zero energy in \(\pi/4\le\theta\le3\pi/4\); \(-N\) at
  \(3\pi/2\); mirror symmetry under \(\theta\leftrightarrow\pi-\theta\).

## NUM003 — Main Fig. 5(a), ground-state overlap

- Target: T001.
- Dependencies: EQC001, EQC002, EQC006–EQC008; METHOD001–METHOD003.
- Paper parameters: \(N=4,6,8,10,12\);
  \(\theta=40^\circ,30^\circ,20^\circ,10^\circ,0^\circ\).
- Calculation: diagonalize the uniform-\(+\) sector and compute the squared
  overlap with the normalized uniform-\(+\) physical MPS.
- Acceptance: all residuals below \(10^{-10}\); overlaps in \([0,1]\);
  larger overlap nearer \(45^\circ\); generated points agree with digitized
  source within its image-derived tolerance. If one isolated point disagrees
  while all algebra, residual, trend, and remaining 24 points pass, retain it
  as an explicit source/numeric discrepancy rather than tuning the model.

## NUM004 — Main Fig. 5(b), first-excited overlap

- Target: T002.
- Dependencies: EQC001, EQC002, EQC006, EQC007, EQC009;
  METHOD001–METHOD003.
- Paper parameters: same \(N,\theta\) grid as T001.
- Calculation: flip one \(w\) to \(-1\), diagonalize its exact sector, and
  compute the squared overlap with the matching one-flip MPS. At selected
  sizes, verify all \(N\) one-flip sector minima are degenerate.
- Acceptance: residuals below \(10^{-10}\); overlaps in \([0,1]\); N-fold
  sector-energy spread below \(10^{-10}\); trend and digitized values match.

## Efficiency And Risk

- Enumerating \(3^N\) Cartesian labels at \(N=12\) is inexpensive; the retained
  fixed-\(w\) matrices are much smaller than the full Hilbert space.
- Matrix assembly uses exact local transition tables and sparse storage.
- The highest risk is not compute but tensor/index convention. Small-\(N\)
  full-space parity, exact-point zero energy, and \(w\)-support tests are
  mandatory before Fig. 5 runs.
- Generated CSV and JSON checks are written before plots.
