# Method trace

## MTH001: GNN path planner

Paper object: a supervised GNN predicts candidate atom-target edges. Labels come from globally optimal Hungarian assignments. A modified auction decoder turns edge probabilities into a one-to-one assignment.

Metric contract after the Stage 13 label audit:

- The paper-facing Fig. 3 metrics are Euclidean average movement distance and
  Euclidean maximum movement distance.
- The training label cost is frozen to squared-distance Hungarian labels. A
  32-sample paper-geometry oracle audit at
  `outputs/checks/paper_gnn_target_stage13_metric_contract_probe/paper_hungarian_metric_contract.json`
  selects `squared_distance` because it better matches the paper's Fig. 3
  Hungarian baseline, especially the maximum-distance baseline.
- The paper-geometry target lattice must span the `127 x 127` initial field:
  target spacing is `(127 - 1) / (101 - 1) = 1.26`, not a same-spacing centered
  `101 x 101` subarray.

Current implementation:

- `src/atom_path_planner.py`
- `scripts/run_reduced_pilot.py`

Model artifact contract:

- The reproduction target is a trained edge-scoring GNN, not only a distance plot.
- Each training run writes `metrics.json`, `training_history.json`, and `model_state.pt`.
- `model_state.pt` stores the model architecture, training configuration, and PyTorch state dict.
- A valid run must support loading the checkpoint and decoding a fresh assignment instance.

Reduced implementation choices:

- Uses small square lattices instead of `127 x 127` to `101 x 101`.
- Uses a lightweight message-passing edge scorer; the current retrained artifact uses 6 message-passing passes to match the paper-level architectural intent at reduced scale.
- Provides both score-Hungarian decoding and a CPU modified-auction bidding decoder. The latter reproduces the decoder object at reduced scale, but not the paper's GPU-parallel implementation.

## MTH002: P2WGS potential generation

Paper object: an FFT/iFFT hologram-generation loop with target-plane amplitude and phase constraints. The target tweezer profile is modeled as a continuous Gaussian rather than a delta pixel.

Current implementation:

- `src/p2wgs_potential.py`
- `scripts/run_reduced_p2wgs_pilot.py`

Reduced implementation choices:

- Uses a small discrete grid.
- Uses straight-line trajectories from the current Hungarian assignment.
- Enforces a zero target phase on the tweezer support to test the continuity metric path.

## MTH003: Pipelined timing model

Paper object: total assembly time is controlled by path-planning overhead, per-frame hologram generation, SLM refresh, frame count, and transfer latency.

Current implementation:

- `src/p2wgs_potential.py`
- `scripts/plot_reduced_outputs.py`

The encoded model is:

```text
total_time = path_planning_ms + transfer_delay_ms + frames * max(per_frame_generation_ms, slm_refresh_ms)
```
