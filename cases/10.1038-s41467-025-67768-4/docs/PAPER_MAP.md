# Paper Map

## Identity

- Paper ID: `10.1038-s41467-025-67768-4`
- Title: *Demonstrating quantum error mitigation on logical qubits*
- Authors: Aosai Zhang, Haipeng Xie, Yu Gao, Jia-Nan Yang, Zehang Bao, Zitian Zhu, Jiachen Chen, Ning Wang, Chuanyu Zhang, Jiarun Zhong, Shibo Xu, Ke Wang, Yaozu Wu, Feitong Jin, Xuhao Zhu, Yiren Zou, Ziqi Tan, Zhengyi Cui, Fanhao Shen, Tingting Li, Yihang Han, Yiyang He, Gongyu Liu, Jiayuan Shen, Han Wang, Yanzhe Wang, Hang Dong, Jinfeng Deng, Hekang Li, Zhen Wang, Chao Song, Qiujiang Guo, Pengfei Zhang, Ying Li, and H. Wang
- Version of record: *Nature Communications* **17**, 1021 (2026), DOI `10.1038/s41467-025-67768-4`
- Preprint identity: arXiv `2501.09079`
- Local paper: `raw/main.pdf`, SHA-256 `f0a1f4b54af6d4b43b971f0c8f420be7b6f537dc8b02bb2f259e6c923259b4d3`
- Local supplement: `raw/supplementary-information.pdf`, SHA-256 `92515e3eccb2e157f9feff09ef802d0a6b58d37f6f1678c96b46c5dcfb2747d9`

## Scientific question

The paper asks whether zero-noise extrapolation (ZNE) can suppress residual
logical errors after quantum error correction. Its central claim is that an
effective distance-`d` code removes all error terms below order
`m = ceil(d/2)`, so the extrapolation basis should start at `r^m` rather than
at `r`.

The reproduction independently evaluates that claim using:

1. exact enumeration of the feedback/post-selection example;
2. closed-form repetition-code failure probabilities;
3. exact Pauli enumeration of a distance-3 rotated surface code under the
   paper's phenomenological depolarizing model;
4. the published Bravyi--Vargo logical-error fit used by Supplementary Fig. 9;
5. independent ZNE weights, bias, and sampling-overhead calculations.

Experimental samples, chip calibration distributions, and author-produced
arrays are comparison context rather than generated results.

## Paper structure

| Section | Role | Reproduction use |
| --- | --- | --- |
| Results, general formalism | Establishes the polynomial in amplified noise | Equation cards ZNE001--ZNE003 |
| Feedback parity-check experiment | Small exactly enumerable example | T001 |
| Repetition-code experiment | Demonstrates distance-dependent suppression | T002--T003 |
| Surface-code experiment | Demonstrates simultaneous X/Z protection | T004 |
| Methods, ZNE protocol | Defines extrapolation weights, bias, and overhead | T001--T006 |
| Supplementary Notes 1--3 | Derivation and circuit-sampling method | Formula and method gates |
| Supplementary Note 4 | Additional experimental and simulation panels | T002, T004, T007 plus explicit exclusions |
| Supplementary Note 5 | Complete ZNE and large-scale logical circuits | T005--T006; Fig. S10 deferred |

## Equation and method inventory

| ID | Source | Role | Initial status |
| --- | --- | --- | --- |
| ZNE001 | Main Results; SI Eqs. (11)--(18) | Expansion of an FTQC observable as a polynomial in noise scale | source-verified |
| ZNE002 | Main Methods Eqs. (3)--(4) | Distance-aware extrapolation weights | source-verified |
| ZNE003 | Main Eqs. (1)--(2), Methods | Bias and sampling overhead | source-verified |
| FB001 | Main Fig. 2 text and SI Note 3 | Exact feedback/post-selection response to Pauli injection | reconstructed from circuit |
| REP001 | Main Fig. 3 and SI Table 3 | Repetition-code logical failure under independent bit flips | independently derived |
| SURF001 | Main Fig. 4 and SI Note 4 | Rotated `[[9,1,3]]` CSS syndrome decoding | independently reconstructed |
| MEM001 | SI Eqs. (22)--(35), Fig. S9; Bravyi--Vargo Eqs. (2)--(3) | Large-scale logical-memory model | source-verified |

## Complete figure and table inventory

The atomic inventory contains **47 displayed items**. Of these, **16** are
eligible scientific numerical items: **13 covered** and **3 uncovered**. The
remaining **31** are explicitly excluded context rather than silently omitted.
The complete machine-readable item list is `figure_coverage.json`.

