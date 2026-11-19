---
title: 'Evidence-Centered Evaluation of AI-Assisted Physics Reproduction'
subtitle: 'A 100-Paper Study with PRAgent and RunThePaper'
date: 'Working manuscript · 21 September 2026'
lang: en
---

\begin{abstract}
AI-assisted scientific reproduction requires evidence that an implementation addresses the physical object, conditions and claim of a source paper. Code availability or a plausible plot alone does not establish this correspondence. We present an evidence-centered evaluation protocol and apply its public-record audit to a fixed cohort of 100 physics papers. At the analysis cutoff, standardized public records were available for 97 cohort members. The audit preserves 3,666 source-inventory entries and recovers 261 unlinked execution-target records, with integrity metadata for 1,721 input files. Although 97 papers have public Python files and 96 have public data files, 88 contain unresolved public references and 47 contain targets not linked to their source inventories. At record level, 2,114 entries simultaneously link to public artifacts and contain unresolved references, demonstrating that artifact availability and evidentiary completeness measure different properties. We distinguish source coverage, physical fidelity, numerical agreement and review finality, and illustrate their implications for entanglement, spin transport and lattice topology. These results characterize the inspectability of a scientific archive; they do not estimate reproduction success. The study provides a unified cohort, a reproducible audit and a structured basis for subsequent independent scientific assessment.
\end{abstract}

# Introduction

Reproducing a physics result with an AI assistant involves a chain of scientific decisions. An equation must be interpreted with the correct convention; a physical model must be translated into an algorithm; parameters and boundary conditions must match the intended claim; and the resulting quantities must be compared with suitable references. An implementation can be internally consistent while addressing a different regime from the source paper. A plot can resemble a published figure even when its inputs, normalization or approximation differ. Evaluating scientific reproduction therefore requires more than checking whether an agent produced runnable software.

Existing benchmarks address important parts of this problem. PaperBench assesses implementation and execution against paper-specific requirements, CORE-Bench evaluates computational reproducibility with research artifacts, and MLE-bench evaluates machine-learning engineering through competition tasks [1–3]. These settings provide useful evaluation designs, but their units of assessment do not automatically determine what counts as faithful reproduction of a physical result. A finite-size demonstration, an exact symmetry-sector reduction and an approximate model can all reduce computational cost while having different implications for a scientific claim. An assessment must preserve those differences.

The practical difficulty is visible in research archives. Evidence is distributed across source inventories, code, generated arrays, runtime records, comparison tables and review documents. These artifacts may have been produced at different times under different conventions. A top-level status can summarize a case while obscuring which physical objects were examined and which claims remain unsupported. Reproducibility guidance emphasizes traceable computational steps and accessible research artifacts [4,5]; an archive-based evaluation must additionally determine whether those artifacts can be connected to the claim being assessed.

Here we develop an evidence-centered protocol around PRAgent, the execution and assessment workflow, and RunThePaper, its public research archive. We study a fixed cohort of 100 papers as a single analysis population. The empirical question in this manuscript is: **what can the available public record establish about the evidentiary basis for AI-assisted physics reproduction?** This question is narrower than whether every paper has been reproduced, but it is a necessary prerequisite for answering that stronger question reproducibly.

The study makes three contributions. First, it specifies distinct units for a paper, a source object, an execution target and an evidence artifact, preventing implementation checks from silently enlarging a scientific denominator. Second, it provides a frozen, reconstructable audit of public evidence across the cohort, including missing references and unmapped targets. Third, it shows how the protocol applies to concrete physical obligations whose acceptance cannot be reduced to visual similarity. The current findings concern evidence organization and availability. Independent reassessment of the scientific values is not a completed endpoint of this analysis.

# Related work

PaperBench evaluates the replication of 20 machine-learning papers using paper-specific rubrics developed with original authors; its 8,316 gradable tasks separate a complex reproduction into inspectable requirements [1]. Our approach shares the need for explicit obligations but focuses on tracing physical conditions and scientific objects through a heterogeneous archive. We do not compare scores because the tasks, resources and grading procedures differ.

