# Figure classification

## Atomic coverage result

- Main-text displayed components inventoried: **17**.
- Eligible scientific numerical/method items: **5**.
- Covered by accepted independent evidence: **5**.
- Enumerated uncovered items: **0**.
- Known main-text item coverage: **5/5 = 100%**.
- Explicitly excluded context: **12** items (3 schematics and 9
  experimental-measurement components).
- Whole-paper inventory boundary: **source blocked**. The APS Supplemental
  Material is subscription-required and may contain an unknown number of
  additional items, so 5/5 must not be presented as whole-paper 100%.

The five covered items have only **51.53/100 mean fidelity**. Coverage answers
whether an eligible scientific object has accepted independent evidence;
fidelity answers how close and paper-specific that evidence is. Four critical
items remain below the 60-point fidelity floor even though they are covered.

| Paper item/component | Classification | Reproduction decision |
| --- | --- | --- |
| Main Fig. 1(a-c) | apparatus/schematic | exclude |
| Main Fig. 2(a), theoretical response component | theory numerical | one panel-level item mapped jointly to T001--T003; covered at fidelity 52.94 |
| Main Fig. 2(a), measured envelopes | experimental measurement | exclude; never reconstructed from pixels or synthetic data |
| Main Fig. 2(b), injected record | experimental measurement | exclude |
| Main Fig. 2(b), matched-filter method component | method numerical | T004; covered at fidelity 50.59 |
| Main Fig. 2(c), noise record | experimental measurement | exclude |
| Main Fig. 2(c), filter-sensitivity component | method numerical | T005; covered at fidelity 47.06 |
| Main Fig. 3(a-d) | experimental calibration/derived experimental analysis | exclude from theory/method denominator; retain visibly in inventory |
| Main Fig. 4(a), estimates and histogram | experimental measurement | exclude |
| Main Fig. 4(a), Gaussian/uncertainty component | method numerical | T006; covered at fidelity 62.35 |
| Main Fig. 4(b), prior constraints | external experimental context | exclude |
| Main Fig. 4(b), new constraint component | theory numerical | T007; covered at fidelity 44.71 |
| Supplemental Material | unknown until authorized source is obtained | inventory scope-blocked; not collapsed into a fake single item |

Every visible main-text subpanel and mixed-panel component is classified. A
target covers only the stated scientific component, never an unavailable
experimental trace. Machine-readable item IDs and the source boundary are in
`figure_coverage.json`.
