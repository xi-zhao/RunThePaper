# Numerical Methods

## Core numerical object

对每个 `(L,W,realization)` 构造开边界稀疏 Anderson Hamiltonian，再用 float64 全对角化。只保留谱中心 20% 作为外层 `n` 状态，但 fidelity susceptibility 对内层 `m` 使用完整谱。

## Operator boundary

- `T_s`：使用论文给出的 next-nearest sublattice hopping，并单独加入 `[-0.15,0.15]` boundary disorder；
- `T`：nearest-neighbor kinetic operator，不加 boundary disorder；
- `n`：从一个 L=38 冻结随机场裁剪并去迹。论文未公布随机配置及裁剪规则，因此参数状态是 reconstructed，而不是 paper-exact。

## Memory strategy

Hamiltonian 以 sparse 形式构造，eigh 前转 dense。operator 以 sparse matrix 作用于 eigenvectors；随后按 central-state block 计算 `O_nm`，只保留 susceptibility、spectral bins、spacing、IPR 和 histogram sufficient statistics，不持久化本征矢。

## Scientific outputs

- unregularized / regularized typical and average susceptibility；
- rescaled quantities；
- full/central spectrum spacing and gap ratio；
- spectral-function weighted bins；
- `log10 chi_n` histogram；
- `T_s` 与 `n` 的强无序微扰基线。

数值 runner 明确禁止读取论文原图、作者代码或作者数值数组。
