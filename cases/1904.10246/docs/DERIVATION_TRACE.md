# Derivation Trace

The numerical code depends only on the eight verified cards in
`EQUATION_CARDS.json`. This document records the independent reasoning behind
their gates; `DERIVATION.md` is generated from the cards.

## EQ001 — Amplified Bernoulli Probability

In the good/bad two-dimensional subspace, \(\mathbf Q\) is a rotation by
\(2\theta_a\). Starting from
\(\sin\theta_a|{\rm good}\rangle+\cos\theta_a|{\rm bad}\rangle\), \(m\)
applications therefore produce angle \((2m+1)\theta_a\). Squaring the good
amplitude gives \(p_m=\sin^2((2m+1)\theta_a)\). The checks
\(p_m+(1-p_m)=1\) and \(p_0=a\) close the gate.

## EQ002 — Joint Likelihood And MLE

For circuit \(k\), \(h_k\) is binomial with parameters \(N_k,p_k\). Constants
\(\binom{N_k}{h_k}\) do not depend on \(a\), so the product likelihood reduces
after taking logs to
\(\sum_k[h_k\log p_k+(N_k-h_k)\log(1-p_k)]\). All \(k\) share the same
\(\theta_a\), which is why their otherwise independent data resolve periodic
aliases. For \(m_k=0\) the score equation yields
\(\hat a=\sum h_k/\sum N_k\), used as an implementation oracle.

## EQ003 — Fisher Information

For one Bernoulli observation the information is
\((\partial_a p)^2/[p(1-p)]\). With
\(\theta=\arcsin\sqrt a\),
\[
\partial_a p_m
=\frac{(2m+1)\sin(2(2m+1)\theta)}{2\sqrt{a(1-a)}}.
\]
Since \(p_m(1-p_m)=\sin^2(2(2m+1)\theta)/4\), the oscillatory factor cancels
away from removable endpoints, leaving
\((2m+1)^2/[a(1-a)]\). Multiplication by \(N_k\) and summation over independent
circuits gives EQ003.

## EQ004 — Query Accounting

Each shot prepares \(\mathcal A|0\rangle\) once. Each \(\mathbf Q\) contains
one \(\mathcal A\) and one \(\mathcal A^{-1}\), so \(m_k\) amplification
operations cost \(2m_k+1\) calls to \(\mathcal A\) or its inverse. Summing
over shots and circuits gives \(N_q\).

## EQ005 — Schedule Sums

For LIS, \(2m_k+1=2k+1\). Thus
\(\sum_{k=0}^M(2k+1)=(M+1)^2\), while expanding
\(\sum(2k+1)^2\) and using the standard sums of \(k\) and \(k^2\) gives
\((M+1)(2M+1)(2M+3)/3\).

For EIS, \(m_0=0\) and \(2m_k+1=2^k+1\) for \(k\ge1\). Geometric sums give
\[
\sum r_k=2^{M+1}+M-1,\qquad
\sum r_k^2=\frac{4^{M+1}-4}{3}+2^{M+2}+M-3.
\]
Direct enumeration for every executed \(M\) is an independent runtime check.

## EQ006 — Table 1 Exponents

- Classical: \(\epsilon\sim N_q^{-1/2}\), hence \(N_q\sim\epsilon^{-2}\);
  the direct sample mean also costs \(O(N_q)\).
- LIS: \(N_q\sim M^2\), \(\mathcal I\sim M^3\), so
  \(\epsilon\sim M^{-3/2}\sim N_q^{-3/4}\) and
  \(N_q\sim\epsilon^{-4/3}\). A \(1/\epsilon\) search grid times
  \(M\sim\epsilon^{-2/3}\) likelihood work gives
  \(O(\epsilon^{-5/3})\).
- EIS: \(N_q\sim2^M\), \(\mathcal I\sim4^M\), hence
  \(\epsilon\sim N_q^{-1}\); a \(1/\epsilon\) grid and
  \(M\sim\log(1/\epsilon)\) likelihood evaluation give
  \(O(\epsilon^{-1}\log\epsilon^{-1})\).

## EQ007 — Appendix Comparator

Conventional AE discretizes the two symmetric phases
\(\theta_a/\pi\) and \(1-\theta_a/\pi\) on a \(Q_m=2^m-1\) grid. The four
floor/ceiling integers are mapped back through \(\sin^2\), and the largest
absolute amplitude error is retained exactly as Appendix A specifies.
Symmetry duplicates candidate amplitudes but is kept explicitly for audit.

## EQ008 — Table 2 Resource Model

The paper fixes \(n=2\), \(b_{\max}=\pi/4\), all-to-all connectivity, and the
Qiskit 0.7 gate convention. Decomposing the displayed circuits into that CNOT
basis gives:

- state preparation \(\mathcal A\): 4 CNOTs;
- one un-controlled \(\mathbf Q\): 14 CNOTs;
- one controlled \(\mathbf Q\): 131 CNOTs;
- an inverse QFT on \(j+1\) phase qubits: \(j(j+1)\) CNOTs.

The proposed circuit with maximum \(q\) uses \(4+14q\). Conventional AE with
maximum power \(q=2^j\) applies controlled \(\mathbf Q\)
\(1+2+\cdots+2^j=2q-1\) times, giving
\[
4+131(2q-1)+j(j+1)=262q+j(j+1)-127.
\]
The proposed circuit stays at three qubits; the conventional circuit uses the
three data/rotation qubits, \(j+1\) phase qubits, and three decomposition
ancillas, i.e. \(j+7\).

## Gate Decision

All cards have a paper source trace plus at least one independent symbolic,
limiting, normalization, dimensional, or numerical check. They are eligible
for `final_reproduction`; no source-only card authorizes a run.
