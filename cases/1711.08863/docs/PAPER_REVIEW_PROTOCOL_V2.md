# Protocol-v2 Paper Review

## Current Verdict Boundary

- Reproducer-side audit status: `passed`
- Protocol-v2 paper assessment: `inconclusive`
- `paper_error_candidate`: **no**
- Reason: Main Fig. 2 survives the implemented falsification checks, and one
  stable supplementary operator-label discrepancy was found, but a genuinely
  fresh inventory-first reviewer has not yet validated either conclusion.
- Machine artifact: `outputs/checks/paper_review_protocol_v2.json`

This document is a formal pre-review audit, not a substitute for
`independent_review.json`. A disagreement is not promoted merely because it is
stable in the reproducer's context.

Its implemented target scope is T001 only. The later whole-paper atomic audit
declares T002-T004 as uncovered analytic claim families; this protocol artifact
does not review them and must not be cited as whole-paper scientific approval.

## Active Falsification of the Numerical Claim

| Attempt | Independent method | Result | Evidence |
| --- | --- | --- | --- |
| Table-I multiplicities may disagree with general Eq. (2) sums | alternative implementation | survived | maximum residual below `1e-12` on 1001 points |
| Zero braided decay may force `g=0` | limiting case at `phi=pi/2` | survived | `(g, Gamma_a, Gamma_b, Gamma_coll)/gamma = (1,0,0,0)` |
| The plot may be grid-sensitive | 1001/2001 shared-point refinement | survived | maximum shared-point residual below `1e-12` |
| Fig. 2 caption may omit or duplicate a visible series | independent curve inventory | survived | 4 solid + 5 dashed + 4 dotted = 13 curves |

These checks provisionally support T001. The formal assessment remains
`inconclusive` until a fresh reviewer independently inventories the paper and
repeats a falsification attempt from the restricted protocol-v2 bundles.

## Stable Supplementary Formula Discrepancy

Supplement Eq. `ME2AtomsMirror` prints

`gamma_2 [1+cos(phi_1+2 phi_2)] D[sigma_-^a]`.

The collapse operator on the preceding line attaches that coefficient to
`sigma_-^b`, so the expanded term must be `D[sigma_-^b]`.

Two distinct checks find the same discrepancy:

1. Analytic expansion: the squared `sigma_-^b` amplitude is exactly
   `gamma_2[1+cos(phi_1+2 phi_2)]`.
2. Limiting case: set `gamma_1=0` and start from `|g,e>`. The correct term gives
   `d<P_e^b>/dt=-2` at zero phase, while the printed `a` operator gives zero.

Source pinpoints:

- TeX: `paper-source/extracted/SuppMat_arXiv.tex:286-295`
- Published supplement extraction: `raw/paper.txt:841-857`, Eq. (S21)

Current classification: `inconclusive`, likely a local symbol typo. It does
not affect Main Fig. 2 because Table I attaches the rate to atom `b` correctly
and T001 evaluates coefficients rather than integrating the misprinted
operator equation. Promotion to `paper_error_candidate` is forbidden until a
fresh review confirms the source and the full protocol-v2 evidence contract.

## Editorial Findings Without Numerical Impact

- Main all-to-all paragraph (`GiantAtoms_arXiv.tex:247`) points its triangular
  graph/circuit to Fig. 3(b,c), although the paragraph and assets identify
  Fig. 4(b,c).
- The supplement's “Braided giant atoms” subsection
  (`SuppMat_arXiv.tex:716-721`) begins “For separate giant atoms” while citing
  and using the braided master equation.

Both are recorded as editorial defects with protocol-v2 assessment
`inconclusive`; neither changes a numerical target.

## Promotion Rules

Only the fresh reviewer may emit `paper_supported`, `reproduction_defect`, or
`paper_error_candidate`. A paper-error candidate requires all of:

- paper-exact parameters and frozen independent data;
- convergence evidence;
- two distinct passing independent cross-check methods, including a strong
  analytic/alternative/invariant/limit/normalization check;
- an explicit falsification of the paper claim;
- the paper source pinpoint, independent result, gap, tolerance basis, and
  evidence paths;
- a current fresh-context protocol-v2 review.

Any missing element leaves the result `inconclusive` or, if traced to this
case's code/configuration, `reproduction_defect`.
