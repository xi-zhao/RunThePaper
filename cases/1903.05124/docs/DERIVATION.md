# Equation-level derivation

This case follows Choi, Bao, Qi, and Altman, *Quantum Error Correction in
Scrambling Dynamics and Measurement-Induced Phase Transition*, Phys. Rev.
Lett. **125**, 030505 (2020). The ten formula objects below were derived and
checked before numerical execution. Every published array is produced by the
equations, a Clifford/stabilizer simulation, or a fit of independently
generated observations. Paper images are downstream comparison references
only.

## Core derivations

### EQC001 — naive loss-style decoupling

The main-text theorem bounds the trace distance by

```text
E_U ||rho_(A2 B~)-rho_A2^max tensor rho_B~||_1
    <= 2^[-(1-2p-gamma)N/2].
```

The exponent is negative precisely when `1-2p-gamma>0`, giving
`gamma<1-2p`. The factor of two multiplying `p` reflects treating measured
qubits as discarded quantum degrees of freedom. This is a sufficient bound,
not the paper's tight projective-measurement result.

### EQC002 — tight bound when measurement outcomes remain accessible

Dilate each projective measurement into a system–device interaction followed
by dephasing into an environment `E`. The recoverable output includes the
system and the classical device register, so loss of coherent information is
controlled by `I(R:E)`. Cauchy–Schwarz gives

```text
||rho_RE-rho_R tensor rho_E||_1^2
 <= 2^(gamma N) 2^(pN)
    [Tr rho_RE^2 - 2^(-gamma N) Tr rho_E^2].
```

Inserting the two Haar/2-design contractions in the supplement cancels the
leading `2^[-(gamma+p)N]` terms. The surviving leading power yields

```text
E_U ||rho_RE-rho_R tensor rho_E||_1
    <=~ 2^[-(1-gamma-p)N/2].
```

Thus `gamma<1-p`. At `gamma=0`, the deep-scrambling transition can approach
`p_c=1`. Direct exponent comparison will be a formula check; no source figure
is needed.

### EQC003 — frame potential as a design diagnostic

For ensemble `nu`,

```text
F_nu^(k) = E_(U,V in nu) |Tr(U^dagger V)|^(2k) >= k!.
```

The Haar equality holds for Hilbert dimension at least `k`, as here. Because
`U^dagger V` from two depth-`d` brick circuits has the distribution of a
depth-`2d-1` circuit, Monte Carlo can sample a single composite circuit. The
scientific check is approach to `1,2,6` for `k=1,2,3`, while the Clifford
ensemble need not approach `24` for `k=4`.

### EQC004 — polynomial Clifford trace calculation

Pauli twirling rewrites `Q_U=|Tr U|^2` as

```text
Q_U = 2^(-n) sum_(P in P+) Tr(U^dagger P U P^dagger).
```

Only Paulis fixed by conjugation up to sign contribute. In binary symplectic
form they are the kernel of `S-I`, where `S` is the Clifford action. If the
kernel has dimension `r` and every kernel generator has positive phase, then
`Q_U=2^r`; if any kernel generator has negative phase, positive and negative
terms pair and `Q_U=0`. Therefore a sample contributes `Q_U^k` to the `k`th
frame potential. Small-`n` dense-unitary traces will independently check this
kernel-and-phase algorithm before `n=22` execution.

### EQC005 — entropy of a stabilizer subsystem

For a pure `n`-qubit stabilizer state with stabilizer group `S`, let `S_A` be
the subgroup whose Pauli support lies entirely in subsystem `A`. Tracing the
stabilizer expansion over the complement leaves `2^dim(S_A)` equally weighted
terms, so

```text
entropy(A) = |A| - dim(S_A)  [bits].
```

Equivalently, if the restriction of the `n` independent stabilizer generators
to the complement has binary rank `r_B`, then `dim(S_A)=n-r_B` and
`entropy(A)=|A|-n+r_B`. Bell pairs, product states, complement symmetry, and
dense-state entropies at small `n` provide independent checks.

### EQC006 — plotted dynamic observables

For half-chain `A`, the plotted density is

```text
s(t) = S_A(t)/(Lm/2).
```

If `S_before(t)` is evaluated immediately after the unitary layer and
`S_after(t)` immediately after the measurement layer, then

```text
Delta S_meas(t) = S_after(t)-S_before(t) <= 0 on average.
```

The sign, timing convention, and normalization are fixed before rendering.

### EQC007 — half-chain finite-size scaling

Near the transition,

```text
S(p,L) = alpha ln L + F((p-p_c)L^(1/nu)),
S(p,L)-S(p_c,L) = F((p-p_c)L^(1/nu)).
```

The second form removes the logarithmic critical entropy. The paper optimizes
`p_c` and `nu` by a collapse cost `Q`, then bootstraps by repeatedly selecting
80 of 100 measurement probabilities. Our implementation will expose the
interpolant and cost explicitly and verify that synthetic curves recover known
parameters before fitting circuit data.

### EQC008 — tripartite mutual information scaling

For four contiguous periodic partitions,

```text
I3(A:B:C) = S_A+S_B+S_C-S_AB-S_BC-S_AC+S_ABC,
I3(p,L) = G((p-p_c)L^(1/nu)).
```

The logarithmic corrections cancel, making the common crossing and collapse a
cleaner estimator. Purity identities reduce redundant entropy calculations but
do not alter the definition.

### EQC009 — channel capacity and conditional entropy

The measurement channel is degradable because its complementary environment
output can be obtained from the classical measurement register. Hence its
capacity single-letterizes. For the block-diagonal output
`rho_SM=sum_i p_i rho_S[i] tensor |i><i|`,

```text
I_c = S_SM-S_E = S_SM-S_M = sum_i p_i S(rho_S[i]),
Q = max_(rho_in) <S>.
```

This proves the scientific interpretation of the entanglement transition even
though no separate numerical figure is generated for the schematic channel.

### EQC010 — logarithmic critical entropy

At the critical point the scaling variable vanishes, so the constant
`F(0)` can be absorbed into the intercept and

```text
S(p_c,L) = alpha ln L + constant.
```

The slope from a weighted linear fit versus `ln L` defines the `alpha` values
in Supp. Fig. S6(c).

## Formula lane status

All ten cards have source anchors and an independent algebraic, limiting, or
small-system check. They authorize exploratory execution. Final numerical
claims still require the method gates, convergence checks, and independent
datasets to pass.
