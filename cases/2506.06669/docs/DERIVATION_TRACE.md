# Derivation Trace

## Formula lane and units

Every coded frequency is an angular frequency in `rad/ns`; a plotted value
`x/2pi` in MHz becomes `2*pi*x*1e-3`. Site labels in the paper are one-based;
arrays are zero-based. The numerical runner receives all paper parameters from
configuration and cannot read the PDF, TeX or source figures.

## QS001: XY model in the zero/single-excitation sector

The Hermitian nearest-neighbour interaction is

`H = sum_n omega_n |n><n| + sum_n J_n (|n><n+1| + |n+1><n|)`.

The vacuum `|0>` is added only when relaxation or a coherent input qubit is
needed. Excitation number is conserved by `H`, so starting with zero or one
excitation makes this reduction exact. The second exchange term printed in
main Eq. (1) repeats the lowering operator; Hermiticity and every subsequent
matrix in the Supplement fix it to the conjugate term used above.

## QS002: zig-zag perfect-state-transfer Hamiltonian

Main Eq. (8) prints `mu_n=1` on odd sites, but that assignment contradicts
Fig. 1(b,d), the stated suppression and elimination of even sites, the
Supplement's denominator `E-2mJ` for an even site, and the paper's own target
spectrum. The consistent reconstruction therefore uses

`omega_n = 2 m J` for even `n`, and zero for odd `n`,

`J_n = (J/2) sqrt[(n+2m mu_n)(N-n+2m mu_(n+1))]`.

while retaining the printed coupling expression. Direct diagonalization then gives

`{-(N-1)/2,...,-1,0,2m+1,...,2m+(N-1)/2}` in units of `J`.

This list has the same trace as the parity-corrected Hamiltonian and separates
the low-energy odd-site manifold from the high-energy even-site manifold. The
alternative literal Eq. (8) implementation is related by an energy reflection
but assigns the eigenfunctions to the wrong site parity, so it is rejected.

It is mirror symmetric. At `tau=pi/J` every adjacent eigenphase differs by an
odd multiple of `pi`, so the endpoint amplitude has unit magnitude. This also
sets `tau=1/(2 J_MHz)` when `J/2pi=J_MHz`.

## QS003: analytic three-site population

For equal couplings and middle-site detuning `Delta`, diagonalize

`H3=[[0,J,0],[J,Delta,J],[0,J,0]]`.

With `Omega^2=Delta^2+8J^2`, the end population is

`P3 = 1/4 (cos(Omega t/2)-cos(Delta t/2))^2`

`   + 1/4 ((Delta/Omega)sin(Omega t/2)-sin(Delta t/2))^2`.

The corresponding source expressions for `P1` and `P2` close normalization:
`P1+P2+P3=1`. Evaluating these formulas, rather than sampling the paper
heatmap, produces Fig. 2(a-c), Fig. S2's direct `(Delta,J)` lane and all eight
Fig. S3 scans.

## QS004: fractional state transfer

For odd `N`, only the two central PST couplings change:

`J_((N-1)/2) -> (cos theta + sin theta) J_((N-1)/2)`,

`J_((N+1)/2) -> (cos theta - sin theta) J_((N+1)/2)`.

This is a unitary similarity transformation, so the eigenvalues remain those
of QS002. At `theta=pi/8` and `tau=pi/J`, endpoint populations are both `1/2`
and intermediate populations vanish. The printed deformation produces an
endpoint Bell-plus gauge, while the prose calls the measured state the Bell
singlet. A local endpoint `Z` phase converts the two, and all population and
`|rho|` panels are invariant. The phase gauge is explicit in fidelity checks.

## QS005: separable 3x3 extension

The public text says the same FST condition is applied in both dimensions but
does not print a full 2D matrix. The unique separable nearest-neighbour
construction is the Kronecker sum

`H_2D = H_x tensor I + I tensor H_y`.

