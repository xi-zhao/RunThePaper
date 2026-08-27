# Lessons Learned

## Case Summary

- Paper: *Edge states and topological invariants of non-Hermitian systems*
- PaperID: `1803.01876`
- Final status: `digitized_curve_match` for all scored targets; the case-level
  similarity tier is `complete_reproduction` under the digitized-curve scoring
  model. This is still not author-data/100% reproduction because reference data
  is digitized EPS/PNG rather than author plotting data, and pixel-level layout
  alignment is not yet treated as the acceptance gate.
- Main reproduced targets: Fig. 2, Fig. 3, Fig. 4, Fig. 5, supplemental numerical figures.
- Main blockers: the missing digitized-reference blocker, Fig. 5 source-path
  spectrum blocker, Fig. 2/Fig. 3 open-chain formula gate blocker, and
  supplemental open-boundary bulk spectrum formula gate blocker are closed. The
  remaining blockers are author plotting data and pixel-perfect layout.

## What Worked

- 公式 gate 非常有效。先做 source trace 和符号核验，再开放数值脚本，避免了从 PDF 直接跳到代码的风险。
- `TARGET_LEDGER.md` 的 target 粒度合适。每个图都能独立记录公式、参数、输出数据和检查结果。
- feature-level checks 比图片相似度更可靠。相变点、winding plateau、`C_beta` 半径、skin localization 这些特征能直接说明物理结果是否对齐。
- TeX source 很有价值。公式、caption、EPS 原图都能被系统化提取，后续 case 应该优先获取 TeX/source。
- all-target digitizer 比零散补图更稳。把 Fig. 2、Fig. 3、Fig. 4、Fig. 5
  和 supplemental panels 统一输出到 `all_digitized_curves.json`，scorecard
  才能明确区分“曲线参考已补齐”和“公式 gate 仍有限制”。

## What Was Difficult

- 非厄米 Hamiltonian 的数值对角化容易不稳定。直接 dense diagonalization 在强 non-normal 区域会破坏 `E -> -E` 配对；即使改用 `CD` block，直接 `eig(CD)` 仍会在负侧 `t1 ~= -gamma/2` 附近产生伪虚部。
- 原文图源格式不统一。有些 panel 可以直接从 Matplotlib EPS 矢量命令提取，
  有些需要从渲染 PNG 中按颜色或 marker 做 digitization。
- p95 距离容易被标签、采样密度和视觉布局放大。点云 panel 的 acceptance
  使用 symmetric median nearest-neighbor distance，p95 保留为 residual
  visual gap，不把它等同于物理复现失败。
- 图中视觉差异不一定代表物理错误。尤其是复平面曲线、采样密度、线条样式和坐标范围，都需要和数值特征分开处理。

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| non_normal_eigensolver_instability | Fig. 2 open-chain spectrum | Check chiral `E -> -E` pairing residual and prefer structure-aware eigensolvers. |
| block_eigensolver_spurious_imaginary_tail | Fig. 2 near `t1=-1` | Check that `Im(E)` vanishes outside the physical `|t1| < gamma/2` window and solve tridiagonal `CD` through its symmetric similar form. |
| open_chain_matrix_entry_drift | Fig. 2 and Fig. 3 shared Hamiltonian | Check `H[A_n,B_n]`, `H[B_n,A_n]`, `H[A_n,B_{n-1}]`, and `H[B_n,A_{n+1}]` entries against the real-space equations before visual tuning. |
| cbeta_branch_averaging | Fig. 5 `C_beta` | Preserve middle-root branch identity and connect within each branch in `angle_beta` order; never average branches into one curve. |
| source_only_formula_cap_after_digitization | Fig. 2, Fig. 3, supplemental figures | Separate reference-curve completeness from formula-card verification tier; close it with source plus code-trace checks before visual tuning. |
| open_boundary_spectrum_formula_drift | Supplemental complex spectra | Check `non_bloch_ab(beta=r exp(ik))` against the paper's signed Eq. `spectra` across all `t1 +/- gamma/2` sign sectors. |
| eps_vector_digitization | Vector-friendly panels | Prefer parsing vector EPS coordinates before falling back to raster image digitization. |
| raster_digitization_needed | Color/marker-only panels | Use rendered source figures when EPS commands do not expose usable curve paths. |
| p95_visual_residual_not_reproduction_failure | Dense point-cloud panels | Track p95 residuals, but gate acceptance on robust symmetric median distance when sampling density differs. |
| formula_used_before_gate | Potential risk in all theory papers | Block numerical scripts until formula cards pass source and symbolic checks where applicable. |
| source_path_trace_as_generated_data | Fig. 5 spectrum | Require `generated_data_provenance`; source EPS paths may be reference comparators, but generated spectrum data must come from independent open-chain numerics. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| formula gate runner | Most theory papers need formula-to-code traceability | `PRAgent-workflow/formula_gate` |
| source figure renderer | Case intro needs stable original-vs-generated comparison | `PRAgent-workflow/render_original_figures` |
| all-target digitized curve checker | Scorecards need one evidence file covering every scored panel | `PRAgent-workflow/reference_curves` |
| feature checker templates | Phase transitions, plateaus, spectra, localization recur across physics papers | `PRAgent-workflow/checks` |
| non-normal eigensolver warning | Non-Hermitian models often need solver sanity checks | `PRAgent-workflow/numerics` |
| generated-data provenance gate | Physics reproduction needs to separate independent generated data from source-derived references | `PRAgent-workflow/rr_harness/similarity_score.py` |

## Harness Backlog Items

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| high | Add formula gate as a standard harness step | `outputs/checks/formula_verification.json`, `core_derivations.json` | copied_to_backlog |
| high | Add feature-level checks before image comparison | all figure checks use physical features | copied_to_backlog |
| medium | Add original figure/source renderer | `internal-source-renders/`, `internal-paper-reference/` | copied_to_backlog |
| medium | Add non-normal solver diagnostics | Fig. 2 direct eig instability | new |
| high | Add generated-data provenance gate | Fig. 5 source-path trace risk | copied_to_backlog |
| high | Add independent branch-regeneration requirement for source-traced spectrum lines | Fig. 5 spectrum | implemented_case_rule |

## Prompt Or Workflow Changes

- Agent should always ask: "Which formulas feed this target?" before writing code.
- Agent should classify figures before implementation.
- Agent should write the expected physical features before plotting.
- Agent should record numerical instability as a first-class result, not hide it behind a prettier plot.
