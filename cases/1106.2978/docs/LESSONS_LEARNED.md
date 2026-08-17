# Lessons Learned

## What worked

- The exact MPO was checked by a mathematically different full-Liouvillian solver rather than a second copy of the same recurrence.
- Scientific arrays were frozen before any original-figure access; RenderContract could improve presentation without changing physics.
- Unreachable auxiliary-state pruning solved easy-axis stability while preserving the exact finite path sum.
- One pixel contract per scientific panel prevented a strong whole-canvas score from hiding a weak inset or axis.

## Failure analysis

| Observed problem | Direct cause | Root cause | Resolution |
| --- | --- | --- | --- |
| initial current dataset stopped at `n=100` | production configuration used an incomplete x-domain | inventory captured caption parameters but not the complete plotted axis | bind axis domain `n=2..400`, rerun isolated numerics, refreeze data |
| easy-axis products underflowed at long size | numerically multiplied paths that could never return to the vacuum | auxiliary truncation encoded the maximum index but not remaining-step reachability | exact reachability pruning plus scaled tridiagonal contraction |
| full-canvas similarity could look strong despite inset typography | white background dominates whole-canvas MAE | whole-canvas score is not target-level scientific evidence | predeclare panel/inset scientific crops as primary; keep full canvas diagnostic |

## Reusable rule

Before freezing a paper-scale configuration, inventory not only captions and printed parameter lists but also every axis domain, inset domain and visible series endpoint. A missing scientific domain must return to the isolated numerical channel; it can never be repaired by renderer interpolation or axis stretching.

## New Failure Modes

- `axis_domain_omission`: a caption-complete inventory can still omit the numerical range encoded only by plotted axes.
- `unreachable_path_underflow`: exact auxiliary paths that cannot contribute may still destabilize a naive contraction if they are propagated numerically.

## Reusable Checks Or Tools

- Axis-domain-to-config validator: compare every numeric figure/inset axis domain with the paper-scale run contract before isolation.
- Return-reachability pruning for banded transfer processes: retain only auxiliary states that can still reach the required terminal state.
- Scientific-domain repair gate: if data coverage is incomplete, reject any RenderContract-only repair and require a new attested numerical run.
