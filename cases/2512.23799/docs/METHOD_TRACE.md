# Method Trace

## Scientific method

The paper propagates circuit-level Pauli errors through a magic-state
preparation circuit and evaluates the resulting Clifford/stabilizer problem.
This case follows that logic without reading author code or numerical arrays.

## Clean-room implementation

`src/steane_h_prep.py` independently implements the public Fig. 9 Steane
logical-H circuit, uniform circuit-level Pauli noise, postselection, and ideal
decoding. The frozen configuration uses the literal gate columns, deterministic
ASAP scheduling, full-lifetime idling, five preregistered physical-error probes,
and 2048 shots per probe.

`scripts/run_attested_reproduction.py` runs the four targets in an isolated
directory. Its attestation records the Git SHA, configuration hash, declared
inputs, file-access list, output hashes, and zero forbidden reference/source
reads. Only after those outputs are frozen does
`scripts/compare_frozen_outputs.py` read the digitized paper curves for
diagnosis.

## Result boundary

- T001 and T002 were genuinely attempted. Structural and intrinsic physics
  checks pass, but their frozen values do not reproduce the paper curves. They
  are `attempted_not_reproduced`, with an implementation defect still a live
  hypothesis for fresh review.
- T003 is `externally_blocked`: the publication omits the original machine,
  software builds, timer protocol, repetitions, and raw absolute timing table.
  The local runtime proxy is mechanism evidence only.
- T004 is `reproduced`: the fitted sampling exponent is
  `-0.49814326365138706`, consistent with `-1/2`.

The authoritative evidence is under `outputs/checks/`, especially
`attested_science_checks.json`, `frozen_reference_comparison.json`, and
`publication_input_audit.json`.
