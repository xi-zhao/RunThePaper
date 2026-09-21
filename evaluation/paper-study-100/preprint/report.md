---
title: 'PRAgent: Building Reproducible Physics Research Workflows with AI Agents'
subtitle: 'A Technical Report on a 100-Paper Project'
date: 'September 2026'
---

\begin{abstract}
Turning a physics paper into executable research requires mathematical interpretation, numerical implementation and evidence that connects computed outputs to the source problem. We present PRAgent, a human-guided workflow for AI-assisted scientific reproduction, together with RunThePaper, a public collection of research cases. The workflow connects source objects and equation-level reasoning to case-specific code, generated arrays, physical diagnostics and versioned reports. We describe its use in a fixed 100-paper project and examine three implemented studies: resource estimation for randomized Hamiltonian simulation, interacting quantum walks and quantum discord. Reanalysis of archived quantum-walk arrays gives particle-number residuals below $3\times10^{-15}$ across 4,509 stored state-time slices. Resource-estimation tables recover distinct gate-count scalings, while discord ensembles expose the importance of separating finite-instance calculations from analytical references. These examples demonstrate concrete implementations and inspectable computational outputs across different numerical tasks. The contribution is a research workflow and its reusable artifacts, rather than a new physical theory or a controlled benchmark of autonomous agents. We provide source-linked figures, analysis code and a unified cohort record to support inspection and further development.
\end{abstract}

# Introduction

A useful scientific assistant must help bridge the distance between a result stated in a paper and a computation that another researcher can inspect. In physics, that distance includes interpreting notation, recovering intermediate derivations, choosing a representation of the state space, implementing a numerical method and deciding whether the resulting observable answers the original question. These steps draw on both domain knowledge and software engineering. Their outputs must also survive beyond the conversation in which they were produced.

AI coding tools can assist with implementations, explanations and debugging, but a research task is rarely specified as a complete software requirement. A paper may leave a convention implicit, report a limiting expression beside a finite-size example, or show experimental measurements alongside a theoretical model. The assistant must operate within a research process that makes these distinctions explicit. Otherwise, a working script can quietly solve a different problem from the one that motivated it.

This report describes the construction of such a process through PRAgent and RunThePaper. PRAgent organizes the reproduction work around a persistent research case; RunThePaper publishes the resulting explanations, implementations and evidence. The project aims to make scientific papers executable starting points for further study: a reader should be able to follow the equations, locate the implementation, inspect generated values and identify the scope of the result.

We report a fixed project cohort of 100 papers and develop three case studies in detail. The examples cover numerical resource-bound evaluation, coherent quantum dynamics and ensemble-based quantum-information calculations. They were selected to expose different implementation decisions rather than to estimate an average success rate. Each example connects a mathematical formulation to actual public code and stored numerical arrays. For this report, we reanalyze those arrays and redraw their results without executing the original scientific solvers.

The technical contributions are threefold. First, the workflow gives paper interpretation, numerical work and evidence management a common case structure. Second, the case implementations show how physical reasoning shapes software choices, including exact particle-sector representations, high-precision resource calculations and explicit statistical treatment of random ensembles. Third, the project makes the resulting work inspectable through a public archive and a unified cohort record. These contributions support a practical account of AI-assisted research development; they do not require a claim that all 100 papers have been fully reproduced or that one model independently completed the project.

# Research context

Computational reproducibility depends on preserving enough information to understand and reconstruct a result. Sandve and colleagues emphasize traceable computation and accessible research materials [1], while the NeurIPS reproducibility program combines reporting requirements, code availability and community verification [2]. These practices motivate the durable case structure used here: a numerical figure should be connected to its equations, inputs and implementation rather than treated as an isolated deliverable.

Recent agent benchmarks examine complementary parts of research work. PaperBench evaluates paper replication against detailed requirements, CORE-Bench studies computational reproducibility with research artifacts, and MLE-bench evaluates machine-learning engineering on competition tasks [3–5]. Their task definitions are useful precedents for explicit evaluation. Our report instead concerns the construction and inspection of physics research cases produced under heterogeneous development conditions. The archive is not a matched-budget comparison with those benchmarks.

