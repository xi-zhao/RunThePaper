# Derivation Trace

## 1. Output Probability

For a circuit `U` applied to the all-zero state, the output state is:

```text
|psi> = U |0...0>
```

For a bitstring `s`, the probability is:

```text
P_U(s) = |<s|psi>|^2
```

This is the starting point shared by statevector simulation and tensor-network contraction.

## 2. Split The Bitstring

The paper splits the final bitstring into closed and open parts:

```text
s = (s1, s2)
```

So the same probability can be written as:

```text
P_U(s) = P_U(s1, s2)
```

Fixing `s1` and enumerating all `s2` gives a correlated batch of output probabilities.

## 3. Head-Tail Amplitude Factorization

The tensor network is cut into two parts connected by a bottleneck. After contraction:

```text
G_head -> v_head(s1)
G_tail -> v_tail(s2)
```

The amplitude is:

```text
psi(s1, s2) = v_head(s1) dot v_tail(s2)
```

Then:

```text
P_U(s1, s2) = |psi(s1, s2)|^2
```

The important point is reuse: once `v_head(s1)` is computed, the same vector is used for every open bitstring `s2`.

## 4. XEB Fidelity

For `L` selected bitstrings, the paper uses:

```text
F_XEB = (2^n / L) * sum_i P_U(s_i) - 1
```

Equivalently:

```text
F_XEB = mean(N p_i) - 1
```

where `N = 2^n` and `p_i = P_U(s_i)`.

In this case:

- the full fixed-subspace batch has XEB close to zero;
- selecting only the highest-probability bitstrings raises XEB;
- selecting all bitstrings returns XEB close to zero.

## 5. Porter-Thomas Distribution

The paper compares scaled probabilities to the Porter-Thomas distribution:

```text
Prob(p) = N exp(-N p)
```

Let:

```text
x = Np
```

Then:

```text
Prob(x) = exp(-x)
```

That is why the histogram becomes a straight red line on the log-scale plots.

## 6. Conditional Probability

For a fixed closed bitstring:

```text
P_U(s1) = sum_s2 P_U(s1, s2)
```

The conditional distribution over open bitstrings is:

```text
P_U(s2 | s1) = P_U(s1, s2) / P_U(s1)
```

After normalization:

```text
sum_s2 P_U(s2 | s1) = 1
```

The check file verifies this to numerical precision.

## 7. Formula Gate Result

`outputs/checks/formula_verification.json` records:

- batch amplitude extraction equals direct amplitude lookup;
- conditional probabilities normalize to one;
- XEB formula is applied as `mean(Np)-1`;
- Porter-Thomas comparison is done in the scaled variable `Np`;
- no formula remains closed before numerical plotting.

## 8. Author closure v6: source-audited analytic and streaming checks

The v6 runner adds source-traced checks without assigning an independent-review verdict:

- bipartition cost: `T_AB = 2^(n_A+n_B+n_AB)`;
- GPU efficiency: `E = 8 T / (capacity * runtime)`;
- batch reuse: `T_reuse(L)=T_head+T_tail,total`, verified by reusing one
  independently constructed reduced public-circuit head for four amplitudes;
- fixed-subspace marginal: for `n=n1+n2` and `L=2^n2`, Eq. (1) gives
  `F_XEB+1 = 2^n1 P(s1)`; a second normalized joint-distribution example
  independently verifies the scaling and conditional normalization;
- complex64 storage: runtime dtype inspection gives eight bytes per element,
  so a rank-53 binary tensor occupies `2^53 * 8 = 2^56` bytes, or
  `72057.594` decimal TB / `65536` TiB;
- precision: identical reduced public-circuit gates are run in complex64 and
  complex128 at three subsystem sizes, recording amplitude, probability, norm,
  and state-fidelity diagnostics;
- mixed XEB: with 220 top and 999780 uniform-random strings,
  `F_mix = 0.00022 F_top` in expectation.

The canonical source audit proves that T005 omits the exact 345/36 tensor
membership and unique partition-search contract, while T009 omits the tested
subtask, metric, result and acceptance threshold. Those are recorded as
`publication_underspecified`; no missing value is inferred merely from a failed
run. The adjacent marginal prose and memory value that disagree with the
rederivations are preserved in `T012.json` and `T013.json` for fresh review.

The formal-PRL additions use one generic reduced-state streaming path:

- batch cardinality is checked as `2^n_closed * 2^n_open = 2^n`;
- each reduced batch is hashed and entered in a deterministic partition ledger;
- the rolling stream hash, normalization, Porter-Thomas histogram and KS
  statistic are accumulated without materializing a paper-scale output array;
- seeded sampling records lag-one correlation and XEB diagnostics;
- the 43-qubit and 50-qubit contracts expose 64-TiB and 8-PiB logical streams,
  respectively, and fail closed before a paper-scale allocation or launch;
- the noisy-fidelity smoke demonstrates an executable state-approximation path,
  but it also proves that fidelity alone does not define the publication's
  claimed work-reduction law.

These checks use public circuit parameters and independently generated arrays.
Author code, author numerical arrays and source pixels are not implementation
inputs.  Exact formal-PRL claims remain zero-credit until their external inputs
and paper-scale executions are independently available.
