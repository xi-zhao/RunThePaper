# Derivation Trace

## 1. From the master equation to plotted observables

Main Eq. (1) separates the two-atom dynamics into coherent exchange `g`, two
individual decay rates `Gamma_a,b`, and collective decay `Gamma_coll`. Main
Fig. 2 plots precisely these coefficients; no time integration of the density
matrix is required.

## 2. Independent connection-point sum

For connection points `j_n` and `k_m`, the general result following Main Eq.
(2) gives

`g_jk = 1/2 sum_nm sqrt(gamma_jn gamma_km) sin(phi_jn,km)`,

with analogous cosine sums for individual and collective decay. For the figure,
all point couplings equal `gamma`, positions are `0, phi, 2phi, 3phi`, and the
four orderings are `ab`, `aabb`, `abab`, and `abba`. The implementation first
enumerates these point pairs directly in
`coefficients_from_ordering`; it does not begin from the plotted curves.

## 3. Recovering Table I

- `aabb`: cross distances have multiplicities `(1,2,1)` at `(phi,2phi,3phi)`.
- `abab`: cross distances have multiplicities `(3,1)` at `(phi,3phi)`.
- `abba`: cross distances have multiplicities `(2,2)` at `(phi,2phi)`.

Grouping these contributions gives the closed forms in `table_coefficients`.
On the frozen 1001-point grid, the two implementations agree to
`8.881784197001252e-16`.

## 4. Central physical check

For the braided ordering at `phi=pi/2`, Table I yields

`Gamma_a = Gamma_b = Gamma_coll = 0` and `g = gamma`.

At the zero-decay point `phi=pi`, both separate and nested geometries instead
give `g=0`. This numerically verifies the paper's central topology-dependent
claim before any pixel comparison.

## 5. Code and evidence

The general coefficient sums also factorize through each atom's emission
phasor,

`A_j = sum_n sqrt(gamma_jn) exp(i k x_jn)`.

Thus `Gamma_j = |A_j|^2` and
`Gamma_coll,jk = Re(A_j A_k*)`.  This is an all-size identity, not an
extrapolation from a finite grid: if an atom is individually dark, every
collective decay coefficient involving it vanishes.  Direct unequal-rate
point-pair sums independently reproduce the factorized expression.

For the protected chain, the even phase columns of the paper's `N x (2N-1)`
zero-decay constraint matrix form the identity matrix.  Therefore its rank is
exactly `N`, its nullity is `N-1`, and the remaining odd phases independently
set the `N-1` nearest-neighbour couplings.  For the all-to-all construction,
the first `N` columns form a unit upper-triangular minor, again proving rank
`N` and leaving `N-1` controls.  The two printed `N=3` phase assignments then
give respectively equal-positive and signed coupling triples while all
individual decay rates vanish.

## 6. Code and evidence

| Formula | Numerical form | Code | Evidence |
| --- | --- | --- | --- |
| EQ001 | Coefficient data object | `src/giant_atoms/model.py::Coefficients` | formula gate |
| EQ002 | General point-pair sums | `coefficients_from_ordering` | general/table residual |
| EQ003 | Table-I closed forms | `table_coefficients` | frozen CSV |
| EQ004 | Special-phase identities | `scientific_checks` | `target_checks.json` |
| EQ005 | General phasor factorization | `claim_campaign.py::collective_decay_factorized` | `claim_implementation_campaign/T002.json` |
| EQ006 | All-N chain rank witness | `claim_campaign.py::chain_tunability_result` | `claim_implementation_campaign/T003.json` |
| EQ007 | All-N all-to-all rank witness | `claim_campaign.py::all_to_all_result` | `claim_implementation_campaign/T004.json` |
