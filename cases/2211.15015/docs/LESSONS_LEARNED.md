# Lessons learned

## New Failure Modes

1. **Font discovery is part of reproducibility.** Matplotlib silently probes fontconfig through child processes. A prebuilt, version-matched font cache is required when the numerical runner forbids subprocesses.
2. **Output names belong to the contract.** The first clean isolated run computed correctly but could not be accepted because renderer filenames lacked target prefixes. A regression test now compares renderer names with both run contracts.
3. **Portable evidence paths matter.** Target checks must store workspace-relative paths, not ephemeral isolated staging paths.
4. **A plot is not a scientific pass.** The reduced run emits all 17 figures, yet every target remains `pending_paper_scale`; output existence and paper-claim validation are separate fields.
5. **T1-heavy vertex dynamics is not automatically a GPU workload.** Condition-level CPU parallelism is the trusted first scaling axis; an A100 becomes valid only after a parity-proven kernel exists.
6. **Source access needs a separate lane.** Side-by-side comparisons are built only after attested data hashes are frozen and are verified not to mutate those data.
7. **Paper review should preserve weak leads without overclaiming.** Cross-reference, factor, and sign issues are recorded as inconclusive until the protocol-v2 fresh reviewer attempts to falsify them.

## Reusable Checks Or Tools

Reusable harness requests: cache/version-check plotting fonts in isolated bundles; statically compare declared outputs with renderer target maps; reject absolute staging paths in generated target evidence.
