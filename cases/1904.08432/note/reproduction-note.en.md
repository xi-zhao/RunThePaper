# Non-Hermitian skin effect and chiral damping

**The principal physical results are reproduced.** All six declared numerical panels were computed independently. Open and periodic chains exhibit different spectra and relaxation; a chiral damping front appears in model I and is absent in the model-II control. The fitted front speed is approximately 0.987, compared with the paper's approximate value 1.

Three residual periodic-curve offsets are explained by stationary-reference selection. At the critical point an even finite ring has a dark mode. A direct stationary solve and independent SVD select a zero-dark-occupation reference, producing a per-cell 1/(2L) offset relative to the half-filled reference. Relative RMSE after alignment is 0.0115%, 0.0249%, and 0.0197%, compatible with the original EPS coordinate precision. The physical evolution and principal mechanisms do not change.

The periodic length L=30 in Fig. 3(a) is a stable inference within the tested candidate family, not author-confirmed metadata. The authors' actual solver is unknown. Calculations use arXiv v2; the final journal text was not audited verbatim. These bounds do not establish a flaw in the main physical result.

[Illustrated report](../docs/report/index.html) · [Reference alignment](../docs/alignment/index.html) · [Derivation](../docs/DERIVATION.md) · [Rerun instructions](../docs/NUMERICAL_METHODS.md)

Distinct numerical formulations include a full-Fock small-system oracle and adaptive covariance ODEs. Scientific assessments come from the same research Agent; code-audit provenance is stated separately. No formal proof or independent peer-review acceptance is claimed.