The physical methods used in the case studies originate in their cited source papers [6–8]. We do not present qDRIFT, the quantum-walk model or quantum discord as new methods developed in this project. Our work lies in their implementation, the associated computational checks and the workflow that packages them as reusable research artifacts. This attribution separates the underlying scientific ideas from the engineering and reproduction work described below.

# Workflow and system design

## The research case as a persistent unit

The central object is a research case associated with an identifiable paper. A case contains the source identity, the intended scientific scope, an equation trace, a numerical implementation, its configuration, generated data and assessment records. Keeping these materials together allows a result to be followed backward from a plot to the computation and assumptions that produced it.

Three relationships are particularly important. A source object identifies what is being addressed in the paper: a curve, a table entry or an analytical statement. An execution target specifies the computation or check that produces evidence for that object. An artifact records an output such as an array, diagnostic or explanatory note. These relationships can be many-to-many. A convergence sweep may support one plotted result, and one propagated state may supply several observables. The workflow preserves the links without counting each supporting check as a new scientific result.

The project uses AI assistance within a human-guided research process (Fig. 1). The execution host supports interpretation, code development and debugging. Shared workflow tools manage case records, validation inputs and report generation. Paper-specific implementations remain in their own cases. This division gives a reusable organization to the work while allowing the numerical method to depend on the physics.

![Architecture of the human-guided research workflow. Human decisions guide the four PRAgent stages; assessment can return work for revision. Derivations, code, data and review records persist in a versioned research case, from which selected artifacts enter RunThePaper. Dashed connections indicate human guidance; solid arrows indicate workflow or artifact transfer. The schematic describes these relationships, not uniform case completion.](figures/fig1_workflow.pdf){width=100%}

## From equations to implementation

The first technical task is to translate the source problem into a numerical contract. The contract identifies the physical model, observable, system size, parameters, boundary conditions and approximation regime. Equation records connect the relevant source expression to the functions and configuration fields that implement it. A derivation note explains intermediate transformations when they are necessary to understand the numerical representation.

This translation is a scientific design decision. In a particle-number-conserving Hamiltonian, an invariant sector may provide an exact representation of the desired dynamics. In a resource estimate, the relevant output may be a bound on circuit length rather than a simulated many-qubit state. In an ensemble calculation, a new sample can probe a stated distribution without reconstructing an unpublished author realization. The case must state which task it performs before its output can be interpreted.

The numerical implementation then separates model construction, solution, observables and rendering. This organization makes it possible to inspect or replace one component without obscuring the rest. For example, a quantum-walk state can be propagated once and used to compute density, correlation and double occupancy. A resource-bound evaluator can produce a numerical table independently of how that table is plotted. Numerical figures in this report are regenerated from stored tables, illustrating that separation directly.

## Physical checks and versioned evidence

Checks are attached to the quantities that give them scientific meaning. Normalization tests apply to quantum states or conserved particle number. A resource-bound check examines the inequality at neighboring integer counts. An ensemble interval quantifies sampling uncertainty under its stated procedure. These diagnostics provide different kinds of evidence and should not be reduced to a count of passing assertions.

PRAgent also separates delivered work from the scientific status of that work. A script, an output array and a review report are individually useful artifacts, but they establish different facts. The workflow records whether the scope has been checked, which conditions were used and whether an assessment applies to the current evidence. In the production design, case state is derived from evidence rather than set by a narrative claim that the task is finished.

This architecture supports a practical development cycle: establish scope, implement, compute, inspect discrepancies, revise and retain the new evidence. It also exposes incomplete work. A runtime problem can be recorded without discarding the derivation; a reference ambiguity can remain visible alongside correct numerical implementation of a stated convention. The value of a persistent case is that these outcomes become material another researcher can examine and extend.

## Public research artifacts

RunThePaper provides the public presentation of the case. Its materials include reproduction notes, derivations, code, generated data, figures and checks. The case identifies its source paper and states what remains approximate, unresolved or unavailable. Public selection is linked to the originating case rather than allowing a manually assembled presentation to redefine its scientific status.

