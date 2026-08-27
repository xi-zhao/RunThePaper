# Figure Classification

The published seven-page PDF is the display-scope authority. The final main
paper contains 31 visible scientific/context items after splitting every
independently judged curve, heat map, reference layer, or experimental series.
The main text also identifies two numerical supplemental tables. This gives 33
known items: 30 eligible theoretical numerical items and 3 excluded context or
experimental items.

The formal APS supplement is subscription-gated. Tables S6 and S7 are known
because the main text names them, but any remaining supplemental figures,
tables, or independent quantitative claims cannot be enumerated. Therefore the
33-item inventory is an explicit lower bound, not a claim that the inaccessible
supplement has no other numerical content.

| Paper scope | Atomic items | Binding | Decision |
| --- | ---: | --- | --- |
| Main Fig. 1 | 1 | none | excluded schematic context |
| Main Fig. 2(a), upper | 5 | T001 | target: two ibDET curves, two GW+DMFT points, one EOM-CCSD reference |
| Main Fig. 2(a), lower | 5 | T002 | target: two ibDET curves, two GW+DMFT points, one EOM-CCSD reference |
| Main Fig. 2(b), three stacked axes | 6 | T003 | target: one method curve plus one displayed EOM-CCSD reference on each axis |
| Main Fig. 3(a) | 2 | T004 | target: GW+ibDET heat map and G0W0@PBE bands |
| Main Fig. 3(b) | 2 | T005 | target: GW+ibDET heat map and G0W0@PBE bands |
| Main Fig. 4(a), theoretical layers | 3 | T006 | target: GW+ibDET heat map, PBE band, G0W0@PBE band |
| Main Fig. 4(a), ARPES layers | 2 | T006 reference only | excluded experimental measurements |
| Main Fig. 4(b) | 1 | T007 | target: local-minus-full DOS heat map |
| Main Fig. 4(c), top | 2 | T008 | target: real and imaginary corrections at -3 eV |
| Main Fig. 4(c), bottom | 2 | T009 | target: real and imaginary corrections at 0 eV |
| Supplement Table S6 | 1 | T004 | deferred: missing_source_input |
| Supplement Table S7 | 1 | T005 | deferred: missing_source_input |

The target remains an execution unit and may serve several atomic items. This
does not merge their coverage decisions: every known eligible item appears
separately in `reproduction_measure.items[]` and, while uncovered, separately
in `uncovered_item_details[]`.

The EOM-CCSD reference is displayed once on each Fig. 2(b) comparison axis, so
the three display instances are separate reproduction items even though one
independently generated reference dataset may cover all three. Conversely, the
two ARPES series are retained in the inventory but excluded from the
formula-driven reproduction denominator because they require new laboratory
measurements.

Printed scalar anchors in the prose support these displayed items and are not
counted a second time as independent claims.
