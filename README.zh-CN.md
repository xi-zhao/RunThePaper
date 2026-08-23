<h1 align="center">RunThePaper</h1>

<p align="center"><strong>让论文不只是能读、能引用，也能运行、能验证、能接力。</strong></p>

<p align="center">
  <a href="README.md">英文版</a> ·
  <strong>简体中文</strong>
</p>

<p align="center">
  <a href="#论文复现目录">案例目录</a> ·
  <a href="#为什么要做-runthepaper">为什么要做</a> ·
  <a href="#科研基础设施模型">基础设施模型</a> ·
  <a href="https://github.com/xi-zhao/runthepaper/issues/new">提交论文</a> ·
  <a href="CONTRIBUTING.md">参与共建</a>
</p>

一篇论文，是一次研究的高度压缩。公式留在正文里，参数散落在图注和补充材料里，
真正把结果重新跑起来，往往还需要许多没有写下来的判断。

RunThePaper 想把这些被压缩的过程重新展开。这里的每个案例都对应一篇可以验证的
论文，包含解释性讲义、可运行代码、生成结果、机器可读的检查，以及仍未解决的边界。
你可以从一张图开始，也可以把它当作下一项研究的起点。

RunThePaper 是一项由社区共同建设的可执行论文复现基础设施。研究者可以在这里阅读、
重跑、检查和继续扩展公开的科研案例。

这里的 100 个案例不是 100 座全部完成的奖杯。部分复现、公开输入缺失、算力限制、
无效运行和待独立评审都会照实保留。有价值的科研基础设施应该保存不确定性，而不是
把它打磨掉。

| 如果你想…… | 从这里进入 |
| --- | --- |
| 先读懂一篇论文 | 打开解释性讲义 |
| 亲手把结果跑出来 | 打开代码、生成图和检查结果 |
| 在现有结果上继续做 | 阅读复现边界，再提交修正、评审或扩展 |

独立基准、合成练习、内部评估和不对应正式论文的案例不会作为论文复现案例发布。

## 为什么要做 RunThePaper

科研面临的不只是生产力问题，也有协作方式的问题。AI 正在加速文献阅读、推导、
编程和数据分析，但科研最主要的交付物仍然是一篇高度压缩的论文。只要推导、代码、
参数、失败记录和验证过程继续散落在个人电脑和临时文件夹里，科研就仍然很难摆脱
小作坊式的交接方式。

与此同时，生成正在变得越来越便宜，验证却没有。未来的科学智能体可以快速提出
大量假设、代码和结果，但未经检查的产出越多，科研系统里的噪声也可能越多。真正
稀缺的将是经过验证、能够理解、可以继续使用的结果。

> 在要求 AI 发现未知科学之前，我们应该先检验它能否可靠地重建、执行和审计已知科学。

RunThePaper 从论文复现开始，因为复现同时检验理解、执行和验证。每个公开案例都试图
把论文重新展开成一种新的科研交付单位：明确的论文身份与主张、推导、代码、生成数据、
机器检查、独立评审状态，以及仍未解决的边界。

## 论文复现目录

<!-- case-catalog:start -->
**100 篇公开案例，按研究主题进入。** 这里的分类是一条主要阅读路径，
很多论文同时横跨多个方向。论文标题保留原文。

选择一个主题展开目录，也可以进入 [完整索引（英文）](CASES.md) 查看论文身份、分数和复现边界。

**快速入口**

