# Numerical methods

The reference backend is float64 NumPy on CPU. This choice is deliberate: T1 events mutate a sparse polygonal topology and are branch-heavy, so an A100 does not automatically accelerate the dominant control flow. Independent parameter conditions are the primary parallelization axis; a future CUDA force kernel must pass CPU parity before use.

Cell polygons are stored as ordered vertex cycles on a sheared periodic lattice. Geometry is locally unwrapped with nearest images. Analytic area/perimeter gradients generate forces; explicit Euler advances reduced coordinates and Euler–Maruyama advances polarization. A T1 flip updates four cell cycles and repositions the new edge perpendicular to the old edge.

Every condition is bound to the semantic config hash, implementation hash, and condition ID. Preparation states are cached per `(p0,seed)`. Long samples are written as nonoverlapping atomic chunks; model checkpoints include flattened topology, positions, polarizations, RNG state, progress, and state hash. Aggregation fails on gaps, overlaps, stale hashes, incomplete targets, or a mismatched config.

Paper-scale sampling uses a fixed number of stress samples per strain, so storage stays bounded across shear rates even though the integration step count grows as `1/gamma_dot`. Only scalar histories and selected final network states are retained; full per-step vertex states are not archived.
