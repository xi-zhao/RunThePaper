<h1 align="center">RunThePaper</h1>

<p align="center"><strong>让论文不只是能读、能引用，也能运行、能验证、能接力。</strong></p>

<p align="center"><strong>From papers to runnable, checkable, and extendable science.</strong></p>

<p align="center">
  <a href="#reproduction-catalog--论文复现目录">Explore cases</a> ·
  <a href="https://github.com/xi-zhao/runthepaper/issues/new">Request a paper</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

一篇论文，是一次研究的高度压缩。公式留在正文里，参数散落在图注和补充材料里，
真正把结果重新跑起来，往往还需要许多没有写下来的判断。

RunThePaper 想把这些被压缩的过程重新展开。这里的每个案例都对应一篇可验证的
论文，包含中英文讲义、可运行代码、生成结果、机器可读的检查，以及仍未解决的边界。
你可以从一张图开始，也可以把它当作下一项研究的起点。

RunThePaper is a community-built library of executable paper reproductions.
It is the public, reusable layer of [PRAgent](#pragent-behind-the-library),
our system for turning static papers into auditable research cases.

The 100 cases here are not 100 completion trophies. Partial reproductions,
missing public inputs, compute limits, invalid runs, and pending independent
review remain visible. A useful scientific library should preserve uncertainty,
not polish it away.

| 如果你想…… / If you want to… | 从这里进入 / Start here |
| --- | --- |
| 先读懂一篇论文 / understand a paper | 打开中文或 English Note |
| 亲手把结果跑出来 / rerun the result | 打开 Code、Figures 和 Checks |
| 在现有结果上继续做 / build on the work | 阅读边界，提交修正、评审或扩展 |

Standalone benchmarks, synthetic exercises, source-contract audits, and
internal evaluations are not published as paper cases.

## Reproduction Catalog / 论文复现目录

<!-- case-catalog:start -->
**100 篇公开案例，按研究主题进入。** 这里的分类是一条主要阅读路径，
很多论文同时横跨多个方向。

**100 public cases, organized as research collections.** Each paper is
placed on one primary path even when its ideas cross several fields.

选择一个主题展开目录，也可以进入 [完整索引](CASES.md) 查看论文身份、分数和复现边界。

Choose a collection to open its catalog, or use the [detailed index](CASES.md)
for paper identities, scores, and reproduction boundaries.

**快速入口 / Jump to a collection**

- [量子计算、算法与纠错 / Quantum computing, algorithms & error correction（25）](#collection-quantum-computing)
- [量子信息、基础问题与精密测量 / Quantum information, foundations & sensing（18）](#collection-quantum-information)
- [多体物理、相变与非平衡动力学 / Many-body physics, phases & nonequilibrium dynamics（27）](#collection-many-body)
- [拓扑、非厄米、材料与输运 / Topology, non-Hermitian physics, materials & transport（21）](#collection-topology-materials)
- [原子、光学、光子学与场论 / Atomic, optical, photonic & field physics（9）](#collection-amo-field)

<a id="collection-quantum-computing"></a>

<details>
<summary><strong>量子计算、算法与纠错 / Quantum computing, algorithms & error correction（25）</strong></summary>

从量子线路编译、量子模拟到容错与误差缓解，关注怎样把量子计算的关键主张真正跑起来。

Circuit compilation, quantum simulation, fault tolerance, and error mitigation as runnable research cases.

| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |
| --- | --- | --- | --- |
| [Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices](cases/10.1145-3297858.3304023/README.md) | SABRE qubit mapping and routing | Partial scientific reproduction | [中文](cases/10.1145-3297858.3304023/note/reproduction-note.zh-CN.md) · [EN](cases/10.1145-3297858.3304023/note/reproduction-note.en.md) · [Code](cases/10.1145-3297858.3304023/code/README.md) |
| [Simulating the Sycamore quantum supremacy circuits](cases/2103.03074/README.md) | Sycamore random-circuit simulation | Partial scientific reproduction | [中文](cases/2103.03074/note/reproduction-note.zh-CN.md) · [EN](cases/2103.03074/note/reproduction-note.en.md) · [Code](cases/2103.03074/code/README.md) |
| [Efficient simulation of logical magic state preparation protocols](cases/2512.23799/README.md) | Logical magic-state preparation simulation | Partial scientific reproduction | [中文](cases/2512.23799/note/reproduction-note.zh-CN.md) · [EN](cases/2512.23799/note/reproduction-note.en.md) · [Code](cases/2512.23799/code/README.md) |
| [Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics](cases/2605.25398/README.md) | Boson sampling and quantum-chaos probes | Partial scientific reproduction | [中文](cases/2605.25398/note/reproduction-note.zh-CN.md) · [EN](cases/2605.25398/note/reproduction-note.en.md) · [Code](cases/2605.25398/code/README.md) |
| [Buffer-atom-mediated quantum logic gates with off-resonant modulated driving](cases/10.1007-s11433-024-2478-8/README.md) | Buffer-atom-mediated Rydberg CZ, dual-pulse Doppler upgrade, and amplitude-ratio robustness via off-resonant modulated driving | Partial scientific reproduction | [中文](cases/10.1007-s11433-024-2478-8/note/reproduction-note.zh-CN.md) · [EN](cases/10.1007-s11433-024-2478-8/note/reproduction-note.en.md) · [Code](cases/10.1007-s11433-024-2478-8/code/README.md) |
| [Strongly correlated quantum walks with a 12-qubit superconducting processor](cases/10.1126-science.aaw1611/README.md) | Strongly interacting one- and two-photon quantum walks on a calibrated superconducting-qubit chain | Partial scientific reproduction | [中文](cases/10.1126-science.aaw1611/note/reproduction-note.zh-CN.md) · [EN](cases/10.1126-science.aaw1611/note/reproduction-note.en.md) · [Code](cases/10.1126-science.aaw1611/code/README.md) |
| [Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates](cases/10.1103-PRXQuantum.6.010331/README.md) | Fidelity-response theory and protocol-level noise susceptibility of high-fidelity Rydberg CZ gates | Partial scientific reproduction | [中文](cases/10.1103-PRXQuantum.6.010331/note/reproduction-note.zh-CN.md) · [EN](cases/10.1103-PRXQuantum.6.010331/note/reproduction-note.en.md) · [Code](cases/10.1103-PRXQuantum.6.010331/code/README.md) |
| [Thermodynamics of Quantum Reservoir Computing](cases/2607.02157/README.md) | Non-equilibrium thermodynamic limits of driven open quantum reservoirs; generalized Landauer bound and information-dissipation identity | Partial scientific reproduction | [中文](cases/2607.02157/note/reproduction-note.zh-CN.md) · [EN](cases/2607.02157/note/reproduction-note.en.md) · [Code](cases/2607.02157/code/README.md) |
| [Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms](cases/2502.20558/README.md) | Delayed-erasure decoding, qubit lifecycle reduction, and loss-aware fault-tolerant quantum algorithms | Partial scientific reproduction | [中文](cases/2502.20558/note/reproduction-note.zh-CN.md) · [EN](cases/2502.20558/note/reproduction-note.en.md) · [Code](cases/2502.20558/code/README.md) |
| [Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate](cases/2607.15597/README.md) | Rydberg atom-ion geometric gates, multi-ion mode closure, deterministic interconnect timing, and hybrid qLDPC memory | Scientific reproduction — invalid | [中文](cases/2607.15597/note/reproduction-note.zh-CN.md) · [EN](cases/2607.15597/note/reproduction-note.en.md) · [Code](cases/2607.15597/code/README.md) |
| [Programmable Open Quantum Systems](cases/2512.08279/README.md) | Programmable Lindblad dynamics, signed quantum-channel sampling, and error-dependent retrieval cost | Partial scientific reproduction | [中文](cases/2512.08279/note/reproduction-note.zh-CN.md) · [EN](cases/2512.08279/note/reproduction-note.en.md) · [Code](cases/2512.08279/code/README.md) |
| [Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition](cases/1903.05124/README.md) | Formula-derived Clifford/stabilizer reproduction of scrambling-enabled quantum error correction and measurement-induced criticality | Scientific reproduction — invalid | [中文](cases/1903.05124/note/reproduction-note.zh-CN.md) · [EN](cases/1903.05124/note/reproduction-note.en.md) · [Code](cases/1903.05124/code/README.md) |
| [Demonstrating quantum error mitigation on logical qubits](cases/10.1038-s41467-025-67768-4/README.md) | Feedback/post-selection expectation under amplified Pauli injection. | Scientific reproduction — invalid | [中文](cases/10.1038-s41467-025-67768-4/note/reproduction-note.zh-CN.md) · [EN](cases/10.1038-s41467-025-67768-4/note/reproduction-note.en.md) · [Code](cases/10.1038-s41467-025-67768-4/code/README.md) |
| [Amplitude Estimation without Phase Estimation](cases/1904.10246/README.md) | quantum algorithms; amplitude estimation; maximum likelihood | Scientific reproduction — invalid | [中文](cases/1904.10246/note/reproduction-note.zh-CN.md) · [EN](cases/1904.10246/note/reproduction-note.en.md) · [Code](cases/1904.10246/code/README.md) |
| [Graph coloring via quantum optimization on a Rydberg-qudit atom array](cases/2504.08598/README.md) | k=3 target-coloring probability versus annealing time and final E/F basis distributions | Scientific reproduction — invalid | [中文](cases/2504.08598/note/reproduction-note.zh-CN.md) · [EN](cases/2504.08598/note/reproduction-note.en.md) · [Code](cases/2504.08598/code/README.md) |
| [Remote Entanglement Generation Via Enhanced Quantum State Transfer](cases/2506.06669/README.md) | quantum state transfer; remote entanglement; superconducting quantum processors | Scientific reproduction — invalid | [中文](cases/2506.06669/note/reproduction-note.zh-CN.md) · [EN](cases/2506.06669/note/reproduction-note.en.md) · [Code](cases/2506.06669/code/README.md) |
| [Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors](cases/2607.08212/README.md) | neutral atoms; quantum compilation; hardware-software codesign | Partial scientific reproduction | [中文](cases/2607.08212/note/reproduction-note.zh-CN.md) · [EN](cases/2607.08212/note/reproduction-note.en.md) · [Code](cases/2607.08212/code/README.md) |
| [Plaquette: A hardware-aware design platform for fault-tolerant quantum computers](cases/2607.08767/README.md) | Fault-tolerant quantum computing; Pauli twirling; hardware-aware quantum error-correction simulation | Partial scientific reproduction | [中文](cases/2607.08767/note/reproduction-note.zh-CN.md) · [EN](cases/2607.08767/note/reproduction-note.en.md) · [Code](cases/2607.08767/code/README.md) |
| [Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search](cases/2607.27060/README.md) | open quantum systems; Trotter-Suzuki product formulas; quantum resource estimation | Scientific reproduction — invalid | [中文](cases/2607.27060/note/reproduction-note.zh-CN.md) · [EN](cases/2607.27060/note/reproduction-note.en.md) · [Code](cases/2607.27060/code/README.md) |
| [High-rate qLDPC processors](cases/2607.28795/README.md) | Mitten-code algebraic parameters and canonical logical weights. | Scientific reproduction — invalid | [中文](cases/2607.28795/note/reproduction-note.zh-CN.md) · [EN](cases/2607.28795/note/reproduction-note.en.md) · [Code](cases/2607.28795/code/README.md) |
| [Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators](cases/2608.03987/README.md) | Realification cost laws and contraction-order transferability for quantum-circuit tensor networks | Partial scientific reproduction | [中文](cases/2608.03987/note/reproduction-note.zh-CN.md) · [EN](cases/2608.03987/note/reproduction-note.en.md) · [Code](cases/2608.03987/code/README.md) |
| [Quantum machine learning in feature Hilbert spaces](cases/1803.07128/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1803.07128/note/reproduction-note.zh-CN.md) · [EN](cases/1803.07128/note/reproduction-note.en.md) · [Code](cases/1803.07128/code/README.md) |
| [A random compiler for fast Hamiltonian simulation](cases/1811.08017/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [中文](cases/1811.08017/note/reproduction-note.zh-CN.md) · [EN](cases/1811.08017/note/reproduction-note.en.md) · [Code](cases/1811.08017/code/README.md) |
| [Obstacles to State Preparation and Variational Optimization from Symmetry Protection](cases/1910.08980/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1910.08980/note/reproduction-note.zh-CN.md) · [EN](cases/1910.08980/note/reproduction-note.en.md) · [Code](cases/1910.08980/code/README.md) |
| [Universal Quantum Computation with Ideal Clifford Gates and Noisy Ancillas](cases/quant-ph-0403025/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/quant-ph-0403025/note/reproduction-note.zh-CN.md) · [EN](cases/quant-ph-0403025/note/reproduction-note.en.md) · [Code](cases/quant-ph-0403025/code/README.md) |

</details>

<a id="collection-quantum-information"></a>

<details>
<summary><strong>量子信息、基础问题与精密测量 / Quantum information, foundations & sensing（18）</strong></summary>

纠缠、量子资源、开放系统、量子基础与精密测量，连接概念推导和可检查的数值结果。

Entanglement, quantum resources, open systems, foundations, and sensing with inspectable derivations and results.

| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |
| --- | --- | --- | --- |
| [Particle exchange statistics beyond fermions and bosons](cases/10.1038-s41586-024-08262-7/README.md) | Paraparticle exclusion statistics, thermodynamics, and exactly solvable spin models | Partial scientific reproduction | [中文](cases/10.1038-s41586-024-08262-7/note/reproduction-note.zh-CN.md) · [EN](cases/10.1038-s41586-024-08262-7/note/reproduction-note.en.md) · [Code](cases/10.1038-s41586-024-08262-7/code/README.md) |
| [Sufficient Wigner Negativity Implies Genuine Multipartite Entanglement](cases/2510.26761/README.md) | Continuous-variable genuine multipartite entanglement witnesses from finite Wigner and characteristic-function measurements | Partial scientific reproduction | [中文](cases/2510.26761/note/reproduction-note.zh-CN.md) · [EN](cases/2510.26761/note/reproduction-note.en.md) · [Code](cases/2510.26761/code/README.md) |
| [Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking](cases/2607.00718/README.md) | Squeezed-reservoir nonreciprocity, Gaussian quantum batteries, ergotropy, and optical isolation | Partial scientific reproduction | [中文](cases/2607.00718/note/reproduction-note.zh-CN.md) · [EN](cases/2607.00718/note/reproduction-note.en.md) · [Code](cases/2607.00718/code/README.md) |
| [Information and Majorization Theory for Fermionic Phase-Space Distributions](cases/2401.08523/README.md) | quantum information; fermionic phase space; majorization; uncertainty relations | Partial scientific reproduction | [中文](cases/2401.08523/note/reproduction-note.zh-CN.md) · [EN](cases/2401.08523/note/reproduction-note.en.md) · [Code](cases/2401.08523/code/README.md) |
| [Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation](cases/2602.12212/README.md) | Spin-1 minimum-variance leaf geometry and leaf-canonical curves. | Partial scientific reproduction | [中文](cases/2602.12212/note/reproduction-note.zh-CN.md) · [EN](cases/2602.12212/note/reproduction-note.en.md) · [Code](cases/2602.12212/code/README.md) |
| [Fixed-detector tilt--defocus sensing by upstream source coding in a time-reversed Young interferometer](cases/2605.02873/README.md) | physical optics; Fisher information; wavefront sensing | Scientific reproduction — invalid | [中文](cases/2605.02873/note/reproduction-note.zh-CN.md) · [EN](cases/2605.02873/note/reproduction-note.en.md) · [Code](cases/2605.02873/code/README.md) |
| [Photonic Violation of Wigner's Inequality](cases/2606.30255/README.md) | quantum foundations; quantum optics; polarization entanglement | Scientific reproduction — invalid | [中文](cases/2606.30255/note/reproduction-note.zh-CN.md) · [EN](cases/2606.30255/note/reproduction-note.en.md) · [Code](cases/2606.30255/code/README.md) |
| [Non-Hermitian-enhanced quantum sensing in an optical interferometer](cases/2607.23978/README.md) | Optimal Hermitian and non-Hermitian interferometric fringe baselines. | Partial scientific reproduction | [中文](cases/2607.23978/note/reproduction-note.zh-CN.md) · [EN](cases/2607.23978/note/reproduction-note.en.md) · [Code](cases/2607.23978/code/README.md) |
| [Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit](cases/2401.05830/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2401.05830/note/reproduction-note.zh-CN.md) · [EN](cases/2401.05830/note/reproduction-note.en.md) · [Code](cases/2401.05830/code/README.md) |
| [Optimal Generators for Quantum Sensing](cases/2305.15556/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [中文](cases/2305.15556/note/reproduction-note.zh-CN.md) · [EN](cases/2305.15556/note/reproduction-note.en.md) · [Code](cases/2305.15556/code/README.md) |
| [New Constraints on Axion-Mediated Spin Interactions Using Magnetic Amplification](cases/PhysRevLett.133.191801/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/PhysRevLett.133.191801/note/reproduction-note.zh-CN.md) · [EN](cases/PhysRevLett.133.191801/note/reproduction-note.en.md) · [Code](cases/PhysRevLett.133.191801/code/README.md) |
| [Precision-Spectroscopic Determination of the Binding Energy of a Two-Body Quantum System: The Hydrogen Atom and the Proton-Size Puzzle](cases/PhysRevLett.132.113001/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/PhysRevLett.132.113001/note/reproduction-note.zh-CN.md) · [EN](cases/PhysRevLett.132.113001/note/reproduction-note.en.md) · [Code](cases/PhysRevLett.132.113001/code/README.md) |
| [Squeezed Spin States](cases/PhysRevA.47.5138/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [中文](cases/PhysRevA.47.5138/note/reproduction-note.zh-CN.md) · [EN](cases/PhysRevA.47.5138/note/reproduction-note.en.md) · [Code](cases/PhysRevA.47.5138/code/README.md) |
| [Entanglement in Quantum Critical Phenomena](cases/quant-ph-0211074/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/quant-ph-0211074/note/reproduction-note.zh-CN.md) · [EN](cases/quant-ph-0211074/note/reproduction-note.en.md) · [Code](cases/quant-ph-0211074/code/README.md) |
| [Entanglement of Formation of an Arbitrary State of Two Qubits](cases/quant-ph-9709029/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/quant-ph-9709029/note/reproduction-note.zh-CN.md) · [EN](cases/quant-ph-9709029/note/reproduction-note.en.md) · [Code](cases/quant-ph-9709029/code/README.md) |
| [Necessary and Sufficient Condition for Nonzero Quantum Discord](cases/1004.0190/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/1004.0190/note/reproduction-note.zh-CN.md) · [EN](cases/1004.0190/note/reproduction-note.en.md) · [Code](cases/1004.0190/code/README.md) |
| [Quantum Speed Limit for Non-Markovian Dynamics](cases/1302.5069/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/1302.5069/note/reproduction-note.zh-CN.md) · [EN](cases/1302.5069/note/reproduction-note.en.md) · [Code](cases/1302.5069/code/README.md) |
| [Quantum Discord and the Power of One Qubit](cases/0709.0548/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/0709.0548/note/reproduction-note.zh-CN.md) · [EN](cases/0709.0548/note/reproduction-note.en.md) · [Code](cases/0709.0548/code/README.md) |

</details>

<a id="collection-many-body"></a>

<details>
<summary><strong>多体物理、相变与非平衡动力学 / Many-body physics, phases & nonequilibrium dynamics（27）</strong></summary>

时间晶体、多体疤痕、量子相变与热化问题，把跨尺度的理论结果拆成可运行的计算对象。

Time crystals, many-body scars, quantum phase transitions, and thermalization turned into executable calculations.

| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |
| --- | --- | --- | --- |
| [Discrete time crystals: rigidity, criticality, and realizations](cases/1608.02589/README.md) | Floquet many-body dynamics and discrete time crystals | Partial scientific reproduction | [中文](cases/1608.02589/note/reproduction-note.zh-CN.md) · [EN](cases/1608.02589/note/reproduction-note.en.md) · [Code](cases/1608.02589/code/README.md) |
| [Quantum many-body scars](cases/1711.03528/README.md) | PXP dynamics and quantum many-body scars | Partial scientific reproduction | [中文](cases/1711.03528/note/reproduction-note.zh-CN.md) · [EN](cases/1711.03528/note/reproduction-note.en.md) · [Code](cases/1711.03528/code/README.md) |
| [Localization Driven Superradiant Instability](cases/10.1103-PhysRevLett.124.113601/README.md) | Aubry–André localization, cavity susceptibility, and superradiant instability | Partial scientific reproduction | [中文](cases/10.1103-PhysRevLett.124.113601/note/reproduction-note.zh-CN.md) · [EN](cases/10.1103-PhysRevLett.124.113601/note/reproduction-note.en.md) · [Code](cases/10.1103-PhysRevLett.124.113601/code/README.md) |
| [Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain](cases/2510.12880/README.md) | Exact algebraic and finite-size validation of the frustration-free 2^N+1 ground-state manifold. | Partial scientific reproduction | [中文](cases/2510.12880/note/reproduction-note.zh-CN.md) · [EN](cases/2510.12880/note/reproduction-note.en.md) · [Code](cases/2510.12880/code/README.md) |
| [Dissipative Phase Transition in the Two-Photon Dicke Model](cases/2412.14271/README.md) | Two-photon Dicke model, dissipative phase transitions, quantum trajectories, and nonlinear stability | Partial scientific reproduction | [中文](cases/2412.14271/note/reproduction-note.zh-CN.md) · [EN](cases/2412.14271/note/reproduction-note.en.md) · [Code](cases/2412.14271/code/README.md) |
| [Boundary time crystals](cases/1708.05014/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1708.05014/note/reproduction-note.zh-CN.md) · [EN](cases/1708.05014/note/reproduction-note.en.md) · [Code](cases/1708.05014/code/README.md) |
| [Exploring the Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice](cases/1709.03478/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1709.03478/note/reproduction-note.zh-CN.md) · [EN](cases/1709.03478/note/reproduction-note.en.md) · [Code](cases/1709.03478/code/README.md) |
| [Self-Bound Quantum Droplets of Atomic Mixtures in Free Space](cases/1710.10890/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1710.10890/note/reproduction-note.zh-CN.md) · [EN](cases/1710.10890/note/reproduction-note.en.md) · [Code](cases/1710.10890/code/README.md) |
| [Symmetry-resolved entanglement in many-body systems](cases/1711.09418/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [中文](cases/1711.09418/note/reproduction-note.zh-CN.md) · [EN](cases/1711.09418/note/reproduction-note.en.md) · [Code](cases/1711.09418/code/README.md) |
| [Exact Spectral Form Factor in a Minimal Model of Many-Body Quantum Chaos](cases/1805.00931/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1805.00931/note/reproduction-note.zh-CN.md) · [EN](cases/1805.00931/note/reproduction-note.en.md) · [Code](cases/1805.00931/code/README.md) |
| [Periodic Orbits, Entanglement, and Quantum Many-Body Scars in Constrained Models: Matrix Product State Approach](cases/1807.01815/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1807.01815/note/reproduction-note.zh-CN.md) · [EN](cases/1807.01815/note/reproduction-note.en.md) · [Code](cases/1807.01815/code/README.md) |
| [Hydrodynamic Diffusion in Integrable Systems](cases/1807.02414/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1807.02414/note/reproduction-note.zh-CN.md) · [EN](cases/1807.02414/note/reproduction-note.en.md) · [Code](cases/1807.02414/code/README.md) |
| [Emergent SU(2) dynamics and perfect quantum many-body scars](cases/1812.05561/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1812.05561/note/reproduction-note.zh-CN.md) · [EN](cases/1812.05561/note/reproduction-note.en.md) · [Code](cases/1812.05561/code/README.md) |
| [Scalable probes of measurement-induced criticality](cases/1910.00020/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1910.00020/note/reproduction-note.zh-CN.md) · [EN](cases/1910.00020/note/reproduction-note.en.md) · [Code](cases/1910.00020/code/README.md) |
| [Entanglement transition in a monitored free fermion chain -- from extended criticality to area law](cases/2005.09722/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2005.09722/note/reproduction-note.zh-CN.md) · [EN](cases/2005.09722/note/reproduction-note.en.md) · [Code](cases/2005.09722/code/README.md) |
| [Exact Quantum Many-Body Scar States in the Rydberg-Blockaded Atom Chain](cases/1810.00888/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/1810.00888/note/reproduction-note.zh-CN.md) · [EN](cases/1810.00888/note/reproduction-note.en.md) · [Code](cases/1810.00888/code/README.md) |
| [Realization of a Laughlin State of Two Rapidly Rotating Fermions](cases/2402.14814/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2402.14814/note/reproduction-note.zh-CN.md) · [EN](cases/2402.14814/note/reproduction-note.en.md) · [Code](cases/2402.14814/code/README.md) |
| [Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances](cases/2409.18176/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2409.18176/note/reproduction-note.zh-CN.md) · [EN](cases/2409.18176/note/reproduction-note.en.md) · [Code](cases/2409.18176/code/README.md) |
| [Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems](cases/2105.08076/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2105.08076/note/reproduction-note.zh-CN.md) · [EN](cases/2105.08076/note/reproduction-note.en.md) · [Code](cases/2105.08076/code/README.md) |
| [Thermodynamics of Quantum Jump Trajectories](cases/0911.0556/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/0911.0556/note/reproduction-note.zh-CN.md) · [EN](cases/0911.0556/note/reproduction-note.en.md) · [Code](cases/0911.0556/code/README.md) |
| [Exact nonequilibrium steady state of a strongly driven open XXZ chain](cases/1106.2978/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/1106.2978/note/reproduction-note.zh-CN.md) · [EN](cases/1106.2978/note/reproduction-note.en.md) · [Code](cases/1106.2978/code/README.md) |
| [Phase Structure of Driven Quantum Systems](cases/1508.03344/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1508.03344/note/reproduction-note.zh-CN.md) · [EN](cases/1508.03344/note/reproduction-note.en.md) · [Code](cases/1508.03344/code/README.md) |
| [Dynamics of a Quantum Phase Transition](cases/cond-mat-0503511/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/cond-mat-0503511/note/reproduction-note.zh-CN.md) · [EN](cases/cond-mat-0503511/note/reproduction-note.en.md) · [Code](cases/cond-mat-0503511/code/README.md) |
| [Localization of Interacting Fermions at High Temperature](cases/cond-mat-0610854/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/cond-mat-0610854/note/reproduction-note.zh-CN.md) · [EN](cases/cond-mat-0610854/note/reproduction-note.en.md) · [Code](cases/cond-mat-0610854/code/README.md) |
| [Dynamics of a Quantum Phase Transition: Exact Solution of the Quantum Ising Model](cases/cond-mat-0509490/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/cond-mat-0509490/note/reproduction-note.zh-CN.md) · [EN](cases/cond-mat-0509490/note/reproduction-note.en.md) · [Code](cases/cond-mat-0509490/code/README.md) |
| [Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model](cases/quant-ph-0507004/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/quant-ph-0507004/note/reproduction-note.zh-CN.md) · [EN](cases/quant-ph-0507004/note/reproduction-note.en.md) · [Code](cases/quant-ph-0507004/code/README.md) |
| [Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model](cases/1206.2505/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/1206.2505/note/reproduction-note.zh-CN.md) · [EN](cases/1206.2505/note/reproduction-note.en.md) · [Code](cases/1206.2505/code/README.md) |

</details>

<a id="collection-topology-materials"></a>

<details>
<summary><strong>拓扑、非厄米、材料与输运 / Topology, non-Hermitian physics, materials & transport（21）</strong></summary>

从非厄米边界态到拓扑材料和量子输运，集中收录谱、相图、边界态与响应函数的复现。

Spectra, phase diagrams, boundary states, and response functions across topology, materials, and transport.

| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |
| --- | --- | --- | --- |
| [Edge states and topological invariants of non-Hermitian systems](cases/1803.01876/README.md) | Non-Hermitian SSH model and non-Bloch bulk-boundary correspondence | Partial scientific reproduction | [中文](cases/1803.01876/note/reproduction-note.zh-CN.md) · [EN](cases/1803.01876/note/reproduction-note.en.md) · [Code](cases/1803.01876/code/README.md) |
| [Non-Hermitian Chern bands](cases/1804.04672/README.md) | Non-Hermitian Chern bands and non-Bloch Chern physics | Partial scientific reproduction | [中文](cases/1804.04672/note/reproduction-note.zh-CN.md) · [EN](cases/1804.04672/note/reproduction-note.en.md) · [Code](cases/1804.04672/code/README.md) |
| [Sensitivity to perturbations in the three-dimensional Anderson model](cases/2605.25594/README.md) | Three-dimensional Anderson localization | Partial scientific reproduction | [中文](cases/2605.25594/note/reproduction-note.zh-CN.md) · [EN](cases/2605.25594/note/reproduction-note.en.md) · [Code](cases/2605.25594/code/README.md) |
| [Lyapunov formulation of band theory for disordered non-Hermitian systems](cases/2507.09447/README.md) | Lyapunov band theory and the non-Hermitian skin–Anderson transition | Partial scientific reproduction | [中文](cases/2507.09447/note/reproduction-note.zh-CN.md) · [EN](cases/2507.09447/note/reproduction-note.en.md) · [Code](cases/2507.09447/code/README.md) |
| [Interband coherence induced correction to adiabatic pumping in periodically driven systems](cases/10.1103-PhysRevB.91.085420/README.md) | Interband-coherence correction to adiabatic pumping in the continuously driven Harper model | Partial scientific reproduction | [中文](cases/10.1103-PhysRevB.91.085420/note/reproduction-note.zh-CN.md) · [EN](cases/10.1103-PhysRevB.91.085420/note/reproduction-note.en.md) · [Code](cases/10.1103-PhysRevB.91.085420/code/README.md) |
| [Geometry-adaptive formulation of non-Bloch bands in arbitrary dimensions and spectral instability](cases/2407.01296/README.md) | Geometry-adaptive non-Bloch bands, non-Hermitian skin effect, and spectral instability | Partial scientific reproduction | [中文](cases/2407.01296/note/reproduction-note.zh-CN.md) · [EN](cases/2407.01296/note/reproduction-note.en.md) · [Code](cases/2407.01296/code/README.md) |
| [Topological Band Theory for Non-Hermitian Hamiltonians](cases/1706.07435/README.md) | Equation-level reproduction of non-Hermitian topology, exceptional points, domain-wall states, and lattice cylinder spectra | Partial scientific reproduction | [中文](cases/1706.07435/note/reproduction-note.zh-CN.md) · [EN](cases/1706.07435/note/reproduction-note.en.md) · [Code](cases/1706.07435/code/README.md) |
| [Topological Phase Transition in Non-Hermitian Quasicrystals](cases/1905.09460/README.md) | non-Hermitian physics; quasicrystals; topological phase transitions; mode-locked lasers | Partial scientific reproduction | [中文](cases/1905.09460/note/reproduction-note.zh-CN.md) · [EN](cases/1905.09460/note/reproduction-note.en.md) · [Code](cases/1905.09460/code/README.md) |
| [Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath](cases/2511.11394/README.md) | Small-q dissipative approach toward the Dirichlet/Chern bound. | Partial scientific reproduction | [中文](cases/2511.11394/note/reproduction-note.zh-CN.md) · [EN](cases/2511.11394/note/reproduction-note.en.md) · [Code](cases/2511.11394/code/README.md) |
| [Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems](cases/2607.22976/README.md) | Topological interface localization and standing/traveling profiles. | Partial scientific reproduction | [中文](cases/2607.22976/note/reproduction-note.zh-CN.md) · [EN](cases/2607.22976/note/reproduction-note.en.md) · [Code](cases/2607.22976/code/README.md) |
| [Hubbard model physics in transition metal dichalcogenide moire bands](cases/1804.03151/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1804.03151/note/reproduction-note.zh-CN.md) · [EN](cases/1804.03151/note/reproduction-note.en.md) · [Code](cases/1804.03151/code/README.md) |
| [Topological insulators in twisted transition metal dichalcogenide homobilayers](cases/1807.03311/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1807.03311/note/reproduction-note.zh-CN.md) · [EN](cases/1807.03311/note/reproduction-note.en.md) · [Code](cases/1807.03311/code/README.md) |
| [All "Magic Angles" Are "Stable" Topological](cases/1807.10676/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1807.10676/note/reproduction-note.zh-CN.md) · [EN](cases/1807.10676/note/reproduction-note.en.md) · [Code](cases/1807.10676/code/README.md) |
| [Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport](cases/2608.05312/README.md) | Open-system dark-state rescue, cavity transport, and finite-temperature mechanism competition | Partial scientific reproduction | [中文](cases/2608.05312/note/reproduction-note.zh-CN.md) · [EN](cases/2608.05312/note/reproduction-note.en.md) · [Code](cases/2608.05312/code/README.md) |
| [Discontinuous Shear Thickening in Biological Tissue Rheology](cases/2211.15015/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2211.15015/note/reproduction-note.zh-CN.md) · [EN](cases/2211.15015/note/reproduction-note.en.md) · [Code](cases/2211.15015/code/README.md) |
| [Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids](cases/2406.07531/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2406.07531/note/reproduction-note.zh-CN.md) · [EN](cases/2406.07531/note/reproduction-note.en.md) · [Code](cases/2406.07531/code/README.md) |
| [Electronic correlations at paramagnetic (001) and (110) NiO surfaces: Charge-transfer and Mott-Hubbard-type gaps at the surface and subsurface of (110) NiO](cases/2101.12558/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2101.12558/note/reproduction-note.zh-CN.md) · [EN](cases/2101.12558/note/reproduction-note.en.md) · [Code](cases/2101.12558/code/README.md) |
| [Anomalous edge states and the bulk-edge correspondence for periodically driven two-dimensional systems](cases/1212.3324/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1212.3324/note/reproduction-note.zh-CN.md) · [EN](cases/1212.3324/note/reproduction-note.en.md) · [Code](cases/1212.3324/code/README.md) |
| [Energy Levels and Wave Functions of Bloch Electrons in Rational and Irrational Magnetic Fields](cases/PhysRevB.14.2239/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/PhysRevB.14.2239/note/reproduction-note.zh-CN.md) · [EN](cases/PhysRevB.14.2239/note/reproduction-note.en.md) · [Code](cases/PhysRevB.14.2239/code/README.md) |
| [Quantum Spin Hall Effect in Graphene](cases/cond-mat-0411737/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/cond-mat-0411737/note/reproduction-note.zh-CN.md) · [EN](cases/cond-mat-0411737/note/reproduction-note.en.md) · [Code](cases/cond-mat-0411737/code/README.md) |
| [Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](cases/physics-9712001/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [中文](cases/physics-9712001/note/reproduction-note.zh-CN.md) · [EN](cases/physics-9712001/note/reproduction-note.en.md) · [Code](cases/physics-9712001/code/README.md) |

</details>

<a id="collection-amo-field"></a>

<details>
<summary><strong>原子、光学、光子学与场论 / Atomic, optical, photonic & field physics（9）</strong></summary>

原子阵列、腔量子电动力学、光子学与场论案例，连接数值模型、实验可观测量和器件语境。

Atomic arrays, cavity QED, photonics, and field theory connecting models, observables, and device context.

| 论文 / Paper | 复现内容 / Reproduced focus | 状态 / Status | 打开 / Open |
| --- | --- | --- | --- |
| [An Algorithm for Fast Assembling Large-Scale Defect-Free Atom Arrays](cases/2604.08669/README.md) | Defect-free atom-array assembly | Partial scientific reproduction | [中文](cases/2604.08669/note/reproduction-note.zh-CN.md) · [EN](cases/2604.08669/note/reproduction-note.en.md) · [Code](cases/2604.08669/code/README.md) |
| [Backreaction of stimulated Hawking radiation in an optical analogue](cases/10.1038-s41586-026-10720-3/README.md) | Stimulated Hawking radiation and backreaction in a fibre-optical analogue horizon | Partial scientific reproduction | [中文](cases/10.1038-s41586-026-10720-3/note/reproduction-note.zh-CN.md) · [EN](cases/10.1038-s41586-026-10720-3/note/reproduction-note.en.md) · [Code](cases/10.1038-s41586-026-10720-3/code/README.md) |
| [Circuit Quantum Electrodynamics](cases/2005.12667/README.md) | Circuit quantization, Jaynes-Cummings and dispersive physics, open quantum systems, measurement, control, bosonic codes, and microwave quantum optics | Partial scientific reproduction | [中文](cases/2005.12667/note/reproduction-note.zh-CN.md) · [EN](cases/2005.12667/note/reproduction-note.en.md) · [Code](cases/2005.12667/code/README.md) |
| [Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass](cases/2607.15070/README.md) | Casimir effect; quantum field theory; position-dependent effective mass | Scientific reproduction — invalid | [中文](cases/2607.15070/note/reproduction-note.zh-CN.md) · [EN](cases/2607.15070/note/reproduction-note.en.md) · [Code](cases/2607.15070/code/README.md) |
| [Boundary element method for resonances in dielectric microcavities](cases/physics-0206018/README.md) | Boundary-integral scattering, resonances, and near- and far-field reconstruction in dielectric microcavities | Partial scientific reproduction | [中文](cases/physics-0206018/note/reproduction-note.zh-CN.md) · [EN](cases/physics-0206018/note/reproduction-note.en.md) · [Code](cases/physics-0206018/code/README.md) |
| [Decoherence-Free Interaction between Giant Atoms in Waveguide QED](cases/1711.08863/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [中文](cases/1711.08863/note/reproduction-note.zh-CN.md) · [EN](cases/1711.08863/note/reproduction-note.en.md) · [Code](cases/1711.08863/code/README.md) |
| [Nonreciprocal Photon Blockade](cases/1807.10084/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/1807.10084/note/reproduction-note.zh-CN.md) · [EN](cases/1807.10084/note/reproduction-note.en.md) · [Code](cases/1807.10084/code/README.md) |
| [Exploring Atom-Ion Feshbach Resonances below the s-Wave Limit](cases/2406.13410/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2406.13410/note/reproduction-note.zh-CN.md) · [EN](cases/2406.13410/note/reproduction-note.en.md) · [Code](cases/2406.13410/code/README.md) |
| [On-Chip Quantum Interference between Independent Lithium Niobate-on-Insulator Photon-Pair Sources](cases/2404.08378/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [中文](cases/2404.08378/note/reproduction-note.zh-CN.md) · [EN](cases/2404.08378/note/reproduction-note.en.md) · [Code](cases/2404.08378/code/README.md) |

</details>

这里的状态描述复现范围，不是论文排名，也不是完成度奖杯。部分复现、输入缺失、算力阻塞和待独立评审都会照实保留。

Status describes reproduction scope, not rank. See [how to read reproduction quality](#how-to-read-reproduction-quality) and the [detailed case index](CASES.md) for paper identities, audit scores, generated figures, checks, and explicit boundaries.
<!-- case-catalog:end -->

## Run One Case / 跑一个案例

Start with the non-Hermitian edge-state case for PRL 121, 086803 (2018):

```bash
git clone https://github.com/xi-zhao/runthepaper.git
cd runthepaper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python cases/1803.01876/code/scripts/run_fig4_winding.py
```

The command regenerates the non-Bloch winding figure, CSV data, and JSON checks
under [`cases/1803.01876/outputs/`](cases/1803.01876/outputs/). The [case
instructions](cases/1803.01876/code/README.md) explain the remaining figures,
dependencies, and reproduction boundary.

## What You Can Do Here / 你可以在这里做什么

- **读懂。** 顺着公式、参数、数值选择和限制，理解一张结果图究竟是怎样得到的。
- **跑起来。** 重新生成图和数据，再用机器可读的证据检查它，而不是只看一张相似的图片。
- **接着做。** 把已有案例当作研究基线，补上缺失输入、修正错误、独立评审，或者探索新的问题。

The cases are meant to be used, questioned, and improved. A careful report that
something cannot yet be reproduced can be as valuable as another successful
figure, provided the boundary is explicit and the evidence is public.

## How To Read Reproduction Quality

Final public figures use the paper's parameters whenever public inputs and
available resources make that possible. Otherwise the case is labeled as
reduced-scale, subset, proxy, or blocked; a test-scale result is never presented
as a complete reproduction.

The audit score measures the coverage of available evidence. It is not a
percentage of physical correctness, a visual similarity rating, a cross-paper
ranking, or a publication threshold. Coverage, fidelity, and lifecycle closure
are separate questions; read the status and limitation statement together with
the score.

The [scientific-lifecycle audit snapshot](cases/scientific-lifecycle-audit-2026-08-01.json)
tracks full-paper claim scope, scientific completion, and pixel evidence as
independent dimensions under the current scientific-first contract.

Original paper PDFs, source archives, standalone original figures, and extracted
plotting data are not redistributed here. A case may include a limited,
source-attributed comparison panel when it is necessary to audit reproduction
quality; the underlying source panel and digitized data remain unpublished.
Each case links to the official paper and states its remaining reproduction
boundary.

## Build It Together / 一起共建

RunThePaper is intended as shared infrastructure for the AI era of science, not
a finished showcase owned by one team. You do not need to contribute an entire
paper. A corrected derivation, an independent rerun, a missing parameter, a
clear failure report, or one better validation check can all move a case forward.

Have a paper you want reproduced? [Open an
issue](https://github.com/xi-zhao/runthepaper/issues/new) with its title, DOI or
arXiv ID, and the figure or claim you care about most. To review or extend an
existing case, see the [contributing guide](CONTRIBUTING.md).

<a id="pragent-behind-the-library"></a>

## PRAgent Behind the Library / PRAgent 是怎么工作的

PRAgent is the reproduction harness behind RunThePaper. It traces a paper's
claims and methods, turns them into explicit reproduction items, implements and
runs the calculations, and packages the results with evidence and remaining
boundaries. RunThePaper is where those cases become public, readable, runnable,
and reusable.

```text
static paper
    ↓  PRAgent: trace → implement → run → check → review
auditable reproduction case
    ↓  RunThePaper: publish → rerun → discuss → extend
shared context for researchers and scientific agents
```

The public 100-case collection is an open testbed. It shows what the current
system can and cannot turn into executable science; it is not a claim of blind
generalization to every unseen paper.

## Toward Agent4Science / 我们对 AI for Science 的判断

Papers alone are too compressed to be the full working context of a scientific
agent. Future agents need derivations, code, data, experimental observations,
and eventually safe interfaces to instruments. They need to see not only the
final claim, but also what was tried, what failed, and what remains uncertain.

RunThePaper already begins to provide part of that context: explicit
derivations, runnable implementations, generated artifacts, checks, and honest
boundaries. Instrument control and live experimental observations are future
layers, not capabilities claimed by this repository today.

That is why executable research infrastructure matters. When scientific agents
start a new exploration from a checked case instead of a static PDF, they inherit
more of the reasoning and evidence needed to ask the next question. We believe
this can make AI for Science more grounded, more collaborative, and easier to
audit.

## License

Code is licensed under the MIT License. Notes, generated figures, and generated
data are licensed under CC BY 4.0 unless a case states otherwise.

Third-party papers, source files, and original figures remain under their
original rights holders' terms and are not covered by this repository's license.
The same exclusion applies to any limited paper excerpts shown inside validation
comparison panels.