- [量子计算、算法与纠错 (25)](#collection-quantum-computing)
- [量子信息、基础问题与精密测量 (18)](#collection-quantum-information)
- [多体物理、相变与非平衡动力学 (27)](#collection-many-body)
- [拓扑、非厄米、材料与输运 (21)](#collection-topology-materials)
- [原子、光学、光子学与场论 (9)](#collection-amo-field)

<a id="collection-quantum-computing"></a>

<details>
<summary><strong>量子计算、算法与纠错 (25)</strong></summary>

从量子线路编译、量子模拟到容错与误差缓解，关注怎样把量子计算的关键主张真正跑起来。

| 论文 | 复现状态 | 查看 |
| --- | --- | --- |
| [Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices](cases/10.1145-3297858.3304023/README.md) | 部分科学复现 | [中文讲义](cases/10.1145-3297858.3304023/note/reproduction-note.zh-CN.md) · [代码](cases/10.1145-3297858.3304023/code/README.md) |
| [Simulating the Sycamore quantum supremacy circuits](cases/2103.03074/README.md) | 部分科学复现 | [中文讲义](cases/2103.03074/note/reproduction-note.zh-CN.md) · [代码](cases/2103.03074/code/README.md) |
| [Efficient simulation of logical magic state preparation protocols](cases/2512.23799/README.md) | 部分科学复现 | [中文讲义](cases/2512.23799/note/reproduction-note.zh-CN.md) · [代码](cases/2512.23799/code/README.md) |
| [Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics](cases/2605.25398/README.md) | 部分科学复现 | [中文讲义](cases/2605.25398/note/reproduction-note.zh-CN.md) · [代码](cases/2605.25398/code/README.md) |
| [Buffer-atom-mediated quantum logic gates with off-resonant modulated driving](cases/10.1007-s11433-024-2478-8/README.md) | 部分科学复现 | [中文讲义](cases/10.1007-s11433-024-2478-8/note/reproduction-note.zh-CN.md) · [代码](cases/10.1007-s11433-024-2478-8/code/README.md) |
| [Strongly correlated quantum walks with a 12-qubit superconducting processor](cases/10.1126-science.aaw1611/README.md) | 部分科学复现 | [中文讲义](cases/10.1126-science.aaw1611/note/reproduction-note.zh-CN.md) · [代码](cases/10.1126-science.aaw1611/code/README.md) |
| [Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates](cases/10.1103-PRXQuantum.6.010331/README.md) | 部分科学复现 | [中文讲义](cases/10.1103-PRXQuantum.6.010331/note/reproduction-note.zh-CN.md) · [代码](cases/10.1103-PRXQuantum.6.010331/code/README.md) |
| [Thermodynamics of Quantum Reservoir Computing](cases/2607.02157/README.md) | 部分科学复现 | [中文讲义](cases/2607.02157/note/reproduction-note.zh-CN.md) · [代码](cases/2607.02157/code/README.md) |
| [Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms](cases/2502.20558/README.md) | 部分科学复现 | [中文讲义](cases/2502.20558/note/reproduction-note.zh-CN.md) · [代码](cases/2502.20558/code/README.md) |
| [Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate](cases/2607.15597/README.md) | 科学复现无效 | [中文讲义](cases/2607.15597/note/reproduction-note.zh-CN.md) · [代码](cases/2607.15597/code/README.md) |
| [Programmable Open Quantum Systems](cases/2512.08279/README.md) | 部分科学复现 | [中文讲义](cases/2512.08279/note/reproduction-note.zh-CN.md) · [代码](cases/2512.08279/code/README.md) |
| [Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition](cases/1903.05124/README.md) | 科学复现无效 | [中文讲义](cases/1903.05124/note/reproduction-note.zh-CN.md) · [代码](cases/1903.05124/code/README.md) |
| [Demonstrating quantum error mitigation on logical qubits](cases/10.1038-s41467-025-67768-4/README.md) | 科学复现无效 | [中文讲义](cases/10.1038-s41467-025-67768-4/note/reproduction-note.zh-CN.md) · [代码](cases/10.1038-s41467-025-67768-4/code/README.md) |
| [Amplitude Estimation without Phase Estimation](cases/1904.10246/README.md) | 科学复现无效 | [中文讲义](cases/1904.10246/note/reproduction-note.zh-CN.md) · [代码](cases/1904.10246/code/README.md) |
| [Graph coloring via quantum optimization on a Rydberg-qudit atom array](cases/2504.08598/README.md) | 科学复现无效 | [中文讲义](cases/2504.08598/note/reproduction-note.zh-CN.md) · [代码](cases/2504.08598/code/README.md) |
| [Remote Entanglement Generation Via Enhanced Quantum State Transfer](cases/2506.06669/README.md) | 科学复现无效 | [中文讲义](cases/2506.06669/note/reproduction-note.zh-CN.md) · [代码](cases/2506.06669/code/README.md) |
| [Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors](cases/2607.08212/README.md) | 部分科学复现 | [中文讲义](cases/2607.08212/note/reproduction-note.zh-CN.md) · [代码](cases/2607.08212/code/README.md) |
| [Plaquette: A hardware-aware design platform for fault-tolerant quantum computers](cases/2607.08767/README.md) | 部分科学复现 | [中文讲义](cases/2607.08767/note/reproduction-note.zh-CN.md) · [代码](cases/2607.08767/code/README.md) |
| [Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search](cases/2607.27060/README.md) | 科学复现无效 | [中文讲义](cases/2607.27060/note/reproduction-note.zh-CN.md) · [代码](cases/2607.27060/code/README.md) |
| [High-rate qLDPC processors](cases/2607.28795/README.md) | 科学复现无效 | [中文讲义](cases/2607.28795/note/reproduction-note.zh-CN.md) · [代码](cases/2607.28795/code/README.md) |
| [Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators](cases/2608.03987/README.md) | 部分科学复现 | [中文讲义](cases/2608.03987/note/reproduction-note.zh-CN.md) · [代码](cases/2608.03987/code/README.md) |
| [Quantum machine learning in feature Hilbert spaces](cases/1803.07128/README.md) | 部分科学复现 | [中文讲义](cases/1803.07128/note/reproduction-note.zh-CN.md) · [代码](cases/1803.07128/code/README.md) |
| [A random compiler for fast Hamiltonian simulation](cases/1811.08017/README.md) | 科学复现，待独立评审 | [中文讲义](cases/1811.08017/note/reproduction-note.zh-CN.md) · [代码](cases/1811.08017/code/README.md) |
| [Obstacles to State Preparation and Variational Optimization from Symmetry Protection](cases/1910.08980/README.md) | 部分科学复现 | [中文讲义](cases/1910.08980/note/reproduction-note.zh-CN.md) · [代码](cases/1910.08980/code/README.md) |
| [Universal Quantum Computation with Ideal Clifford Gates and Noisy Ancillas](cases/quant-ph-0403025/README.md) | 部分科学复现 | [中文讲义](cases/quant-ph-0403025/note/reproduction-note.zh-CN.md) · [代码](cases/quant-ph-0403025/code/README.md) |

</details>

<a id="collection-quantum-information"></a>

<details>
<summary><strong>量子信息、基础问题与精密测量 (18)</strong></summary>

纠缠、量子资源、开放系统、量子基础与精密测量，连接概念推导和可检查的数值结果。

| 论文 | 复现状态 | 查看 |
| --- | --- | --- |
| [Particle exchange statistics beyond fermions and bosons](cases/10.1038-s41586-024-08262-7/README.md) | 部分科学复现 | [中文讲义](cases/10.1038-s41586-024-08262-7/note/reproduction-note.zh-CN.md) · [代码](cases/10.1038-s41586-024-08262-7/code/README.md) |
| [Sufficient Wigner Negativity Implies Genuine Multipartite Entanglement](cases/2510.26761/README.md) | 部分科学复现 | [中文讲义](cases/2510.26761/note/reproduction-note.zh-CN.md) · [代码](cases/2510.26761/code/README.md) |
| [Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking](cases/2607.00718/README.md) | 部分科学复现 | [中文讲义](cases/2607.00718/note/reproduction-note.zh-CN.md) · [代码](cases/2607.00718/code/README.md) |
| [Information and Majorization Theory for Fermionic Phase-Space Distributions](cases/2401.08523/README.md) | 部分科学复现 | [中文讲义](cases/2401.08523/note/reproduction-note.zh-CN.md) · [代码](cases/2401.08523/code/README.md) |
| [Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation](cases/2602.12212/README.md) | 部分科学复现 | [中文讲义](cases/2602.12212/note/reproduction-note.zh-CN.md) · [代码](cases/2602.12212/code/README.md) |
| [Fixed-detector tilt--defocus sensing by upstream source coding in a time-reversed Young interferometer](cases/2605.02873/README.md) | 科学复现无效 | [中文讲义](cases/2605.02873/note/reproduction-note.zh-CN.md) · [代码](cases/2605.02873/code/README.md) |
| [Photonic Violation of Wigner's Inequality](cases/2606.30255/README.md) | 科学复现无效 | [中文讲义](cases/2606.30255/note/reproduction-note.zh-CN.md) · [代码](cases/2606.30255/code/README.md) |
| [Non-Hermitian-enhanced quantum sensing in an optical interferometer](cases/2607.23978/README.md) | 部分科学复现 | [中文讲义](cases/2607.23978/note/reproduction-note.zh-CN.md) · [代码](cases/2607.23978/code/README.md) |
| [Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit](cases/2401.05830/README.md) | 部分科学复现 | [中文讲义](cases/2401.05830/note/reproduction-note.zh-CN.md) · [代码](cases/2401.05830/code/README.md) |
| [Optimal Generators for Quantum Sensing](cases/2305.15556/README.md) | 科学复现，待独立评审 | [中文讲义](cases/2305.15556/note/reproduction-note.zh-CN.md) · [代码](cases/2305.15556/code/README.md) |
| [New Constraints on Axion-Mediated Spin Interactions Using Magnetic Amplification](cases/PhysRevLett.133.191801/README.md) | 部分科学复现 | [中文讲义](cases/PhysRevLett.133.191801/note/reproduction-note.zh-CN.md) · [代码](cases/PhysRevLett.133.191801/code/README.md) |
| [Precision-Spectroscopic Determination of the Binding Energy of a Two-Body Quantum System: The Hydrogen Atom and the Proton-Size Puzzle](cases/PhysRevLett.132.113001/README.md) | 部分科学复现 | [中文讲义](cases/PhysRevLett.132.113001/note/reproduction-note.zh-CN.md) · [代码](cases/PhysRevLett.132.113001/code/README.md) |
| [Squeezed Spin States](cases/PhysRevA.47.5138/README.md) | 科学复现，待独立评审 | [中文讲义](cases/PhysRevA.47.5138/note/reproduction-note.zh-CN.md) · [代码](cases/PhysRevA.47.5138/code/README.md) |
| [Entanglement in Quantum Critical Phenomena](cases/quant-ph-0211074/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/quant-ph-0211074/note/reproduction-note.zh-CN.md) · [代码](cases/quant-ph-0211074/code/README.md) |
| [Entanglement of Formation of an Arbitrary State of Two Qubits](cases/quant-ph-9709029/README.md) | 部分科学复现 | [中文讲义](cases/quant-ph-9709029/note/reproduction-note.zh-CN.md) · [代码](cases/quant-ph-9709029/code/README.md) |
| [Necessary and Sufficient Condition for Nonzero Quantum Discord](cases/1004.0190/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/1004.0190/note/reproduction-note.zh-CN.md) · [代码](cases/1004.0190/code/README.md) |
| [Quantum Speed Limit for Non-Markovian Dynamics](cases/1302.5069/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/1302.5069/note/reproduction-note.zh-CN.md) · [代码](cases/1302.5069/code/README.md) |
| [Quantum Discord and the Power of One Qubit](cases/0709.0548/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/0709.0548/note/reproduction-note.zh-CN.md) · [代码](cases/0709.0548/code/README.md) |

</details>

<a id="collection-many-body"></a>

<details>
<summary><strong>多体物理、相变与非平衡动力学 (27)</strong></summary>

时间晶体、多体疤痕、量子相变与热化问题，把跨尺度的理论结果拆成可运行的计算对象。

| 论文 | 复现状态 | 查看 |
| --- | --- | --- |
| [Discrete time crystals: rigidity, criticality, and realizations](cases/1608.02589/README.md) | 部分科学复现 | [中文讲义](cases/1608.02589/note/reproduction-note.zh-CN.md) · [代码](cases/1608.02589/code/README.md) |
| [Quantum many-body scars](cases/1711.03528/README.md) | 部分科学复现 | [中文讲义](cases/1711.03528/note/reproduction-note.zh-CN.md) · [代码](cases/1711.03528/code/README.md) |
| [Localization Driven Superradiant Instability](cases/10.1103-PhysRevLett.124.113601/README.md) | 部分科学复现 | [中文讲义](cases/10.1103-PhysRevLett.124.113601/note/reproduction-note.zh-CN.md) · [代码](cases/10.1103-PhysRevLett.124.113601/code/README.md) |
| [Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain](cases/2510.12880/README.md) | 部分科学复现 | [中文讲义](cases/2510.12880/note/reproduction-note.zh-CN.md) · [代码](cases/2510.12880/code/README.md) |
| [Dissipative Phase Transition in the Two-Photon Dicke Model](cases/2412.14271/README.md) | 部分科学复现 | [中文讲义](cases/2412.14271/note/reproduction-note.zh-CN.md) · [代码](cases/2412.14271/code/README.md) |
| [Boundary time crystals](cases/1708.05014/README.md) | 部分科学复现 | [中文讲义](cases/1708.05014/note/reproduction-note.zh-CN.md) · [代码](cases/1708.05014/code/README.md) |
| [Exploring the Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice](cases/1709.03478/README.md) | 部分科学复现 | [中文讲义](cases/1709.03478/note/reproduction-note.zh-CN.md) · [代码](cases/1709.03478/code/README.md) |
| [Self-Bound Quantum Droplets of Atomic Mixtures in Free Space](cases/1710.10890/README.md) | 部分科学复现 | [中文讲义](cases/1710.10890/note/reproduction-note.zh-CN.md) · [代码](cases/1710.10890/code/README.md) |
| [Symmetry-resolved entanglement in many-body systems](cases/1711.09418/README.md) | 科学复现，待独立评审 | [中文讲义](cases/1711.09418/note/reproduction-note.zh-CN.md) · [代码](cases/1711.09418/code/README.md) |
| [Exact Spectral Form Factor in a Minimal Model of Many-Body Quantum Chaos](cases/1805.00931/README.md) | 部分科学复现 | [中文讲义](cases/1805.00931/note/reproduction-note.zh-CN.md) · [代码](cases/1805.00931/code/README.md) |
| [Periodic Orbits, Entanglement, and Quantum Many-Body Scars in Constrained Models: Matrix Product State Approach](cases/1807.01815/README.md) | 部分科学复现 | [中文讲义](cases/1807.01815/note/reproduction-note.zh-CN.md) · [代码](cases/1807.01815/code/README.md) |
| [Hydrodynamic Diffusion in Integrable Systems](cases/1807.02414/README.md) | 部分科学复现 | [中文讲义](cases/1807.02414/note/reproduction-note.zh-CN.md) · [代码](cases/1807.02414/code/README.md) |
| [Emergent SU(2) dynamics and perfect quantum many-body scars](cases/1812.05561/README.md) | 部分科学复现 | [中文讲义](cases/1812.05561/note/reproduction-note.zh-CN.md) · [代码](cases/1812.05561/code/README.md) |
| [Scalable probes of measurement-induced criticality](cases/1910.00020/README.md) | 部分科学复现 | [中文讲义](cases/1910.00020/note/reproduction-note.zh-CN.md) · [代码](cases/1910.00020/code/README.md) |
| [Entanglement transition in a monitored free fermion chain -- from extended criticality to area law](cases/2005.09722/README.md) | 部分科学复现 | [中文讲义](cases/2005.09722/note/reproduction-note.zh-CN.md) · [代码](cases/2005.09722/code/README.md) |
| [Exact Quantum Many-Body Scar States in the Rydberg-Blockaded Atom Chain](cases/1810.00888/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/1810.00888/note/reproduction-note.zh-CN.md) · [代码](cases/1810.00888/code/README.md) |
| [Realization of a Laughlin State of Two Rapidly Rotating Fermions](cases/2402.14814/README.md) | 部分科学复现 | [中文讲义](cases/2402.14814/note/reproduction-note.zh-CN.md) · [代码](cases/2402.14814/code/README.md) |
| [Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances](cases/2409.18176/README.md) | 部分科学复现 | [中文讲义](cases/2409.18176/note/reproduction-note.zh-CN.md) · [代码](cases/2409.18176/code/README.md) |
| [Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems](cases/2105.08076/README.md) | 部分科学复现 | [中文讲义](cases/2105.08076/note/reproduction-note.zh-CN.md) · [代码](cases/2105.08076/code/README.md) |
| [Thermodynamics of Quantum Jump Trajectories](cases/0911.0556/README.md) | 部分科学复现 | [中文讲义](cases/0911.0556/note/reproduction-note.zh-CN.md) · [代码](cases/0911.0556/code/README.md) |
| [Exact nonequilibrium steady state of a strongly driven open XXZ chain](cases/1106.2978/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/1106.2978/note/reproduction-note.zh-CN.md) · [代码](cases/1106.2978/code/README.md) |
| [Phase Structure of Driven Quantum Systems](cases/1508.03344/README.md) | 部分科学复现 | [中文讲义](cases/1508.03344/note/reproduction-note.zh-CN.md) · [代码](cases/1508.03344/code/README.md) |
| [Dynamics of a Quantum Phase Transition](cases/cond-mat-0503511/README.md) | 部分科学复现 | [中文讲义](cases/cond-mat-0503511/note/reproduction-note.zh-CN.md) · [代码](cases/cond-mat-0503511/code/README.md) |
| [Localization of Interacting Fermions at High Temperature](cases/cond-mat-0610854/README.md) | 部分科学复现 | [中文讲义](cases/cond-mat-0610854/note/reproduction-note.zh-CN.md) · [代码](cases/cond-mat-0610854/code/README.md) |
| [Dynamics of a Quantum Phase Transition: Exact Solution of the Quantum Ising Model](cases/cond-mat-0509490/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/cond-mat-0509490/note/reproduction-note.zh-CN.md) · [代码](cases/cond-mat-0509490/code/README.md) |
| [Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model](cases/quant-ph-0507004/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/quant-ph-0507004/note/reproduction-note.zh-CN.md) · [代码](cases/quant-ph-0507004/code/README.md) |
| [Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model](cases/1206.2505/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/1206.2505/note/reproduction-note.zh-CN.md) · [代码](cases/1206.2505/code/README.md) |

</details>

<a id="collection-topology-materials"></a>

<details>
<summary><strong>拓扑、非厄米、材料与输运 (21)</strong></summary>

从非厄米边界态到拓扑材料和量子输运，集中收录谱、相图、边界态与响应函数的复现。

| 论文 | 复现状态 | 查看 |
| --- | --- | --- |
| [Edge states and topological invariants of non-Hermitian systems](cases/1803.01876/README.md) | 部分科学复现 | [中文讲义](cases/1803.01876/note/reproduction-note.zh-CN.md) · [代码](cases/1803.01876/code/README.md) |
| [Non-Hermitian Chern bands](cases/1804.04672/README.md) | 部分科学复现 | [中文讲义](cases/1804.04672/note/reproduction-note.zh-CN.md) · [代码](cases/1804.04672/code/README.md) |
| [Sensitivity to perturbations in the three-dimensional Anderson model](cases/2605.25594/README.md) | 部分科学复现 | [中文讲义](cases/2605.25594/note/reproduction-note.zh-CN.md) · [代码](cases/2605.25594/code/README.md) |
| [Lyapunov formulation of band theory for disordered non-Hermitian systems](cases/2507.09447/README.md) | 部分科学复现 | [中文讲义](cases/2507.09447/note/reproduction-note.zh-CN.md) · [代码](cases/2507.09447/code/README.md) |
| [Interband coherence induced correction to adiabatic pumping in periodically driven systems](cases/10.1103-PhysRevB.91.085420/README.md) | 部分科学复现 | [中文讲义](cases/10.1103-PhysRevB.91.085420/note/reproduction-note.zh-CN.md) · [代码](cases/10.1103-PhysRevB.91.085420/code/README.md) |
| [Geometry-adaptive formulation of non-Bloch bands in arbitrary dimensions and spectral instability](cases/2407.01296/README.md) | 部分科学复现 | [中文讲义](cases/2407.01296/note/reproduction-note.zh-CN.md) · [代码](cases/2407.01296/code/README.md) |
| [Topological Band Theory for Non-Hermitian Hamiltonians](cases/1706.07435/README.md) | 部分科学复现 | [中文讲义](cases/1706.07435/note/reproduction-note.zh-CN.md) · [代码](cases/1706.07435/code/README.md) |
| [Topological Phase Transition in Non-Hermitian Quasicrystals](cases/1905.09460/README.md) | 部分科学复现 | [中文讲义](cases/1905.09460/note/reproduction-note.zh-CN.md) · [代码](cases/1905.09460/code/README.md) |
| [Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath](cases/2511.11394/README.md) | 部分科学复现 | [中文讲义](cases/2511.11394/note/reproduction-note.zh-CN.md) · [代码](cases/2511.11394/code/README.md) |
| [Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems](cases/2607.22976/README.md) | 部分科学复现 | [中文讲义](cases/2607.22976/note/reproduction-note.zh-CN.md) · [代码](cases/2607.22976/code/README.md) |
| [Hubbard model physics in transition metal dichalcogenide moire bands](cases/1804.03151/README.md) | 部分科学复现 | [中文讲义](cases/1804.03151/note/reproduction-note.zh-CN.md) · [代码](cases/1804.03151/code/README.md) |
| [Topological insulators in twisted transition metal dichalcogenide homobilayers](cases/1807.03311/README.md) | 部分科学复现 | [中文讲义](cases/1807.03311/note/reproduction-note.zh-CN.md) · [代码](cases/1807.03311/code/README.md) |
| [All "Magic Angles" Are "Stable" Topological](cases/1807.10676/README.md) | 部分科学复现 | [中文讲义](cases/1807.10676/note/reproduction-note.zh-CN.md) · [代码](cases/1807.10676/code/README.md) |
| [Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport](cases/2608.05312/README.md) | 部分科学复现 | [中文讲义](cases/2608.05312/note/reproduction-note.zh-CN.md) · [代码](cases/2608.05312/code/README.md) |
| [Discontinuous Shear Thickening in Biological Tissue Rheology](cases/2211.15015/README.md) | 部分科学复现 | [中文讲义](cases/2211.15015/note/reproduction-note.zh-CN.md) · [代码](cases/2211.15015/code/README.md) |
| [Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids](cases/2406.07531/README.md) | 部分科学复现 | [中文讲义](cases/2406.07531/note/reproduction-note.zh-CN.md) · [代码](cases/2406.07531/code/README.md) |
| [Electronic correlations at paramagnetic (001) and (110) NiO surfaces: Charge-transfer and Mott-Hubbard-type gaps at the surface and subsurface of (110) NiO](cases/2101.12558/README.md) | 部分科学复现 | [中文讲义](cases/2101.12558/note/reproduction-note.zh-CN.md) · [代码](cases/2101.12558/code/README.md) |
| [Anomalous edge states and the bulk-edge correspondence for periodically driven two-dimensional systems](cases/1212.3324/README.md) | 部分科学复现 | [中文讲义](cases/1212.3324/note/reproduction-note.zh-CN.md) · [代码](cases/1212.3324/code/README.md) |
| [Energy Levels and Wave Functions of Bloch Electrons in Rational and Irrational Magnetic Fields](cases/PhysRevB.14.2239/README.md) | 部分科学复现 | [中文讲义](cases/PhysRevB.14.2239/note/reproduction-note.zh-CN.md) · [代码](cases/PhysRevB.14.2239/code/README.md) |
| [Quantum Spin Hall Effect in Graphene](cases/cond-mat-0411737/README.md) | 部分科学复现 | [中文讲义](cases/cond-mat-0411737/note/reproduction-note.zh-CN.md) · [代码](cases/cond-mat-0411737/code/README.md) |
| [Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](cases/physics-9712001/README.md) | 科学复现，发现论文错误候选 | [中文讲义](cases/physics-9712001/note/reproduction-note.zh-CN.md) · [代码](cases/physics-9712001/code/README.md) |

</details>

<a id="collection-amo-field"></a>

<details>
<summary><strong>原子、光学、光子学与场论 (9)</strong></summary>

原子阵列、腔量子电动力学、光子学与场论案例，连接数值模型、实验可观测量和器件语境。

| 论文 | 复现状态 | 查看 |
| --- | --- | --- |
| [An Algorithm for Fast Assembling Large-Scale Defect-Free Atom Arrays](cases/2604.08669/README.md) | 部分科学复现 | [中文讲义](cases/2604.08669/note/reproduction-note.zh-CN.md) · [代码](cases/2604.08669/code/README.md) |
| [Backreaction of stimulated Hawking radiation in an optical analogue](cases/10.1038-s41586-026-10720-3/README.md) | 部分科学复现 | [中文讲义](cases/10.1038-s41586-026-10720-3/note/reproduction-note.zh-CN.md) · [代码](cases/10.1038-s41586-026-10720-3/code/README.md) |
| [Circuit Quantum Electrodynamics](cases/2005.12667/README.md) | 部分科学复现 | [中文讲义](cases/2005.12667/note/reproduction-note.zh-CN.md) · [代码](cases/2005.12667/code/README.md) |
| [Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass](cases/2607.15070/README.md) | 科学复现无效 | [中文讲义](cases/2607.15070/note/reproduction-note.zh-CN.md) · [代码](cases/2607.15070/code/README.md) |
| [Boundary element method for resonances in dielectric microcavities](cases/physics-0206018/README.md) | 部分科学复现 | [中文讲义](cases/physics-0206018/note/reproduction-note.zh-CN.md) · [代码](cases/physics-0206018/code/README.md) |
| [Decoherence-Free Interaction between Giant Atoms in Waveguide QED](cases/1711.08863/README.md) | 科学复现，待独立评审 | [中文讲义](cases/1711.08863/note/reproduction-note.zh-CN.md) · [代码](cases/1711.08863/code/README.md) |
| [Nonreciprocal Photon Blockade](cases/1807.10084/README.md) | 部分科学复现 | [中文讲义](cases/1807.10084/note/reproduction-note.zh-CN.md) · [代码](cases/1807.10084/code/README.md) |
| [Exploring Atom-Ion Feshbach Resonances below the s-Wave Limit](cases/2406.13410/README.md) | 部分科学复现 | [中文讲义](cases/2406.13410/note/reproduction-note.zh-CN.md) · [代码](cases/2406.13410/code/README.md) |
| [On-Chip Quantum Interference between Independent Lithium Niobate-on-Insulator Photon-Pair Sources](cases/2404.08378/README.md) | 部分科学复现 | [中文讲义](cases/2404.08378/note/reproduction-note.zh-CN.md) · [代码](cases/2404.08378/code/README.md) |

</details>

这里的状态描述复现范围，不是论文排名，也不是完成度奖杯。部分复现、输入缺失、算力阻塞和待独立评审都会照实保留。详情可查看[如何理解复现质量](#如何理解复现质量)和[完整索引（英文）](CASES.md)。
<!-- case-catalog:end -->

## 运行一个案例

可以从 PRL 121, 086803（2018）的非厄米边界态案例开始：

```bash
git clone https://github.com/xi-zhao/runthepaper.git
cd runthepaper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python cases/1803.01876/code/scripts/run_fig4_winding.py
```

这条命令会在 [`cases/1803.01876/outputs/`](cases/1803.01876/outputs/) 下
重新生成非布洛赫绕数图、CSV 数据和 JSON 检查。其他图、依赖和复现边界请查看
[案例运行说明](cases/1803.01876/code/README.md)。

## 你可以在这里做什么

- **读懂。** 顺着公式、参数、数值选择和限制，理解一项结果究竟怎样得到。
- **跑起来。** 重新生成图和数据，检查机器可读证据，而不是只判断图片是否相似。
- **接着做。** 补充缺失输入、修正错误、进行独立评审，或者把案例作为新问题的研究基线。

只要边界说清楚、证据能够公开，一份严谨的“目前无法复现”报告，也可能和一张成功
生成的图片同样有价值。

## 如何理解复现质量

只要公开输入和可用资源允许，最终公开图就使用论文参数。如果无法做到，案例会明确
标记为缩小规模、局部范围、替代结果或阻塞状态；测试规模的结果不会被描述成完整复现。

审计分数衡量的是现有证据的覆盖情况。它不是物理正确率、视觉相似度、跨论文排名或
发表门槛。覆盖度、保真度和科研生命周期闭环是三个不同问题，阅读分数时必须同时查看
案例状态和限制说明。

[科研生命周期审计快照](cases/scientific-lifecycle-audit-2026-08-01.json)
在当前以科学内容为先的合同下，分别记录整篇论文的主张范围、科学完成状态和像素证据。

本仓库不会重新分发原论文 PDF、源文件包、单独的原始图片或提取出的原图数据。为了
审计复现质量，个别案例可能包含最小范围、注明来源的对照面板；原始面板和数字化数据
不会单独公开。每个案例都会链接到论文正式来源并说明剩余复现边界。

## 一起共建

RunThePaper 不是由一个团队维护的成果橱窗，而是一种大家可以共同改进的科研协作单元。
贡献不必从零复现整篇论文；确认一次运行、修正一个公式、补充一项输入、解释一次失败，
或者完成一次独立评审，都能让这个公共上下文更可靠。

如果有希望复现的论文，可以[提交问题](https://github.com/xi-zhao/runthepaper/issues/new)，
附上论文标题、DOI 或 arXiv 编号，以及最关心的图或主张。复核和扩展已有案例前，
请先阅读[贡献指南](CONTRIBUTING.md)。

<a id="科研基础设施模型"></a>

## 科研基础设施模型

RunThePaper 把可执行的科研案例作为基本单元。一个案例不只保存最终图片，还把论文身份、
复现范围、推导、代码、运行结果、机器检查、评审状态和未解决边界组织在一起。研究者和
科学智能体可以从同一个公开对象出发，而不是各自在 PDF 和临时文件夹中重新猜测研究过程。

```text
论文
  ↓
主张与范围 → 推导 → 代码 → 运行结果
  ↓
机器检查 → 评审状态 → 明确边界
  ↓
公共科研案例
  ↓
阅读 → 重跑 → 讨论 → 修正 → 扩展
```

作为科研基础设施，RunThePaper 承担四个作用：为人和智能体提供可操作的公共上下文，
保存验证证据，让成功与失败都成为可以读取的长期记忆，并为跨团队协作提供共同入口。
它不是完成案例的陈列柜，而是能够被持续运行、质疑和改进的公共工作台。

这 100 个公开案例是一组开放测试床。它展示目前能够和不能够被转化为可执行科学的部分，
并不用于证明系统可以盲目泛化到所有未见论文。

## 走向科学智能体

我们目前对 AI for Science 有三个判断。

| 判断 | 含义 |
| --- | --- |
| **先验证，再发现** | 如果智能体还不能稳定重建和审计已知结果，我们就没有足够理由相信它在未知空间中的新发现。 |
| **先建立可操作上下文，再谈自主性** | 智能体需要的不只是论文文本，还需要推导、代码、数据、观测、工具接口、历史失败和明确边界。 |
| **人的判断仍在循环中** | 问题品位、社会需求、科学意义和最终证据裁决，仍然需要研究者承担。 |

我们的目标不是让智能体一次性生成一个看起来合理的答案，而是逐步形成能够自我修正的
科研循环：提出方案、执行、获得观测、验证、写入记忆，再决定下一次探索。RunThePaper
目前提供的是这个循环最基础的可执行上下文和验证记忆。

| 层级 | 进入智能体上下文的信息 | 边界 |
| --- | --- | --- |
| **现在** | 论文主张、详细推导、代码、生成数据与图、机器检查、评审状态和未解决边界 | 本仓库已经公开提供 |
| **继续建设** | 跨案例记忆、可复用科研技能、更强的独立评审与因果化失败诊断 | 发展方向，不是已完成能力 |
| **未来** | 实验数据、实时观测，以及安全、可审计的实验器材操作接口 | 本仓库目前不具备 |

当科学智能体从一个经过检查的案例而不是一份静态 PDF 开始探索时，它继承的不只是结论，
还有得出结论的路径与证据。我们相信，这种基础设施会让 AI for Science 更可靠、更开放，
也更容易被人类理解和共同建设。

支撑这些案例持续建设的 **PRAgent** 仍在优化中。待系统进一步成熟后，我们计划将其
开源，让更多研究者能够共同使用和改进，敬请期待。

## 许可证

代码采用 MIT 许可证。除非个别案例另有说明，讲义、生成图片和生成数据采用 CC BY 4.0
许可证。

第三方论文、源文件和原始图片仍受原权利人条款约束，不属于本仓库许可证范围。验证对照
面板中展示的有限论文片段同样不在本仓库许可证授权范围内。
