# Formula Verification

All nine numerical cards are open for implementation.  Open means that the
implemented numerical form is source-traced and independently checked; it does
not mean that every printed sentence is self-consistent.

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | Microscopic hopping | open | Hermiticity, translation invariance, and nearest-neighbor limit checked |
| EQ002 | Monitored trajectory | open | Diagonal exponential derived through Ito order; particle number preserved |
| EQ003 | Gaussian observables | open | Entropy and positive correlation follow from the one-body projector |
| EQ004 | Wick sign audit | open with discrepancy | Exact contraction and Fock-space check give a minus sign |
| EQ005 | Scaling fits | open | Printed fit forms and windows; synthetic recovery required |
| EQ006 | Replica long-range term | open | Second-order kernel explains exponent doubling |
| EQ007 | Infrared kernel | open | Direct quadrature checks the threshold at `p=3/2` |
| EQ008 | Dark-state exponents | open | Fourier scaling and `b=2-a` verified |
| EQ009 | RG flow | open | ODE direction agrees with canonical power counting |

Machine-readable evaluation is written by:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2105.08076 --write
```

## Source limitations that cap parameter provenance

- no time step, burn-in, stationary time, trajectory count, fit weighting, or
  random seeds;
- no explicit finite-ring distance convention;
- no author numerical arrays or source program in the arXiv archive;
- phase names in two captions conflict with their printed parameter values.

These omissions require independently converged settings and prevent a
paper-exact parameter claim even if scientific features agree.
