# Paper map — cond-mat/0503511

## Scientific question

The paper asks how a finite open transverse-field Ising chain responds when the
field is quenched linearly from the paramagnet through the quantum critical point
into the ferromagnet. Its two main displayed claims are:

1. the residual kink density follows the Kibble-Zurek square-root scaling in its
   domain of validity;
2. the slow-quench, low-defect regime is described by the finite-size
   Landau-Zener gap and therefore requires a quench time proportional to `N^2`.

## Source inventory

- Main paper: `raw/paper.pdf`, SHA256
  `f504a15b68f934109b3a373e12b2aaf3ac10ecd964658ccab76dd735afa07f98`.
- arXiv source archive: `paper-source.tar`, SHA256
  `dd65ae42089d2ba467246add75b80d088addc2c9bd537f0125bf83a4e724aafe`.
- The archive contains only `article.tex` and three EPS figures. It contains no
  computational source code, scripts, notebooks, or author numerical arrays.
- Method reference: `references/Dorner2003_quant-ph-0212039.pdf`.
  It is read only to recover the published Majorana method and the definitions of
  the fidelity bounds; no author code or arrays are present or used.
- No Supplemental Material is linked or included in the arXiv bundle.

The whole-paper audit also tests an independent no-display scalar claim: whether
Eq. (15) yields the stated LZF-to-KZM density ratio at `f=0.5`.

## Complete reproduction-item inventory

| Source item | Type | Atomic item count | Target | W1 status |
|---|---|---:|---|---|
| Main Fig. 1 | numerical series | 7 | T001 | all covered |
| Main Fig. 2(a) | numerical series families | 4 | T002 | all covered; fidelity capped by unpublished display subset |
| Main Fig. 2(b) | numerical series and fits | 4 | T003 | all covered |
| Main Fig. 2(c) | numerical bounds and fits | 12 | T004 | all covered |
| Main Fig. 3 | numerical series and fits | 18 | T005 | all covered |
| Eq. (15) plus following sentence | independent quantitative claim | 1 | T006 | uncovered |

There are no schematic-only figures, experimental panels, tables, or supplement.
The resulting whole-paper denominator is 46 eligible items: 45 display items are
covered and one independent scalar claim is uncovered, for 97.83% W1 coverage.
The EPS/PDF graphics are comparison-only evidence; they are never numerical
inputs.

## Explicit uncovered item

| Item | Paper location | Scientific object | Direct cause | Root cause | Code fault | Next discriminating test |
|---|---|---|---|---|---|---|
| `C1-lzf-kzm-ratio-f05` / T006 | Main PDF p. 4, Eq. (15) and following paragraph | LZF/KZM density ratio at `f=0.5` | literal coefficient gives `0.105723838752`, prose gives about `0.14`, and no independent claim artifact exists | unresolved, open | not excluded; current figure code never evaluates this scalar as a target | independently re-derive Eqs. (10),(14),(15), evaluate with a second implementation, then fresh-context review |

## Source anchors

- Hamiltonian and open boundary: `paper-source/article.tex:150-171`.
- Gap, relaxation and healing length: `paper-source/article.tex:176-201`.
- Kibble-Zurek derivation: `paper-source/article.tex:217-265`.
- Fig. 1 parameters and claims: `paper-source/article.tex:276-292`.
- Fig. 2 parameters and claims: `paper-source/article.tex:293-313`.
- Landau-Zener derivation and accessible gap: `paper-source/article.tex:356-419`.
- Eq. (15) scalar and the `0.14` prose statement:
  `paper-source/article.tex:415-424`.
- Fig. 3 parameters and claims: `paper-source/article.tex:438-458`.
- Published Majorana evolution and fidelity moments:
  `references/Dorner2003_quant-ph-0212039.pdf`, page 3.
