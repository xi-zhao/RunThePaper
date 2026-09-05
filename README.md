<h1 align="center">RunThePaper</h1>

<p align="center"><strong>An executable history of science.</strong></p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">Simplified Chinese</a>
</p>

<p align="center">
  <a href="LEARNING_PATHS.md">Learning paths</a> ·
  <a href="#browse-the-papers">Paper catalog</a> ·
  <a href="HISTORY.md">Paper timeline</a> ·
  <a href="UPDATES.md">Case updates</a> ·
  <a href="#run-this-example">Run an example</a>
</p>

**RunThePaper is building an executable history of science.** Our paper
reproduction agent, **PRAgent**, reconstructs the derivations, methods, and
computations behind papers. RunThePaper brings the resulting code, notes, data,
figures, and evidence together, organized by research field, learning path, and
paper chronology. The current collection focuses on physics and quantum science,
with English and Chinese notes.

A paper compresses a research result. Getting started often requires working
through intermediate derivations, parameter choices, and numerical decisions.
We preserve that path so the next researcher can understand how a result was
obtained, run the calculation, and build on it. Making these working foundations
accessible to students, researchers, and scientific agents is our approach to
research infrastructure for the AI era.

| What you want to do | Your starting point |
| --- | --- |
| **Enter a research field** | Prerequisites, a suggested paper order, and a first exercise for beginning graduate students and undergraduates with the relevant foundations. [Choose a learning path](LEARNING_PATHS.md). |
| **Continue existing work** | Derivations, code, results, and checks together for verification, teaching, new parameter studies, and extensions. [Browse the cases](CASES.md). |
| **Build AI for Science** | A machine-readable case index, executable calculations, and evidence records as domain context and validation material for scientific agents. [Explore the index](cases/catalog.json). |

Start with one formula, run one calculation, explain its output, then change an
assumption. Each case records the scope it reproduces and the work still open,
so you can choose a starting point with its limitations in view.

## Start with a result

How many quantum gates does Hamiltonian simulation require? The
[qDRIFT case](cases/1811.08017/README.md) reconstructs the resource estimates in
*A random compiler for fast Hamiltonian simulation*, comparing qDRIFT with
Trotter methods for three molecular examples.

![Independently generated Fig. 2: qDRIFT and Trotter gate-count bounds for propane, carbon dioxide, and ethane](cases/1811.08017/outputs/figures/fig2_gate_counts_reproduction.png)

*Generated reproduction of Fig. 2.* Follow the
[derivation](cases/1811.08017/note/reproduction-note.en.md), inspect the
[CSV data](cases/1811.08017/outputs/data/fig2_gate_counts.csv), or read the
[numerical checks](cases/1811.08017/outputs/checks/target_checks.json).
The case is [awaiting independent review](cases/1811.08017/outputs/checks/completion_assessment.json).

## Run this example

The qDRIFT example runs locally on a CPU with Python 3.11 or newer. From a
macOS or Linux terminal:

