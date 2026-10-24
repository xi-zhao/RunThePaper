# Numerical methods and rerun scope for 1612.02058

This public package is a projection of a frozen native PRAgent run (`source_run_id` and `source_snapshot_sha256` are recorded in `outputs/checks/publication_provenance.json`). The included `code/model` files are independently written implementations, controls and checkers. `code/scripts/run_reproduction.py` copies the model to a fresh directory and executes one selected entrypoint; it never rewrites frozen outputs.

Because the ten source cases used different primary entrypoints, inspect the included model files before treating a rerun as representative. A fresh calculation is scientific evidence for the executed program only; it is not whole-paper acceptance and does not alter the authoritative status. The frozen source export may contain more evidence than this deliberately bounded public projection.
