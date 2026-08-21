# Derivation Trace

1. For a pure initial state, `cos L=sqrt(<psi0|rho_t|psi0>)`. Direct differentiation gives the time-local Bures-angle velocity used by both QSL bounds.
2. The von Neumann trace inequality bounds the overlap with `L_t(rho_t)` by its largest singular value. Time integration gives the operator- and trace-norm ML-type bounds.
3. Cauchy--Schwarz instead gives the Hilbert--Schmidt MT-type bound. Schatten ordering makes the operator-norm contribution the sharpest of the three.
4. The Lorentzian bath is independently represented by an excited amplitude and one damped pseudomode. Eliminating the pseudomode gives `G''+lambda G'+gamma0*lambda*G/2=0` and the paper's closed amplitude.
5. For the initially excited atom, `p=|G|^2` and `dot(rho)=diag(dot(p),-dot(p))`. Its two singular values are both `|dot(p)|`, so the operator, Hilbert--Schmidt and trace norms have factors `1`, `sqrt(2)` and `2`.
6. Therefore `sin^2 L=1-p(tau)` and each QSL curve is the net population loss divided by the corresponding total variation. Monotonic Markovian decay makes the operator bound exactly equal to `tau`; revivals increase total variation and lower the bound.
7. The analytic amplitude is evaluated with a regularized `sinh(z)/z` at the critical point and checked against an independent pseudomode ODE. The time integral is checked by doubling the grid.
8. Two printed identities are tested separately from the figure generator: `||H rho||_tr=<H>` fails for noncommuting positive `H,rho`, and the printed ladder convention lacks the standard factor `1/2`. These discrepancies remain frozen for independent review rather than being tuned away.

Every equation used by the numerical runner is mapped in `EQUATION_CARDS.json` and independently checked before rendering.
