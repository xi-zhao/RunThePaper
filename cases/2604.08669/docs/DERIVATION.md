# Derivation of the atom-array assembly reproduction

The paper decomposes defect-free atom-array assembly into assignment, motion
planning, hologram generation and execution timing. This case reconstructs
those scientific objects independently and treats the trained path planner as
a model artifact rather than as a plotted curve alone.

## Assignment objective

Let \(x_i\) be occupied source sites and \(y_j\) target sites. A valid
one-to-one assignment \(\sigma\) minimizes the total squared transport cost

\[
L(\sigma)=\sum_j \lVert x_{\sigma(j)}-y_j\rVert_2^2.
\]

The Hungarian solution is the exact optimization baseline. The reproduced GNN
constructs a sparse \(K\)-nearest-neighbour candidate graph, predicts edge
scores and decodes a consistent assignment. Its paper-facing observables are
the mean and maximum Euclidean transport distances, compared with the exact
assignment on held-out atom-loading samples.

## Geometry and training contract

The paper-scale geometry uses a \(127\times127\) source lattice with loading
probability 0.75 and a \(101\times101\) target lattice spanning the same field,
so the target spacing is \((127-1)/(101-1)=1.26\). A reproduction run records
the generated sample seeds, exact labels, graph parameters, model
architecture, optimizer, checkpoint, loss history and held-out metrics. A plot
without a reloadable checkpoint and evaluation path is not counted as model
reproduction.

## Optical update

The SLM and tweezer planes are related by a Fourier transform. Each P2WGS
iteration propagates the phase-only SLM field to the tweezer plane, imposes the
desired Gaussian support and target phase, inverse-transforms it, then retains
the updated SLM phase with fixed input amplitude. Intensity and wrapped-phase
continuity between successive frames quantify whether the generated hologram
sequence can drive smooth atom motion.

## Timing model and boundary

For \(F\) hologram frames the independently reconstructed latency is

\[
T_{\mathrm{total}}=T_{\mathrm{path}}+T_{\mathrm{transfer}}
 +F\max(T_{\mathrm{generation/frame}},T_{\mathrm{SLM\ refresh}}).
\]

The reduced run verifies data generation, labels, training, checkpoint reload
and evaluation. Paper-scale training remains objectively separate: it needs
million-scale graph samples and the GPU-parallel decoder. The public package
therefore exposes runnable reduced training while retaining the paper-scale
resource boundary.
