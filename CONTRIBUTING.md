# Contributing

RunThePaper accepts contributions that make a reproduction case more accurate,
clear, runnable, or honest.

Good contributions include:

- fixing a derivation mistake;
- improving a numerical method;
- adding a missing validation check;
- reducing ambiguity in a reproduction note;
- reporting a mismatch between generated results and the paper;
- adding a new case with clear evidence boundaries.

Please do not add original paper PDFs, publisher source archives, or original
figure assets unless the license explicitly allows redistribution and the case
documents that permission.

Limited source-versus-reproduction comparison panels are allowed only when they
are necessary for validation. Use the minimum source excerpt, label both sides,
cite the official paper, keep the standalone source panel out of the repository,
and state that visual agreement is not author-data-level equivalence.

Every formula/theory case must ship, so readers can follow the science:

- an **equation-level derivation** at `docs/DERIVATION.md` — the actual equations
  the reproduction depends on, in the order understand → derive → numericalize.
  It is generated from the reproduction's equation cards, not hand-written after
  the fact, and the numerical code must follow the derivation, not precede it;
- **source-vs-reproduction comparison panels** under `docs/comparisons/` for the
  reproduced figures (see the limited-excerpt rules above).

Reproductions of algorithm or benchmarking papers may substitute a
method/algorithm trace for the equation derivation. A standalone benchmark,
synthetic task, source-contract audit, or internal evaluation is not a
RunThePaper case and must not receive its own catalog entry.

For each case, keep the public boundary clear:

- generated data belongs in `outputs/data/`;
- generated figures belong in `outputs/figures/`;
- limited validation comparison panels belong in `docs/comparisons/`;
- validation results belong in `outputs/checks/`;
- paper/source references should be links or citations, not copied raw assets.

In `cases/catalog.json`, record the preprint and formal publication as separate
objects. A published entry needs its formal title, venue, full citation, DOI,
and article/page/PII locator. If no formal publication can be found, use
`publication.status: "not_recorded"` together with `checked_at`; do not use an
empty DOI as an implicit status.

Case files and lifecycle fields are generated from the corresponding PRAgent
master projection. A contribution must update the PRAgent case and its
`workspace/publish_manifest.json` first; RunThePaper does not accept a manually
authored case directory or completion claim.

At least one paper identity must be verifiable. A case may have an unrecorded
preprint or an unrecorded formal publication, but never both. Before adding a
case, confirm that its code, generated data, figures, and checks reproduce
claims or numerical results belonging to that identified paper.

Every case must include scientific Python code in `code/` beyond
`verify_public_artifacts.py`. The verifier proves that frozen files are intact;
it does not replace the implementation that computes or reanalyzes the paper's
scientific result.

## Organize the library and record updates

The public library has one case catalog, one editorial organization file, and
Git history:

- `cases/catalog.json` receives paper identity, scientific state and evidence
  pointers from the PRAgent projection.
- `cases/collections.json` assigns every case to one primary research
  collection. Each collection also owns bilingual prerequisites and an ordered
  learning route with a concrete exercise per paper. Refer to existing paper
  IDs; do not copy scientific status into the editorial metadata.
- `UPDATES.md` is generated from committed case history. It distinguishes
  additions, updates and removals, and names the changed kinds of material.
  Reading routes and directory-only changes are not scientific case updates.

For each increment:

1. Fix or reproduce the paper in PRAgent, validate its evidence and export the
   permitted public files through its publish manifest.
2. Assign a new paper to a collection; revise learning routes when a paper is
   removed or a better starting sequence is available. Every case must appear
   in exactly one primary collection.
3. Regenerate navigation, run the public checks below, review and commit the
   case projection. This commit is the immutable source of the update record.
4. Run the generator again to include that commit in `UPDATES.md`; verify and
   commit the changed navigation. Only changed pages are written. A repeated
   run with the same inputs changes no files.

The generator refreshes both READMEs, `CASES.md`, `LEARNING_PATHS.md`,
`UPDATES.md`, and case navigation together. It reads complete local Git history;
a shallow clone must retrieve missing history before regeneration. It does
not fetch papers, run scientific experiments, commit, or publish on its own.

## Checks before a pull request

Regenerate navigation after changing a catalog entry or learning route:

```bash
python scripts/render_case_catalog.py
```

Then verify the public package:

```bash
python scripts/render_case_catalog.py --check
python scripts/validate_public_cases.py
python -m unittest discover -s tests -q
python -m compileall -q scripts cases
```