This layer serves both reproducibility and communication. A researcher can inspect a specific array or function; a learner can enter through the explanatory note; and a developer can reuse an implementation pattern. The present report concentrates on the implemented workflow and published artifacts. It does not claim measured improvements in learning efficiency or model capability from the archive.

# Project scope and analysis procedure

The project is organized around one fixed cohort of 100 paper identities. The full roster accompanies the report. It is a purposive research collection, with outcome-informed selection and feasibility considerations; the preserved selection history contains 103 distinct identities. The cohort size describes project scope, not a count of fully successful reproductions. Missing measurements remain attached to their identities in the same roster.

At the frozen archive revision used here, standardized public extraction is available for 97 cohort members. Those records contain public Python files for 97 papers and public data files for 96. The extraction preserves 3,666 source-inventory entries and 261 unlinked target records. Their combined 3,927 records describe the organization of evidence, not a common scientific-result denominator. Details of availability and unresolved links are retained in the audit materials rather than used as the main measure of system capability.

We selected the three studies below to illustrate complementary computational work: stable evaluation of analytical resource formulas, exact dynamics in restricted Hilbert spaces and numerical analysis of quantum correlations. Selection was not blinded to the available outputs. The examples therefore support statements about these implementations, without estimating performance over the entire cohort.

All displayed numerical results are drawn from public files at [RunThePaper revision 43a64cd](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361). The report's analysis reads the Git objects, records their hashes, rechecks specified properties of stored arrays and regenerates figures. It does not import case modules or run scientific solvers. We distinguish these new array-level calculations from historical execution and review claims. The full input ledger and computed summaries accompany the source package.

# Representative implementations and results

## Stable resource estimation for Hamiltonian simulation

The qDRIFT study addresses how the circuit resources required for Hamiltonian simulation depend on the simulation time and an error criterion [6]. Its inputs include Hamiltonian summary parameters and the error-bound expressions associated with different compilation methods. This is a resource-estimation task: the molecular qubit counts in the source configuration do not imply that the project simulates the corresponding full many-qubit wavefunctions.

The archived implementation evaluates qDRIFT and deterministic or randomized product-formula bounds. It computes multiplicative expressions in logarithmic form and handles competing terms using stable log-sum-exp calculations. These choices matter because the resource counts span many orders of magnitude. A naive evaluation can overflow even when the final comparison is meaningful.

A second issue arises when the output is the smallest integer satisfying a bound. At sufficiently large counts, adjacent integers have identical floating-point representations. The case implementation therefore uses a floating-point bracket as a starting point and refines the boundary using 60-digit decimal logarithms. The relevant question is whether the bound holds at $N$ and fails at $N-1$, not merely whether a continuous estimate looks plausible. This is an example of a numerical-analysis requirement that emerges from the scientific output being requested.

The public tables contain 366 rows for time-dependent resource estimates and 366 rows for phase-estimation estimates. Figure 2a redraws the propane resource curves directly from these tables. Figure 2b compares the stored randomized second-order Trotter and qDRIFT phase-estimation counts at failure probability 0.05. The resulting ratios are 303.72 for carbon dioxide, 788.73 for ethane and 1405.51 for propane. These are ratios of theoretical resource estimates under the case's declared formulas and parameters; they are not measured wall-clock speedups of PRAgent or demonstrations on quantum hardware.

The case demonstrates the implementation of a scientific comparison across numerical scales, including precision-sensitive integer decisions. Its public record also retains unresolved interpretation of a printed source value and a pending fresh review. We use the available calculations as a scoped implementation result rather than promoting that unresolved comparison into a confirmed correction of the paper.

![Hamiltonian-simulation resource estimates redrawn from the public qDRIFT case. **a**, The stored propane gate-count bounds for five compilation strategies across the source time range. **b**, Ratios of randomized second-order Trotter to qDRIFT counts in the phase-estimation table at failure probability 0.05. These are formula-based resource estimates; neither panel reports physical quantum-device execution or an agent runtime advantage.](figures/fig2_resources.pdf){width=100%}

