# Scientific Derivation

The central scientific claim is that whenever the two neutrality bands of the one-valley moire model are isolated, their Wilson spectrum has odd winding. The numerical path therefore cannot start from the plotted curves. It starts from the paper's momentum-space Hamiltonian, checks where the central pair is isolated, constructs its occupied projector, and only then evaluates the Wilson product.

The dimensionless continuum object implemented by the solver is

$$
\frac{H_{\mathbf Q\mathbf Q'}(\mathbf k)}{v_F k_D}
=\delta_{\mathbf Q\mathbf Q'}(\bar{\mathbf k}-\bar{\mathbf Q})\cdot\boldsymbol\sigma
+\alpha\sum_{j=1}^{3}
\left(\delta_{\bar{\mathbf Q'}-\bar{\mathbf Q},\bar{\mathbf q}_j}
+\delta_{\bar{\mathbf Q}-\bar{\mathbf Q'},\bar{\mathbf q}_j}\right)T^j.
$$

For each transverse momentum, the topological observable is the eigenphase spectrum of the discretized occupied-subspace product

$$
W(k_1)=U_0^\dagger U_1 U_1^\dagger U_2\cdots
U_{N-1}^\dagger V^{(0,2\pi)}U_0,
$$

with every neighbor overlap replaced numerically by its polar-unitary factor.

The same rule is applied to every auxiliary result: magic-angle velocities are derivatives of independently diagonalized bands; Dirac nodes are zeros of the computed central-band gap with vorticity determined from the local real two-band Jacobian; tight-binding bands are eigenvalues of the printed lattice Hamiltonians; and the Wannier panel is a Fourier transform of the paper's projection construction.

This establishes a causal chain from paper equations to arrays to figures. Pixel comparison is downstream evidence about presentation and curve agreement, never an input to the scientific solver.
