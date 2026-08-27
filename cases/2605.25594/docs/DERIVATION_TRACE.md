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

## Formula Gate Result

- Machine-readable check: `outputs/checks/formula_verification.json`
- Status: `passed`
- Remaining issue: 公式实现通过，但纸面大系统标度没有在本地小尺寸上关闭。
