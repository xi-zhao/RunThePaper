# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 2 | Both numerical main figures pass paper-exact scientific checks. |
| feature_match | 0 | No target is limited to qualitative agreement. |
| partial_match | 0 | No in-scope target remains partial. |
| blocked | 0 | No external data or compute blocker remains. |
| not_in_scope | 3 | Main and Supplemental schematics are contextual only. |

## Per-Target Consistency

| Target | Paper item | Level | Evidence | Remaining difference | Reason |
| --- | --- | --- | --- | --- | --- |
| `T001` | Main Fig. 2 | `exact_match` | `t001_final_run.json`, `t001_scientific_comparison.json` | Monte Carlo points are not point-identical | paper seed not disclosed |
| `T002` | Main Fig. 3 | `exact_match` | `t002_final_run.json`, `t002_scientific_comparison.json` | comparison uses digitized pixels, not author arrays | source arrays and solver tolerances not published |

## Source-Level Findings

### Liouville transpose convention

The Supplemental displayed loss terms are inconsistent with
\(\mathrm{vec}(ABC)=(A\otimes C^T)\mathrm{vec}(B)\). Direct derivation gives

\[
L\otimes\bar L
-\tfrac12 L^\dagger L\otimes I
-\tfrac12 I\otimes(L^\dagger L)^T.
\]

The discrepancy does not change the reproduced models because
\(L^\dagger L\) is real diagonal.

### Fig. 3 endpoint

The paper-linked scripts allocate \(0:0.01:10\) but loop over 1000 entries,
ending at \(9.99\). The source-exact grid was used for comparison. Every
retrieved map also satisfies the \(t=10\) constraint within the declared
\(5\times10^{-4}\) feasibility tolerance.

### Cost notation

The logarithmic monotone is \(\gamma_\epsilon=\log_2\kappa_\epsilon\); the
figure displays the operational overhead \(\kappa_\epsilon\). Both columns are
stored so the distinction remains auditable.
