# Method Trace

## EXACT_TRANSFER: exact auxiliary-space contraction

- Source: Eqs. (4)-(22), all printed corollaries and the root-of-unity paragraph.
- Inputs: printed `Delta`, `epsilon`, system sizes and formula-derived sampling grids.
- Outputs: profiles, currents, correlations, explicit physical MPOs, structural identities, complexity counts and asymptotic checks.
- Code: `src/open_xxz/transfer.py`.
- Stability: scaled tridiagonal products and exact removal of auxiliary states that cannot return to the vacuum within the remaining steps.
- Complexity: `O(n^2)` path contraction rather than full `4^n` density-matrix evolution.

## DENSE_LIOUVILLIAN: structurally independent check

- Source: printed Hamiltonian and Lindblad jump operators, not the MPO construction.
- Inputs: `n=2,3,4`, all three anisotropies and two boundary couplings.
- Outputs: stationary density matrix, site magnetization, bond currents and residuals.
- Code: `src/open_xxz/liouvillian.py`.
- Independence: builds and solves the full Liouvillian directly; it never calls the transfer solver.

## SCIENTIFIC_RUNNER: provenance boundary

- Contract: `run_contract.json` and `config/paper_exact.json`.
- Inputs: exact case-local source files plus JSON configuration only.
- Forbidden: `raw/`, `references/`, PDF, original figure, network and subprocess.
- Final run: `1106.2978-paper-exact-v6`, attested in `11.358127 s`, 21 targets, 51/51 assertions and zero forbidden accesses.

## RENDER_ONLY: post-freeze presentation

- Contract: `config/render_contract.json`.
- Inputs: hash-verified frozen CSV/JSON only.
- Allowed: canvas, axes position, font, line style, palette and interpolation.
- Locked: formulas, parameters, numerical arrays and scientific runner.
