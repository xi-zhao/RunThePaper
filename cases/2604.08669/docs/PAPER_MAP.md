# Paper map

## Core story

The paper addresses the assembly of a defect-free neutral-atom array at the 10k-qubit scale. The bottleneck is not a single numerical routine. It is the combination of two constraints:

1. Path planning must assign many initially loaded atoms to target sites with short, collision-avoiding straight paths.
2. Potential generation must turn those paths into smooth SLM hologram frames without intensity or phase jumps that heat atoms.

The paper's proposed solution is a two-stage algorithm:

- Stage A: GNN path planner plus modified auction decoder.
- Stage B: phase and profile-aware WGS, abbreviated P2WGS.
- Stage C: a pipelined execution model showing that path planning, hologram generation, SLM refresh, and transfer latency fit within the vacuum-lifetime constraint.

## Figure map

| Figure | Role | Reproduction target |
| --- | --- | --- |
| Fig. 1 | Task decomposition | Context only. It defines the interface between path planning and potential generation. |
| Fig. 2 | Algorithm schematic | Context only. It identifies graph construction, decoder, FFT/iFFT, and P2WGS constraints. |
| Fig. 3 | GNN path-planner performance | Numeric target T001. Reproduce Hungarian labels, GNN edge scoring, decoded assignment, and movement-distance metrics. |
| Fig. 4 | P2WGS continuity | Numeric target T002. Reproduce intensity and phase continuity across frames as iteration count changes. |
| Fig. 5 | Runtime and pipelined assembly | Numeric/model target T003. Reproduce the bottleneck-switch timing model and later measure actual GPU timings. |

## Current status

The case now treats the Fig. 3 object as a model-training reproduction target rather than only a plotted proxy:

- T001 has a reduced-scale retrained 6-pass GNN checkpoint, training history, and assignment-distance evaluation.
- T002 has a small P2WGS continuity pilot.
- T003 has the pipelined timing formula encoded and plotted.
- The software-only assembly pipeline now reuses one decoded assignment as the moving-trap trajectory input, runs P2WGS frames, and feeds measured frame-generation time into the timing model.
- The software assembly sweep repeats this joined chain over multiple reduced configurations so the next repair loop has a quality surface instead of a single anecdotal run.
- The same sweep can be forced to Hungarian labels, giving a zero-gap reference for decoder strategy comparisons.

Paper-scale evidence remains blocked by dataset scale, decoder fidelity, GPU time, and by the missing private Zhuifeng implementation.
