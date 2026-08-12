# Paper Review Protocol v2

This case is both a reproduction and a paper audit.  Its conclusions are
fail-closed.

1. The complete ten-page paper and supplement were inventoried before numerical
   implementation: nine numerical panels and two schematic panels.
2. The arXiv archive contains TeX, bibliography files, and four figure PDFs but
   no numerical program or array.  No author code, author arrays, curve
   digitization, or source pixels may enter the scientific runner.
3. Generated numerical arrays and their hashes must be frozen by an isolated,
   attested run before source figures are extracted for comparison.
4. A discrepancy may become `paper_error_candidate` only after two distinct
   strong checks, explicit falsification attempts, exact source pinpoints, and a
   fresh-context independent review.
5. Reduced-size solver failures remain reproduction failures even when a source
   formula appears inconsistent.
6. The isolated feature run froze all numerical arrays before the source figure
   PDFs were extracted.  The RenderContract rechecked every data hash after
   building comparison boards.
7. The fresh review bundles may be built, but the case must remain partial until
   a different reviewer completes both inventory-first and falsification phases.

The initial audit leads are `DISC_WICK_SIGN`,
`DISC_RELEVANCE_INEQUALITY`, and `DISC_PHASE_LABEL_SWAP`.  All are currently
`inconclusive`.  T003 and T007 are separately classified as reproduction-side
scientific failures at reduced scale; they are not evidence for or against any
of the three source discrepancies.