Its propagator factorizes. Applying the one-dimensional endpoint split in both
directions produces equal amplitudes on the four corners, hence the stated
four-qubit W state after the declared local phase gauge. This reconstruction is
checked against the `56 ns` corner split and `111 ns` revival.

## QS006: open-system evolution and fidelity

The density matrix obeys

`rho_dot = -i[H(t),rho] + sum_n D[L1_n]rho + sum_n D[Lphi_n]rho`,

with `L1_n=sqrt(1/T1)|0><n|`,
`Lphi_n=sqrt(2/Tphi)|n><n|`, and
`1/Tphi=1/T2-1/(2T1)` for the 1D simulations. Independent collapse operators
are used per qubit; interpreting the source summation as one collective
operator would introduce unreported correlated noise.

For 1D, `T1=16 us`, `T2=0.75 us`; for 2D, `T1=16 us`, `Tphi=0.5 us`. Target
fidelities are direct overlaps with the phase-gauged Bell/W projectors. Reduced
two-end density matrices trace the other sites into `|00>`.

## QS007: static Gaussian parameter noise

For each reported noise intensity, independent Gaussian offsets are added to
either all even-site frequencies, all odd-site frequencies, or every coupling.
The paper specifies 50 PST and 100 FST samples but not the seed or exact scan
array. The case uses a fixed seed and declared uniform scan arrays, stores every
sample value, and reports the mean and standard deviation of `F/F0`.

For PST, the excitation-transfer channel has endpoint amplitude `f`. After
removing the known ideal transfer phase, its process fidelity is
`F_e=(1+|f|)^2/4`. For FST, the fidelity is the overlap with the phase-gauged
endpoint Bell projector.

## QS008: large-m limit

Eliminating an even site gives

`c_even=(J_left c_left + J_right c_right)/(E-2mJ)`.

Taking `m -> infinity` yields the odd-site chain

`J_eff=-(J/2)sqrt[n'((N+1)/2-n')]`,

`omega_eff=-J(N-1)/4`.

Thus increasing `m` suppresses even-site occupation without removing the PST
structure. The Supplement contains an index typo in the intermediate site-3
equation; the final effective formulas and direct Schur complement agree.

## QS009: reconstructed effective pulse envelope

The source gives physical flattop-Gaussian widths (`1.25 ns` for qubit lines,
`2 ns` for coupler lines) and a `7.5 ns` buffer, but not the nonlinear transfer
functions from control amplitude to effective `omega_n(t),J_n(t)`. Applying
the two raw envelopes directly to the effective coefficients destroys the
reported large-m saturation and is therefore not a justified paper model.

The auditable reconstruction uses a shared effective envelope

`g(t)=1/2[erf(t/(sqrt(2)sigma))-erf((t-tau)/(sqrt(2)sigma))]`,

with `sigma=2 ns`, integrated from `-buffer` to `tau+buffer`. It preserves the
Hamiltonian ratios and pulse area. It is validated against the three numerical
anchors reported for Fig. S9 (`m=0,4,50`) but remains `reconstructed`, never
`paper_exact`.

## Public-source discrepancies and missing inputs

- Main Eq. (1) repeats a lowering operator instead of printing its Hermitian
  conjugate.
- Main Eq. (8) assigns `mu_n=1` to odd sites, but Fig. 1, the target spectrum,
  the even-site suppression claim and the Supplement's Schur elimination all
  require the `2mJ` onsite energy on even sites. The numerical model applies
  this parity correction and records the source inconsistency.
- The Supplement's even-site elimination has an index/eigenvalue typo in the
  intermediate equation; its final limit is consistent.
- The printed FST endpoint sign and the named Bell singlet differ by a local
  phase gauge that the magnitude-only density panels cannot resolve.
- Fig. 2's coupler-frequency transfer function, main Fig. 4's `m`, exact noise
  scan arrays/seeds and the physical-control transfer functions are not public.
- Calibration, optimization and experimental tomography arrays are absent.

These omissions limit strict paper-exact claims; they do not justify reading
the original figure pixels into the numerical runner.
