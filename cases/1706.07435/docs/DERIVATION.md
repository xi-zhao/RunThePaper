# Equation-level derivation

This case follows Shen, Zhen, and Fu, *Topological Band Theory for
Non-Hermitian Hamiltonians*, Phys. Rev. Lett. **120**, 146402 (2018). The
numerical artifacts are generated from the equations below; the paper figures
are used only after generation as visual references.

## 1. Biorthogonal Chern number

For a separable non-Hermitian band, the four left/right Berry-curvature
definitions integrate to the same integer:

$$
N_n^{LL}=N_n^{LR}=N_n^{RL}=N_n^{RR},\qquad
N_n^{\alpha\beta}=\frac{1}{2\pi}\int_{BZ}
\epsilon_{ij}B_{n,ij}^{\alpha\beta}\,d^2k.
$$

The equality follows because the differences between the four connections are
globally defined gauge terms whose curl integrates to zero on the Brillouin
torus.

## 2. Generalized non-Hermitian Dirac spectrum

For

$$
H=(\mathbf{k}+i\boldsymbol\kappa)\cdot\boldsymbol\sigma
 +(m+i\delta)\sigma_z,
$$

direct diagonalization gives

$$
E_\pm=\pm\sqrt{k^2-\kappa^2+m^2-\delta^2
 +2i(\mathbf{k}\cdot\boldsymbol\kappa+m\delta)}.
$$

Exceptional points occur where both the real and imaginary parts of the
radicand vanish. These two real constraints explain the generic codimension
two of exceptional degeneracies.

## 3. Domain-wall matching

With a mode proportional to $e^{x/\lambda_i}$ on each side of an interface,
the characteristic equation is

$$
E^2=(m_i+i\delta_i)^2+(k_y+i\kappa_{i,y})^2
 -(\lambda_i^{-1}-\kappa_{i,x})^2.
$$

The two half-space spinors must be proportional. Solving the shared-spinor
condition gives the edge energy and the two inverse localization lengths. The
accepted branch must decay into both half spaces and satisfy both matrix
residuals.

## 4. Exceptional-point vorticity

For the paper convention $\sigma_+=\sigma_x+i\sigma_y$, the canonical model is

$$
H=\sigma_+ + k_x\sigma_x+k_y\sigma_y,\qquad
E_\pm^2=k_x^2+k_y^2+2k_x+2ik_y.
$$

On the unit loop $(k_x,k_y)=(\cos\theta,\sin\theta)$, the radicand is
$1+2e^{i\theta}$ and winds once around zero. A continuous square root changes
sign after one circuit, so the two eigenvalue sheets exchange and

$$
\nu_{mn}(\Gamma)=-\frac{1}{2\pi}\oint_\Gamma
\nabla_k\arg(E_m-E_n)\cdot d\mathbf{k}
$$

has magnitude $1/2$. At the origin the Hamiltonian is nonzero, rank one, and
nilpotent, proving that the degeneracy is defective.

## 5. Lattice cylinder

The supplemental lattice Hamiltonian is

$$
H(\mathbf{k})=(\sin k_x+i\kappa_x)\sigma_x
 +(\sin k_y+i\kappa_y)\sigma_y
 +(\cos k_x+\cos k_y+m+i\delta)\sigma_z.
$$

Fourier transforming only $k_x$ yields an open-$x$, periodic-$y$ block
tridiagonal matrix. For the paper value $n=40$, each sampled $k_y$ therefore
requires one dense $80\times80$ complex eigensystem. Boundary weights of the
eigenvectors identify the chiral edge branches.

## 6. Hybrid exceptional point

At the merger of two exceptional points, the local dispersion becomes

$$
E_\pm=\pm\sqrt{k_x^2+k_y^2+2ik_xm}\qquad(m=\delta).
$$

Along $k_y=0$ the leading term is proportional to $\sqrt{k_x}$, whereas along
$k_x=0$ it is proportional to $|k_y|$. The fitted exponents are therefore
$1/2$ and $1$, respectively, while a small loop has zero net winding because
the opposite half charges have merged.

## Code trace

- `code/src/nonhermitian_topology.py` contains the equation-level model.
- `code/scripts/run_main_fig1.py` through `run_supp_fig4.py` generate the six
  scoped figures and machine-readable checks.
- `code/tests/test_nonhermitian_topology.py` checks direct diagonalization,
  branch exchange, defectiveness, domain-wall limits, and cylinder identities.
