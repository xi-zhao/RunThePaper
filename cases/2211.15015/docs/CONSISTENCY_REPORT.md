# Paper consistency report

## Review posture

The implementation attempts to falsify as well as reproduce the paper. A mismatch is not called a paper error unless protocol v2 has paper-exact inputs, frozen independent numerics, convergence, two distinct strong checks, an explicit falsification attempt, and a fresh-context independent review.

## Leads

### C001 — Fig. 4 prose cross-reference

The prose points distributions and snapshots to panels shifted by one, while the caption and source assets place them in Fig. 4(c) and Fig. 4(d,e). This is a stable editorial cross-reference discrepancy. It has no numerical effect and is currently `inconclusive` pending fresh review.

### C002 — main-text area-force magnitude

The verbal main-text magnitude omits the factor `1/2` obtained by differentiating the triangle contribution to Eq. (1); Appendix Eqs. (A11–A12) and the direct energy gradient contain the factor. The implementation uses the energy gradient and passes a central finite-difference check. Because the sentence may be shorthand rather than an executable formula, classification remains `inconclusive`.

### C003 — appendix gradient sign label

Part of the appendix labels a vector as `∇E` while its direction matches the force `-∇E`. The code keeps energy gradient and force as separate objects and verifies passive energy descent. The issue appears notational and remains `inconclusive`.

## Current conclusion

No paper-error candidate is emitted. The three leads are included in the falsification bundle so a fresh reviewer can accept, reject, or refine them without seeing the reproducer's conversation.