CORE-Bench contains 270 tasks associated with 90 papers and examines agents' ability to reproduce computational results using research artifacts at different difficulty levels [2]. It motivates the separation of environment execution from the interpretation of outputs. Our archive audit does not rerun those environments and cannot estimate the performance of an execution agent. MLE-bench uses 75 Kaggle competitions to assess machine-learning engineering [3]. Competition metrics provide well-defined endpoints within those tasks, whereas a physics paper can contain several observables, derivations and regimes without a single shared numerical objective.

The NeurIPS reproducibility program combines disclosure practices, code availability and community verification [4]. Sandve and colleagues emphasize traceability of computational steps, versioning and access to the materials underlying results [5]. These principles inform the provenance layer of the present protocol. Our additional focus is on maintaining the distinction between a recoverable artifact and evidence adequate for a specific physical claim. We do not claim that the audit replaces expert scientific review or that the proposed representation is itself a new theory of reproducibility.

# Study design and evidence model

## One cohort, multiple measurement units

The study population comprises 100 fixed paper identities listed in the accompanying cohort table. Every identity remains in the study whether its evidence is available, incomplete or unassessed. Analyses of paper-level availability use 100 as their cohort denominator. Measurements that require an extracted public record report their available-case denominator explicitly. An unavailable field is retained as unknown, rather than being converted into either a negative scientific result or a zero-valued measurement.

The cohort is purposive and outcome-informed. Its selection record contains 103 distinct identities, including three exclusions from an earlier candidate list whose archived evidence did not establish the specified paper-level results. That record is preserved with reasons in the frozen selection manifest. Feasibility, including low computational cost, influenced selection. Consequently, the present cohort does not support a population estimate of reproducibility across physics, and its size must not be interpreted as a count of successful reproductions. The manuscript does not use selection provenance to define comparison groups.

We distinguish four units. A **paper** is an identified source work and version. A **source object** is a claim-bearing item in that work, such as a figure series, table entry, quantitative statement or derivation. An **execution target** is an operational task intended to produce evidence for one or more source objects. An **artifact** is a stored item, such as code, a numerical array, an execution receipt or a review. The relationships are not necessarily one-to-one. Several targets may support one object, and a single array may contribute to multiple comparisons. Counting every target or artifact as an independent scientific result would therefore inflate coverage.

The extraction preserves the granularity declared in the archive. It does not infer that a figure panel and an individual curve represent comparable amounts of scientific work. A source-object denominator suitable for scientific assessment requires a separate reconciliation against the original paper, including the scope of analytical and textual claims. Until that reconciliation is complete, the extracted rows are evidence records rather than accepted independent results.

## A traceable scientific contract

The protocol links a source object to its physical assumptions, implementation, execution evidence and assessment (Fig. 1). A scientific contract records the observable, equations, units, parameter values, system size, boundary conditions and approximation regime. It also specifies how an output will be compared with a reference, including numerical uncertainty and the basis for any tolerance. These fields make the acceptance question explicit before an attractive output can influence the interpretation of success.

Four assessment dimensions remain separate. **Source coverage** asks whether the intended objects and obligations have been identified. **Physical fidelity** asks whether the implementation addresses the stated model and conditions. **Numerical agreement** asks whether comparable quantities agree within a justified criterion. **Review finality** asks whether the evidence supporting that assessment has been independently examined and remains current for the implementation and outputs under review. A favorable value on one dimension cannot substitute for a missing value on another.

PRAgent owns production case identity, execution records and the associated acceptance workflow. RunThePaper receives selected public artifacts through the case publication manifest. This division keeps a public presentation linked to its originating evidence rather than allowing a manually assembled folder to establish scientific completion. Figure 1 describes the required chain; it does not assert that each stage has been completed for every cohort member. In particular, software-development diagnostics outside the verified production workflow are not counted as accepted scientific results.

