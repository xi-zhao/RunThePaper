# Derivation Trace

## T-type lane: five-qubit projector to Fig. 2

After Clifford dephasing, one input qubit is a classical mixture of the two
`T` eigenstates with probabilities `1-epsilon` and `epsilon`. Five copies give
32 orthogonal error strings. The printed stabilizers define

```text
Pi = product_j (I + S_j) / 16.
```

The implementation constructs this 32 by 32 matrix from Pauli tensor products,
checks that it is a rank-two Hermitian projector, and projects every error
string. Grouping accepted weights by decoded logical eigensector yields

```text
p_s = [(1-e)^5 + 5 e^2(1-e)^3 + 5 e^3(1-e)^2 + e^5] / 6,
e_out = [e^5 + 5 e^2(1-e)^3] / [6 p_s].
```

The second line is algebraically equivalent to Eq. (23). This route does not
assume the plotted polynomial and is therefore a genuine cross-check.

## H-type lane: Reed-Muller truth tables to Fig. 3

Evaluate all nonzero four-bit inputs. The four linear Boolean functions span
`L1` (16 words); adding the six quadratic monomials spans `L2` (1024 words).
Direct enumeration verifies the printed dimensions, parity properties and

```text
W_L1(x,y) = x^15 + 15 x^7 y^8.
```

The implementation computes success and logical-error weights directly from
the enumerated `L2` and `L2 + [1]` cosets. It then compares them pointwise with
Eqs. (35)-(36), providing an independent route to Fig. 3.

## Thresholds and asymptotics

- T fixed point: factor `e_out(e)-e`; its interior root is exactly
  `(1-sqrt(3/7))/2`.
- H fixed point: bisection on `(0, 1/2)` excluding zero and one half, followed
  by a residual check.
- Small-error limits are evaluated at a shrinking sequence rather than inferred
  from the plotted pixels: `e_out/e^2 -> 5` and `e_out/e^3 -> 35`.
- The recursive exponents follow from one accepted output per 30 T inputs and
  per 15 H inputs, combined with quadratic and cubic suppression.

## Boundary not derivable from the paper

Section VII says simulations were performed for “some” `n=11` and `n=17`
GF(4)-linear codes, but gives no code generators, search rule, threshold values,
sample set, tolerances, or result arrays. Many inequivalent codes satisfy the
stated length condition. The exact claim therefore has no uniquely defined
numerical input. It is an evidence gap, not a compute shortage and not a code
failure.
