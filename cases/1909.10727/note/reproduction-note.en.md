# Dynamically corrected gates and error correlations

Edmunds et al. measured spatiotemporal error correlations using randomized benchmarking on trapped ions. We implemented primitive, CORPSE, WAMF and BB1 pulses and propagated each segment exactly for piecewise constant noise. The audit addressed 18 numerical panels by calculation or readback from published plots. [Published paper](https://doi.org/10.1103/PhysRevResearch.2.013156)

## Recalculation

For 50 new length-100 Clifford sequences, increasing the number of noise realizations averaged from 1 to 200 reduced the variance across sequences by factors of 2.24 for quasistatic noise and 112.70 for fast noise. The ideal implementations of all 24 Cliffords agreed to numerical precision.

A shared static detuning leaves a first-order term of −2iδY for the +π, −π identity pair described in Appendix C. Replacing that pair with two rotations in the same direction changed the block-length-100 CORPSE variance ratio from 15.88 to 133.73 on otherwise identical sequences. The published plot gives approximately 82.67. This control isolates the sensitivity to the identity construction. [Derivation](../docs/DERIVATION.md) · [Scalar checks](../outputs/checks/numerical-checks.json)

For the amplitude-noise moment in Table III, a clock updated each physical π/2 duration gives π²/24. Splitting each pulse into two independent intervals gives the printed π²/36. A two-sample counterexample also gives a finite mixed term in Eq. (5) despite zero sample-mean noise.

## Scope

This is a partial reproduction. The original sequence IDs, hardware idle pulses and AWG noise waveforms, and shot-resolved single- and five-ion readouts are needed to resolve the experimental magnitudes and uncertainties. The published five-ion statistics and single-ion plot allow only aggregate comparisons. The included figure and arrays come from new propagation. [Rerun instructions](../docs/NUMERICAL_METHODS.md) · [Missing inputs](../docs/DATA-AVAILABILITY.md)
