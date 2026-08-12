# Derivation Trace

## Scientific chain

1. At fixed \(n\) and \(|m_l|=1\), build the tridiagonal matrix of \(z/a_0\)
   from the analytic radial/angular element in EQ001.  Its spectrum must be
   exactly \(3nk/2\); this is the independent check that the basis and matrix
   normalization are correct.
2. Add the reduced-mass leading Dirac correction (EQ003) on the \(l\) basis.
   The fixed \(m_l,m_s\) expectation of \(1/(j+1/2)\) is calculated from exact
   Clebsch-Gordan weights, not fitted from the figure.
3. Diagonalize \(H_0+eFz\), follow the \(k=0\) eigenvector continuously from
   high to low field, and add the analytic neighboring-manifold \(F^2\)
   correction (EQ004).  A separately declared \(n^{-5}\) hyperfine estimate
   resolves the five close branches; it is the main approximation.
4. For Fig. 3, combine the exact first-order Stark centers with the six
   Gaussian-error-function components of EQ006.
5. For Fig. 4, Fig. 5 and Tables I-II, recompute normalized offsets,
   regressions, uncertainty quadrature and decimal frequency arithmetic from
   printed scalar inputs.  Missing point-level observations are never inferred
   from raster figures.

## Review-sensitive conclusions

- The 52.23-Hz difference between the sum of rounded printed inputs and the
  printed binding frequency is compatible with unpublished guard digits.  It
  is `inconclusive`, not a paper-error candidate.
- The stated 4.5-sigma CODATA-2010 comparison follows a one-sided uncertainty
  convention; combined uncertainty gives a smaller value.  The convention is
  recorded explicitly and remains `inconclusive` without a fresh independent
  review.
- Table I's displayed rows do not alone close to the reported aggregate
  uncertainties.  The missing quadrature components are exposed rather than
  silently redistributed.
