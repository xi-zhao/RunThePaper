<h1 align="center">RunThePaper</h1>

<p align="center"><strong>From papers to runnable, checkable, and extendable science.</strong></p>

<p align="center">
  <strong>English</strong> ·
  <a href="README.zh-CN.md">Simplified Chinese</a>
</p>

<p align="center">
  <a href="#reproduction-catalog">Explore cases</a> ·
  <a href="#why-this-exists">Why this exists</a> ·
  <a href="#infrastructure-model">Infrastructure</a> ·
  <a href="https://github.com/xi-zhao/runthepaper/issues/new">Request a paper</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

A paper is a highly compressed record of research. Formulas remain in the main
text, parameters are scattered across captions and supplements, and rerunning a
result often requires judgments that were never written down.

RunThePaper unfolds that compressed process. Each case corresponds to an
identifiable paper and combines an explanatory note, runnable code, generated
results, machine-readable checks, and an explicit remaining boundary. Start
with one figure, or use the case as the beginning of the next investigation.

RunThePaper is community-built infrastructure for executable paper
reproductions: a public place where research cases can be read, rerun, checked,
and extended.

The 100 cases here are not 100 completion trophies. Partial reproductions,
missing public inputs, compute limits, invalid runs, and pending independent
review remain visible. Useful scientific infrastructure should preserve
uncertainty, not polish it away.

| If you want to... | Start here |
| --- | --- |
| Understand a paper | Open its explanatory note |
| Rerun a result | Open the code, figures, and checks |
| Build on existing work | Read the boundary, then contribute a correction, review, or extension |

Standalone benchmarks, synthetic exercises, source-contract audits, and
internal evaluations are not published as paper cases.

<a id="why-this-exists"></a>

## Why This Exists

Research has both a productivity bottleneck and a collaboration bottleneck.
AI can accelerate reading, reasoning, coding, and analysis, but the paper is
still a compressed record rather than a complete working context. Derivations,
parameters, failed attempts, and validation evidence are often lost between
teams.

Generation is becoming cheaper; verification is not. Scientific agents may
produce more hypotheses, programs, and results than researchers can inspect.
The scarce output is therefore not merely an answer, but an answer that is
checkable, understandable, and reusable.

> Before asking AI to discover unknown science, we should test whether it can
> reliably reconstruct, execute, and audit known science.

RunThePaper starts with reproduction because reproduction tests understanding,
execution, and verification together. Each public case unfolds a paper into a
new unit of research delivery: a clear paper identity and claim scope,
derivation, code, generated data, machine checks, review state, and remaining
boundary.

## Reproduction Catalog

<!-- case-catalog:start -->
**100 public cases, organized as research collections.** Each paper is
placed on one primary path even when its ideas cross several fields.

Choose a collection to open its catalog, or use the [detailed index](CASES.md)
for paper identities, scores, and reproduction boundaries.

**Jump to a collection**

