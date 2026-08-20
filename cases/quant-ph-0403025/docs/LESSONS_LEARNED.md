# Lessons Learned

## Case Summary

- Paper: Bravyi–Kitaev magic-state distillation
- PaperID: `quant-ph-0403025`
- Current authority boundary: fresh-context review pending
- Reproduced: all three numerical panels, all printed executable threshold/resource claims
- Publication blocker: undefined `n=11,17` exploratory GF(4) simulations

## What Worked

- A closed-form curve was never treated as self-validating: T used an explicit `32 x 32` projector and H used a structurally different codeword enumerator.
- The numerical runner was kept free of Matplotlib, raw files and reference images, making the access boundary small and auditable.
- The post-freeze RenderContract matched old EPS presentation very closely without touching a physical array.
- One complete scientific crop per numeric panel prevented a high full-canvas score from hiding a weak subplot.

## Generalized Experience

| Lesson | Why it matters | Future recommendation |
| --- | --- | --- |
| Closed form plus a distinct combinatorial construction is stronger than two algebraically similar functions | Shared transcription errors become less likely | Seek different mathematical objects for the second method |
| Publication omissions must be split from compute limits | More hardware cannot recover an undefined code | Record the direct cause, root cause and missing object explicitly |
| Renderer inputs should be individual frozen files, not an entire source tree | It reduces accidental source-image access and pycache noise | Declare the minimal file bundle in the run contract |
| EPS-derived references can be used safely after freeze | Exact presentation can be optimized without contaminating science | Keep reference paths out of the numerical contract |

## Pitfalls

| Pitfall | Evidence here | Prevention |
| --- | --- | --- |
| Broad `src/` input declarations include bytecode caches | The first isolated run exposed unnecessary inputs | List exact source files; rerun attestation |
| Calling an underspecified claim “compute blocked” | `n=11,17` lacks the code itself | Require an executable problem definition before estimating compute |
| Reporting a single average pixel score | Fig. 2 contains two independent numerical panels | Register each panel as a separate lifecycle-eligible target |

## Reusable Checks

- Hash-before/hash-after assertion in the renderer.
- Fail-closed renderer test for tampered scientific CSV.
- Independent algebraic-vs-combinatorial map comparison across an audit grid.
- Explicit publication-omission diagnosis with a next discriminating evidence request.

## New Failure Modes

| Failure mode | Where it appeared | Detection |
| --- | --- | --- |
| Over-broad isolated input bundle | v1 declared a source directory and admitted bytecode caches | reject directory-level scientific inputs when exact files can be listed |
| Undefined published computation mislabeled as a resource shortage | Sec. VII `n=11,17` statement | require the actual mathematical input object before assigning `insufficient_compute` |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Minimal-input contract lint | Smaller provenance surface and deterministic hashes for every case | isolated-run preflight |
| Independent map parity helper | Compares closed forms with matrix/combinatorial constructions on a declared grid | case-local first, generic numeric helper later |

## Harness Backlog

No new global Harness item is proposed: minimal isolated inputs, RenderContract separation, per-panel scientific crops and causal diagnosis are already active rules. This case validates those mechanisms rather than introducing another special case.
