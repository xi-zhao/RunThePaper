# Lessons Learned

## Case Summary

- Final status: numerical feature reproduction plus complete feasible proxy campaign.
- Exact/subset results: Möbius algebra and Fig. 3 gate accounting.
- Proxy results: Figs. 4/5/8 eight-family matrix, Fig. 6 scaling, Fig. 7 sensitivity.
- Remaining blockers: concrete SAT input, author route state, ZX setup.

## What Worked

- Exhaustive bounded algebra checks were stronger and cheaper than sampling.
- Vector-source inspection recovered the auditable Fig. 3 support stream.
- A durable approval/contract kept proxy output separate from exact claims.
- Eight-family coverage and QFT/GHZ controls exposed whether the effect was tied
  to many-body support rather than a universal router bias.
- Fixed-route sensitivity isolated native-fidelity assumptions efficiently.

## What Changed After User Feedback

The first workflow treated the exact-data boundary as a stopping point after a
small proxy pilot. The user clarified that every feasible reproduction should
run. The corrected control rule is:

> Exact-vs-proxy is a claim boundary, not an execution boundary.

Once proxy scope is approved, the agent should exhaust all bounded, meaningful,
and locally verifiable proxy targets before requesting author artifacts.

## Generalized Lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Separate exact and proxy target IDs | Proxy completion must not inflate exact claims | Keep distinct verdicts and score caps |
| Expand an approved proxy systematically | A pilot alone can leave cheap evidence unused | Inventory every figure/family/observable first |
| Preserve mismatches | Tuning can hide a weak route model | Record failed contours and diagnose the model |
| Treat route residency as physics-relevant state | Gate census alone cannot determine movement/idle balance | Require route exposures before sensitivity claims |
| Aggregate agent verdicts | Reading one pilot file can cause premature stop | Build a campaign verdict over all component checks |

## New Failure Modes

| Failure mode | Detection | Interpretation |
| --- | --- | --- |
| `proxy_break_even_not_reproduced` | no zero contour in declared Fig. 7 grid | toy return-to-storage route over-penalizes ZAP |
| `premature_proxy_stop` | feasible target inventory remains after a pilot | agent control-flow defect, not scientific blocker |
| `depth_ordering_mismatch` | counts match but DAG depth differs | exact instruction order is missing |

## Reusable Checks Or Tools

| Candidate | Reuse value | Current location |
| --- | --- | --- |
| Proxy campaign aggregate verdict | prevents stopping after one successful component | `scripts/summarize_proxy_campaign.py` |
| Fixed-route fidelity reevaluator | separates routing from native-error scans | `src/proxy_router.py` |
| Benchmark-contract completeness gate | prevents guessed systems-paper reruns | harness backlog |

## Harness Backlog

The existing benchmark-contract backlog remains valid. A future generic helper
should additionally model a proxy campaign as component targets plus one
aggregate verdict, so the agent stops only when every approved component is in a
terminal state.
