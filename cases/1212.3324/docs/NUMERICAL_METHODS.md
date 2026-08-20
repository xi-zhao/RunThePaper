# Numerical methods and scale boundary

The primary isolated campaign is intentionally a convergence-qualified CPU
run.  It uses exact matrix exponentials for finite strips, analytic two-level
step exponentials in Bloch space, a gauge-aware Fukui mesh for Chern numbers,
and a central-difference three-torus integral for the return-map winding.

The paper prints the physical Hamiltonian parameters but not every numerical
choice used to render Figs. 3 and 6.  Therefore strip width, momentum grid,
time grid, edge-weight cutoff and Floquet replica cutoff are declared
reconstruction parameters.  They are not inferred by fitting paper pixels.
The primary configuration is sized to run in seconds to minutes and includes
unitarity, Hermiticity, topology, time-convergence and limiting-case gates. The
weak-drive open-y matrix is additionally rebuilt by independent inverse
Bloch-Fourier quadrature and compared to the hand-derived bond construction.

`config/paper_scale.json` provides the complete higher-resolution path for all
nine targets: wider strips, denser Brillouin-zone and phase scans, and a denser
time product.  It remains `paper_scale_reconstructed`, not `paper_exact`,
because the paper omits the original finite-size and grid choices and because
the $\delta_{AB}$ notation contains a factor-two conflict. Figs. 3(a-c) use the
displayed-equation reading, while the phase scan records both readings. This is
an evidence boundary, not a missing implementation or local-compute failure.

The matrix sizes do not benefit materially from an A100.  The accepted route is
deterministic SciPy/NumPy CPU linear algebra; using the available GPU would add
backend complexity without changing the scientific scale boundary.
