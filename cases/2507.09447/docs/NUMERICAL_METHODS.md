# Numerical Methods

## NUM001：共享 Lyapunov band 模型

- Target：T001–T003。
- 公式卡：EQC001–EQC008。
- 参数：`M=2, t2=0.5, t1=1.5, t-1=t-2=1`，`w_i∈[-W,W]`。
- 边界：OBC 和 PBC；绕数另用带 twist 的 PBC。
- Solver：`scipy.linalg.eigvals` 做有限链谱；batched `numpy.linalg.qr`
  做 transfer product 的 Lyapunov 谱。
- QR 规则：每个格点 QR，累计 `log|diag(R)|/L`，指数升序排列。
- 随机种子：`250709447`。
- 输出：长表 CSV（能量、势、密度、LE、分类、`W`、`L`）和 JSON checks。
- 验证：clean beta limit、转移递推、ED/LE 势 MAE、密度重叠、双路径绕数、
  标度指数、`alpha` 和 contour-area 趋势。

## T001 / T002 运行卡

- ED：`L=120`，24 个无序 realization。
- LE：`73×45` 复能量网格，transfer length 900。
- density：ED 二维 histogram 与 LE 势的离散 Laplacian，各自归一化后比较重叠。
- 标度：`L=40,80,120,180`，每个长度 256 个 realization；理论势用
  transfer length 300000。
- 绕数：LE 路径用 transfer length 12000；独立路径用 `L=160` twisted chain，
  129 个 twist 点。

## T003 运行卡

- 论文 contour 参数：`W={0.4,0.8,1.2,1.6,2.0}`。
- `alpha(W)`：`W∈[0,3]` 的 17 个点。
- LE：`57×37` 网格，transfer length 700。
- ED：`L=100`，6 个 realization。
- 迁移边必须分别画连续场 `gamma_2=0` 与 `gamma_3=0`；不能直接对分段选择的
  signed essential exponent 画零线，否则分支切换会制造假 contour。

## Efficiency And Reuse Plan

- baseline：逐能量、逐格点 transfer multiplication。
- 主瓶颈：复能量网格上的 QR 和 disorder ensemble 的 dense ED。
- 当前优化：同一格点把整个能量网格打成 batch 做 `4×4` QR；ED 按 seed 独立。
- scaling：LE 约为 `O(N_E L M^3)`，这里 `M=2`；dense ED 约为 `O(L^3)`。
- generic promotion：batch QR、seed-sweep checkpoint 可以进入 harness；
  非厄米模型参数、分类规则和图形布局留在 case。
- 性能证据：feature run internal timer `30.40 s`；论文尺度单样本 benchmark 见
  `outputs/checks/paper_scale_single_sample_benchmark.json`。

## NUM004：补充材料 S1/S2 最近邻 transfer

- Target：T004–T005。
- 公式卡：EQC009。
- 不变量：transfer 第一个分母必须与 ED 的 `H[j,j+1]=t+gamma(+w_j)` 相同。
- 验证：两种模型均将 transfer 生成的 `psi_(j+1)` 代回 ED 行方程；方向对调会使
  残差测试失败。

## NUM005：单向跃迁密度恒等式

- Target：T006。
- 公式卡：EQC010。
- 方法：独立构造上/下三角 OBC Hamiltonian，比较有限谱与 onsite 对角元的排序
  多重集；该检查对任意 `rho_w` 的有限样本逐点成立。
- 数据：`outputs/data/unidirectional_density.csv`。

## NUM006：Fig. S3 多精度 ED/QR

- Target：T007。
- 公式卡：EQC011。
- ED：`mpmath` arbitrary-precision dense eigensolver；QR：独立的 4x4
  modified-Gram-Schmidt transfer path。
- Paper contract：`L=1000`、1600 realizations、64/112/160/208-bit、256-bit ED
  reference、`E=-0.72,3.20`。
- 当前运行：相同精度/能量的 `L=12 x 2` 实测 pilot；论文尺度只保留可运行配置和
  由实测导出的资源投影，不伪装成正式结果。

## NUM007：Fig. S4 Lyapunov-gap 标度

- Target：T008。
- 公式卡：EQC012。
- 执行论文报告的 `L=50,...,400`、`L_ref=1000`、
  `E0=-0.9328+0.2210i`。
- 同时拟合 `log(d_L)~L` 与 `log(d_L)~log(L)`，不得只报有利模型。
- 论文未报告 ensemble/seed/QR interval；当前固定 64 realizations、seed 和
  `qr_interval=1`，因此是可证伪尝试而非 paper-exact 数值身份。
- 另做协议敏感性扫描：realizations=`16,64,128`，三个独立 seed，
  `qr_interval=1,4`。只有扫描显示结论会随这些缺失设置翻转时，才允许把
  未复现直接归因于“论文协议缺失”；否则保留为已尝试的科学差异。
