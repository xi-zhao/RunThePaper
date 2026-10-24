# Necessary finite-range condition for the literal Figure 1(c) model

This is stronger than a log-log slope observation. It uses only the fixed source's N=4, T=6*2=12, system-only Pauli observable A, factorized initial state with Z-diagonal bath, H=K(t)+lambda V, V=sum_i (X_i X_bi+Z_bi)/2, and the caption's lambda=-log(1-epsilon)/2 and absolute error definition. Unknown graph, rotations, beta and system state do not enter the bound.

1. The interaction-picture first-order term is a time integral of the system commutator with the bath expectation of V. The X_bi means vanish. The bath-only term contributes a scalar identity to that expectation and its commutator is zero. Thus a1=0.
2. Each pair operator V_i=(X_i X_bi+Z_bi)/2 has V_i^2=I/2 because the two Pauli strings anticommute. Distinct pairs commute. Therefore ||V||=4/sqrt(2)=2 sqrt(2). The trace-norm induced commutator norm is at most 2||V||, and conjugating by arbitrary K(t) does not increase it.
3. The third-order Volterra remainder in the physical joint density matrix contains three interaction-picture noise generators acting on a positive trace-one intermediate state. Integrating its trace-norm bound over the ordered time simplex gives |R3(lambda)| <= C lambda^3 with C=(2||V|| T)^3/6. The scalar expectation satisfies E(lambda)-E(0)=a2 lambda^2+R3(lambda). This is a finite-lambda bound, not an assumption that the displayed interval is asymptotic. No exp(C lambda) factor is needed for this remainder form because its innermost density matrix is the actual physical state of trace norm one.
4. At two positive rates a<b, reverse triangle inequalities give

   |a2| >= [Delta(a)-C a^3]/a^2,

   Delta(b) >= (b/a)^2 [Delta(a)-C a^3] - C b^3.

   Signs of the expectation errors may differ: these inequalities already allow either sign and all admissible higher-order cancellation.
5. `code/bath_consistency_bound.py` evaluates this with 80 decimal digits. It conservatively expands each reference error by 0.5% and each plotted epsilon by +/-3e-6, larger than the vector-coordinate extraction precision. The coefficient lower bound uses the first error's lower limit and the largest first rate. Each predicted error lower bound uses the smallest second rate in the quadratic term and the largest rate in the remainder term. This is deliberately conservative. Every point from epsilon=.002 to .01 is checked, not a selected endpoint.

The resulting incompatibility pertains to the conjunction of printed model and figure conventions. A changed interpretation (for example a different noise-coupling scale or a relative rather than absolute plotted error) could evade these assumptions. Those changes would need to be explicitly documented to reproduce the source figure. A square-root-coupling diagnostic is saved separately and is not substituted for the literal model. This does not refute the valid Richardson moment equations or their cancellation theorem.

Implementation alternatives excluded: the bound does not use our random Hamiltonian or propagation code; the no-linear-term prediction is independently seen in a full eight-qubit Taylor hierarchy and numerical propagation. Coordinate reading is checked against the source vector file. Choosing another graph, seed, Pauli or normalized thermal state within these assumptions cannot remove the bound. Source ambiguity about the beta normalization is immaterial to this conclusion for a physical normalized Z-diagonal state.
