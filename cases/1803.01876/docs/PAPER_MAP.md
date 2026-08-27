# Paper Map: arXiv 1803.01876

## Identity

- arXiv: 1803.01876
- Title: Edge states and topological invariants of non-Hermitian systems
- Formal publication: *Edge States and Topological Invariants of Non-Hermitian Systems*, Phys. Rev. Lett. 121, 086803 (2018)
- Publication DOI: `10.1103/PhysRevLett.121.086803`
- Pilot scope: non-Hermitian SSH model, open-boundary spectra, and the first
  figure-family reproduction loop.

## Local Sources

- PDF: `../raw/paper.pdf`
- TeX: `../paper-source/nonHermitian.tex`
- Source figures: `../paper-source/*.eps`

## Core Model Extracted From TeX

The main model is the non-Hermitian SSH Hamiltonian. The Bloch Hamiltonian is

```text
H(k) = d_x sigma_x + (d_y + i gamma/2) sigma_y
d_x = t1 + (t2 + t3) cos(k)
d_y = (t2 - t3) sin(k)
```

The first pilot uses the simplified case `t3 = 0`, as the paper does before
introducing the generalized Brillouin zone machinery for nonzero `t3`.

The real-space bulk equations for `t3 = 0` are:

```text
t2 psi_{n-1,B} + (t1 + gamma/2) psi_{n,B} = E psi_{n,A}
(t1 - gamma/2) psi_{n,A} + t2 psi_{n+1,A} = E psi_{n,B}
```

This fixes the open-chain Hamiltonian convention used in `src/nonhermitian_ssh.py`.

## Whole-paper Item Inventory

W1 全文复核按可独立裁决的 panel/series 原子化，而不是沿用整图分组：

| Source | Display items | Numeric items | Target |
| --- | ---: | ---: | --- |
| Fig. 1 | 1 | 0 | excluded schematic |
| Fig. 2(a-d) | 4 | 4 | T001 |
| Fig. 3(a-c) | 6 | 6 | T002 |
| Fig. 4 | 1 | 1 | T003 |
| Fig. 5(a-b) | 3 | 3 | T004 |
| Supplemental Fig. 6 | 6 | 6 | T005 |
| Supplemental Fig. 7 | 2 | 2 | T005 |

因此共有 23 个 display items：22 个理论/解析数值项全部已有独立数据绑定，
1 个示意图明确排除。Fig. 3(b) 的单位圆虽是 supporting comparator，仍能由
解析式独立生成，所以保留在数值分母，不能以“只是参考线”为由删除。

全文另有 3 个无显示承载的独立定量 claim：

- T006：两个零模在三个精确 `t1` 区间中的端点迁移；当前未覆盖；
- T007：多带情形 `W=sum_l W^(l)`；当前未覆盖；
- T008：对 Ref. 49 零模区间的明确纠错；当前缺引用论文的完整科学输入。

总计 25 个 eligible items、22 covered、3 uncovered，coverage 为 88.00%。

## Historical Pilot Choice

Start with Fig. 2(a-c): this in-scope numerical target is directly tied to a
finite matrix diagonalization and has clear parameters in the caption. It is the
best first test of the paper-to-code loop.
