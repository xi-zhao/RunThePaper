---
title: 'PRAgent: AI-Assisted Physics Paper Reproduction'
subtitle: 'Capabilities and Evidence from a 100-Paper Project'
date: 'September 2026'
---

\begin{abstract}
Reproducing a physics paper requires an executable interpretation of its model, a suitable numerical method and checks that connect the computed observables to the scientific question. We present PRAgent, an AI-assisted system that brings these tasks together in a human-guided research workflow. We examine its implemented capabilities through three public research cases: precision-aware evaluation of Hamiltonian-simulation resource bounds, quantum dynamics in exact particle-number sectors, and ensemble-based quantum-discord calculations. The cases show how physical structure determines the computational representation, how numerical difficulties are handled in code, and how controls and statistical comparisons constrain the interpretation of results. A fixed 100-paper project provides a broader view of recorded reproduction coverage and verification status. Further diagnostic examples examine source ambiguity, incomplete model implementations and resource requirements. Our evidence consists of case-specific implementations, archived computational outputs and new checks of selected stored arrays. It supports an account of PRAgent's demonstrated capabilities within the recorded human-guided workflow. RunThePaper makes the resulting code, data and explanations available as research artifacts that can be inspected and extended.
\end{abstract}

# Introduction

A physics paper specifies a scientific argument, but rarely a complete software task. Reproducing it requires decisions about notation, state-space representation, numerical precision, observables and comparison conditions. A program can run successfully while computing a different model or testing a weaker claim. A useful scientific agent must therefore connect implementation to the physical question and make that connection available for inspection.

PRAgent is an AI-assisted system for this work. It organizes paper interpretation, numerical implementation and assessment around a persistent research case. Its public output, distributed through RunThePaper, includes derivations, case-specific code, generated arrays and explanations of what the calculation establishes. The system is used with human guidance; throughout this report, demonstrated capability refers to what is implemented and evidenced in that combined workflow.

We examine three aspects of PRAgent's capability. **Scientific formulation** connects a paper's model and observable to an explicit computational representation. **Numerical implementation** handles the practical requirements of that representation, including precision, basis construction and sampling. **Verification and diagnosis** use physical checks, control models and targeted comparisons to assess results and identify the next investigation when a reproduction remains incomplete.

Three detailed cases make these capabilities concrete. Hamiltonian-simulation resource estimates require stable arithmetic and precision-aware integer decisions. Quantum walks use conserved particle sectors to construct exact finite-dimensional dynamics. Quantum-discord calculations distinguish finite ensembles from an analytical reference and from an unpublished author realization. We then place these implementations in the context of one fixed 100-paper project and examine diagnostic records for incomplete targets. The technical contribution is the implemented research system and its inspectable evidence across these tasks; the source papers supply the underlying physical methods.

# Research context

Traceable computation and accessible research materials are central to computational reproducibility [1,2]. They motivate PRAgent's persistent case structure: a numerical figure should be connected to equations, inputs, implementation and checks. This also provides a way to evaluate an agent's scientific work through the objects it produces.

PaperBench, CORE-Bench and MLE-bench evaluate complementary forms of research replication and computational engineering [3–5]. The present report is a capability study of a system used across heterogeneous physics tasks. It examines implemented methods and their evidence; comparative performance under matched budgets remains an experimental question. The detailed physical examples implement qDRIFT resource formulas, a quantum-walk model and DQC1 discord calculations from their respective source papers [6–8].

# PRAgent capabilities and system design

## Connecting the scientific task to executable code

A PRAgent research case records the paper identity, scientific scope, equations, configuration, implementation, generated outputs and assessment. A source object identifies a curve, table entry or analytical statement. An execution target specifies the computation that addresses it. Artifacts preserve the resulting arrays, diagnostics and explanation. One propagation can support several observables, while one plotted result may require several convergence checks; these relationships remain explicit in the case.

The numerical task fixes the model, observable, system size, parameters, boundary conditions and approximation regime. Equation records connect the source expressions to the functions and configuration fields that implement them. This connection is where the case-specific physics enters: a conserved sector can define an exact basis, a resource estimate can require inequality evaluation, and an ensemble study must specify which distribution is sampled.

