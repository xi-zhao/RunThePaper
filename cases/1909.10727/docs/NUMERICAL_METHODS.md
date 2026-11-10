# Rerunning the pulse and benchmarking model / 复算方法

Use Python 3.13 and the pinned requirements in the code README. The command runs the independent quaternion propagator, the table-based variance model and the centered autocorrelation calculation. It writes a fresh `results` directory with `model.json`, `trials.npz` and `autocorrelation.json`. Use `--output` to name a new output directory. No data download is needed.

The noise clock starts at the sequence origin and spans pulse segments. The quasistatic noise component is held constant within a specified Clifford block. The same-direction CORPSE identity is an explicit controlled variant. The five-ion variance curves in the model use the fitted strengths reported in the paper's caption. The other simulation trials use fixed new seeds. [Pulse conventions and formulas](DERIVATION.md)

Compare the run with the frozen arrays and the scalar checks. The stored model data contains a legacy uncentered correlation calculation alongside other model quantities. The separate autocorrelation file contains the centered and normalized panel on the full 100-by-101 grid. [Frozen outputs](../outputs/data) · [Scalar checks](../outputs/checks/numerical-checks.json)

入口一次运行脉冲传播与中心化自相关，输出写入新目录。方差比对照固定随机序列并只改变空闲脉冲方向。五离子方差模型沿用论文图注的拟合参数，实机联合读出仍需原数据。[公开计算代码](../code/README.md) · [数据缺口](DATA-AVAILABILITY.md)
