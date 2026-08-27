# Figure Classification

The inventory covers the complete 21-page arXiv v2 PDF and both TeX sources.
There are four main-text figures, two supplemental figures, and no tables.

| Item | Panels | Class | Reproduce? | Reason | Target ID / blocker |
| --- | --- | --- | --- | --- | --- |
| Main Fig. 1 | a,b | numeric_reproduction | yes | TDVP phase portrait/error and exact local dynamics are central claims | T_FIG1A, T_FIG1B; reduced evidence plus code-ready unrun `main_paper_scale` implementation |
| Main Fig. 2(a) | a | numeric_reproduction | yes | chaos statistic distinguishes integrable/chaotic sectors; exact paper L sequence is omitted | T_FIG2A; reduced evidence plus executable candidate-size shards; parameter ambiguity retained |
| Main Fig. 2(b,c) | b,c | numeric_reproduction | yes | six-/one-site entropy distinguish generic and scarred dynamics | T_FIG2B, T_FIG2C; reduced exact evidence plus code-ready unrun `fig2_tdmrg_paper_scale` implementation |
| Main Fig. 3 | a,b | schematic_context | no | explanatory tangent-space and tensor-network artwork contains no plotted numerical observable | excluded |
| Main Fig. 4 | a,b,c,d | numeric_reproduction | yes | extends the periodic-orbit/revival mechanism to spin 1 and 2 | T_FIG4A, T_FIG4B, T_FIG4C, T_FIG4D; reduced evidence plus code-ready unrun `main_paper_scale` implementation |
| Supplement Fig. S1 | h/Omega=-0.2,0,0.2,0.4 | numeric_reproduction | yes | deformed TDVP vector fields test persistence of the closed orbit | T_FIGS1_HM020, T_FIGS1_H000, T_FIGS1_H020, T_FIGS1_H040 |
| Supplement Fig. S2 | a,b | numeric_reproduction | yes | integrated residual and fluctuation quantify the optimal deformation | T_FIGS2A, T_FIGS2B |

The source PDF/PNG assets are reference-only. Their paths and hashes are frozen
in `SOURCE_FREEZE.json`; they do not count as generated coverage.

Every numerical item has an executed target. All five item-level paths that the
coverage gate identifies as scale-limited now reference executable top-level
implementations in `figure_coverage.json`: `main_paper_scale` covers Fig. 1,
Fig. 2(a), and Fig. 4, while `fig2_tdmrg_paper_scale` covers Fig. 2(b,c).
The former has 30 production work units with streaming state checkpoints; the
latter has six finite-MPS refinement lanes. Neither production campaign has
been run. Fig. 2(a) remains non-paper-exact because the plotted size sequence
is absent from the paper, not because code is missing. Fig. 3 is the sole
non-numerical exclusion.