## Implementing and checking the calculation

Case implementations separate model construction, solution, observables and rendering. This allows generated numerical tables to be inspected independently of the plot, and lets several observables share one solver output. Checks are tied to the scientific object: conservation for dynamics, neighboring integer inequalities for resource bounds, and sampling intervals for an ensemble. Control calculations test the consequences of changing a physical assumption.

The workflow in Fig. 1 connects these computations to assessment and revision. PRAgent retains the target, configuration and evidence associated with each result, including unresolved comparisons. This supports targeted follow-up: revise the model, investigate a convention, extend a calculation or obtain a missing input. The scientific meaning of a check is preserved alongside its pass or fail status.

![PRAgent's human-guided research workflow. Paper interpretation, numerical implementation and assessment produce a persistent research case. Human guidance can shape the task and revisions; case-specific code performs the numerical work. Derivations, arrays and review records remain linked to the result, and selected artifacts enter the public RunThePaper collection. Dashed connections indicate human guidance; solid arrows indicate workflow or artifact transfer.](figures/fig1_workflow.pdf){width=100%}

## Evidence used to assess capability

The examples below are drawn from public files at [RunThePaper revision 43a64cd](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361). We inspect the recorded implementations, reanalyze selected stored arrays and regenerate numerical figures. The accompanying analysis reads frozen Git objects and records input hashes; it does not execute the original scientific solvers. Historical execution and diagnostic claims are identified as such. The cases were selected for contrasting numerical tasks and inspectable outputs, so they establish concrete examples of implemented capability rather than an average success rate.

# Demonstrated scientific capabilities

The following cases connect each capability to a scientific requirement, an implemented method and observable evidence. They also identify the remaining case-specific boundary needed to interpret that evidence.

## Stable resource estimation for Hamiltonian simulation

PRAgent's qDRIFT case demonstrates precision-aware numerical implementation: it evaluates how Hamiltonian-simulation resource bounds depend on simulation time and an error criterion [6]. Its inputs include Hamiltonian summary parameters and the error-bound expressions associated with different compilation methods. The scientific output is an integer circuit-resource bound, which determines the numerical requirements of the implementation.

The archived implementation evaluates qDRIFT and deterministic or randomized product-formula bounds. It computes multiplicative expressions in logarithmic form and handles competing terms using stable log-sum-exp calculations. These choices matter because the resource counts span many orders of magnitude. A naive evaluation can overflow even when the final comparison is meaningful.

A second issue arises when the output is the smallest integer satisfying a bound. At sufficiently large counts, adjacent integers have identical floating-point representations. The case implementation therefore uses a floating-point bracket as a starting point and refines the boundary using 60-digit decimal logarithms. The relevant question is whether the bound holds at $N$ and fails at $N-1$, not merely whether a continuous estimate looks plausible. This is an example of a numerical-analysis requirement that emerges from the scientific output being requested.

The public tables contain 366 rows for time-dependent resource estimates and 366 rows for phase-estimation estimates. Figure 2a redraws the propane resource curves directly from these tables. Figure 2b compares the stored randomized second-order Trotter and qDRIFT phase-estimation counts at failure probability 0.05. The resulting ratios are 303.72 for carbon dioxide, 788.73 for ethane and 1405.51 for propane. These are ratios of theoretical resource estimates under the case's declared formulas and parameters; they are not measured wall-clock speedups of PRAgent or demonstrations on quantum hardware.

This case demonstrates PRAgent's implementation of a scientific comparison across numerical scales, including precision-sensitive integer decisions. The remaining source-value discrepancy and pending review limit the case-level conclusion; they do not alter the bound-evaluation method described here.

![Hamiltonian-simulation resource estimates redrawn from the public qDRIFT case. **a**, The stored propane gate-count bounds for five compilation strategies across the source time range. **b**, Ratios of randomized second-order Trotter to qDRIFT counts in the phase-estimation table at failure probability 0.05. These are formula-based resource estimates; neither panel reports physical quantum-device execution or an agent runtime advantage.](figures/fig2_resources.pdf){width=100%}

## Interacting quantum walks in exact particle sectors

PRAgent's quantum-walk case demonstrates model-based representation and physical validation. It implements the coherent theoretical model associated with the superconducting-processor experiment of Yan and colleagues [7]. A Bose-Hubbard Hamiltonian provides the case formulation,
\[
H=\sum_{j=1}^{L-1}J_j(a_j^\dagger a_{j+1}+a_{j+1}^\dagger a_j)
+\sum_{j=1}^{L}\frac{U_j}{2}n_j(n_j-1)+\sum_{j=1}^{L}h_jn_j.
\]
The implementation retains source-linked coupling and interaction parameters and works in fixed-particle-number sectors. The one-excitation calculation uses an 11-site sector for the corresponding source setup. The two-excitation calculation uses 12 sites, with 78 bosonic occupation states and 66 states in the hard-core limit. These representations implement the stated theoretical sectors; they do not reproduce the experimental hardware or its raw measurements.

The computational structure makes the physical model inspectable. The basis is enumerated as occupation tuples, and hopping matrix elements carry the bosonic factors $\sqrt{n_j(n_{j+1}+1)}$. A Hermitian eigendecomposition is reused to evaluate time evolution on the requested grid. Observable functions then compute site density and the two-particle correlator,
\[
G_{ij}=\langle a_i^\dagger a_j^\dagger a_i a_j\rangle,
\]
including the diagonal convention $G_{ii}=\langle n_i(n_i-1)\rangle$. The calibrated interaction, free-boson and hard-core cases share a transparent comparison structure.

Figure 3a displays the stored one-excitation density for a central launch. The correlation matrices in Fig. 3b–d show the calibrated interaction and its two control models for the same two-excitation launch and displayed time. The shared solver and observable definitions allow a controlled comparison of how the interaction model changes the spatial correlation pattern.

We independently recomputed the density-sum diagnostic from the stored CSV values. Across 1,503 one-excitation state-time slices, the maximum deviation from one is $1.78\times10^{-15}$. Across 3,006 two-excitation slices, including the recorded model and launch combinations, the maximum deviation from two is $2.66\times10^{-15}$. These residuals demonstrate conservation consistency in the inspected arrays. They do not by themselves establish agreement with all observables or source conditions.

The capability evidenced here is the connection between physical structure and computation: the conserved sector determines the basis, one propagation supplies several observables, and explicit limits provide controls. A source-time discrepancy in supplementary comparisons and missing author realization-level parameters remain open in the broader case.

![Quantum-walk outputs regenerated from stored arrays. **a**, One-excitation density after launch at site Q6 in the 11-site setup. **b–d**, Two-excitation correlators at 55.5 ns for launch Q6+Q7 in the 12-site setup, using calibrated interactions, the hard-core limit and free bosons. The correlation panels share a color scale. These are generated model outputs, not experimental measurements; the displayed time is taken from the archived table and is not an adjudication of the case's unresolved source-time issue.](figures/fig3_quantum_walks.pdf){width=100%}

## Quantum discord: separating ensembles, references and logical claims

PRAgent's discord case demonstrates ensemble-based computation and interpretation of a numerical discrepancy. It implements the DQC1 correlation problem considered by Datta, Shaji and Caves [8]. For a unitary $U$ acting on a register of dimension $d$ and control polarization $\alpha$, the case constructs
\[
\rho=\frac{1}{2d}\begin{pmatrix}I_d&\alpha U^\dagger\\\alpha U&I_d\end{pmatrix}.
\]
It computes entropic quantities and measurement-dependent conditional entropies using explicit numerical representations. The source question motivates comparing the resulting discord with an analytical reference, while the implementation must also specify the unitary ensemble and optimization procedure.

The public numerical-method record describes two independent ensembles of 500 matrices in $U(32)$: a QR-based Haar construction and a depth-32 local brickwork construction. The latter is explicitly identified as an independent probe because the original finite pseudorandom generator is not published. Each curve is stored on a 41-point polarization grid, with mean, standard deviation, standard error and interval fields. This representation keeps sampling variation visible instead of presenting an individual realization as a universal result.

Figure 4 shows the archived means and their deviations from the analytical reference. At $\alpha=1$, the stored QR-Haar mean is 0.537735 bits, the brickwork mean is 0.537483 bits and the reference is 0.557305 bits. Their corresponding differences from the reference are approximately $-0.01957$ and $-0.01982$ bits. The displayed bands use the case's stored pointwise 95\% interval endpoints. They describe ensemble uncertainty under the recorded procedure, not simultaneous confidence bands or uncertainty in the analytical expression.

The implemented comparison keeps the finite register, sampled ensemble and analytical reference distinct. This is the capability demonstrated by the case: it exposes a reproducible numerical difference together with the conditions under which it occurs. Explaining that difference requires further analysis of finite-size and optimization effects; the plot alone does not diagnose a source-paper error.

The code also makes a useful logical distinction in its treatment of entanglement. For the control-register split, it constructs a convex product-state decomposition from the eigenbasis of $U$. For other partitions, one-sided tests such as negativity are recorded as detection criteria. Failure to detect entanglement is not used as a separability proof. This illustrates how the interpretation of a numerical check can be as important as its implementation.

![Quantum-discord outputs redrawn from the archived DQC1 case. **a**, The analytical reference and means of the QR-Haar and independent brickwork ensembles. **b**, Mean-minus-reference residuals expose deviations that are less visible in the main curves. Shading uses the stored pointwise interval endpoints. Ensemble specifications originate in the public method record; these are generated case outputs rather than recovered author samples.](figures/fig4_discord.pdf){width=100%}

# Coverage across the 100-paper project

The project is organized around one fixed cohort of 100 paper identities. The full roster accompanies the report. It is a purposive research collection, with outcome-informed selection and feasibility considerations; the preserved selection history contains 103 distinct identities. The cohort size describes project scope, not a count of fully successful reproductions. Missing measurements remain attached to their identities in the same roster.

The frozen public extraction contains code for 97 cohort members and data for 96. The supplementary roster records availability and mapping gaps. These artifacts establish the breadth of implemented work; the coverage and assessment measures below describe how much of the scientific task was checked.

## Coverage and verification answer different questions

Figure 5 aligns the archived claim-coverage table of 27 August 2026 to the unified 100-paper roster. Coverage is measured for 97 papers; three remain unmeasured. The records contain 1,399 numerical claims and 3,667 distinct checks. For claim $c$, $r_c=n_{c,\mathrm{reproduced}}/n_{c,\mathrm{checks}}$. Reconstruction uses all listed claim associations, including supporting associations; checks can be shared across claims. Fifteen non-numerical claims are excluded.

Equal weighting of measured claims gives 40.9% reproduced, 21.3% externally blocked and 37.8% attempted but not reproduced (Fig. 5a). Averaging first within each paper and then across measured papers gives 57.8% coverage (Fig. 5b). Unequal claim counts explain the difference. Missing measurements are not imputed; these percentages describe recorded claim coverage rather than whole-paper success.

Coverage asks how much of the recorded claim set has supporting checks. Assessment separately asks whether the numerical scope is complete, whether scientific gates pass, and whether independent review passes. These requirements can be satisfied separately. The frozen records report complete numerical scope for 83 papers, passed scientific checks for 34 and passed independent review for 26 (Fig. 5c). These overlapping attributes are not a completion funnel. Although 26 papers have full recorded claim coverage, none of the available whole-paper assessments records completion. Historical coverage and assessment records need not represent the same evaluation event; coverage does not override later or stricter checks. No new scientific verdicts are issued here.

![Overall reproduction profile of the unified 100-paper project. **a**, Archived dispositions averaged equally over 1,399 measured numerical claims; checks may be shared across claims. **b**, One bar per paper, ordered by recorded reproduced coverage, with the same colors as panel a. Hatched bars retain the three papers without measurements; they are not zero scores. The 57.8% mean gives each measured paper equal weight. **c**, Stored scope, scientific-check and independent-review dimensions, each with a fixed denominator of 100 papers; hatched segments indicate unavailable assessments. Coverage comes from the archived August 2026 table; assessment dimensions are read from the frozen case records. Panel c retains completion-summary labels; six differ from the detailed state, as discussed below. No panel represents a new independent assessment or an autonomous-agent success rate.](figures/fig_overall_reproduction.pdf){width=100%}

# Diagnostic capability and observed obstacles

PRAgent's diagnostic records connect an observed obstacle to a discriminating test or a missing scientific requirement. Source ambiguity, incomplete implementation, execution resources and experimental apparatus provide four directions for investigation. The three examples below illustrate this process without estimating cause prevalence. Six cases have inconsistent summary and detailed science labels; the supplementary ledger preserves them. Source pointers and recorded confidence for the examples are supplied in `anc/obstacle_examples.json`.

**Testing source identifiability.** For Fig. 2 of Phys. Rev. Lett. 124, 113601 (target T001), the archived diagnosis identifies unspecified finite-chain boundaries, site-index origin and localization conventions. The recorded source audit and identifiability test find that publication-compatible choices produce different energy and inverse-participation-ratio arrays and localized-state counts. This supports a limitation on identifying one exact numerical target from the disclosed inputs. Resolving it requires obtaining the missing conventions, fixing them before comparison and rerunning the calculation. Pending gates remain in the record; the diagnosis does not establish a false physical claim or independently exclude implementation error.

**Checking implementation scope.** In `2502.20558` (T001), a repetition-code mechanism model passes its local checks, yet its output remains orders of magnitude above the paper's surface-code maximum-likelihood-decoding curves. The implementation audit identifies the missing scientific object: the required surface-code circuit and lifecycle-aware decoder have not been implemented. Checks for the simpler model therefore cannot validate the original observable. The follow-up is to implement that circuit and decoder, validate tractable instances and evaluate the paper-level target. Additional hardware alone would not supply the missing method.

**Relating execution requirements to measurements.** Case `1709.03478` (T002) records reduced-scale tests and one full-size stationary block, while the complete production and convergence campaign remains unexecuted. Its diagnosis reports 2,784 CPU tasks and 27.004229 seconds for the measured block, giving a 20.88 CPU-hour baseline before aggregation. Finite-time tasks may take longer; the available A100 has no validated CUDA implementation. This provides an execution estimate for the current method, without separating resource allocation from scheduling or backend choices. Follow-up requires an allocated CPU campaign or a validated alternative backend, then convergence checks.

These are archived diagnostic examples, not new independent causal verdicts. Missing data or supplementary material does not establish missing experimental apparatus; that requires checking the physical operations and device access. Evidence availability also limits diagnosis: in `2506.06669`, a later pulse-definition explanation cites a detailed test file absent from the public snapshot. That explanation still needs inspectable support. Retaining such limits lets the workflow specify what evidence is needed next.

# Capability boundaries and next evaluation steps

The cases demonstrate different components of PRAgent's scientific work: implementing the relevant mathematical object, handling numerical constraints, checking physical structure and retaining evidence for further investigation. The implementations are reusable beyond the original interaction. A particle-sector solver, precision-aware bound evaluator or ensemble-analysis routine can support a new calculation when its model assumptions remain appropriate.

These capabilities were exercised within a human-guided system. Historical model versions, interaction budgets and interventions are not uniformly recorded, so the evidence does not isolate an autonomous model's contribution or measure the gain over a human-only workflow. The fixed cohort is purposively selected, and the detailed examples were chosen with knowledge of their outputs. A controlled evaluation would need recorded intervention and resource budgets, common acceptance criteria and a comparison condition.

The report's new computations check selected archived arrays. They do not independently revalidate all earlier execution, diagnostic or review claims. The public archive also omits some evidence from the originating workspace. The documented production workflow retains an infrastructure gap: a verified numerical isolation backend sufficient for the relevant completion conditions was not established in the study record. Historical outputs and implemented code remain distinguishable from a newly completed production campaign.

The next evaluation should test whether these implemented capabilities transfer to new papers under a recorded protocol. Useful measures include agreement with independently checked observables, correct handling of model limits, the validity of diagnostic follow-up and the human effort needed to complete a task. Source clarification, missing method implementations and full-scale execution remain concrete development priorities identified by the cases.

# Conclusion

PRAgent demonstrates a set of implemented capabilities for AI-assisted physics paper reproduction: translating scientific models into computational representations, solving case-specific numerical problems, and checking outputs against physical and statistical requirements. Precision-aware resource estimation, exact-sector quantum walks and ensemble-based discord analysis provide inspectable evidence for these capabilities. The 100-paper project places that technical depth in a broader record of coverage and verification, while diagnostic cases show how the workflow makes incomplete work actionable. RunThePaper preserves the resulting code, data and explanations for inspection and further research.

# Data, code and reproducibility {.unnumbered}

The public case archive is available at [RunThePaper, revision 43a64cd](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361). The three implementations are identified by case IDs `1811.08017`, `10.1126-science.aaw1611` and `0709.0548`. The report package includes an input-hash ledger, numerical summaries and a unified cohort roster. The accompanying analysis script reads frozen public Git objects and reconstructs all new figures without executing case code. The private production environment is not included in this release.

# AI assistance and manuscript responsibility {.unnumbered}

AI-assisted tools were used in software development, manuscript preparation and the visual design of the workflow schematic. Numerical figures were plotted from the archived arrays. The report does not attribute authorship to an AI system or claim a uniformly autonomous experimental campaign. The human authors are responsible for the interpretation of results, citations and final submitted text.

# References {.unnumbered}

\begingroup\small

1. Sandve, G. K., Nekrutenko, A., Taylor, J. and Hovig, E. Ten Simple Rules for Reproducible Computational Research. *PLoS Computational Biology* **9**, e1003285 (2013). [doi:10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285).

2. Pineau, J. et al. Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program). *Journal of Machine Learning Research* **22**(164), 1–20 (2021). [jmlr.org/papers/v22/20-303.html](https://www.jmlr.org/papers/v22/20-303.html).

3. Starace, G. et al. PaperBench: Evaluating AI's Ability to Replicate AI Research. *arXiv* **2504.01848** (2025). [arxiv.org/abs/2504.01848](https://arxiv.org/abs/2504.01848).

4. Siegel, Z. S., Kapoor, S., Nagdir, N., Stroebl, B. and Narayanan, A. CORE-Bench: Fostering the Credibility of Published Research Through a Computational Reproducibility Agent Benchmark. *arXiv* **2409.11363** (2024). [arxiv.org/abs/2409.11363](https://arxiv.org/abs/2409.11363).

5. Chan, J. S. et al. MLE-bench: Evaluating Machine Learning Agents on Machine Learning Engineering. *arXiv* **2410.07095** (2024). [arxiv.org/abs/2410.07095](https://arxiv.org/abs/2410.07095).

6. Campbell, E. A random compiler for fast Hamiltonian simulation. *Physical Review Letters* **123**, 070503 (2019). [doi:10.1103/PhysRevLett.123.070503](https://doi.org/10.1103/PhysRevLett.123.070503). Source preprint: [arXiv:1811.08017v2](https://arxiv.org/abs/1811.08017v2).

7. Yan, Z. et al. Strongly correlated quantum walks with a 12-qubit superconducting processor. *Science* **364**, 753–756 (2019). [doi:10.1126/science.aaw1611](https://doi.org/10.1126/science.aaw1611).

8. Datta, A., Shaji, A. and Caves, C. M. Quantum Discord and the Power of One Qubit. *Physical Review Letters* **100**, 050502 (2008). [doi:10.1103/PhysRevLett.100.050502](https://doi.org/10.1103/PhysRevLett.100.050502). Source preprint: [arXiv:0709.0548](https://arxiv.org/abs/0709.0548).

\endgroup

\clearpage

# Supplement: unified project roster {.unnumbered}

The project retains all 100 identities in one roster. The matrix below records evidence availability and mapping gaps, without defining origin-based comparison groups. Blue indicates available extracted material, amber a recorded gap, white absence within an available extraction and gray a measurement not assessed. These indicators describe public evidence organization, not scientific-success grades. Full titles and the selection provenance are supplied with the accompanying data.

\begin{center}
\includegraphics[width=0.94\textwidth,height=0.78\textheight,keepaspectratio]{figures/figS1_cohort_matrix.pdf}

\small\textbf{Supplementary Fig. S1.} Evidence availability for the fixed 100-paper project.
\end{center}