![Required evidence chain for a scientific reproduction claim. Each arrow requires an explicit correspondence: a source locator is connected to physical conditions, an implementation, generated evidence and an assessment. The four dimensions below the chain are recorded separately. The diagram describes the evaluation protocol, not the completed state of the cohort.](figures/fig1_evidence_chain.pdf){width=100%}

## Frozen public-record extraction

We fixed the public archive at RunThePaper commit `43a64cd03824edb136b549f352412e8d263d9361`. The extraction reads Git objects rather than a moving working directory. Consumed inputs include source inventories, declared targets, completion metadata, publication provenance and referenced artifacts. Each consumed file has a path, Git object identifier, SHA-256 digest and byte count. The input ledger covers 1,721 files. These records support reconstruction of the audit and detection of changed bytes; they do not verify the scientific contents of a file.

The extraction does not import case implementations, execute solvers or notebooks, or change the archived cases. It preserves source locators, declared links, available artifact references and unresolved public references. Existing parameter labels and review statuses are retained as archive declarations, not converted into new assessments. The exact model revision, token consumption and human-intervention history are not consistently established by the public extraction and remain unknown where unrecorded. We therefore make no claim about common-budget autonomous performance.

An inventory entry becomes one evidence record. A declared target that cannot be linked to an inventory entry is retained in a separate recovery record so that it remains visible to later review. The resulting table contains 3,666 original inventory records and 261 recovery records. Recovery does not establish a previously missing source object; it establishes an unresolved mapping obligation. For analyses of target declarations, we deduplicate by the pair of paper identity and target identity, verifying that repeated declarations agree. This produces 1,116 unique archived targets.

## Audit endpoints and missingness

At paper level, we measure the availability of a standardized extraction, public Python files, public data files and a stored review file. We also identify papers containing unmapped targets or unresolved public references. File categories follow the extraction rules; a count of zero in a category is not a statement about every possible form of evidence. In particular, a stored review file is not equivalent to a current independent acceptance decision.

At record level, we examine whether an entry links to at least one available public artifact and whether it contains at least one unresolved public reference. These indicators are not complements. A record may contain both a data file and an unavailable execution receipt. We report their joint distribution rather than treating the two counts as mutually exclusive. The absence of an unresolved reference also does not prove completeness: a necessary reference might never have been declared.

The statistical analysis is descriptive. Counts of papers, inventory entries, recovery records and unique targets are never pooled into a single rate. We summarize the distribution of evidence rows across papers to expose granularity differences, and preserve missingness in the unified table. We do not estimate uncertainty for a population parameter because no probability sample or population estimand is defined. No performance ranking, causal comparison or aggregate scientific-success score is computed.

# Results

## Public artifacts are widespread, but evidence availability is uneven

At the analysis cutoff of 21 September 2026, 97 of the 100 cohort members had a standardized public extraction. Public Python files were present for 97 papers and public data files for 96. A stored review file was available for 44 papers. The remaining measurements are represented explicitly as absent within the available extraction or not assessed, as appropriate (Fig. 2a). All 100 identities remain visible in Supplementary Fig. S1 and the accompanying machine-readable roster.

These observations establish that substantial computational material is publicly inspectable. They do not establish that the code implements the paper conditions, that a data file contains a matching numerical result, or that an available review is current. In particular, the stored-review count is an availability measure. Historical status strings are not used as the endpoint of this study because their scope and relationship to the assessed implementation have not been independently re-established here.

Unresolved public references occur in 88 papers, and unmapped targets occur in 47 papers. Both counts refer to detected properties within the available public extraction; the unassessed identities remain unknown. Missing public references may reflect a projection boundary or an archive maintenance issue, rather than an absence of evidence in the originating private workspace. Nevertheless, an external reader cannot resolve the declared evidence chain using this frozen public projection alone when a required reference is unavailable.

