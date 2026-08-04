# Lessons learned

1. A single minus sign in a susceptibility definition can make an otherwise
   familiar kernel impossible; close the response/Hessian loop before coding.
2. Momentum-space ultraviolet behavior controls short-distance structure, not
   automatically the coordinate-space long-distance tail.
3. A correct scalar root cannot rescue a benchmark whose source and sign
   contracts are broken.

## New Failure Modes

- The prompt may preserve a source equation but flip the definition of an
  adjacent symbol, leaving the printed formula superficially recognizable.
- A Fourier argument may swap ultraviolet/short-distance with
  infrared/long-distance behavior.
- A synthetic extension may be attributed to the wrong venue and subfield even
  when its mathematical lineage is recoverable.

## Reusable Checks Or Tools

- Response closure: derive `delta rho/delta V` independently from the Hessian
  and compare signs before accepting an inverse-susceptibility formula.
- Tail counterexample: test claims about `q^-2` with both Coulomb `1/q^2` and
  Yukawa `1/(q^2+mu^2)` kernels.
- High-precision guard digits: estimate cancellation order before selecting
  decimal precision for asymptotic probes.
