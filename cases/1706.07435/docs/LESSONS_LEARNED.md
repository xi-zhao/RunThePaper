# Lessons learned

1. The scientific object must be frozen before visual tuning. Here that object
   consists of the Hamiltonians, paper parameters, branch conventions,
   boundary conditions, numerical grids, and physical assertions.
2. Principal complex square roots are not continuous eigenvalue sheets.
   Explicit phase unwrapping is required to observe branch exchange and the
   half-integer exceptional-point charge.
3. An edge-looking eigenvalue is not enough. The domain-wall solution must pass
   localization and spinor-matching checks, and cylinder states must carry
   boundary weight.
4. Dense diagonalization is appropriate for the paper-exact $80\times80$
   cylinder matrices. Replacing it with a proxy would save little time and
   weaken the reproduction claim.
5. Scientific fidelity and raster similarity answer different questions. The
   former reaches 90/100 with machine-precision residuals and complete panel
   coverage; the latter is initially 60.28/100 because layout, 3D camera,
   typography, and mesh density still differ.
6. Pixel comparison is a downstream audit only. It may guide render parameters,
   but it may not create or modify scientific arrays from paper pixels.
