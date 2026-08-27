# Target ledger

| Target | Figure | Object | Current evidence | Next repair |
| --- | --- | --- | --- | --- |
| T001 | Fig. 3 | Trained GNN path-planner for atom-to-target assignment | `outputs/checks/retrained_gnn_model/model_state.pt`, `training_history.json`, `metrics.json`, `outputs/figures/fig3_reduced_gnn_metrics.png`, `outputs/checks/paper_gnn_target_stage13_metric_contract_probe/paper_hungarian_metric_contract.json`, and `outputs/checks/source_topk_scale_slope_closure.json` | Closed for same-recipe scaling: do not promote source-topk to train256/val64. Reopen only with a new mechanism hypothesis and direct paper-facing Euclidean metrics. |
| T002 | Fig. 4 | P2WGS trap intensity and phase continuity across frames | `outputs/checks/reduced_p2wgs_pilot/metrics.json` and `outputs/figures/fig4_reduced_p2wgs_continuity.png` | Larger-grid GPU run and comparison against the Fig. 4 iteration trend. |
| T003 | Fig. 5 | Pipelined assembly time versus SLM refresh time | `outputs/checks/timing_model/metrics.json` and `outputs/figures/fig5_reduced_timing_model.png` | Actual path-planning and P2WGS timing on available GPU hardware. |
| T004 | Fig. 3-5 interface | Software-only assembly chain from decoded assignment to P2WGS frames to timing ledger | `outputs/checks/software_assembly_pipeline/metrics.json`, `outputs/checks/software_assembly_sweep/metrics.json`, `outputs/checks/software_assembly_sweep_hungarian/metrics.json`, and `outputs/checks/software_assembly_sweep_modified_auction/metrics.json` | Interface wiring is retained as reduced-scale evidence; no further GNN scaling is authorized by this target. |

The current target order follows the paper story: first assignment, then hologram smoothness, then total runtime.
