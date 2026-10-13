# 从码矩阵到接受率

## 1. 群代数与 CSS 条件

对有限阿贝尔群 $`G`$，令 $`P_g`$ 为正规表示的置换矩阵。二元多项式 $`a=\sum_g a_g g`$ 对应 $`A=\sum_g a_gP_g`$，求和在 GF(2) 上进行。交换群保证这些矩阵彼此对易。将原文的四个多项式代入 [construct](../code/preparation/src/generate_algebra.py) 得到 $`H_X,H_Z,M_X,M_Z`$。

对 $`X`$ 型和 $`Z`$ 型 Pauli 稳定子，对易符号由支持集的二元内积给出，因此

$$H_XH_Z^T=0\pmod2.$$

元校验把冗余稳定子相乘成恒等算符，得到 $`M_XH_X=M_ZH_Z=0`$。逻辑维数由商空间而来：$`k=n-\mathrm{rank}(H_X)-\mathrm{rank}(H_Z)`$。数值检查使用二元消元，不用浮点秩阈值。

距离需要另一个问题：在 $`\ker H_X`$ 中寻找不属于 $`\mathrm{row}(H_Z)`$ 的最小重量向量，反向交换 X/Z 同理。找到一个重量 $`w`$ 的合法逻辑算符只证明 $`d\le w`$；只有排除更小重量才给出精确距离。矩阵秩正确不能替代距离检查。

## 2. 从故障到检测器分布

将一个固定 noisy circuit 转成 detector error model。独立机制 $`e_i\sim\mathrm{Bernoulli}(p_i)`$ 产生检测器字 $`D=Ae`$，所有加法均为 XOR。字符变换给出

$$\phi(k)=E[(-1)^{k\cdot D}]=\prod_{i:k\cdot A_i=1}(1-2p_i),$$

$$P(D=d)=2^{-r}\sum_k(-1)^{k\cdot d}\phi(k).$$

先按 GF(2) 秩压缩独立字符，再做有限 Walsh 变换。当前程序在 float64 上完成有限求和；这是无抽样误差的分布计算，不是任意精度或区间证书。

## 3. 制备译码与信息边界

可访问元校验 $`S=My`$，隐藏 frame 为 $`F=B(y\oplus\sigma)`$。$`\sigma`$ 是 escape 前的实际稳定子符号。模型构造用理想标签识别联合分布；操作中的 decoder 只见到 $`S`$。

$$\widehat F_{\rm MAP}(s)=\arg\max_fP(F=f\mid S=s).$$

故障 MLE 则最大化单个机制向量的概率，并把它映射为 frame。MAP 合并简并故障类，MLE 不做这种求和，所以两者通常不同。

接受事件为 $`A=\{D\oplus\widehat F(S)=0\}`$。在固定可用信息下，$`\sum_s\max_dP(S=s,D=d)`$ 是任意确定性修复规则的接受率上界。若允许更多记录，信息集合已经变化，旧上界不再约束新 decoder。

## 4. 接受率不是条件逻辑错误率

$$\alpha=P(A),\qquad p_L=P(L\ne0\mid A)=\frac{P(L\ne0,A)}{\alpha}.$$

故障子集质量只能给出对应分子的下界。分母必须使用同一门序、噪声时点和后选择条件。保留旧逻辑标签、改变接受 mask 时，也必须继续核验 frame 到逻辑观测量的映射。

若每次尝试体积为 $`V`$，输出为 $`m`$ 个可用态且重试独立，单个接受输出的平均成本是 $`V/(m\alpha)`$。此算式并不保证目标 $`p_L`$，也不验证作者的完整 optimized schedule。因此资源优势需要先闭合错误率、接受率和计数口径。

以上推导的公共实现见 [preparation](../code/preparation/src/)；[数据](../outputs/data/preparation/results.json)与[数值方法](NUMERICAL_METHODS.md)保留实际条件。没有把改变物理定义当作绘图修正。
