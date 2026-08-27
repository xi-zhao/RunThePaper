# Paper Map

## Identity

- Preprint: arXiv:2005.09722, *Entanglement transition in a monitored free
  fermion chain -- from extended criticality to area law*.
- Authors: O. Alberton, M. Buchhold, S. Diehl.
- Publication: Physical Review Letters **126**, 170602 (2021), DOI
  10.1103/PhysRevLett.126.170602.
- Primary source: `paper-source/main.tex`, 433 lines, read in full.

## Scientific question

A half-filled periodic free-fermion chain starts from a Néel state and is
continuously monitored in the local number basis. The paper asks whether the
competition between coherent hopping and measurement back-action produces an
extended logarithmic-entanglement regime and a transition to a quantum-Zeno
area law. The central control is QSDc: the same non-unitary noise without true
measurement back-action.

## Model and numerical route

1. Represent every trajectory by an `L×(L/2)` occupied-orbital matrix `U`.
2. Apply nearest-neighbour hopping and the QSD/QSDc diagonal stochastic factor
   with `dt=0.05`, then re-orthonormalize by QR.
3. Form `D=UU†`; obtain interval entropy from restricted-correlation
   eigenvalues, mutual information from entropy combinations, and connected
   correlations from `|D[i+l,i]|²`.
4. Independently implement the event-driven QJ protocol and the binary random
   hopping Hamiltonian in the supplement.
5. Average observables only after evaluating each stochastic trajectory.

## Figure inventory

- Main Fig. 1(a,b): model and phase-diagram schematics; excluded.
- Main Fig. 1(c-e), including three insets: numerical.
- Main Fig. 2(a-c), including the insets in (a,b): numerical.
- Main Fig. 3(a-d), including insets in (a,d): numerical.
- Supplement Fig. 4(a-d), including the inset in (b): numerical QSD/QJ/QSDc.
- Supplement autocorrelation Fig. (a,b): numerical.
- Supplement random-hopping Fig.: numerical.
- Supplement trajectory-statistics Fig.: six numerical histogram axes.

The complete machine-readable enumeration has 31 targets in
`figure_coverage.json`; no numerical axis is silently omitted.

## Paper-scale parameters and missing information

- `dt=0.05`; half filling; periodic chain; Néel initial state.
- Regular QSD reaches `L=800`; QJ and random-hopping panels use `L=200`;
  autocorrelation uses `L=400`.
- The histogram figure states 5000 trajectories per histogram. The connected
  density check states independent sets of 250 trajectories and a direct set
  of 500 trajectories.
- Most other trajectory counts, every random seed, exact steady-state stopping
  time, and the precise fit windows are unpublished.

Consequently paper-exact stochastic sample identity is impossible. The case
uses a predeclared reduced-scale protocol (`L≤96`) that covers every numerical
axis and is labeled exploratory/reduced-scale throughout.
