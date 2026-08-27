# Consistency Report

| Level | Count | Targets |
| --- | ---: | --- |
| quantitative feature match | 7 | Fig. 1(a), Fig. 2(b,c), Fig. 4(a-d) |
| qualitative formula/flow match | 4 | Fig. S1 four panels |
| partial reduced-scale match | 2 | Fig. 1(b), Fig. 2(a) |
| parameter-ambiguous target | 2 | Fig. S2(a,b) |

## Strong anchors

- TDVP periods: relative errors 1.56%, 0.096%, and 0.207% for s=1/2,1,2.
- Integrated leakages: absolute differences 0.00464, 0.00170, 0.00232.
- Unitary propagation norm error: 7.6e-15.
- Thermal zero-quench means agree with analytic constrained values at reduced
  size within the expected finite-size fluctuation.
- Deformed h=0 flow identity: 1.4e-16.
- Deformed matrix-H projection to printed flow: 3.9e-4 at L=12.
- Fig. S2 finite-ring convergence: 1.4e-7 from L=12 to 14.
- Fig. 2 finite-MPS smoke: blocked/unblocked Hamiltonians agree below 1e-14;
  small exact evolution agrees below 2e-6; six-lane dt/bond changes are
  1.67e-7 / 8.69e-8 bits; forbidden-state weight is at most 4.12e-12.
- Main paper-scale runner smoke: 12 L<=6 units aggregate successfully;
  streaming magnetization agrees with the independent batched path within
  2e-12, and an interrupted quench resumes to the same time series.

## Open discrepancies

The displayed dynamics envelopes and r-statistic curve are not paper-exact
because the executed run uses smaller systems. Fig. 1 and Fig. 4 now have a
complete streaming candidate-size implementation contract, and Fig. 2(b,c) has a
complete L=30 finite-MPS contract, but neither full computation was run; their
smokes are not counted as paper evidence. The paper does not report the Fig. 1
or Fig. 4 quench L values, so those lanes also remain parameter ambiguity.
Fig. 2(a) has executable candidate
size shards but cannot claim the plotted sequence because the paper omits the
exact L list.

Fig. S2 is not aligned after the printed Hamiltonian-to-flow projection and
ring convergence pass independent checks. The supplement does not provide the
closed deformed residual construction or numerical orbit-integral procedure,
so protocol-v2 assigns `parameter_ambiguity`. `paper_error_candidate` is
ineligible because `paper_exact` and `fresh_independent_review` fail. No
source-pixel adjustment was made.
