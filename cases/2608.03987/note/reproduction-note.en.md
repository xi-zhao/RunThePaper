# Independent reproduction of arXiv:2608.03987

## Paper and scope

- Paper: [arXiv:2608.03987v2](https://arxiv.org/abs/2608.03987), *Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators*.
- Raw benchmark inputs: [Zenodo 10.5281/zenodo.21791682](https://doi.org/10.5281/zenodo.21791682), released under CC-BY-4.0.
- This package targets Figures 8 and 9 on all 67 circuits: 12 random, 24 Clifford+T, 10 QAOA, and 21 VQE.

## Independence boundary

The numerical core is a clean-room Python tensor-network implementation of the
paper's equations. It does not execute, translate, or wrap the authors' Rust
code. The primary optimizer reads exactly 122 raw payloads from the public ZIP:
12 qsim circuits, 55 structured circuit JSON files, and 55 observable files.
The recorded member audit confirms that no author Rust crate, contraction tree,
optimization plan, or result CSV enters this path.

The third-party package `cotengra==0.7.5` supplies only generic FLOP-oriented
candidate trees. Circuit lowering, the realification cost model, pass/ride/merge
classification, NNI simulated annealing, tree hashing, and all reported
statistics are implemented here. Author results are consulted only after the
independent records exist, for a post-hoc comparison that cannot affect search.

## Results

The evidence score is **72/100**: a numerical-feature reproduction, not a full
numerical match.

- **Figure 8 passes.** All 67 circuits satisfy the exact relation
  `o = 1 + 2m + r` and the analytic band `[1+2m, 2+m]`; the largest residual is
  `4.44e-16`. In the post-hoc comparison, overhead correlation with the release
  is `0.9881` and MAE is `0.0600`.
- **Figure 9 is partial.** The paper reports 66/67 circuits below the `5e-4`
  transfer-gap threshold; the independent optimizer obtains 57/67. Threshold
  labels agree for 58/67 circuits, with most differences in Clifford+T and VQE.
  The largest underlying real-cost gap is `20.35%`.

The exact arithmetic law is therefore independently verified. The empirical
claim that a skeleton-optimized tree transfers almost losslessly to the
realified network remains broadly true, but is weaker under a different search
algorithm. The mismatch is retained rather than hidden by relaxed tolerances.

## Quick run

Run from this case directory:

```bash
# Download and verify the official data release.
python code/scripts/fetch_benchmark_inputs.py

# Exercise the independent primary path on the five-qubit test circuit.
python code/scripts/run_independent_reimplementation.py \
  --preset smoke --scope random --circuit test
```

Full 67-circuit run:

```bash
python code/scripts/run_independent_reimplementation.py \
  --preset full \
  --output-dir outputs/data/independent_python_full
python code/scripts/run_reproduction.py
```

See the retained [Figure 8](../outputs/figures/fig8_cost_law.png),
[Figure 9](../outputs/figures/fig9_pipeline.png), and the
[machine-readable checks](../outputs/checks/numerical_feature_checks.json).

## Compute and boundary

The full configuration fixes seed 42, ten cotengra candidates, 600,000 NNI
steps per objective, and 60,000 low-temperature polish steps. Per-circuit
recorded runtimes sum to about 29.3 minutes; the completed three-process local
campaign took about 14 minutes wall time.

Figures 8 and 9 evaluate contraction-tree arithmetic rather than executing
large tensor contractions, so an A100 is not the bottleneck here. This package
does not reproduce the paper's Ascend 910/A800 kernel timings, precision study,
or end-to-end acceleration tables; those belong to a separate GPU/NPU execution
target.
