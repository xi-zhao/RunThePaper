# Numerical methods

## Path-planning object

The paper's path-planning task starts from a stochastically loaded tweezer array
and a target defect-free array. The numerical object is a one-to-one assignment
from occupied atom sites to target sites. The main quality metrics are the
average movement distance and the maximum movement distance.

For the paper-scale Fig. 3 contract, the `101 x 101` target lattice is treated
as spanning the `127 x 127` initial field, with target spacing `(127 - 1) /
(101 - 1) = 1.26` in units of the initial lattice spacing. This geometry brings
the local Hungarian baseline onto the same scale as the paper's reported
`0.5112` average move and `1.82` maximum move baselines. A same-spacing centered
target subarray is not the paper benchmark and should not be used for future
paper-target training data.

The training labels use squared-distance Hungarian assignments. The public
quality contract remains Euclidean: report average movement distance, maximum
movement distance, and their gaps to the selected Hungarian baseline.

## Reduced-scale pilot

The pilot implements the path-planning target as a supervised edge prediction
problem.

- Atom sites and target sites are graph vertices.
- Each atom is connected to nearby targets.
- Atom-atom and target-target edges provide local geometric context.
- The Hungarian assignment gives binary labels for atom-target edges.
- A small PyTorch message-passing model predicts candidate edge probabilities.
- Probability-weighted Hungarian decoding converts edge scores into a valid
  one-to-one assignment.

This first decoder is intentionally conservative. It verifies the learning
pipeline before implementing the paper's modified auction decoder.

## Current limitation

The paper reports a six-layer GNN trained on a million-scale dataset for 288 GPU
hours using four NVIDIA A40 GPUs. This pilot is smaller and should be treated as
a proof that the reproduction chain is live, not as paper-scale reproduction.

## P2WGS continuity object

The P2WGS pilot treats the SLM plane and tweezer plane as Fourier-conjugate
planes. Each target tweezer is modeled as a Gaussian amplitude profile. During
each WGS iteration, the reduced implementation enforces the target amplitude and
phase on the tweezer support, transforms back to the SLM plane, and keeps the
phase-only hologram with fixed input amplitude.

The reported continuity metrics follow the paper text:

- intensity continuity is the mean relative frame-to-frame change of integrated
  local trap intensity;
- phase continuity is the mean wrapped frame-to-frame phase change normalized by
  `2 pi`.

This reduced implementation verifies the metric and algorithm chain. It is not
yet a substitute for the paper's `N=10201` GPU-scale P2WGS benchmark.

## Software assembly object

The joined software pipeline treats the paper's first three numerical figures as
one algorithmic chain instead of three isolated plots:

- Fig. 3 supplies the decoded atom-to-target assignment.
- The assignment defines straight moving-tweezer trajectories for Fig. 4.
- The measured P2WGS frame-generation time becomes the compute term in the
  Fig. 5 pipelined assembly formula.

The current joined run uses the local GNN checkpoint when it exists and records
the assignment source in `software_assembly_pipeline/metrics.json`. This is a
software-interface reproduction, not a hardware claim: SLM refresh, transfer
latency, vacuum lifetime, and real atom feedback remain explicit parameters.

## Sweep object

The sweep runner repeats the joined software pipeline over a small configuration
grid and writes one row per configuration. Each row keeps the assignment source,
movement-distance gaps, P2WGS continuity, frame-generation time, and total
assembly time together. This makes the next iteration measurable: a decoder or
P2WGS change should improve the sweep table, not only make one hand-picked run
look better.

The assignment step is now an explicit strategy field:

- `hungarian_ground_truth`: uses the label assignment as a zero-gap reference.
- `gnn_score_hungarian`: scores atom-target edges with the retrained GNN and
  decodes with linear-sum assignment over predicted scores.
- `modified_auction`: uses a CPU bidding decoder inspired by the auction
  algorithm on the GNN-predicted atom-target scores. This reproduces the
  decoder object but not the paper's GPU-parallel implementation.
