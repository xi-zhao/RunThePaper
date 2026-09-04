# Start Researching / 从这里开始研究

[English introduction](README.md) · [中文介绍](README.zh-CN.md) · [All papers / 完整目录](CASES.md)

Choose a direction, check the prerequisites, then follow the suggested paper order. These are learning routes, not a ranking of scientific completion.
先选方向、确认基础，再按建议顺序进入论文。这里给出学习路径；案例是否完成复现，仍以各自的证据和评审状态为准。

## Your first investigation / 第一次动手

1. Read one derivation and identify its assumptions. / 读一段推导，写清所用假设。
2. Follow the case's run instructions, starting with its documented small run when available. / 按案例说明运行；有小规模配置时，先用它检查环境。
3. Compare an output with its numerical check and explain one discrepancy or limitation. / 对照生成结果和数值检查，解释一处差异或限制。
4. Copy a configuration, change one assumption, and keep the new result separate from the paper reproduction. / 复制配置后只改一个假设，将探索结果与原论文复现结果分开记录。

The [qDRIFT example](README.md#run-this-example) is the currently verified first run. Other routes link to their case-specific commands and compute boundaries; they do not promise the same runtime or a completed independent review.
[qDRIFT 示例](README.zh-CN.md#运行这个示例)已有首次运行验证。其他路线请按案例说明查看命令与算力需求。运行时间和独立评审状态因案例而异。

- [量子计算、算法与纠错 / Quantum computing, algorithms & error correction](#learn-quantum-computing)
- [量子信息、基础问题与精密测量 / Quantum information, foundations & sensing](#learn-quantum-information)
- [多体物理、相变与非平衡动力学 / Many-body physics, phases & nonequilibrium dynamics](#learn-many-body)
- [拓扑、非厄米、材料与输运 / Topology, non-Hermitian physics, materials & transport](#learn-topology-materials)
- [原子、光学、光子学与场论 / Atomic, optical, photonic & field physics](#learn-amo-field)

<a id="learn-quantum-computing"></a>

## 量子计算、算法与纠错 / Quantum computing, algorithms & error correction

**先修知识：** 线性代数、量子线路与误差上界；会用 Python 处理数组和绘图。

**Prerequisites:** Linear algebra, basic quantum circuits and error bounds; Python arrays and plotting.

### 1. [A random compiler for fast Hamiltonian simulation](cases/1811.08017/README.md)

把哈密顿量模拟的误差上界变成可计算的资源需求。 / Connect a Hamiltonian simulation error bound to a resource estimate.

**动手任务：** 跑通首页示例，用生成的 CSV 解释量子门数怎样随演化时间变化。

**Try:** Run the README example, then use the generated CSV to explain how the gate count changes with evolution time.

[中文讲义](cases/1811.08017/note/reproduction-note.zh-CN.md) · [English note](cases/1811.08017/note/reproduction-note.en.md) · [Derivation / 推导](cases/1811.08017/docs/DERIVATION.md) · [Run / 运行](cases/1811.08017/code/README.md)

Recorded status / 已记录状态: **Scientific reproduction — independent review pending**. [Evidence and remaining work / 证据与待完成工作](cases/1811.08017/outputs/checks/completion_assessment.json).

### 2. [Amplitude estimation without phase estimation](cases/1904.10246/README.md)

理解怎样不通过相位估计来估计量子振幅。 / Study how amplitude estimation can be formulated without phase estimation.

**动手任务：** 按运行说明执行小规模配置，追踪一个概率估计量怎样从方法变成数值结果。

**Try:** Follow the documented smoke run and trace one estimated probability from the method to the generated result.

[中文讲义](cases/1904.10246/note/reproduction-note.zh-CN.md) · [English note](cases/1904.10246/note/reproduction-note.en.md) · [Derivation / 推导](cases/1904.10246/docs/DERIVATION.md) · [Run / 运行](cases/1904.10246/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/1904.10246/outputs/checks/completion_assessment.json).

[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-quantum-computing)


<a id="learn-quantum-information"></a>

## 量子信息、基础问题与精密测量 / Quantum information, foundations & sensing

**先修知识：** 密度矩阵、本征值、偏迹与熵；能用 Python 做小矩阵计算。

**Prerequisites:** Density matrices, eigenvalues, partial traces and entropy; small matrix calculations in Python.

### 1. [Entanglement of Formation of an Arbitrary State of Two Qubits](cases/quant-ph-9709029/README.md)

把两比特纠缠公式变成能直接计算的量。 / Turn a two-qubit entanglement formula into a numerical observable.

**动手任务：** 找到输入密度矩阵，沿代码检查 concurrence 的计算过程，并比较两个示例态。

**Try:** Identify the input density matrix and follow its transformation through the concurrence calculation; compare two example states.

[中文讲义](cases/quant-ph-9709029/note/reproduction-note.zh-CN.md) · [English note](cases/quant-ph-9709029/note/reproduction-note.en.md) · [Derivation / 推导](cases/quant-ph-9709029/docs/DERIVATION.md) · [Run / 运行](cases/quant-ph-9709029/code/README.md)

Recorded status / 已记录状态: **Scientific reproduction — independent review pending**. [Evidence and remaining work / 证据与待完成工作](cases/quant-ph-9709029/outputs/checks/completion_assessment.json).

### 2. [Quantum Discord and the Power of One Qubit](cases/0709.0548/README.md)

从纠缠继续理解量子失谐。 / Extend the discussion from entanglement to quantum discord.

**动手任务：** 说明案例测量的是哪类关联，以及计算中使用了什么优化或近似。

**Try:** Write down which correlations the case measures and which optimization or approximation it uses.

[中文讲义](cases/0709.0548/note/reproduction-note.zh-CN.md) · [English note](cases/0709.0548/note/reproduction-note.en.md) · [Derivation / 推导](cases/0709.0548/docs/DERIVATION.md) · [Run / 运行](cases/0709.0548/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/0709.0548/outputs/checks/completion_assessment.json).

[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-quantum-information)


<a id="learn-many-body"></a>

## 多体物理、相变与非平衡动力学 / Many-body physics, phases & nonequilibrium dynamics

**先修知识：** 自旋哈密顿量、本征态和基本相变概念；理解有限尺寸数值计算。

**Prerequisites:** Spin Hamiltonians, eigenstates and basic phase transitions; finite-size numerical calculations.

### 1. [Dynamics of a Quantum Phase Transition](cases/cond-mat-0503511/README.md)

从一个动力学量子相变计算入手。 / Follow a dynamical quantum phase-transition calculation.

**动手任务：** 按小规模运行说明，找出控制参数、观测量和有限尺寸限制。

**Try:** Use the small-run instructions to identify the control parameter, observable and finite-size limitations.

[中文讲义](cases/cond-mat-0503511/note/reproduction-note.zh-CN.md) · [English note](cases/cond-mat-0503511/note/reproduction-note.en.md) · [Derivation / 推导](cases/cond-mat-0503511/docs/DERIVATION.md) · [Run / 运行](cases/cond-mat-0503511/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/cond-mat-0503511/outputs/checks/completion_assessment.json).

### 2. [Dynamics of a Quantum Phase Transition: Exact Solution of the Quantum Ising Model](cases/cond-mat-0509490/README.md)

继续把数值计算与量子 Ising 模型的精确解联系起来。 / Connect the numerical calculation to the exact quantum Ising solution.

**动手任务：** 比较两篇论文的假设，找出一个能相互核验的极限。

**Try:** Compare the assumptions of the two papers and identify one limit where their descriptions can be checked against each other.

[中文讲义](cases/cond-mat-0509490/note/reproduction-note.zh-CN.md) · [English note](cases/cond-mat-0509490/note/reproduction-note.en.md) · [Derivation / 推导](cases/cond-mat-0509490/docs/DERIVATION.md) · [Run / 运行](cases/cond-mat-0509490/code/README.md)

Recorded status / 已记录状态: **Scientific reproduction — independent review pending**. [Evidence and remaining work / 证据与待完成工作](cases/cond-mat-0509490/outputs/checks/completion_assessment.json).

[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-many-body)


<a id="learn-topology-materials"></a>

## 拓扑、非厄米、材料与输运 / Topology, non-Hermitian physics, materials & transport

**先修知识：** 本征值问题、晶格哈密顿量、复数与边界条件。

**Prerequisites:** Eigenvalue problems, lattice Hamiltonians, complex numbers and boundary conditions.

### 1. [Edge states and topological invariants of non-Hermitian systems](cases/1803.01876/README.md)

把一维晶格模型与边界态、绕数联系起来。 / Connect a one-dimensional lattice model to edge states and a winding number.

**动手任务：** 执行案例当前的小规模配置，把一个绕数结果追溯到公式；将小规模运行与论文尺度验收区分开。

**Try:** Run the documented reduced-scale configuration and trace one winding-number result to its formula. Keep the small-run result distinct from paper-scale validation.

[中文讲义](cases/1803.01876/note/reproduction-note.zh-CN.md) · [English note](cases/1803.01876/note/reproduction-note.en.md) · [Derivation / 推导](cases/1803.01876/docs/DERIVATION.md) · [Run / 运行](cases/1803.01876/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/1803.01876/outputs/checks/completion_assessment.json).

### 2. [Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](cases/physics-9712001/README.md)

进一步研究非厄米算符与能谱的关系。 / Explore the relation between non-Hermitian operators and their spectra.

**动手任务：** 找出小规模配置中的离散化或截断，设计一项收敛检查。

**Try:** Identify the discretization or truncation used in the smoke configuration and propose a convergence check.

[中文讲义](cases/physics-9712001/note/reproduction-note.zh-CN.md) · [English note](cases/physics-9712001/note/reproduction-note.en.md) · [Derivation / 推导](cases/physics-9712001/docs/DERIVATION.md) · [Run / 运行](cases/physics-9712001/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/physics-9712001/outputs/checks/completion_assessment.json).

[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-topology-materials)


<a id="learn-amo-field"></a>

## 原子、光学、光子学与场论 / Atomic, optical, photonic & field physics

**先修知识：** 两能级系统、干涉、衰减与常微分方程；了解基本数值积分。

**Prerequisites:** Two-level systems, interference, decay and ordinary differential equations; basic numerical integration.

### 1. [Decoherence-Free Interaction between Giant Atoms in Waveguide QED](cases/1711.08863/README.md)

把波导耦合几何与相互作用、衰减联系起来。 / Relate waveguide coupling geometry to interaction and decay.

**动手任务：** 选择一条生成曲线，从几何相关的系数追到最终观测量。

**Try:** Trace one of the generated curves from its geometry-dependent coefficients to the plotted observable.

[中文讲义](cases/1711.08863/note/reproduction-note.zh-CN.md) · [English note](cases/1711.08863/note/reproduction-note.en.md) · [Derivation / 推导](cases/1711.08863/docs/DERIVATION.md) · [Run / 运行](cases/1711.08863/code/README.md)

Recorded status / 已记录状态: **Scientific reproduction — independent review pending**. [Evidence and remaining work / 证据与待完成工作](cases/1711.08863/outputs/checks/completion_assessment.json).

### 2. [Nonreciprocal Photon Blockade](cases/1807.10084/README.md)

继续进入光子阻塞的开放系统模型。 / Move on to an open-system model of photon blockade.

**动手任务：** 找出用来判断光子阻塞的观测量，追踪一个模型参数对数值输出的作用。

**Try:** Identify the observable used to diagnose blockade and trace one model parameter to the numerical output.

[中文讲义](cases/1807.10084/note/reproduction-note.zh-CN.md) · [English note](cases/1807.10084/note/reproduction-note.en.md) · [Derivation / 推导](cases/1807.10084/docs/DERIVATION.md) · [Run / 运行](cases/1807.10084/code/README.md)

Recorded status / 已记录状态: **Partial scientific reproduction**. [Evidence and remaining work / 证据与待完成工作](cases/1807.10084/outputs/checks/completion_assessment.json).

[Continue in this collection / 浏览这个方向的全部论文](CASES.md#collection-amo-field)
