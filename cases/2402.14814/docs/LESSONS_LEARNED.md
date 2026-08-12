# Lessons Learned

## Case Summary

- PaperID: `2402.14814`
- Current status: review pending; theory implementation complete
- Main result: 18 formula-derived targets executed in 3.57 s with zero forbidden accesses
- Main blockers: three omitted calibrations, 17 missing experimental arrays, fresh review

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Keep physical coefficients semantically exact | A doubled quartic coefficient and halved matrix element can accidentally preserve one gap while corrupting the model | Test both printed coefficient semantics and final eigenvalue anchors |
| Derive pulse endpoints before fitting a plotted phase | A visually plausible Ramsey curve can start at the wrong physical state | Add protocol endpoint assertions before RenderContract tuning |
| Separate theory components from experimental panels | Reconstructing an analytic line does not recreate unavailable experimental samples | Give theory and author-data items distinct coverage entries |
| Common energy shifts need review, not immediate error labels | Spectra may use an implicit energy zero | Check gaps, slopes and degeneracies; classify absolute offset separately |
| Fixed font caches improve isolation | Matplotlib may silently spawn processes on first use | Declare a deterministic font cache as a hashed input |

## New Failure Modes And Checks

| Failure mode | Detection |
| --- | --- |
| Compensating parameter/matrix mistakes | assert the printed coefficient and the observable independently |
| Wrong Ramsey phase convention | assert zero-delay and half-period protocol anchors |
| Mixed-panel pixel score inflation | require a predeclared scientific-only crop or mark pixel score N/A |
| Caption/body numerical inconsistency | record both source pinpoints and attempt alternative-quantity falsification |

## Reusable Checks Or Tools

| Candidate | Why reusable | Suggested destination |
| --- | --- | --- |
| pulse-sequence endpoint assertion | catches phase-sign errors before visual comparison | target-contract assertion library |
| additive-spectrum-offset diagnostic | separates energy-zero conventions from wrong gaps/slopes | scientific comparison utilities |
| mixed-panel theory mask contract | allows honest theory-only pixel metrics without digitizing experiments | RenderContract tooling |

## Harness Backlog

| Priority | Improvement | Status |
| --- | --- | --- |
| medium | Add a reusable protocol-endpoint assertion type for pulse sequences | proposed |
| medium | Support theory-only color/geometry masks in mixed experimental panels | proposed |
| low | Detect common additive energy offsets separately from spectral-shape mismatch | proposed |