![Evidence availability at two distinct units of analysis. **a**, Availability among the fixed cohort of 100 papers; blue indicates presence, amber absence within an available extraction, and gray a measurement not assessed at the cutoff. Stored-review presence does not imply scientific acceptance. **b**, Joint distribution of artifact links and unresolved references across 3,927 evidence records. Percentages use the record denominator and do not measure scientific success.](figures/fig2_availability.pdf){width=100%}

## Available artifacts and unresolved links frequently coexist

Of the 3,927 evidence records, 2,767 link to at least one available public artifact and 2,444 contain at least one unresolved public reference. Their overlap is substantial: 2,114 records have both properties (Fig. 2b). A further 653 records have an artifact link without an unresolved reference, 330 have an unresolved reference without an artifact link, and 830 have neither. These four mutually exclusive cells sum to the full record count.

This joint distribution is the central empirical observation of the audit. A binary indicator that an artifact exists would classify many records as populated while leaving their evidence chains incomplete. Conversely, records without a linked numerical artifact cannot automatically be classified as scientific failures. They may represent a different kind of obligation, an unresolved target mapping or incomplete recording. The present analysis does not adjudicate these possibilities from filenames or metadata alone.

Even the 653 records with a linked artifact and no unresolved reference require scientific examination. Byte-level integrity cannot establish that an array is generated from the stated equations, that the units match the source, or that the comparison is adequate. The audit identifies where a reviewer can begin following declared evidence and where a link is unavailable; it does not turn link closure into an acceptance criterion.

## Inventory granularity precludes a common result denominator

The original inventories contain 1,926 figure-series entries and 1,270 figure-panel entries; the remaining 470 entries span other figure units, tables, quantitative statements and method claims (Fig. 3a). An entire figure can be one entry in one paper, while individual series are separate entries in another. This heterogeneity prevents a direct interpretation of row counts as comparable scientific workload or coverage.

Including recovery records, available papers have a median of 25 evidence rows, with an interquartile range of 14–47 and a range of 4–315. The broad distribution reflects recording choices as well as differences between source papers. Pooling all rows into a success percentage would assign much greater weight to papers with fine-grained inventories. A paper-level summary would avoid that particular weighting but still require a defensible rule for reconciling its heterogeneous obligations.

The 261 unlinked-target records make the denominator problem concrete. They preserve operational work that would otherwise disappear when joining the target and inventory tables, but they do not independently establish additional source claims. A subsequent reviewer must decide whether each target maps to an existing object, represents supporting work, exposes an omitted obligation, or falls outside the paper's scientific scope. That decision requires the original source and the relevant evidence, not a mechanical increase in the denominator.

## Declared physical conditions vary across targets

After deduplication, the archive contains 1,116 unique target declarations. Their parameter labels comprise 510 marked as matching paper conditions, 195 as covering a paper subset, 163 as reduced scale, 34 as proxy models, 83 as not applicable, and 131 as unknown (Fig. 3b). These are archived labels whose scientific accuracy has not been reassessed in this analysis. Repeated links from inventory entries to the same target are counted once in this distribution.

The distribution shows why an executable-output count cannot stand in for a fidelity assessment. An output associated with a proxy model and an output claimed to match paper conditions pose different verification questions. The label alone remains insufficient: an exact invariant-sector representation can reduce matrix dimension without changing the relevant physical problem, while an apparently minor truncation can change the regime of validity. Source-level review must inspect the transformation and its assumptions before assigning a physical interpretation.

The present extraction yields no new independently accepted scientific verdicts. This means that scientific reassessment is not performed by the extraction procedure; it is not an estimate of zero scientific success. The distinction remains explicit in the data, where the scientific-success rate is undefined rather than zero.

