# Numerical methods and scale boundary

The primary isolated campaign is intentionally a convergence-qualified CPU
run.  It uses exact matrix exponentials for finite strips, analytic two-level
step exponentials in Bloch space, a gauge-aware Fukui mesh for Chern numbers,
and a central-difference three-torus integral for the return-map winding. Both
primitive reciprocal seams use the required $\sigma_z$ basis transition before
the momentum derivatives are formed.

The paper prints the physical Hamiltonian parameters and the $M=1$ Floquet
replica truncation, but not every finite-system choice used to render Figs. 3
and 6. Therefore strip width, momentum grid and edge-weight display cutoff are
declared reconstruction parameters. The independent time-product grid is a
convergence-check choice, not a recovered author setting. None of these values
is inferred by fitting paper pixels.
The primary configuration is sized to run in seconds to minutes and includes
unitarity, Hermiticity, topology, time-convergence and limiting-case gates. The
weak-drive open-y matrix is additionally rebuilt by independent inverse
Bloch-Fourier quadrature and compared to the hand-derived bond construction.

`config/paper_scale.json` provides the complete higher-resolution path for all
nine targets: wider strips, denser Brillouin-zone and phase scans, and a denser
time product. Figure 3(d) is a genuine two-axis campaign rather than a decorated
one-dimensional cut: two source-convention branches share a frozen grid, and
each open-gap point receives direct winding and Chern evaluations. Ambiguous
finite-grid points are adaptively recomputed on a finer momentum-time mesh.
The run remains `paper_scale_reconstructed`, not `paper_exact`,
because the paper omits the original finite-size and grid choices and because
the $\delta_{AB}$ notation contains a factor-two conflict. Figs. 3(a-c) use the
displayed-equation reading, while the phase scan records both readings. This is
an evidence boundary, not a missing implementation or local-compute failure.

The matrix sizes do not benefit materially from an A100.  The accepted route is
deterministic SciPy/NumPy CPU linear algebra; using the available GPU would add
backend complexity without changing the scientific scale boundary.
