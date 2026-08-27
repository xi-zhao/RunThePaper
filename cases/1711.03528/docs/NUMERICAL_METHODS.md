# Numerical Methods

## Local Compute Decision

The current machine is an Apple M3 Pro with 18 GB memory. This is enough for feature-level exact diagonalization of the constrained PXP chain, but not enough for the paper's full L=32 symmetry-resolved campaign.

Default local scale:

- exact diagonalization for the main scar plot: `L=16`, PBC, full constrained Hilbert space;
- time evolution: `L=16`, PBC, finite-size exact evolution;
- level statistics: `L=12, 14, 16`, full constrained sector.

## Model Implementation

The code builds the constrained Hilbert space explicitly. A basis state is a bitstring with no adjacent excitations. The Hamiltonian matrix has unit entries between two basis states if one allowed Rydberg flip connects them.

Implemented files:

- `src/pxp_scars.py`: basis, Hamiltonian, symmetry checks, FSA, dynamics, ED observables.
- `scripts/run_reproduction.py`: generates CSV data and JSON checks.
- `scripts/plot_reproduction.py`: renders all reproduction figures from CSV.

## Data Generated Before Plotting

- `outputs/data/fig1_graph_nodes.csv`
- `outputs/data/fig1_graph_edges.csv`
- `outputs/data/fig_ent_dynamics.csv`
- `outputs/data/fig2a_scar_overlaps.csv`
- `outputs/data/fig2bc_fsa_basis_overlaps.csv`
- `outputs/data/fig2d_participation_ratio.csv`
- `outputs/data/fig4_level_spacing_distribution.csv`
- `outputs/data/fig4_density_of_states.csv`

## Feature Checks

The run checks:

- Fibonacci Hilbert-space dimension.
- Particle-hole anticommutation.
- `H = H+ + H-`.
- FSA closure to `L+1` basis vectors.
- `Z2` oscillation period.
- `Z2` return revival compared with the vacuum state.
- High-overlap scar tower.
- Participation-ratio enhancement of special states.
- Small-size level-spacing trend.