![Distinct denominators for evidence organization and physical-condition declarations. **a**, Original inventory entries by dominant granularity; all other types are combined for display. **b**, Parameter labels for 1,116 targets deduplicated by paper and target identity. These labels describe what the archive declares, not what the present study has independently verified. Neither panel is a reproduction-success distribution.](figures/fig3_units_and_conditions.pdf){width=100%}

# Physical obligations beyond runnable code

The following examples are drawn from source papers in the cohort [6–8]. They illustrate acceptance questions implied by established analytical formulations; they are not reported as newly accepted numerical experiments. Their purpose is to make the assessment dimensions scientifically concrete.

## Entanglement: conventions and the logical scope of a criterion

For a bipartite density matrix, partial transposition on the first subsystem is defined by
\[
(\rho^{T_A})_{m\mu,n\nu}=\rho_{n\mu,m\nu}.
\]
Peres's criterion requires a separable state to remain positive under this operation [6]. For the two-qubit family with $0\leq x\leq1$,
\[
\rho=x|\psi^-\rangle\langle\psi^-|+(1-x)I_4/4,
\]
the partial-transpose eigenvalues are three copies of $(1+x)/4$ and one value $(1-3x)/4$. The latter changes sign at $x=1/3$.

An implementation obligation therefore includes the subsystem-index convention, density-matrix normalization and the full spectrum, not only a curve that changes sign. Tests near the boundary must state their numerical tolerance. More fundamentally, a successful example does not prove a general converse: the necessary condition cannot be promoted to a universal sufficiency statement. This example separates numerical agreement on a family of states from the logical scope of the source claim.

## Spin transport: exact reduction versus a smaller physical problem

For the engineered one-excitation chain of Christandl and colleagues [7], let the off-diagonal couplings be
\[
J_n=\frac{\lambda}{2}\sqrt{n(N-n)},\qquad n=1,\ldots,N-1.
\]
The resulting tridiagonal matrix equals $\lambda S_x$ in the spin-$(N-1)/2$ representation. Its end-to-end amplitude is
\[
F(t)=\left[-i\sin(\lambda t/2)\right]^{N-1},
\]
giving unit transfer probability at $t=\pi/\lambda$ under these conventions.

Here, using an excitation sector can be an exact representation of the stated dynamics rather than an approximation to a shorter chain. Acceptance requires checking that correspondence and the coupling normalization. Comparing only $|F|^2$ would discard the transfer phase. Likewise, agreement for several chain lengths cannot establish a general theorem outside the tested family. The contract must identify whether a target concerns probability, amplitude, a special case or a general analytical statement.

## Lattice topology: an integer is not a sufficient diagnostic

For an isolated band, the discretized construction of Fukui, Hatsugai and Suzuki [8] uses normalized overlaps
\[
U_\mu(k)=\frac{\langle u(k)|u(k+\hat\mu)\rangle}
{|\langle u(k)|u(k+\hat\mu)\rangle|}.
\]
The oriented plaquette product defines a principal-branch phase, whose sum divided by $2\pi$ gives a lattice Chern number. This construction makes gauge consistency and branch handling explicit.

An integer-valued output alone does not establish that the intended continuum invariant has been resolved. A scientific assessment must also examine the band gap, vanishing overlaps, plaquette admissibility, orientation and mesh refinement. A zero overlap makes the displayed normalization undefined; silently replacing it with a convenient phase changes the calculation. These obligations show how an implementation can satisfy an attractive scalar check while failing a prerequisite for interpreting that scalar. Source conditions and failure handling must therefore accompany the final invariant.

# Discussion

## What the audit establishes

The public-record audit demonstrates a measurable distinction between artifact availability and the completeness of declared evidence links. Computational files are widespread, yet unresolved references and unmapped targets are also common within the extracted record. The coexistence is not contradictory: creating a useful implementation and assembling a public chain of evidence are different tasks. An archive can be valuable for further research while remaining insufficient for a paper-level acceptance claim.

