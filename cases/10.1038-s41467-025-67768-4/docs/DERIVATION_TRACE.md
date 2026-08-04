# Derivation Trace

## 1. Why the extrapolation starts at `ceil(d/2)`

Supplementary Eqs. (11)--(18) expand every noisy operation into an ideal
component plus an error component. If every physical error probability is
scaled by the same factor `r`, a term containing exactly `k` errors acquires
the factor `r^k`. This yields ZNE001.

For a distance-`d` code with ideal syndrome extraction, every pattern with
fewer than `m=ceil(d/2)` relevant errors is corrected. The first logical-error
term is therefore order `r^m`. Fitting the basis

```text
1, r^m, r^(m+1), ..., r^(m+K-1)
```

and taking the constant coefficient cancels the first `K` surviving logical
orders. Numerically, solving `V.T @ b = e0` is more stable and clearer than
forming an explicit matrix inverse.

## 2. Bias and overhead

For a Pauli observable measured with `N_k` shots, the sample-mean variance is
`(1-O_k^2)/N_k`. The paper allocates
`N_k = N_tot |b_k| / sum |b|`. Substituting this allocation into the variance
of the weighted sum gives ZNE003 directly. This makes the trade-off explicit:
nearby noise scales or higher-order cancellation create large signed weights,
which can reduce bias while increasing variance.

## 3. Feedback example: exact 64-pattern reduction

Only X and Y insertions flip a Z-basis outcome, so one data qubit flips with
probability `q=2rp/3`. Let the three data-qubit flip bits be `e0,e2,e4`.

- The uncorrected Q0 sign is `(-1)^e0`, giving `1-2q`.
- Q3 post-selection accepts exactly when `e2=e4`.
- Q1 reports `e0 xor e2`; applying the feedback flip leaves residual error
  `e2` on Q0.
- Conditional on acceptance, the no-residual and residual weights are
  `(1-q)^2` and `q^2`.

Multiplication by the ideal input value `cos(theta_0)` gives FB001. The code
also enumerates all `4^3` Pauli patterns as an independent check of this closed
form.

## 4. Repetition code

In one injection layer, the decoder fails only if at least `ceil(d/2)` data
qubits have a bit-flip component. The logical failure probability is therefore
the binomial tail in REP001. Each of the `M` parity rounds plus the terminal
injection/readout layer contributes an independent logical sign, so logical-Z
attenuations multiply across `M+1` layers.

Supplementary Table 3 is a useful internal consistency check. Holding the
cumulative probability `P_tot` fixed across `M+1` layers implies

```text
p_M = 1 - (1 - P_tot) ** (1 / (M + 1)).
```

Taking the displayed `M=1` value `p_1=0.136` fixes
`P_tot=1-(1-0.136)^2`. The exact schedule is then
`[13.600, 9.286, 7.048, 5.680]%`, whereas the paper prints
`[13.6, 9.4, 7.2, 5.7]%`. The latter gives cumulative probabilities
`[0.25350, 0.25632, 0.25836, 0.25431]`, with a 1.9005% relative range.
Thus “fixed” is a useful approximation, not an exact identity or a rounding
consequence.

## 5. Distance-3 surface code

The nine data qubits are row-major `D0,...,D8`. The reconstructed CSS checks
are

```text
X: {D0,D1,D3,D4}, {D1,D2}, {D4,D5,D7,D8}, {D6,D7}
Z: {D0,D3}, {D1,D2,D4,D5}, {D3,D4,D6,D7}, {D5,D8}
```

with the paper's logical operators

```text
XL = X_D1 X_D4 X_D7
ZL = Z_D3 Z_D4 Z_D5.
```

All X/Z check overlaps are even; each logical commutes with all checks; XL and
ZL overlap once and anticommute. For each syndrome, the implementation chooses
a deterministic minimum-weight X and Z correction by exhaustive search over
`2^9` binary patterns. It then enumerates all `4^9` physical Pauli errors,
classifies the corrected logical I/X/Y/Z outcome, and evaluates the exact
probability polynomial at each depolarizing rate. No Monte Carlo noise or plot
data enter this target.

## 6. Large-scale logical memory

Supplementary Fig. 9 points to the Bravyi--Vargo logical-error fit. The target
paper's odd distances map to the reference's defect radius as
`r_d=(d+1)/4`, so `d=7,11,15` map to `r_d=2,3,4`. The noisy-syndrome,
path-like coefficients reproduce the target paper's explicit anchor:

```text
P_L(p=1e-3, d=11) = 2.033751778...e-10.
```

Using `O(r)=[1-2 P_L(rp,d)]^N`, the distance-aware weights from ZNE002, and
the overhead from ZNE003 fully determines Supplementary Fig. 9 without author
data.

## Unresolved scientific inputs

- Per-gate Processor-I calibration maps used by the dashed repetition curves.
- The surface-code injection unit probability.
- qLDPC circuit/decoder definition for Supplementary Fig. 2.
- Exact lattice-surgery schedule/decoder/shot contract for Supplementary
  Fig. 10.
- The noise-amplification convention used by the plotted Main Fig. 2(c)
  simulator: literal probabilities `p_X=p_Y=p_Z=rp/3` force a high-r sign
  change that is absent from the paper curve.

These gaps cap the affected targets; they are not filled by reading pixels.