## Interacting quantum walks in exact particle sectors

The quantum-walk study implements the coherent theoretical model associated with the superconducting-processor experiment of Yan and colleagues [7]. A Bose-Hubbard Hamiltonian provides the case formulation,
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

Figure 3a displays the stored one-excitation density for a central launch. The correlation matrices in Fig. 3b–d show the calibrated interaction and its two control models for the same two-excitation launch and displayed time. Replotting these arrays exposes the connection between the chosen physical approximation and the spatial correlation pattern. The controls answer a modeling question within the case; they are not baselines for comparing AI agents.

We independently recomputed the density-sum diagnostic from the stored CSV values. Across 1,503 one-excitation state-time slices, the maximum deviation from one is $1.78\times10^{-15}$. Across 3,006 two-excitation slices, including the recorded model and launch combinations, the maximum deviation from two is $2.66\times10^{-15}$. These residuals demonstrate conservation consistency in the inspected arrays. They do not by themselves establish agreement with all observables or source conditions.

The implementation illustrates how physical structure can guide an efficient and interpretable computation: the conserved sector determines the basis, one propagation supplies several observables, and explicit limits provide controls. The broader case still records a source-time discrepancy for supplementary comparisons and incomplete knowledge of author realization-level parameters. Those boundaries do not erase the implemented dynamics, but they constrain a whole-paper claim.