This distinction changes how progress should be reported. A system can deliver source parsing, derivations, implementations and diagnostic outputs before completing scientific assessment. Recording these contributions is useful, provided they remain distinguishable from a verified result under the paper's conditions. Likewise, a reviewer can identify a limitation without establishing that a paper is wrong. Missing evidence, implementation disagreement, unsupported generalization and a candidate source error require different records and different follow-up work.

The proposed four-dimensional assessment makes these intermediate states explicit. Source coverage prevents a convenient subset from silently becoming the entire task. Physical fidelity constrains which comparisons are meaningful. Numerical agreement requires a justified reference and tolerance. Review finality records whether the assessment applies to the actual evidence being presented. Their separation allows progress to remain visible without collapsing unfinished work into either success or failure.

## Implications for an evaluation of scientific agents

An evaluation of agent capability would require additional controls beyond this audit. The agent version, available tools, compute resources, interaction budget and allowed human interventions would need to be recorded consistently. Acceptance criteria would need to be fixed before inspecting the outputs, and the assessor would need access to an immutable evidence bundle. Comparing systems would additionally require comparable tasks and resource conditions. The current archive does not establish these prerequisites uniformly, so no model ranking or causal performance claim is warranted.

The physics examples also caution against rewarding only easily scored outputs. A correct special case does not establish a general claim; a probability curve may conceal a phase error; and a quantized scalar may conceal an invalid intermediate operation. A useful benchmark should preserve these distinctions in its task representation. This does not require treating every derivation and data point as equally difficult. It requires knowing which scientific obligation a score purports to measure.

A unified cohort remains compatible with heterogeneous execution histories. All 100 paper identities can be retained in one roster while each measurement carries its own availability and provenance. That design avoids dropping incomplete work from the study and avoids implying that every observation came from one agent configuration. It also permits subsequent evidence to fill a missing measurement without changing the cohort or retroactively rewriting the archived observation.

## Limitations

The cohort is selected for a research program rather than sampled randomly. Outcome-informed exclusions and feasibility-based choices limit generalization, and the preserved selection history is necessary for interpreting the study. Well-known source papers may have appeared in model training data; the study does not assess novelty of exposure. The heterogeneous archive was not generated under a uniform model revision, resource budget or intervention policy.

The audit observes a public projection. An unresolved reference may be available privately, and a stored file may be scientifically inadequate despite being readable. Extraction rules can detect declared relationships but cannot discover every omitted obligation. The source inventories have not been re-established against all original papers in this analysis, and the original scientific values have not been independently re-evaluated. Consequently, neither inventory size nor link resolution is a measure of whole-paper reproduction.

Execution readiness is another boundary. The production workflow used for the current implementation work has reported that a verified numerical isolation backend is unavailable. Development diagnostics therefore remain preparation evidence; they are not substituted for production execution or independent acceptance. This manuscript's numerical findings are computed from the frozen public metadata and file records, not from unreported production experiments.

The protocol itself also requires evaluation. Its capacity to improve reviewer agreement, reduce mistaken acceptance or make assessment more efficient has not been measured here. Those benefits are plausible design objectives, not empirical conclusions of this study. Establishing them would require a prospective assessment with recorded reviewer decisions and a suitable comparison procedure.

# Conclusion

A fixed 100-paper study can preserve useful research progress without treating every delivered artifact as an accepted scientific result. In the available public record, artifacts and unresolved evidence links frequently coexist, while heterogeneous inventories and target conditions prevent a simple pooled reproduction score. The resulting need is concrete: connect each source object to its physical assumptions, implementation, execution evidence and current assessment. PRAgent and RunThePaper provide the workflow and public archive for organizing that chain. This manuscript contributes the reproducible audit and a scientifically explicit assessment protocol; independent source-level verification remains the next empirical endpoint.

# Data and code availability {.unnumbered}

The frozen public archive is available in [RunThePaper at commit 43a64cd](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361).

