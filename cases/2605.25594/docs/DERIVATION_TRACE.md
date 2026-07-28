# Derivation Trace

## Core Idea

论文研究的是本征态对一个小扰动的敏感程度。先写

```text
H_lambda = H_0 + lambda O
```

再问：当 `lambda` 发生一个很小变化时，同一个本征态会不会快速改变？如果变化很大，说明这个状态对扰动很敏感。

## E001: From Eigenstate Overlap To Fidelity Susceptibility

对 `H_lambda |n(lambda)> = E_n(lambda)|n(lambda)>` 做一阶微扰展开：

```text
|n(lambda + d lambda)> =
|n> + d lambda * sum_{m != n} |m> <m|O|n> / (E_n - E_m) + ...
```

重叠的二阶项给出

```text
chi_n = sum_{m != n} |<n|O|m>|^2 / (E_n - E_m)^2
```

这就是代码里的 unregularized susceptibility。实现时必须去掉 `m=n`，否则分母为零。

## E002: Regularization

原始 `chi_n` 很容易被极小能级间隔控制，不适合直接平均。论文用频率 cutoff `mu` 替换核函数：

```text
omega^2 / (omega^2 + mu^2)^2
```

于是

```text
chi_n^r = sum_m omega_nm^2 / (omega_nm^2 + mu^2)^2 * |O_nm|^2
```

这个核在 `omega=0` 处自动为零，在 `omega ~ mu` 附近最敏感。物理上，它相当于在时间尺度 `t ~ 1/mu` 上观察系统对扰动的响应。

## E003: Average And Typical

论文同时看 average 和 typical：

```text
chi_av^r  = mean_n chi_n^r
chi_typ^r = exp(mean_n log chi_n^r)
```

average 会被少数大值拉高；typical 更接近“多数本征态”的行为。局域相里二者开始分离，这正是论文后半部分的重要特征。

## E004: Anderson Model

数值模型是三维开边界 Anderson Hamiltonian：

```text
H_A = - sum_<i,j> c_i^\dag c_j + sum_i epsilon_i c_i^\dag c_i
epsilon_i ~ Uniform[-W/2, W/2]
```

我们把它写成 `V=L^3` 维实对称矩阵。开边界条件很重要，因为论文明确用它来避免 `W -> 0` 附近的大量简并。

## E005: Perturbation Operators

论文讨论三种扰动：

```text
T   = - sum_<i,j> c_i^\dag c_j
T_s = - sum_alpha sum_<<i,j>>_alpha (1/alpha) c_i^\dag c_j
n   = sum_i (r_i c_i^\dag c_i - r_i/V)
```

当前本地复现主跑 `T_s`，因为它最直接显示弱无序 crossover。`T` 和 `n` 在完整大规模重跑计划里保留。

## E006: Rescaling

论文画图使用 rescaled susceptibility：

```text
tilde chi_typ   = chi_typ * omega_typ
tilde chi_typ^r = chi_typ^r * mu
tilde chi_av^r  = chi_av^r  * mu
```

代码同时输出 raw 和 rescaled 数值，生成图时优先使用 rescaled quantity。

## E007: Spectral Function From Off-Diagonal Matrix Elements

论文的谱函数不是从图像拟合出来的，而是先定义一个可计算对象。对谱中央
`20%` 的本征态集合 `Lambda`，把能量差落入同一个对数频率 bin 的非对角
矩阵元放在一起：

```text
|f(omega)|^2 ≈
Z / |Lambda(omega)|
* sum_{n,m in Lambda; omega_nm in bin(omega)} |<n|O|m>|^2
```

这里 `|Lambda(omega)|` 是该 bin 中矩阵元的数量，`Z` 是单粒子 Hilbert
空间维数。代码因此执行 `Z * mean(|O_nm|^2)`，并显式排除 `m=n`。这一步
闭合的是“矩阵元 -> 谱函数”的定义；Lorentzian 或幂律是后续要检验的物理
特征，不应预先写进数据。

## E008: Strong-Disorder Perturbation Theory For T_s

在无限无序极限附近，零阶本征态局域在单个格点，零阶能量就是 onsite
potential。论文对 `T_s` 给出的最低阶式子是

```text
chi_n^r ≈ sum_{m != n}
  [omega_mn^(0) / ((omega_mn^(0))^2 + mu^2)]^2
  * |<n^(0)|T_s|m^(0)>|^2
```

`T_s` 只连接指定的次近邻，因此化成

```text
chi_n^r ≈ sum_{n''}
  [omega_nn''^(0) / ((omega_nn''^(0))^2 + mu^2)]^2
```

当典型 `|omega_nn''| ~ W >> mu` 时，每项按 `W^-2` 衰减。当前代码对所有
连接边取平均，而不是逐态求和，所以它验证的是强无序趋势，绝对纵向归一化
可能相差一个与配位数有关的常数。这也是公式卡标记为 `reconstructed`
而不是完整 paper-exact 的原因。

## E009: Adjacent-Gap Ratio

附录用相邻能级间隔比判断谱统计：

```text
delta_n = E_n - E_(n-1)
r_n = min(delta_(n+1), delta_n) / max(delta_(n+1), delta_n)
```

只要能级已排序且没有多重简并，就有 `0 <= r_n <= 1`。平均后，GOE 参考值
约为 `0.5307`，Poisson 参考值约为 `0.386`。代码先去掉数值上近零的 gap，
再按同一 `min/max` 定义计算，因而 Fig. A1 的目标不再借用一个不存在的
占位公式。

## E010: Drude Slow-Mode Envelope And Source Inconsistency

现象学模型先把每个慢模写成 Lorentzian：

```text
|f(omega)|^2 ~ sum_j D_j/pi * Gamma_j/(omega^2 + Gamma_j^2)
```

论文随后假定 `D_j -> D_0/N`，并给出速率分布

```text
p(Gamma) ∝ Gamma^(zeta-2).
```

两者直接相乘，连续极限应为

```text
|f(omega)|^2 ∝ integral dGamma
  Gamma^(zeta-1)/(Gamma^2 + omega^2).
```

令 `Gamma = omega*u`，中间频率窗口
`Gamma_min << omega << Gamma_max` 中可提出

```text
omega^(zeta-2) = omega^-(2-zeta),
```

这与论文声称的包络一致。若 `Gamma_min ≈ Gamma_max`，分布退化为单一
Lorentzian，其半高宽就是 `Gamma`。

必须保留一个原文边界：印刷版 Eq. `(explanation)` 的分子写成
`Gamma^(zeta+1)`。它既不等于前一段两个因子的乘积，也推不出后一段的
`omega^-(2-zeta)`。当前代码采样 `p(Gamma) ∝ Gamma^(zeta-2)` 并逐个叠加
Lorentzian，所以实现的是前后自洽的 `Gamma^(zeta-1)` 路径；这条公式只能
标记为“重建且已解释原文不一致”，不能冒充无歧义的逐字验证。

## Formula Gate Result

- Machine-readable check: `outputs/checks/formula_verification.json`
- Status: `passed`
- Remaining issue: 公式实现通过，但纸面大系统标度没有在本地小尺寸上关闭；Fig. 11 的精确调参还缺作者未公开的输入。
