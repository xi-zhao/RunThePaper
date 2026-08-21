# Method trace

1. Build both exact parity blocks directly from Eq. (1).
2. Cross-check a small block against an independently assembled dense matrix.
3. For Fig. 1, obey the strict caption interval `500<N<1500` and freeze both
   parity sectors plus midpoint, straddling, and local-minimum-gap selectors.
   Each convention is fitted independently to `Delta E=f(lambda)/ln N`.
4. Run a value-window eigensolver at N=10000..250000 and fit a declared
   `a/ln(N)+b/ln(N)^2` convergence model. This tests the leading coefficient
   without pretending the added grid was used by the authors.
5. For Fig. 2, diagonalize N=5000 and freeze the literal merged spectrum and
   both parity-sector alternatives. Render exactly k=8,16,... among the first
   500 levels and fit k=8..500.
6. Fit fixed-k energies across N=1000..5000 to test N^-1/3 independently.
7. Solve the `K=-1` curve of Eq. (16), integrate the canonical area of both
   separatrix lobes, and insert that action into the printed WKB condition.
   Independently identify the exact local minimal-gap pair, evaluate its
   first-20-component mass, measure the interval required for 50%, 75%, 90%,
   and 99% probability, and compare only with states outside that pair.
8. For the normal phase, bin every same-parity adjacent gap over the full band.
   Report the increasing lower-energy branch and the returning upper branch
   separately; never infer a full-band monotonic result from two points.
9. Quantize Eq. (16) with symmetric and sandwich self-adjoint orderings and
   compare their complete spectra against normalized Eq. (1) over N=40..1280.
10. Locate exceptional points by solving `det(H-E)=0` and
    `partial_E det(H-E)=0` together in complex lambda using matrix-norm
    backward errors. Retain a root only when an independent dense complex
    eigensolve also shows eigenvalue coalescence, center agreement, and an
    ill-conditioned eigenbasis. Record the entire deterministic seed census;
    do not treat it as a certified continuous-domain root count.

All unpublished choices are compared, not tuned. No source figure is digitized.
