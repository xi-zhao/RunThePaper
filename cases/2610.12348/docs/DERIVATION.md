# 暗态空间、守恒荷与轨迹熵

## 1. 零空间为何给出无退相干子空间

取 $`O=\sum_{j=1}^{L-1}c_j^\dagger c_{j+1}`$、$`H/\hbar=\delta a^\dagger a-g(a^\dagger O+aO^\dagger)`$，跳跃算符 $`J=\sqrt\Gamma a`$。若 $`O|\psi\rangle=0`$，则对 $`|\Psi\rangle=|0\rangle|\psi\rangle`$，$`H|\Psi\rangle=J|\Psi\rangle=0`$。任意零空间向量之间的 $`|\Psi_i\rangle\langle\Psi_j|`$ 也满足 $`\mathcal L(\rho)=0`$。因此不只是概率混合，子空间内相干也可保留。

这一构造是充分条件；更广条件下“所有稳态都如此”需要另证。本报告不把存在性证明改写成唯一性定理。

## 2. 定粒子数扇区与计数

令 $`X=\sum_j jn_j`$（位置从 1 开始）。$`O`$ 把 $`X`$ 降低 1，于是可以在相邻 $`X`$ 扇区之间构造矩阵并求核。利用带权提升算符

$$O_+=\sum_{j=1}^{L-1}j(L-j)c_{j+1}^\dagger c_j,\qquad Z=2X-N(L+1),$$

得到 $`[Z,O]=-2O`$、$`[Z,O_+]=2O_+`$、$`[O_+,O]=Z`$。$`O_+`$ 一般不是 $`O^\dagger`$。表示论把位置扇区的维数差与最低权态数联系起来；独立整数递推计算 Gaussian binomial 系数，矩阵零空间维数提供另一种检查。

对报告中的 $`N=8,L=16`$ fermion 与 $`N=8,L=9`$ boson，两种计数均给出总暗态维数 526。23 个选定 $`(X,N_p)`$ 扇区的零空间由 SVD 求得，并检查 $`\|OU\|`$、$`\|U^\dagger U-I\|`$ 及配对算符残差。有限尺寸熵曲线不证明渐近体积律，后者还需要指定随尺寸变化的扇区、粒子数和平均方式。

## 3. 三种不同的“守恒”

$`Q=a^\dagger a+X`$ 与 $`H`$ 对易，因为 $`a^\dagger O`$ 同时增加一个光子、把 $`X`$ 降低一。无跳跃演化保留确定 $`Q`$ 的扇区，但光子跳跃 $`a`$ 把 $`Q`$ 降低一；所以不能把 $`Q`$ 称为完整耗散过程的强守恒量。

与 Hamiltonian 和跳跃算符同时对易的配对量子数才提供强对称性分块。只在暗态空间出现的代数性质也不能自动扩展到完整 Liouvillian 动力学。

## 4. 量子轨迹的归一化

无跳跃段使用 $`H_{\rm eff}=H-i\hbar\Gamma a^\dagger a/2`$，其未归一化范数平方 $`w`$ 表示该段的生存概率。归一化纯态的约化密度矩阵 $`\rho_A`$ 给出物理纠缠熵

$$S=-\mathrm{Tr}(\rho_A\ln\rho_A),\qquad\mathrm{Tr}\rho_A=1.$$

若错误地或有意地对 $`w\rho_A`$ 取谱，则

$$S_{\rm raw}=wS-w\ln w.$$

这不是统一比例变化，而含非线性偏移。必须先逐轨迹应用，再平均：一般有 $`E[wS]\ne E[w]E[S]`$。当前诊断记录求解器实际终段范数；原图未提供的实现细节不能由恒等式本身推断。

腔是第一个子系统，本实现 cut index 0 为腔对全部物质的切分，之后逐站加入物质。与原图 bond 的对应必须事先指定。相干 GS 的熵不能由跨 $`Q`$ 去相干的密度矩阵或线性观测均值替代。

## 5. H2 的整数边界

对确定 $`Q`$ 的 Fock 轨迹，$`\langle X\rangle=Q-\langle n_{\rm ph}\rangle`$。若 $`0<p\ll1`$，直接 float 减法可能得到精确整数 Q，而数学上的 floor 是 $`Q-1`$。使用

$$\lfloor Q-p\rfloor=Q-\lceil p\rceil$$

避免减法消去。它仍依赖 photon 期望值本身可信；高精度重做减法不能修复上游 ODE 或截断误差。相干 GS 没有单一确定 Q，不能套用此式。

实现见 [静态算符](../code/h3/solvers/generate_statics.py)、[轨迹](../code/h3/generate.py)及[尾部算法](../code/base/scripts/generate_h2_tail_v2.py)。本报告的数值状态与边界见[主报告](../note/reproduction-note.zh-CN.md)。