![Quantum-walk outputs regenerated from stored arrays. **a**, One-excitation density after launch at site Q6 in the 11-site setup. **b–d**, Two-excitation correlators at 55.5 ns for launch Q6+Q7 in the 12-site setup, using calibrated interactions, the hard-core limit and free bosons. The correlation panels share a color scale. These are generated model outputs, not experimental measurements; the displayed time is taken from the archived table and is not an adjudication of the case's unresolved source-time issue.](figures/fig3_quantum_walks.pdf){width=100%}

## Quantum discord: separating ensembles, references and logical claims

The discord study implements the DQC1 correlation problem considered by Datta, Shaji and Caves [8]. For a unitary $U$ acting on a register of dimension $d$ and control polarization $\alpha$, the case constructs
\[
\rho=\frac{1}{2d}\begin{pmatrix}I_d&\alpha U^\dagger\\\alpha U&I_d\end{pmatrix}.
\]
It computes entropic quantities and measurement-dependent conditional entropies using explicit numerical representations. The source question motivates comparing the resulting discord with an analytical reference, while the implementation must also specify the unitary ensemble and optimization procedure.

The public numerical-method record describes two independent ensembles of 500 matrices in $U(32)$: a QR-based Haar construction and a depth-32 local brickwork construction. The latter is explicitly identified as an independent probe because the original finite pseudorandom generator is not published. Each curve is stored on a 41-point polarization grid, with mean, standard deviation, standard error and interval fields. This representation keeps sampling variation visible instead of presenting an individual realization as a universal result.

Figure 4 shows the archived means and their deviations from the analytical reference. At $\alpha=1$, the stored QR-Haar mean is 0.537735 bits, the brickwork mean is 0.537483 bits and the reference is 0.557305 bits. Their corresponding differences from the reference are approximately $-0.01957$ and $-0.01982$ bits. The displayed bands use the case's stored pointwise 95\% interval endpoints. They describe ensemble uncertainty under the recorded procedure, not simultaneous confidence bands or uncertainty in the analytical expression.

The discrepancy is informative because it prevents several distinct objects from being conflated: a finite register, a finite ensemble, an unpublished source realization and an analytical limiting expression. The plot records their relationship under the case configuration. It does not establish a new general result about discord or a confirmed error in the source paper.

The code also makes a useful logical distinction in its treatment of entanglement. For the control-register split, it constructs a convex product-state decomposition from the eigenbasis of $U$. For other partitions, one-sided tests such as negativity are recorded as detection criteria. Failure to detect entanglement is not used as a separability proof. This illustrates how the interpretation of a numerical check can be as important as its implementation.

![Quantum-discord outputs redrawn from the archived DQC1 case. **a**, The analytical reference and means of the QR-Haar and independent brickwork ensembles. **b**, Mean-minus-reference residuals expose deviations that are less visible in the main curves. Shading uses the stored pointwise interval endpoints. Ensemble specifications originate in the public method record; these are generated case outputs rather than recovered author samples.](figures/fig4_discord.pdf){width=100%}

# Lessons for AI-assisted scientific work

## Domain reasoning determines the computational task

The examples share a workflow but require different numerical decisions. Resource estimation calls for stable formulas and precision-aware integer search. Quantum transport calls for a faithful Hilbert-space representation and consistent observable definitions. Discord calculations call for explicit ensemble design and careful interpretation of analytical references. A generic instruction to reproduce a figure does not specify these choices.

The role of the research workflow is to expose those choices in inspectable artifacts. A derivation explains the transformation, a configuration records the conditions, code implements the calculation, and a numerical table makes the result accessible independently of the plot. These are concrete outputs through which scientific and engineering decisions can be evaluated. The system's usefulness is demonstrated here by those implementations and records, rather than by a claim that language-model fluency establishes scientific correctness.

## Reusable structure should preserve case-specific physics

Several patterns recur: source-to-equation traces, separation of solver and rendering code, conservation checks, analytic controls and versioned output tables. They are candidates for reuse across research tasks. However, their acceptance rules remain tied to the problem. The numerical tolerance appropriate to particle-number conservation is not a substitute for uncertainty in an experimental comparison, and agreement with a resource formula says nothing about the fidelity of a quantum-device implementation.

The architecture therefore keeps shared evidence-management tools separate from domain implementations. This boundary allows common reporting and provenance without requiring every physical problem to fit one solver or one score. It also provides a practical route for extending the project: retain a stable case interface while introducing new numerical methods where the physics requires them.

## Partial results can be substantive research assets

An incomplete paper reproduction can still contain a useful derivation, a verified local calculation or a reusable implementation. The quantum-walk sector solver and resource-bound evaluator are examples of concrete computational work whose value is more specific than a single case-level status. Reporting that scope allows a reader to judge whether the artifact is relevant to a new question.

The same precision is necessary when describing AI assistance. This project combines human choices, AI-supported development and deterministic checks. Historical model revisions, interaction budgets and intervention records are not uniformly available. Accordingly, the report documents the resulting system and artifacts, not a controlled measurement of an autonomous model's ability. Attribution of authorship and responsibility remains with the human contributors.

# Limitations and future work

The 100-paper cohort is heterogeneous and purposively selected. The detailed studies were chosen for their inspectable implementations and contrasting numerical tasks. They do not estimate a population success rate, and no matched-budget agent comparison or ablation is reported. The public-array reanalysis performed for this manuscript verifies only the explicitly described properties; it is not a new independent assessment of every source claim.

The public archive can also omit evidence available in the originating workspace. Reference gaps, unmapped targets and historical review state are therefore retained in the accompanying audit. Current production execution has an additional infrastructure boundary: the configured workflow does not yet provide a verified numerical isolation backend sufficient to close the relevant completion conditions. Development artifacts and historical numerical outputs must not be presented as a newly completed production campaign.

The next empirical steps are to complete source-level assessment under explicit criteria, close the production execution and reviewer handoff, and evaluate the workflow under recorded resource and intervention budgets. Comparisons could then measure reviewer agreement, implementation reliability or research effort. Those are future experiments rather than benefits established by the present report.

# Conclusion

PRAgent and RunThePaper organize AI-assisted physics work around executable, inspectable research cases. The project connects paper interpretation, numerical implementation and public evidence across a fixed 100-paper scope. Detailed examples demonstrate stable resource estimation, exact-sector quantum dynamics and ensemble-based correlation analysis, with generated arrays that support further inspection. The contribution is a concrete integration of scientific reasoning and research software: the result of a task can be studied, checked and extended after the original development interaction ends.

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
