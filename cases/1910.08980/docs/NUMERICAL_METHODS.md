# Numerical Methods

The numerical object is a paired benchmark of level-1 QAOA and RQAOA on random
signed cubic Ising models.

1. Generate 16 degree-three graphs for each `n=32` and `n=100`; assign each
   edge an independent coupling `±1`.
2. Prove `E_max` with a zero-gap HiGHS binary MILP.
3. Evaluate the paper's closed-form level-1 correlations.  Optimize beta
   analytically and gamma through a complete-period scan plus local polishing.
4. For RQAOA, recursively contract the strongest correlation to the paper's
   cutoff, solve the remaining Ising model exactly, and reconstruct the full
   spin assignment.
5. Freeze all coupling matrices, seeds, ratios, traces, solver gaps, and hashes
   before rendering.

The final generated ensemble uses declared master seed `191008981` because the
paper's sample identity is missing.  This is `paper_subset`: system sizes, distribution, sample count,
algorithm, and cutoffs are paper-exact, while the individual samples differ.

The A100 is not used for this case.  A measured `n=100` instance spends about
three seconds in branch-and-bound and about 23 seconds in many small recursive
QAOA evaluations; this CPU/MILP workload does not map efficiently to the GPU.
