# Methods draft: archive extraction and prospective study

**Draft boundary.** This text describes the work actually recorded in the study directory. The extraction is complete; source-level scientific reassessment and the prospective production experiments are not. It does not report a reproduction success rate.

## Population and selection

The historical sampling frame contains 100 paper cases. We retained 97 for detailed retrospective analysis and preserved the three outcome-informed exclusions in `cohort.json`. Three additional, deliberately low-compute papers form a separate prospective group, giving a planned analysis set of 100 and a selection history of 103 distinct papers. The additions are not substitutes for unreported historical failures. They will remain in the study if incomplete, blocked, or unsuccessful. This design is neither a random sample nor a common-budget benchmark.

## Frozen retrospective evidence

We read public Git objects at RunThePaper commit `43a64cd03824edb136b549f352412e8d263d9361`. Cohort membership and the bytes of the historical paper table are checked against the frozen plan. The extraction program reads archived inventories, target declarations, completion metadata, publication provenance, and referenced artifacts. It does not import case code, execute notebooks or solvers, run scientific checks, or modify historical cases. Each consumed file has a Git object identifier, a SHA-256 digest, and a byte count in `data/inputs.jsonl`.

The paper-level table preserves recorded identity, provenance, inventory size, available public artifact categories, and historical state. The result-level table preserves source locators, target links, artifact references, and unresolved references. Historical evaluations are explicitly labelled as archived declarations. Comparison values, actual conditions, source-scope completeness, model identity, and intervention counts remain unknown unless independently established by subsequent review. An unavailable public reference does not establish absence from the private archive.

The first extraction retained 3,666 original inventory entries and 261 archived targets that were not linked to those inventories, yielding 3,927 records across all 97 retained papers. The 261 recovery records are not additional independent results. Input integrity was recorded for 1,721 files. These counts are reproducible with `build_archive_report.py`; their source is `analysis/archive_descriptive_counts.json`. Inventory granularity varies between papers, so these records cannot serve as a common scientific-result denominator. No paper's original scope was re-established by this extraction alone.

## Review and interpretation

Subsequent review must reconcile each source object and version, inspect the relevant implementation and stored values, and record the physical conditions, comparison object, units, uncertainty and tolerance. Support checks cannot increase the number of independent paper objects. Missing information, unsupported claims, disagreements and positive evidence must be distinguished. Pixel similarity, file presence, historical top-level labels and aggregate legacy scores are not scientific endpoints. We will not pool errors of incompatible physical quantities or infer a causal system improvement without a suitable comparison design.

## Prospective production cases

The fixed additions are Peres (quant-ph/9604005v2), Christandl et al. (quant-ph/0309131v2), and Fukui et al. (cond-mat/0503172v2). PRAgent owns their source snapshots, equation traces, implementation, runtime records, and independent acceptance. Their source pages were inspected and their initial scientific configurations and diagnostic tolerances were recorded before numerical development. The Peres configuration then received one explicitly archived amendment to record diagnostic inputs before its first numerical execution; no measured outcome was available for that amendment. The scope includes analytic and textual obligations, not only plotted examples. Model exposure to these well-known papers is possible and no novelty-of-exposure claim is made.

The current user-selected execution mode is the production case workflow. Ordinary-workspace diagnostics are software-development evidence. The production entry point has reported an unavailable verified isolation backend for all three cases, with no production numerical execution. These preparation-stage observations must not be described as scientific acceptance. The exact model revision and model-token accounting were not exposed and remain unrecorded. After suitable production execution and independent review, public files must be selected through PRAgent's manifest projection before they enter RunThePaper case records.

## Limitations still requiring explicit treatment

The archive is heterogeneous and its exclusions are retrospective. The additions are selected for feasibility rather than representativeness. Public records may omit private evidence, resource histories and human interventions. Source-level semantic review remains incomplete. Current descriptive results concern evidence availability and provenance, not correctness or whole-paper reproduction. The final title, result figures, comparison tables and abstract must follow the completed review, including its unresolved outcomes.