The study directory `evaluation/paper-study-100/` contains the selection manifest, extraction and validation programs, paper-level and record-level data, and input-integrity ledger. The accompanying manuscript package provides the unified cohort in CSV and JSON formats, all figure data, and the figure-generation script. The data represent a public evidence audit and retain unknown scientific assessments explicitly. Private development diagnostics and source-paper copies are not included in this public manuscript package. Availability of the production execution environment is not claimed by the release of these analysis materials.

# Manuscript status {.unnumbered}

This working manuscript reports a completed public-record analysis and a defined scientific-assessment protocol. It does not report completion of scientific reassessment across the cohort. Author names, affiliations, contributions and declarations must be supplied by the authors before submission; none are inferred from repository ownership.

# References {.unnumbered}

1. Starace, G. et al. PaperBench: Evaluating AI's Ability to Replicate AI Research. *arXiv* **2504.01848** (2025). [https://arxiv.org/abs/2504.01848](https://arxiv.org/abs/2504.01848).

2. Siegel, Z. S., Kapoor, S., Nagdir, N., Stroebl, B. & Narayanan, A. CORE-Bench: Fostering the Credibility of Published Research Through a Computational Reproducibility Agent Benchmark. *arXiv* **2409.11363** (2024). [https://arxiv.org/abs/2409.11363](https://arxiv.org/abs/2409.11363).

3. Chan, J. S. et al. MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering. *arXiv* **2410.07095** (2024). [https://arxiv.org/abs/2410.07095](https://arxiv.org/abs/2410.07095).

4. Pineau, J. et al. Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program). *Journal of Machine Learning Research* **22**(164), 1–20 (2021). [https://www.jmlr.org/papers/v22/20-303.html](https://www.jmlr.org/papers/v22/20-303.html).

5. Sandve, G. K., Nekrutenko, A., Taylor, J. & Hovig, E. Ten Simple Rules for Reproducible Computational Research. *PLoS Computational Biology* **9**, e1003285 (2013). [https://doi.org/10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).

6. Peres, A. Separability Criterion for Density Matrices. *Physical Review Letters* **77**, 1413–1415 (1996). [https://doi.org/10.1103/PhysRevLett.77.1413](https://doi.org/10.1103/PhysRevLett.77.1413). Source version: [arXiv:quant-ph/9604005v2](https://arxiv.org/abs/quant-ph/9604005v2).

7. Christandl, M., Datta, N., Ekert, A. & Landahl, A. J. Perfect State Transfer in Quantum Spin Networks. *Physical Review Letters* **92**, 187902 (2004). [https://doi.org/10.1103/PhysRevLett.92.187902](https://doi.org/10.1103/PhysRevLett.92.187902). Source version: [arXiv:quant-ph/0309131v2](https://arxiv.org/abs/quant-ph/0309131v2).

8. Fukui, T., Hatsugai, Y. & Suzuki, H. Chern Numbers in Discretized Brillouin Zone: Efficient Method of Computing (Spin) Hall Conductances. *Journal of the Physical Society of Japan* **74**, 1674–1677 (2005). [https://doi.org/10.1143/JPSJ.74.1674](https://doi.org/10.1143/JPSJ.74.1674). Source version: [arXiv:cond-mat/0503172v2](https://arxiv.org/abs/cond-mat/0503172v2).

\clearpage

# Supplementary cohort audit {.unnumbered}

All 100 paper identities appear below in lexical order. The corresponding full titles are supplied in `cohort_100.csv`. This table uses no origin-based study groups. Blue indicates the availability of an extracted record or file category. Amber indicates a detected mapping or reference gap. White indicates absence within an available extraction; gray indicates a measurement not assessed in this public-record analysis. None of these colors is a scientific verdict.

\begin{center}
\includegraphics[width=0.94\textwidth,height=0.80\textheight,keepaspectratio]{figures/figS1_cohort_matrix.pdf}

\small\textbf{Supplementary Fig. S1.} Unified availability and gap matrix for the fixed 100-paper cohort.
\end{center}
