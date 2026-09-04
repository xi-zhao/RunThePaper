<h1 align="center">RunThePaper</h1>

<p align="center"><strong>Read the paper. Run the result.</strong></p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">Simplified Chinese</a>
</p>

<p align="center">
  <a href="#browse-the-papers">Browse papers</a> ·
  <a href="#run-this-example">Run an example</a> ·
  <a href="#how-to-read-the-results">Read the evidence</a> ·
  <a href="#contribute">Contribute</a>
</p>

**RunThePaper is an open library of physics paper reproductions.** Each case
brings together the derivation, runnable code, generated data and figures,
validation checks, and a clear account of what remains unresolved. Notes are
available in English and Chinese.

Use a case to understand a method, check a published result, or start a new
calculation without rebuilding the whole research context from a PDF.

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

[Find a learning path](LEARNING_PATHS.md) · [Recent case updates](UPDATES.md)

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

## How cases are made

We build cases with **PRAgent**, our paper reproduction harness: it organizes
paper understanding, derivation, implementation, numerical execution, checks,
and independent review. RunThePaper publishes the resulting research materials
and their recorded boundaries. The PRAgent execution system is developed
separately and is not distributed in this repository.

Our aim is to make each reproduction useful to the next researcher: a place
to rerun a result, investigate a discrepancy, or change an assumption and ask a
new question. See the [roadmap](ROADMAP.md) for planned work.

## Contribute

- **Request a paper:** [open an issue](https://github.com/xi-zhao/runthepaper/issues/new)
  with its DOI or arXiv ID and the figure or claim you want to reproduce.
- **Report a run or discrepancy:** include the case, command, environment, and
  observed result so someone else can check it.
- **Review or extend a case:** contribute a derivation check, missing input,
  correction, or additional result through the [contribution workflow](CONTRIBUTING.md).

When using a case in your work, cite the original paper and link the case at
the commit you used so readers can inspect the same materials.

## License

Code: [MIT](LICENSE-CODE). Notes, generated data, and generated figures:
[CC BY 4.0](LICENSE-CONTENT), unless a case states otherwise.
Third-party material, including attributed paper excerpts in comparison panels,
retains its original terms; see [NOTICE.md](NOTICE.md).
