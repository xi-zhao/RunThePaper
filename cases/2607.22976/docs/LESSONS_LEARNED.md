# Lessons Learned

## Case summary

- Paper: *Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems*
- Scope: every numerical main/supplement figure
- Scientific result: 5/5 checks passed
- Main uncertainty: several discrete implementation/plot selections are not reported

## Reusable lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| One domain model should feed the whole paper | Spectra, eigenvectors, winding, Ronkin, GBZ, flux and DOS cross-check each other. | Avoid per-figure scripts with duplicated physics. |
| Multi-valued beta means all roots | Selecting one root produces a visually plausible but scientifically incomplete GBZ. | Preserve branch multiplicity in data schemas and tests. |
| Missing finite stencils are model uncertainty | Bulk Laurent equations do not uniquely define a cross-interface finite matrix. | Declare stencil conventions and cap parameter status at `paper_subset`. |
| Unreported representative energies must not be read from pixels | Fig. 3 labels `E1/E2/E3` without numeric values. | Use a deterministic equation-based selection policy and expose it. |
| Sign conventions need explicit orientation | Flux winding sign changes under reversed site orientation. | Store orientation in configuration/check evidence. |
| Shared-grid method comparisons are stronger than visual checks | Ronkin and diagonalization densities can be compared numerically on one grid. | Require correlation/support checks before rendering. |
| Comparison renders belong in the isolated runner | Manual registered copies weaken provenance. | Generate them only from fresh runner outputs and declare their hashes. |

## Efficiency

The paper-scale CPU run completes in 69.39 s. A single `186 x 186` eigensystem and shared energy/root scans feed all targets, avoiding repeated diagonalizations. A100 use would not address the dominant small dense linear algebra/root-grid workload enough to justify remote orchestration.

## New Failure Modes

| Failure mode | Detection |
| --- | --- |
| A single GBZ branch is plotted for a multi-valued characteristic equation. | Assert the full root count and retain a branch identifier for every beta sample. |
| A finite interface convention is silently treated as paper-exact. | Require a paper-vs-generated stencil mapping and downgrade to `paper_subset` when absent. |
| Flux winding has the right support but an unexplained sign. | Record the site orientation and test the effect of reversal explicitly. |

## Reusable Checks Or Tools

| Check/tool | Reuse |
| --- | --- |
| Laurent-root residual plus root-count winding | Any finite-range non-Hermitian band model. |
| Shared-grid Ronkin/diagonalization density comparison | Spectral-potential reproductions. |
| Isolated generated-image registration | Any case whose comparison renderer must remain source-blind. |

## Harness backlog

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| P1 | Require comparison render paths in isolated contracts. | Five registered copies were initially manual. | implemented in this case |
| P1 | Add branch-count assertions for multi-valued complex roots. | Fig. 3(f-h) can look plausible with missing branches. | proposed |
| P1 | Add an explicit convention-uncertainty object for stencil/orientation. | Four targets are paper-subset for different missing choices. | proposed |
| P2 | Add scientific foreground submasks for heatmaps/scatter plots. | Foreground MAE mixes annotations with scientific fields. | proposed |