| Item | Content | Scientific decision |
| --- | --- | --- |
| Main Fig. 1 | Concept sketch of physical/logical ZNE | schematic; excluded |
| Main Fig. 2(a) | Feedback circuit drawing | schematic; excluded |
| Main Fig. 2(b) | Experimental response surfaces | hardware data; user-descoped |
| Main Fig. 2(c) | Experimental points plus numerical simulation curves | reproduce simulation component as T001 |
| Main Fig. 3(a,b) | Layout and circuit drawings | schematic; excluded |
| Main Fig. 3(c) | Experimental points plus repetition-code simulations | reproduce simulation component as T002 |
| Main Fig. 3(d) | ZNE scatter from experimental samples | hardware data; user-descoped |
| Main Fig. 3(e) | Multi-round experimental points plus simulations | reproduce simulation component as T003 |
| Main Fig. 3(f) | Experimental ZNE scatter | hardware data; user-descoped |
| Main Fig. 4(a) | Surface-code layout/circuit | schematic; excluded |
| Main Fig. 4(b,c) | Experimental values plus depolarizing-model simulations | reproduce simulation components as T004 |
| Main Fig. 4(d) | ZNE scatter from experimental samples | hardware data; user-descoped |
| Main Fig. 5 | Processor calibration distributions | hardware characterization; user-descoped |
| Supp. Fig. 1 | Feedback/post-selection circuit | schematic; excluded |
| Supp. Fig. 2 | `[[72,12,6]]` qLDPC Monte Carlo histogram | uncovered item `supp_fig2_qldpc_logical_error_distribution` (T008): decoder/circuit benchmark metadata absent |
| Supp. Table 1 | Measured processor statistics | hardware characterization; user-descoped |
| Supp. Table 2 | Chosen experimental circuit counts | experimental acquisition plan; user-descoped |
| Supp. Fig. 3 | Experimental standard errors | hardware data; user-descoped |
| Supp. Fig. 4 | Experimental values plus uncorrected simulations | reproduce simulation component with T002 |
| Supp. Table 3 | Fixed-total-error schedule | independently reconstruct as T007 |
| Supp. Fig. 5 | Experimental ZNE bias/overhead | hardware data; user-descoped |
| Supp. Fig. 6 | Logical-state preparation circuit | schematic; excluded |
| Supp. Fig. 7(a,c,e) | Experimental values plus surface-code simulations | reproduce simulation components with T004 |
| Supp. Fig. 7(b,d,f) | Experimental ZNE scatter | hardware data; user-descoped |
| Supp. Fig. 8 | Complete versus partial ZNE simulations | reproduce as T005 |
| Supp. Fig. 9 | Large-scale surface-code memory model | reproduce as T006 |
| Supp. Fig. 10(a) | Lattice-surgery circuit drawing | schematic; excluded |
| Supp. Fig. 10(b) | Circuit-level logical-CNOT expectation | uncovered item `supp_fig10b_logical_cnot_expectation` (T009): exact schedule/decoder/syndrome-round/sampling metadata absent |
| Supp. Fig. 10(c) | Lattice-surgery ZNE bias versus overhead | uncovered item `supp_fig10c_lattice_surgery_bias_overhead` (T009): same benchmark contract absent |

## Assumptions and identified gaps

- The paper discloses aggregate processor error statistics, but not the
  per-qubit/per-gate calibration map used by its dashed simulations. T002 and
  T003 therefore report both an injection-only analytic result and a declared
  median-calibration model; neither is called author-data-level exact.
- The unit injected error probability for the surface-code plots is not stated
  explicitly. T004 uses the paper's repetition-code value `p=0.036` as a
  disclosed cross-experiment assumption and retains `p_prep=0.075` exactly.
- The distance-3 surface-code stabilizers are reconstructed from the published
  layout and logical operators. Every commutator and logical-distance property
  is checked before the model is used.
- Supplementary Fig. 2 names the code, physical error rate, and Monte Carlo
  goal but omits a full circuit/noise/decoder specification.
- Supplementary Fig. 10 omits the exact lattice-surgery schedule, decoder,
  number of syndrome rounds, and shot counts. More CPU/GPU cannot recover
  those missing scientific inputs.
- These publication boundaries account for all three items preventing 100%
  coverage. They are neither unrun code nor evidence of a detected code bug.