```bash
git clone https://github.com/xi-zhao/runthepaper.git
cd runthepaper
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd cases/1811.08017/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

This recomputes the numerical data behind Figs. 2 and 4 and writes:

- `cases/1811.08017/outputs/data/fig2_gate_counts.csv`
- `cases/1811.08017/outputs/data/fig4_phase_estimation_counts.csv`
- `cases/1811.08017/outputs/checks/target_checks.json`

The check file reports `"status": "passed"` when the numerical checks pass.
The plotted figures are included in the repository; this command regenerates
the data and checks. See the [case instructions](cases/1811.08017/code/README.md)
for its scope and remaining review work.

## Browse the papers

<!-- case-catalog:start -->
**100 public paper cases**, including partial and blocked reproductions.
Open a collection in the [full catalog](CASES.md) for paper references,
recorded status, bilingual notes, code, and evidence.

[Learning paths](LEARNING_PATHS.md) · [Paper timeline](HISTORY.md) · [Recent case updates](UPDATES.md)

| Research collection | Cases |
| --- | ---: |
| [Quantum computing, algorithms & error correction](CASES.md#collection-quantum-computing) | 25 |
| [Quantum information, foundations & sensing](CASES.md#collection-quantum-information) | 18 |
| [Many-body physics, phases & nonequilibrium dynamics](CASES.md#collection-many-body) | 27 |
| [Topology, non-Hermitian physics, materials & transport](CASES.md#collection-topology-materials) | 21 |
| [Atomic, optical, photonic & field physics](CASES.md#collection-amo-field) | 9 |
<!-- case-catalog:end -->

For another starting point, explore [non-Hermitian edge states](cases/1803.01876/README.md)
or [disorder and Lyapunov band theory](cases/2507.09447/README.md).
Their case pages link the paper, derivations, results, and current limitations.

## How to read the results

Three questions matter when using a reproduction:

| Question | Where to look |
| --- | --- |
| **What was reproduced?** | The case overview names the figures or claims covered, parameters used, and any missing inputs or compute limits. |
| **Do the results agree?** | Generated data and scientific checks show numerical agreement, discrepancies, and tolerances. Visual similarity is recorded separately. |
| **What remains open?** | The completion assessment records unresolved targets and independent review status. Passing a run does not close the whole case. |

The collection includes partial results and unsuccessful attempts with their
evidence. A paper-error candidate is a finding to investigate, not a settled
correction to the paper.

The [frozen 100-paper audit](evaluation/claim-first-100/README.md) maps 3,933
checks to 1,427 scientific claims. With each numerical claim weighted equally,
its outcomes are:

| Outcome | Share |
| --- | ---: |
| Successfully reproduced | 40.55% |
| Blocked by documented external limitations | 21.93% |
| Attempted but not reproduced | 37.52% |

These are claim-level outcomes, not a percentage of fully reproduced papers.
The audit includes the [full ledger and measurement method](evaluation/claim-first-100/README.md),
including fidelity evidence and its limits.

## What makes this history executable

**PRAgent reproduces papers; RunThePaper organizes and accumulates the work.**
PRAgent handles paper understanding, derivation, implementation, and computation,
and organizes validation and independent review. RunThePaper publishes the
shareable materials, evidence, and recorded review state. The PRAgent execution
system is developed separately and is not distributed in this repository.

A paper is one entry into this history. Its case connects a research question
to the claims, derivations, code, generated results, and checks behind it.
You can follow that chain, rerun a calculation, inspect a discrepancy, or ask
what happens when an assumption changes.

As these cases accumulate, they form a shared knowledge foundation for
learning and further research. Tracing relationships between discoveries,
retrieving across cases, and measuring their value to scientific agents are
[next-stage work](ROADMAP.md).

## A history that keeps growing

Research collections organize the papers by field. Learning paths add
prerequisites, reading order, and exercises. The [paper timeline](HISTORY.md)
provides a chronological route into the collection. These views refer to the
same cases and their recorded scientific state.

The [update history](UPDATES.md) is generated from actual commits. It separates
new papers, updates, and removals, and shows whether code, derivations, data,
figures, or validation evidence changed. Every entry links an exact revision.
The catalog, learning paths, paper timeline, and update history follow one
[maintenance workflow](CONTRIBUTING.md#organize-the-library-and-record-updates).

## Contribute

- **Request a paper:** [open an issue](https://github.com/xi-zhao/runthepaper/issues/new)
  with its DOI or arXiv ID and the figure or claim you want to reproduce.
- **Report a run or discrepancy:** include the case, command, environment, and
  observed result so someone else can check it.
- **Review or extend a case:** contribute a derivation check, missing input,
  correction, or additional result through the [contribution workflow](CONTRIBUTING.md).
- **Improve a learning path:** report a missing prerequisite, unclear
  derivation, or command that failed, or suggest a paper order and exercise.
  A specific learning experience can improve the shared research foundation.

When using a case in your work, cite the original paper and link the case at
the commit you used so readers can inspect the same materials.

## License

Code: [MIT](LICENSE-CODE). Notes, generated data, and generated figures:
[CC BY 4.0](LICENSE-CONTENT), unless a case states otherwise.
Third-party material, including attributed paper excerpts in comparison panels,
retains its original terms; see [NOTICE.md](NOTICE.md).
