# Numerical Methods

## Numerical objects

The calculation never ingests source images. Closed dynamics use the exact zero/single-excitation Hamiltonian; noisy dynamics add one vacuum state and integrate independent Lindblad channels. The 2D model is a Kronecker sum of two 1D FST chains. Every target writes a compressed NPZ before any rendering begins.

| Method | Targets | Solver | Grid / samples | Main validation |
| --- | --- | --- | --- | --- |
| `NUM001` | T001–T003 | dense Hermitian diagonalization and spectral propagation | paper axes; at most 5 sites | analytic spectrum, closed-form 3-site identity, PST error `<5e-16` |
| `NUM002` | T004–T005, T007, T009–T010 | adaptive RK45 on vectorized density matrices | paper time axes; `m=0..50` sweeps | trace error `<1.8e-15`, positivity and target fidelity |
| `NUM003` | T006, T008 | independent Gaussian Monte Carlo | 100 and 50 samples per point | zero-noise normalization and robustness ordering |

## Units and tolerances

- Internal frequencies: `rad/ns`; a plotted MHz value is multiplied by `2*pi*1e-3`.
- Site indexing: paper one-based, arrays zero-based.
- Random seeds: `25060669` for FST and `25060670` for PST; both are replacements because the paper does not publish seeds.
- Density propagation: adaptive relative/absolute tolerances are declared in `config/paper_reconstruction.json`.
- Output hashes: frozen in `outputs/runs/paper-reconstruction-source-blind-v4/run_attestation.json`.

## Efficiency and isolation

Small dense matrices make CPU execution faster and simpler than an A100 path. The final 10-target run took 25.09 s on an Apple M4. The isolated runner recorded 626 file events, zero denied/forbidden source accesses, configuration/input hashes, output hashes and base Git SHA. Rendering is a separate 1.93 s source-blind run over frozen NPZ arrays and a style-only RenderContract.

The only potentially reusable implementation is the vacuum/single-excitation Lindblad reduction. Paper-specific parity corrections, phase gauges and pulse assumptions remain case-local.
