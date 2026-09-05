# RunThePaper Roadmap

**An executable history of science / 可执行的科学史。**

We are building a shared research foundation where people can revisit a
scientific idea through its derivation, implementation, results, and evidence,
then continue the investigation. PRAgent reproduces papers; RunThePaper
organizes and accumulates the public work. We begin with physics and quantum
science and design for both human learning and future AI for Science uses.

## Available foundations

- Paper cases connect bilingual notes, derivations, runnable implementations,
  generated results, and explicit evidence boundaries. Individual cases still
  include partial results, blockers, and pending reviews; see the
  [fixed-cohort audit](evaluation/claim-first-100/README.md).
- [Research collections](CASES.md) organize papers by field.
  [Learning paths](LEARNING_PATHS.md) add prerequisites and first exercises.
  The [paper timeline](HISTORY.md) makes the recorded chronology browsable.
- A [structured catalog](cases/catalog.json) provides stable case identities
  and evidence pointers. The [update history](UPDATES.md) tracks actual case
  changes; repeat generation only writes changed pages.
- [Contribution rules](CONTRIBUTING.md), case validation, and navigation checks
  protect consistency with the PRAgent public projection.

These are working entry points. Learning paths have not yet been validated
through a student study, and chronology alone does not explain intellectual
connections between papers.

## Next: validate the first research experience

The first audience is beginning graduate students and undergraduates with the
relevant foundations. Choose a small set of routes and observe whether readers
can understand a derivation, run a documented calculation, explain its result,
and change one assumption.

Record prerequisite gaps, failed commands, compute requirements, and points of
confusion against the exact case version. Improve the affected material in
PRAgent or the editorial learning path, then repeat the exercise. Report how
many learners attempted and completed each step before claiming a reduction
in time to first research result.

## Then: connect discoveries and methods

Develop curated histories around scientific questions: what problem motivated
a method, which assumptions changed, and which later papers extended or
challenged it. Each relationship needs a source and a clear explanation.

Link existing cases rather than creating duplicate scientific records. A
useful first milestone is one reviewed path that a reader can follow across
several papers, with a reproducible calculation at each step. Keep chronology,
pedagogical order, and evidence of scientific influence distinct.

## Build an evidence base for AI for Science

Use the existing identities, methods, code, and validation records to explore
retrieval across cases and scientific-agent workflows. The first evaluation
should ask whether these materials help an agent solve a defined scientific
task, with a fixed task set, a comparison baseline, and inspectable run evidence.

Measure retrieval quality, execution success, and scientific correctness
separately. Record failures and resource limits. Claims about better scientific
agents or accelerated discovery follow the evaluation; they are not established
by publishing a structured catalog.

## Keep the foundation usable as it grows

Add new papers and revise existing cases through the same projection and
navigation workflow. Introduce small, bounded CI checks for public entry
commands and stale navigation, with failures attributed to a case and version.
Expensive scientific runs keep their resource requirements and explicit scope.

The public repository remains the place to learn, inspect, run, and build on
reproductions. PRAgent retains the execution system and scientific state
authority. No roadmap item changes a case's recorded completion status.
