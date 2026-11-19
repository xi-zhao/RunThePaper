# 八个旧归因记录的复查

这是公开冻结记录的交叉核对，不是新一轮科学验收。8个案例共44条旧记录都有具体边界说明；其中3条已有更新的结构化诊断，41条仍保留旧unresolved编码。不能把这个元数据计数解释为8个完全不知原因的物理失败。

## 10.1038-s41467-025-67768-4

Calibration and benchmark definitions are incomplete; aggregate noise models reproduce trends but not all source curves.

Gate/readout calibration, per-round noise and surface injection parameters are not specified in the recorded source contract.

Still required: Resolve source calibration and independently test source alignment; do not infer a code defect or blame the source solely from curve disagreement.

Evidence: cases/10.1038-s41467-025-67768-4/docs/CONSISTENCY_REPORT.md | cases/10.1038-s41467-025-67768-4/docs/TARGET_LEDGER.md

## 1805.00931

Executed data use smaller Hilbert spaces, ensembles and transfer times; the full-scale implementations have not completed.

T001/T002 use L=8 and 128 samples rather than L=15 and 9490; T004 uses t=7 rather than t=13. Separate high-time CUDA targets have resource diagnostics.

Still required: Run and attest the declared full-scale campaign; smaller-system consistency does not establish source-scale agreement.

Evidence: cases/1805.00931/docs/CONSISTENCY_REPORT.md | cases/1805.00931/docs/TARGET_LEDGER.md

## 1807.01815

Reduced-size dynamics and unexecuted full-scale campaigns coexist with missing source size/procedure specifications.

The target ledger separates code-ready MPS/quench campaigns from accepted data; some original quench sizes and the level-statistics size sequence are not printed.

Still required: Clarify the missing size/procedure contract and complete the declared full-scale/convergence runs before quantitative acceptance.

Evidence: cases/1807.01815/docs/CONSISTENCY_REPORT.md | cases/1807.01815/docs/TARGET_LEDGER.md

## 1807.10676

Finite sampling grids support qualitative/topological checks; paper-scale theory and licensed DFT campaigns are not attested.

Ten legacy unresolved theory targets retain explicit finite-resolution gaps. The separate DFT scope requires a licensed VASP/PAW campaign.

Still required: Execute the higher-resolution convergence campaign; obtain the licensed DFT environment for the separate external targets. Do not equate a finite grid with a numerical defect.

Evidence: cases/1807.10676/docs/CONSISTENCY_REPORT.md | cases/1807.10676/docs/TARGET_LEDGER.md

## 2407.01296

Full-size and dense-grid computations remain unexecuted; selected eigenstate energies and some geometric conventions are not fixed by the source.

T004/T005/T006/T008 declare unrun scale/sampling profiles; T007 additionally lacks selected eigenstate energies.

Still required: Complete the declared profiles and resolve state-selection/convention inputs; reduced runs alone cannot establish the missing comparisons.

Evidence: cases/2407.01296/docs/CONSISTENCY_REPORT.md | cases/2407.01296/docs/TARGET_LEDGER.md

## 2506.06669

Legacy targets mix theory/experimental scope, missing hardware calibration and unspecified random seeds/grids. A separate pulse-sensitive discrepancy has a recorded follow-up diagnosis.

T001/T003/T005 are auxiliary source-schematic/experimental counterparts in the item ledger. D001 is attributed by the scorecard to unspecified channel-resolved pulse functions/timing, but its cited detailed test JSON is absent from the public snapshot.

Still required: Reconcile eligible scope and calibration; provide the D001 pulse-comparison evidence and independently verify it before accepting the attribution.

Evidence: cases/2506.06669/docs/CONSISTENCY_REPORT.md | cases/2506.06669/docs/TARGET_LEDGER.md

## 2510.12880

The legacy T002 label concerns unavailable solver settings despite recorded marker agreement; five separate source claims lack implementations.

The ledger records T002 25/25 marker comparisons and explicit missing eigensolver/threshold/tolerance metadata. V003-V007 are unimplemented open-boundary/parity/perturbative claims.

Still required: Validate solver/degeneracy robustness and implement V003-V007 with claim-specific tests; do not call the known missing implementation a mysterious physics failure.

Evidence: cases/2510.12880/docs/CONSISTENCY_REPORT.md | cases/2510.12880/docs/TARGET_LEDGER.md

## 2607.02157

The detailed state is out of sync with target-specific compute diagnostics; a provenance-bound full-scale campaign has not completed.

All three scorecard targets now diagnose compute_capacity_shortfall. The resource benchmark enumerates 12665500 sequence evaluations, 1125000000 filter updates and 400101 eigendecompositions; historical arrays are not accepted as final-run evidence.

Still required: Complete and attest the frozen campaign, audit readout/configuration hashes and reconcile the derived state. Existing narrative claims are not a substitute for a bound run.

Evidence: cases/2607.02157/docs/CONSISTENCY_REPORT.md | cases/2607.02157/docs/TARGET_LEDGER.md