- [Quantum computing, algorithms & error correction (25)](#collection-quantum-computing)
- [Quantum information, foundations & sensing (18)](#collection-quantum-information)
- [Many-body physics, phases & nonequilibrium dynamics (27)](#collection-many-body)
- [Topology, non-Hermitian physics, materials & transport (21)](#collection-topology-materials)
- [Atomic, optical, photonic & field physics (9)](#collection-amo-field)

<a id="collection-quantum-computing"></a>

<details>
<summary><strong>Quantum computing, algorithms & error correction (25)</strong></summary>

Circuit compilation, quantum simulation, fault tolerance, and error mitigation as runnable research cases.

| Paper | Reproduced focus | Status | Open |
| --- | --- | --- | --- |
| [Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices](cases/10.1145-3297858.3304023/README.md) | SABRE qubit mapping and routing | Partial scientific reproduction | [Note](cases/10.1145-3297858.3304023/note/reproduction-note.en.md) · [Code](cases/10.1145-3297858.3304023/code/README.md) |
| [Simulating the Sycamore quantum supremacy circuits](cases/2103.03074/README.md) | Sycamore random-circuit simulation | Partial scientific reproduction | [Note](cases/2103.03074/note/reproduction-note.en.md) · [Code](cases/2103.03074/code/README.md) |
| [Efficient simulation of logical magic state preparation protocols](cases/2512.23799/README.md) | Logical magic-state preparation simulation | Partial scientific reproduction | [Note](cases/2512.23799/note/reproduction-note.en.md) · [Code](cases/2512.23799/code/README.md) |
| [Boson Sampling as a Probe of Chaotic and Integrable Quantum Dynamics](cases/2605.25398/README.md) | Boson sampling and quantum-chaos probes | Partial scientific reproduction | [Note](cases/2605.25398/note/reproduction-note.en.md) · [Code](cases/2605.25398/code/README.md) |
| [Buffer-atom-mediated quantum logic gates with off-resonant modulated driving](cases/10.1007-s11433-024-2478-8/README.md) | Buffer-atom-mediated Rydberg CZ, dual-pulse Doppler upgrade, and amplitude-ratio robustness via off-resonant modulated driving | Partial scientific reproduction | [Note](cases/10.1007-s11433-024-2478-8/note/reproduction-note.en.md) · [Code](cases/10.1007-s11433-024-2478-8/code/README.md) |
| [Strongly correlated quantum walks with a 12-qubit superconducting processor](cases/10.1126-science.aaw1611/README.md) | Strongly interacting one- and two-photon quantum walks on a calibrated superconducting-qubit chain | Partial scientific reproduction | [Note](cases/10.1126-science.aaw1611/note/reproduction-note.en.md) · [Code](cases/10.1126-science.aaw1611/code/README.md) |
| [Benchmarking and Fidelity Response Theory of High-Fidelity Rydberg Entangling Gates](cases/10.1103-PRXQuantum.6.010331/README.md) | Fidelity-response theory and protocol-level noise susceptibility of high-fidelity Rydberg CZ gates | Partial scientific reproduction | [Note](cases/10.1103-PRXQuantum.6.010331/note/reproduction-note.en.md) · [Code](cases/10.1103-PRXQuantum.6.010331/code/README.md) |
| [Thermodynamics of Quantum Reservoir Computing](cases/2607.02157/README.md) | Non-equilibrium thermodynamic limits of driven open quantum reservoirs; generalized Landauer bound and information-dissipation identity | Partial scientific reproduction | [Note](cases/2607.02157/note/reproduction-note.en.md) · [Code](cases/2607.02157/code/README.md) |
| [Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms](cases/2502.20558/README.md) | Delayed-erasure decoding, qubit lifecycle reduction, and loss-aware fault-tolerant quantum algorithms | Partial scientific reproduction | [Note](cases/2502.20558/note/reproduction-note.en.md) · [Code](cases/2502.20558/code/README.md) |
| [Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate](cases/2607.15597/README.md) | Rydberg atom-ion geometric gates, multi-ion mode closure, deterministic interconnect timing, and hybrid qLDPC memory | Scientific reproduction — invalid | [Note](cases/2607.15597/note/reproduction-note.en.md) · [Code](cases/2607.15597/code/README.md) |
| [Programmable Open Quantum Systems](cases/2512.08279/README.md) | Programmable Lindblad dynamics, signed quantum-channel sampling, and error-dependent retrieval cost | Partial scientific reproduction | [Note](cases/2512.08279/note/reproduction-note.en.md) · [Code](cases/2512.08279/code/README.md) |
| [Quantum Error Correction in Scrambling Dynamics and Measurement-Induced Phase Transition](cases/1903.05124/README.md) | Formula-derived Clifford/stabilizer reproduction of scrambling-enabled quantum error correction and measurement-induced criticality | Scientific reproduction — invalid | [Note](cases/1903.05124/note/reproduction-note.en.md) · [Code](cases/1903.05124/code/README.md) |
| [Demonstrating quantum error mitigation on logical qubits](cases/10.1038-s41467-025-67768-4/README.md) | Feedback/post-selection expectation under amplified Pauli injection. | Scientific reproduction — invalid | [Note](cases/10.1038-s41467-025-67768-4/note/reproduction-note.en.md) · [Code](cases/10.1038-s41467-025-67768-4/code/README.md) |
| [Amplitude Estimation without Phase Estimation](cases/1904.10246/README.md) | quantum algorithms; amplitude estimation; maximum likelihood | Scientific reproduction — invalid | [Note](cases/1904.10246/note/reproduction-note.en.md) · [Code](cases/1904.10246/code/README.md) |
| [Graph coloring via quantum optimization on a Rydberg-qudit atom array](cases/2504.08598/README.md) | k=3 target-coloring probability versus annealing time and final E/F basis distributions | Scientific reproduction — invalid | [Note](cases/2504.08598/note/reproduction-note.en.md) · [Code](cases/2504.08598/code/README.md) |
| [Remote Entanglement Generation Via Enhanced Quantum State Transfer](cases/2506.06669/README.md) | quantum state transfer; remote entanglement; superconducting quantum processors | Scientific reproduction — invalid | [Note](cases/2506.06669/note/reproduction-note.en.md) · [Code](cases/2506.06669/code/README.md) |
| [Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors](cases/2607.08212/README.md) | neutral atoms; quantum compilation; hardware-software codesign | Partial scientific reproduction | [Note](cases/2607.08212/note/reproduction-note.en.md) · [Code](cases/2607.08212/code/README.md) |
| [Plaquette: A hardware-aware design platform for fault-tolerant quantum computers](cases/2607.08767/README.md) | Fault-tolerant quantum computing; Pauli twirling; hardware-aware quantum error-correction simulation | Partial scientific reproduction | [Note](cases/2607.08767/note/reproduction-note.en.md) · [Code](cases/2607.08767/code/README.md) |
| [Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search](cases/2607.27060/README.md) | open quantum systems; Trotter-Suzuki product formulas; quantum resource estimation | Scientific reproduction — invalid | [Note](cases/2607.27060/note/reproduction-note.en.md) · [Code](cases/2607.27060/code/README.md) |
| [High-rate qLDPC processors](cases/2607.28795/README.md) | Mitten-code algebraic parameters and canonical logical weights. | Scientific reproduction — invalid | [Note](cases/2607.28795/note/reproduction-note.en.md) · [Code](cases/2607.28795/code/README.md) |
| [Realified tensor networks: quantum circuit simulation on real-valued matrix accelerators](cases/2608.03987/README.md) | Realification cost laws and contraction-order transferability for quantum-circuit tensor networks | Partial scientific reproduction | [Note](cases/2608.03987/note/reproduction-note.en.md) · [Code](cases/2608.03987/code/README.md) |
| [Quantum machine learning in feature Hilbert spaces](cases/1803.07128/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1803.07128/note/reproduction-note.en.md) · [Code](cases/1803.07128/code/README.md) |
| [A random compiler for fast Hamiltonian simulation](cases/1811.08017/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [Note](cases/1811.08017/note/reproduction-note.en.md) · [Code](cases/1811.08017/code/README.md) |
| [Obstacles to State Preparation and Variational Optimization from Symmetry Protection](cases/1910.08980/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1910.08980/note/reproduction-note.en.md) · [Code](cases/1910.08980/code/README.md) |
| [Universal Quantum Computation with Ideal Clifford Gates and Noisy Ancillas](cases/quant-ph-0403025/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/quant-ph-0403025/note/reproduction-note.en.md) · [Code](cases/quant-ph-0403025/code/README.md) |

</details>

<a id="collection-quantum-information"></a>

<details>
<summary><strong>Quantum information, foundations & sensing (18)</strong></summary>

Entanglement, quantum resources, open systems, foundations, and sensing with inspectable derivations and results.

| Paper | Reproduced focus | Status | Open |
| --- | --- | --- | --- |
| [Particle exchange statistics beyond fermions and bosons](cases/10.1038-s41586-024-08262-7/README.md) | Paraparticle exclusion statistics, thermodynamics, and exactly solvable spin models | Partial scientific reproduction | [Note](cases/10.1038-s41586-024-08262-7/note/reproduction-note.en.md) · [Code](cases/10.1038-s41586-024-08262-7/code/README.md) |
| [Sufficient Wigner Negativity Implies Genuine Multipartite Entanglement](cases/2510.26761/README.md) | Continuous-variable genuine multipartite entanglement witnesses from finite Wigner and characteristic-function measurements | Partial scientific reproduction | [Note](cases/2510.26761/note/reproduction-note.en.md) · [Code](cases/2510.26761/code/README.md) |
| [Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking](cases/2607.00718/README.md) | Squeezed-reservoir nonreciprocity, Gaussian quantum batteries, ergotropy, and optical isolation | Partial scientific reproduction | [Note](cases/2607.00718/note/reproduction-note.en.md) · [Code](cases/2607.00718/code/README.md) |
| [Information and Majorization Theory for Fermionic Phase-Space Distributions](cases/2401.08523/README.md) | quantum information; fermionic phase space; majorization; uncertainty relations | Partial scientific reproduction | [Note](cases/2401.08523/note/reproduction-note.en.md) · [Code](cases/2401.08523/code/README.md) |
| [Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation](cases/2602.12212/README.md) | Spin-1 minimum-variance leaf geometry and leaf-canonical curves. | Partial scientific reproduction | [Note](cases/2602.12212/note/reproduction-note.en.md) · [Code](cases/2602.12212/code/README.md) |
| [Fixed-detector tilt--defocus sensing by upstream source coding in a time-reversed Young interferometer](cases/2605.02873/README.md) | physical optics; Fisher information; wavefront sensing | Scientific reproduction — invalid | [Note](cases/2605.02873/note/reproduction-note.en.md) · [Code](cases/2605.02873/code/README.md) |
| [Photonic Violation of Wigner's Inequality](cases/2606.30255/README.md) | quantum foundations; quantum optics; polarization entanglement | Scientific reproduction — invalid | [Note](cases/2606.30255/note/reproduction-note.en.md) · [Code](cases/2606.30255/code/README.md) |
| [Non-Hermitian-enhanced quantum sensing in an optical interferometer](cases/2607.23978/README.md) | Optimal Hermitian and non-Hermitian interferometric fringe baselines. | Partial scientific reproduction | [Note](cases/2607.23978/note/reproduction-note.en.md) · [Code](cases/2607.23978/code/README.md) |
| [Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit](cases/2401.05830/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2401.05830/note/reproduction-note.en.md) · [Code](cases/2401.05830/code/README.md) |
| [Optimal Generators for Quantum Sensing](cases/2305.15556/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [Note](cases/2305.15556/note/reproduction-note.en.md) · [Code](cases/2305.15556/code/README.md) |
| [New Constraints on Axion-Mediated Spin Interactions Using Magnetic Amplification](cases/PhysRevLett.133.191801/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/PhysRevLett.133.191801/note/reproduction-note.en.md) · [Code](cases/PhysRevLett.133.191801/code/README.md) |
| [Precision-Spectroscopic Determination of the Binding Energy of a Two-Body Quantum System: The Hydrogen Atom and the Proton-Size Puzzle](cases/PhysRevLett.132.113001/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/PhysRevLett.132.113001/note/reproduction-note.en.md) · [Code](cases/PhysRevLett.132.113001/code/README.md) |
| [Squeezed Spin States](cases/PhysRevA.47.5138/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [Note](cases/PhysRevA.47.5138/note/reproduction-note.en.md) · [Code](cases/PhysRevA.47.5138/code/README.md) |
| [Entanglement in Quantum Critical Phenomena](cases/quant-ph-0211074/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/quant-ph-0211074/note/reproduction-note.en.md) · [Code](cases/quant-ph-0211074/code/README.md) |
| [Entanglement of Formation of an Arbitrary State of Two Qubits](cases/quant-ph-9709029/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/quant-ph-9709029/note/reproduction-note.en.md) · [Code](cases/quant-ph-9709029/code/README.md) |
| [Necessary and Sufficient Condition for Nonzero Quantum Discord](cases/1004.0190/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/1004.0190/note/reproduction-note.en.md) · [Code](cases/1004.0190/code/README.md) |
| [Quantum Speed Limit for Non-Markovian Dynamics](cases/1302.5069/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/1302.5069/note/reproduction-note.en.md) · [Code](cases/1302.5069/code/README.md) |
| [Quantum Discord and the Power of One Qubit](cases/0709.0548/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/0709.0548/note/reproduction-note.en.md) · [Code](cases/0709.0548/code/README.md) |

</details>

<a id="collection-many-body"></a>

<details>
<summary><strong>Many-body physics, phases & nonequilibrium dynamics (27)</strong></summary>

Time crystals, many-body scars, quantum phase transitions, and thermalization turned into executable calculations.

| Paper | Reproduced focus | Status | Open |
| --- | --- | --- | --- |
| [Discrete time crystals: rigidity, criticality, and realizations](cases/1608.02589/README.md) | Floquet many-body dynamics and discrete time crystals | Partial scientific reproduction | [Note](cases/1608.02589/note/reproduction-note.en.md) · [Code](cases/1608.02589/code/README.md) |
| [Quantum many-body scars](cases/1711.03528/README.md) | PXP dynamics and quantum many-body scars | Partial scientific reproduction | [Note](cases/1711.03528/note/reproduction-note.en.md) · [Code](cases/1711.03528/code/README.md) |
| [Localization Driven Superradiant Instability](cases/10.1103-PhysRevLett.124.113601/README.md) | Aubry–André localization, cavity susceptibility, and superradiant instability | Partial scientific reproduction | [Note](cases/10.1103-PhysRevLett.124.113601/note/reproduction-note.en.md) · [Code](cases/10.1103-PhysRevLett.124.113601/code/README.md) |
| [Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain](cases/2510.12880/README.md) | Exact algebraic and finite-size validation of the frustration-free 2^N+1 ground-state manifold. | Partial scientific reproduction | [Note](cases/2510.12880/note/reproduction-note.en.md) · [Code](cases/2510.12880/code/README.md) |
| [Dissipative Phase Transition in the Two-Photon Dicke Model](cases/2412.14271/README.md) | Two-photon Dicke model, dissipative phase transitions, quantum trajectories, and nonlinear stability | Partial scientific reproduction | [Note](cases/2412.14271/note/reproduction-note.en.md) · [Code](cases/2412.14271/code/README.md) |
| [Boundary time crystals](cases/1708.05014/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1708.05014/note/reproduction-note.en.md) · [Code](cases/1708.05014/code/README.md) |
| [Exploring the Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice](cases/1709.03478/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1709.03478/note/reproduction-note.en.md) · [Code](cases/1709.03478/code/README.md) |
| [Self-Bound Quantum Droplets of Atomic Mixtures in Free Space](cases/1710.10890/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1710.10890/note/reproduction-note.en.md) · [Code](cases/1710.10890/code/README.md) |
| [Symmetry-resolved entanglement in many-body systems](cases/1711.09418/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [Note](cases/1711.09418/note/reproduction-note.en.md) · [Code](cases/1711.09418/code/README.md) |
| [Exact Spectral Form Factor in a Minimal Model of Many-Body Quantum Chaos](cases/1805.00931/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1805.00931/note/reproduction-note.en.md) · [Code](cases/1805.00931/code/README.md) |
| [Periodic Orbits, Entanglement, and Quantum Many-Body Scars in Constrained Models: Matrix Product State Approach](cases/1807.01815/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1807.01815/note/reproduction-note.en.md) · [Code](cases/1807.01815/code/README.md) |
| [Hydrodynamic Diffusion in Integrable Systems](cases/1807.02414/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1807.02414/note/reproduction-note.en.md) · [Code](cases/1807.02414/code/README.md) |
| [Emergent SU(2) dynamics and perfect quantum many-body scars](cases/1812.05561/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1812.05561/note/reproduction-note.en.md) · [Code](cases/1812.05561/code/README.md) |
| [Scalable probes of measurement-induced criticality](cases/1910.00020/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1910.00020/note/reproduction-note.en.md) · [Code](cases/1910.00020/code/README.md) |
| [Entanglement transition in a monitored free fermion chain -- from extended criticality to area law](cases/2005.09722/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2005.09722/note/reproduction-note.en.md) · [Code](cases/2005.09722/code/README.md) |
| [Exact Quantum Many-Body Scar States in the Rydberg-Blockaded Atom Chain](cases/1810.00888/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/1810.00888/note/reproduction-note.en.md) · [Code](cases/1810.00888/code/README.md) |
| [Realization of a Laughlin State of Two Rapidly Rotating Fermions](cases/2402.14814/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2402.14814/note/reproduction-note.en.md) · [Code](cases/2402.14814/code/README.md) |
| [Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances](cases/2409.18176/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2409.18176/note/reproduction-note.en.md) · [Code](cases/2409.18176/code/README.md) |
| [Measurement-Induced Dark State Phase Transitions in Long-Ranged Fermion Systems](cases/2105.08076/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2105.08076/note/reproduction-note.en.md) · [Code](cases/2105.08076/code/README.md) |
| [Thermodynamics of Quantum Jump Trajectories](cases/0911.0556/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/0911.0556/note/reproduction-note.en.md) · [Code](cases/0911.0556/code/README.md) |
| [Exact nonequilibrium steady state of a strongly driven open XXZ chain](cases/1106.2978/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/1106.2978/note/reproduction-note.en.md) · [Code](cases/1106.2978/code/README.md) |
| [Phase Structure of Driven Quantum Systems](cases/1508.03344/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1508.03344/note/reproduction-note.en.md) · [Code](cases/1508.03344/code/README.md) |
| [Dynamics of a Quantum Phase Transition](cases/cond-mat-0503511/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/cond-mat-0503511/note/reproduction-note.en.md) · [Code](cases/cond-mat-0503511/code/README.md) |
| [Localization of Interacting Fermions at High Temperature](cases/cond-mat-0610854/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/cond-mat-0610854/note/reproduction-note.en.md) · [Code](cases/cond-mat-0610854/code/README.md) |
| [Dynamics of a Quantum Phase Transition: Exact Solution of the Quantum Ising Model](cases/cond-mat-0509490/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/cond-mat-0509490/note/reproduction-note.en.md) · [Code](cases/cond-mat-0509490/code/README.md) |
| [Large-N Scaling Behavior of the Lipkin-Meshkov-Glick Model](cases/quant-ph-0507004/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/quant-ph-0507004/note/reproduction-note.en.md) · [Code](cases/quant-ph-0507004/code/README.md) |
| [Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model](cases/1206.2505/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/1206.2505/note/reproduction-note.en.md) · [Code](cases/1206.2505/code/README.md) |

</details>

<a id="collection-topology-materials"></a>

<details>
<summary><strong>Topology, non-Hermitian physics, materials & transport (21)</strong></summary>

Spectra, phase diagrams, boundary states, and response functions across topology, materials, and transport.

| Paper | Reproduced focus | Status | Open |
| --- | --- | --- | --- |
| [Edge states and topological invariants of non-Hermitian systems](cases/1803.01876/README.md) | Non-Hermitian SSH model and non-Bloch bulk-boundary correspondence | Partial scientific reproduction | [Note](cases/1803.01876/note/reproduction-note.en.md) · [Code](cases/1803.01876/code/README.md) |
| [Non-Hermitian Chern bands](cases/1804.04672/README.md) | Non-Hermitian Chern bands and non-Bloch Chern physics | Partial scientific reproduction | [Note](cases/1804.04672/note/reproduction-note.en.md) · [Code](cases/1804.04672/code/README.md) |
| [Sensitivity to perturbations in the three-dimensional Anderson model](cases/2605.25594/README.md) | Three-dimensional Anderson localization | Partial scientific reproduction | [Note](cases/2605.25594/note/reproduction-note.en.md) · [Code](cases/2605.25594/code/README.md) |
| [Lyapunov formulation of band theory for disordered non-Hermitian systems](cases/2507.09447/README.md) | Lyapunov band theory and the non-Hermitian skin–Anderson transition | Partial scientific reproduction | [Note](cases/2507.09447/note/reproduction-note.en.md) · [Code](cases/2507.09447/code/README.md) |
| [Interband coherence induced correction to adiabatic pumping in periodically driven systems](cases/10.1103-PhysRevB.91.085420/README.md) | Interband-coherence correction to adiabatic pumping in the continuously driven Harper model | Partial scientific reproduction | [Note](cases/10.1103-PhysRevB.91.085420/note/reproduction-note.en.md) · [Code](cases/10.1103-PhysRevB.91.085420/code/README.md) |
| [Geometry-adaptive formulation of non-Bloch bands in arbitrary dimensions and spectral instability](cases/2407.01296/README.md) | Geometry-adaptive non-Bloch bands, non-Hermitian skin effect, and spectral instability | Partial scientific reproduction | [Note](cases/2407.01296/note/reproduction-note.en.md) · [Code](cases/2407.01296/code/README.md) |
| [Topological Band Theory for Non-Hermitian Hamiltonians](cases/1706.07435/README.md) | Equation-level reproduction of non-Hermitian topology, exceptional points, domain-wall states, and lattice cylinder spectra | Partial scientific reproduction | [Note](cases/1706.07435/note/reproduction-note.en.md) · [Code](cases/1706.07435/code/README.md) |
| [Topological Phase Transition in Non-Hermitian Quasicrystals](cases/1905.09460/README.md) | non-Hermitian physics; quasicrystals; topological phase transitions; mode-locked lasers | Partial scientific reproduction | [Note](cases/1905.09460/note/reproduction-note.en.md) · [Code](cases/1905.09460/code/README.md) |
| [Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath](cases/2511.11394/README.md) | Small-q dissipative approach toward the Dirichlet/Chern bound. | Partial scientific reproduction | [Note](cases/2511.11394/note/reproduction-note.en.md) · [Code](cases/2511.11394/code/README.md) |
| [Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems](cases/2607.22976/README.md) | Topological interface localization and standing/traveling profiles. | Partial scientific reproduction | [Note](cases/2607.22976/note/reproduction-note.en.md) · [Code](cases/2607.22976/code/README.md) |
| [Hubbard model physics in transition metal dichalcogenide moire bands](cases/1804.03151/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1804.03151/note/reproduction-note.en.md) · [Code](cases/1804.03151/code/README.md) |
| [Topological insulators in twisted transition metal dichalcogenide homobilayers](cases/1807.03311/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1807.03311/note/reproduction-note.en.md) · [Code](cases/1807.03311/code/README.md) |
| [All "Magic Angles" Are "Stable" Topological](cases/1807.10676/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1807.10676/note/reproduction-note.en.md) · [Code](cases/1807.10676/code/README.md) |
| [Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport](cases/2608.05312/README.md) | Open-system dark-state rescue, cavity transport, and finite-temperature mechanism competition | Partial scientific reproduction | [Note](cases/2608.05312/note/reproduction-note.en.md) · [Code](cases/2608.05312/code/README.md) |
| [Discontinuous Shear Thickening in Biological Tissue Rheology](cases/2211.15015/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2211.15015/note/reproduction-note.en.md) · [Code](cases/2211.15015/code/README.md) |
| [Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids](cases/2406.07531/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2406.07531/note/reproduction-note.en.md) · [Code](cases/2406.07531/code/README.md) |
| [Electronic correlations at paramagnetic (001) and (110) NiO surfaces: Charge-transfer and Mott-Hubbard-type gaps at the surface and subsurface of (110) NiO](cases/2101.12558/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2101.12558/note/reproduction-note.en.md) · [Code](cases/2101.12558/code/README.md) |
| [Anomalous edge states and the bulk-edge correspondence for periodically driven two-dimensional systems](cases/1212.3324/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1212.3324/note/reproduction-note.en.md) · [Code](cases/1212.3324/code/README.md) |
| [Energy Levels and Wave Functions of Bloch Electrons in Rational and Irrational Magnetic Fields](cases/PhysRevB.14.2239/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/PhysRevB.14.2239/note/reproduction-note.en.md) · [Code](cases/PhysRevB.14.2239/code/README.md) |
| [Quantum Spin Hall Effect in Graphene](cases/cond-mat-0411737/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/cond-mat-0411737/note/reproduction-note.en.md) · [Code](cases/cond-mat-0411737/code/README.md) |
| [Real Spectra in Non-Hermitian Hamiltonians Having PT Symmetry](cases/physics-9712001/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — paper-error candidates identified | [Note](cases/physics-9712001/note/reproduction-note.en.md) · [Code](cases/physics-9712001/code/README.md) |

</details>

<a id="collection-amo-field"></a>

<details>
<summary><strong>Atomic, optical, photonic & field physics (9)</strong></summary>

Atomic arrays, cavity QED, photonics, and field theory connecting models, observables, and device context.

| Paper | Reproduced focus | Status | Open |
| --- | --- | --- | --- |
| [An Algorithm for Fast Assembling Large-Scale Defect-Free Atom Arrays](cases/2604.08669/README.md) | Defect-free atom-array assembly | Partial scientific reproduction | [Note](cases/2604.08669/note/reproduction-note.en.md) · [Code](cases/2604.08669/code/README.md) |
| [Backreaction of stimulated Hawking radiation in an optical analogue](cases/10.1038-s41586-026-10720-3/README.md) | Stimulated Hawking radiation and backreaction in a fibre-optical analogue horizon | Partial scientific reproduction | [Note](cases/10.1038-s41586-026-10720-3/note/reproduction-note.en.md) · [Code](cases/10.1038-s41586-026-10720-3/code/README.md) |
| [Circuit Quantum Electrodynamics](cases/2005.12667/README.md) | Circuit quantization, Jaynes-Cummings and dispersive physics, open quantum systems, measurement, control, bosonic codes, and microwave quantum optics | Partial scientific reproduction | [Note](cases/2005.12667/note/reproduction-note.en.md) · [Code](cases/2005.12667/code/README.md) |
| [Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass](cases/2607.15070/README.md) | Casimir effect; quantum field theory; position-dependent effective mass | Scientific reproduction — invalid | [Note](cases/2607.15070/note/reproduction-note.en.md) · [Code](cases/2607.15070/code/README.md) |
| [Boundary element method for resonances in dielectric microcavities](cases/physics-0206018/README.md) | Boundary-integral scattering, resonances, and near- and far-field reconstruction in dielectric microcavities | Partial scientific reproduction | [Note](cases/physics-0206018/note/reproduction-note.en.md) · [Code](cases/physics-0206018/code/README.md) |
| [Decoherence-Free Interaction between Giant Atoms in Waveguide QED](cases/1711.08863/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Scientific reproduction — independent review pending | [Note](cases/1711.08863/note/reproduction-note.en.md) · [Code](cases/1711.08863/code/README.md) |
| [Nonreciprocal Photon Blockade](cases/1807.10084/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/1807.10084/note/reproduction-note.en.md) · [Code](cases/1807.10084/code/README.md) |
| [Exploring Atom-Ion Feshbach Resonances below the s-Wave Limit](cases/2406.13410/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2406.13410/note/reproduction-note.en.md) · [Code](cases/2406.13410/code/README.md) |
| [On-Chip Quantum Interference between Independent Lithium Niobate-on-Insulator Photon-Pair Sources](cases/2404.08378/README.md) | Independent formula, code, and data reconstruction with explicit remaining boundaries. | Partial scientific reproduction | [Note](cases/2404.08378/note/reproduction-note.en.md) · [Code](cases/2404.08378/code/README.md) |

</details>

Status describes reproduction scope, not rank. See [how to read reproduction quality](#how-to-read-reproduction-quality) and the [detailed case index](CASES.md) for paper identities, audit scores, generated figures, checks, and explicit boundaries.
<!-- case-catalog:end -->

## Run One Case

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

## What You Can Do Here

- **Understand the method.** Trace the formulas, parameters, numerical choices,
  and limitations behind a result.
- **Run and verify it.** Recompute figures, inspect generated data, and read the
  machine-readable evidence instead of judging only visual similarity.
- **Build on it.** Add a missing input, correct an error, perform an independent
  review, or use the case as a baseline for a new question.

A careful report that something cannot yet be reproduced can be as valuable as
another successful figure, provided the boundary is explicit and the evidence
is public.

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

## Build It Together

RunThePaper is not a finished showcase owned by one team. It is a unit of
scientific collaboration that a community can improve. You do not need to
reproduce an entire paper: confirming one run, correcting one formula, adding a
missing input, explaining one failure, or completing an independent review can
make the shared context more reliable.

Have a paper you want reproduced? [Open an
issue](https://github.com/xi-zhao/runthepaper/issues/new) with its title, DOI or
arXiv ID, and the figure or claim you care about most. To review or extend an
existing case, see the [contributing guide](CONTRIBUTING.md).

<a id="infrastructure-model"></a>

## The Infrastructure Model

RunThePaper treats an executable research case as the basic unit of scientific
collaboration. A case keeps the paper identity, reproduced scope, derivation,
code, run outputs, machine-readable checks, review state, and remaining boundary
together in one public object.

```text
paper
  ↓
claim and scope → derivation → code → run outputs
  ↓
checks → review state → explicit boundary
  ↓
public research case
  ↓
read → rerun → discuss → correct → extend
```

As infrastructure, RunThePaper provides operational public context, preserves
verification evidence, keeps both success and failure as shared memory, and
gives different teams a common place to rerun and extend research. It is not a
display cabinet for completed work, but a public workbench that can be run,
questioned, and improved.

The public 100-case collection is an open testbed. It shows what the current
system can and cannot turn into executable science; it is not a claim of blind
generalization to every unseen paper.

## Toward Agent4Science

Our current view of AI for Science rests on three principles.

| Principle | What it means |
| --- | --- |
| **Verification before discovery** | If an agent cannot reliably reconstruct and audit known results, there is not yet enough reason to trust its discoveries in unknown territory. |
| **Operational context before autonomy** | An agent needs more than paper text. It needs derivations, code, data, observations, tool interfaces, failed attempts, and explicit boundaries. |
| **Human judgment stays in the loop** | Researchers still choose worthwhile problems, connect work to real needs, judge scientific significance, and make the final evidence call. |

The goal is not a one-shot scientific answer. It is a research loop that can
propose, execute, observe, verify, remember, and choose the next exploration.
RunThePaper currently provides the loop's foundational executable context and
verification memory.

| Layer | Context available to agents | Boundary |
| --- | --- | --- |
| **Now** | Paper claims, detailed derivations, code, generated data and figures, machine checks, review states, and remaining boundaries | Publicly available in this repository |
| **Next** | Cross-case memory, reusable scientific skills, stronger independent review, and causal failure diagnosis | Direction of development, not a completed capability |
| **Future** | Experimental data, live observations, and safe, auditable interfaces to scientific instruments | Not provided by this repository today |

When a scientific agent starts from a checked case instead of a static PDF, it
inherits not only the conclusion but also the path and evidence behind it. We
believe this kind of infrastructure can make AI for Science more reliable, more
open, and easier to build together.

The **PRAgent** system supporting this work is still being improved. We plan to
open-source it after further refinement so that more researchers can use and
develop it together. Stay tuned.

## License

Code is licensed under the MIT License. Notes, generated figures, and generated
data are licensed under CC BY 4.0 unless a case states otherwise.

Third-party papers, source files, and original figures remain under their
original rights holders' terms and are not covered by this repository's license.
The same exclusion applies to any limited paper excerpts shown inside validation
comparison panels.
