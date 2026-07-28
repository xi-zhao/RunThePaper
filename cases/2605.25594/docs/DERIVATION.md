# Derivation

Equation-level derivation for **2605.25594**, generated from the reproduction's
equation cards (10 equations). Each block is an equation the reproduction
depends on, transcribed from the paper with its source location and tagged by
derivation status. For the narrative walk-through see `DERIVATION_TRACE.md`.

## Equations

### FS001 — Eigenstate fidelity susceptibility

*Defines unregularized eigenstate sensitivity to perturbation.*

$$
chi_n=sum_{m != n}|<n|O|m>|^2/(E_n-E_m)^2
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines unregularized eigenstate sensitivity to perturbation.
```

Code: `code/src/anderson_sensitivity.py::operator_in_eigenbasis`,
`code/src/anderson_sensitivity.py::susceptibility_metrics`

### FS002 — Regularized susceptibility kernel

*Defines finite-frequency cutoff kernel.*

$$
omega^2/(omega^2+mu^2)^2
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines finite-frequency cutoff kernel.
```

Code: `code/src/anderson_sensitivity.py::susceptibility_metrics`

### FS003 — Average and typical susceptibility

*Defines average and typical sensitivity observables.*

$$
chi_av=mean chi_n; chi_typ=exp(mean log chi_n)
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines average and typical sensitivity observables.
```

Code: `code/src/anderson_sensitivity.py::susceptibility_metrics`

### FS004 — 3D Anderson Hamiltonian

*Defines open-boundary cubic Anderson model.*

$$
H_A=-sum_<ij> c_i^dag c_j + sum_i epsilon_i c_i^dag c_i
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines open-boundary cubic Anderson model.
```

Code: `code/src/anderson_sensitivity.py::anderson_hamiltonian`

### FS005 — Perturbation operators

*Defines perturbations used by susceptibility targets.*

$$
T, T_s, n perturbation operators
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines perturbations used by susceptibility targets.
```

Code: `code/src/anderson_sensitivity.py::sublattice_kinetic_matrix`,
`code/src/anderson_sensitivity.py::randomized_site_operator`

### FS006 — Rescaled susceptibility

*Defines plotted rescaled observables.*

$$
tilde chi_typ=chi_typ omega_typ; tilde chi^r=chi^r mu
$$

status: `verified` · source: derivation trace

Numerical form:

```text
Defines plotted rescaled observables.
```

Code: `code/src/anderson_sensitivity.py::susceptibility_metrics`

### FS007 — Spectral function mechanism

*Defines spectral-function diagnostic for mechanism figures.*

$$
|f(omega)|^2 approx Z/|Lambda(omega)| sum_{n,m in Lambda; omega_nm in bin(omega)} |<n|O|m>|^2
$$

status: `verified` · derived from: `FS004`, `FS005` · source: Eq. (spectral)
and derivation trace E007

Numerical form:

```text
For each logarithmic omega bin, exclude m=n, average |O_nm|^2 over qualifying pairs, and multiply by the Hilbert-space dimension Z.
```

Code: `code/src/anderson_sensitivity.py::spectral_function`

### FS008 — Perturbative Ts trend

*Defines localized-regime perturbative trend proxy.*

$$
chi_n^r approx sum_{n''} [omega_{n n''}^{(0)}/(([omega_{n n''}^{(0)}]^2+mu^2))]^2
$$

status: `reconstructed` · derived from: `FS002`, `FS004`, `FS005` · source:
Eq. (pert), its nearest-neighbor reduction, and derivation trace E008

Numerical form:

```text
Average [Delta epsilon/(Delta epsilon^2+mu^2)]^2 over T_s-connected site pairs; compare the W dependence, not the absolute vertical normalization, with chi_typ^r.
```

Code: `code/src/anderson_sensitivity.py::perturbation_theory_ts`

### FS009 — Adjacent-gap ratio

*Defines the level-statistics observable used to locate chaotic and localized regimes.*

$$
r_n=min(delta_{n+1},delta_n)/max(delta_{n+1},delta_n), delta_n=E_n-E_{n-1}
$$

status: `verified` · derived from: `FS004` · source: appendix
spectral-statistics definition and derivation trace E009

Numerical form:

```text
Sort eigenvalues, form positive adjacent gaps in the selected spectral window, compute min(g_i,g_{i+1})/max(g_i,g_{i+1}), then average.
```

Code: `code/src/anderson_sensitivity.py::spacing_stats`

### FS010 — Slow-mode Drude envelope

*Defines the phenomenological power-law envelope and its single-Lorentzian limit.*

$$
|f(omega)|^2 propto integral_{Gamma_min}^{Gamma_max} dGamma Gamma^{zeta-1}/(Gamma^2+omega^2) propto omega^{zeta-2}
$$

status: `reconstructed` · derived from: `FS007` · source: Eqs. (Drude),
(eq_envelope), and (explanation), with the inconsistency explained in
derivation trace E010

Numerical form:

```text
Sample Gamma from p(Gamma) proportional to Gamma^(zeta-2), average Gamma/[pi(omega^2+Gamma^2)], and fit the intermediate window to omega^-a with a=2-zeta.
```

Code: `code/scripts/run_fig11_phenomenological_model.py::sample_rates`,
`code/scripts/run_fig11_phenomenological_model.py::spectral_function`
