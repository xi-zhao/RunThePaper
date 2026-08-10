# Numerical Methods

| Target | Numerical object | Resolution/training | Validation | Parameter status |
| --- | --- | --- | --- | --- |
| T001 | Eq. (8) real two-mode kernel | 121×121 grid, three `c` | center=1, monotonic half-height width | paper-exact |
| T002 | six SVC decisions | 121×121 render grid; 50/150 and 500/100 splits | accuracy and capacity checks | benchmark metadata reconstructed |
| T003 | real two-mode Fock features | 14 even terms/mode; 1/500/5000 epochs | final train=1, held-out <1 | benchmark/cutoff reconstructed |
| T004 | four-block CV circuit; sector-factorized paper-scale variant | accepted cutoff 8 plus code-ready cutoffs through 32; 32 params; 5000×5 Adam; three seeds | dense-vs-sector parity, retained mass, cutoff-map convergence, accuracy and loss reduction | reduced result; paper-scale code ready; missing training metadata |

## Efficiency

- Analytic vectorization evaluates each SVC Gram/grid block directly; no state-vector simulation is used for the implicit kernel.
- The perceptron stores only even Fock components, reducing its two-mode feature dimension to `14²`.
- T004 applies local gates as `8×8` matrices and the beamsplitter as `64×64`; a full isolated run takes about 113 seconds on one local CPU thread.
- The accepted cutoff-8 feature run remains a local CPU task. The cutoff-32 convergence
  campaign uses fixed-photon sectors and tensor-factorized local gates, and is routed to
  the user's A100 one condition at a time.
