# 复算方法 / Numerical methods

## 环境与入口

建议 Python 3.12。在仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.10731/code/requirements.txt
python cases/2610.10731/code/scripts/run_reproduction.py --mode quick
```

核心库为 NumPy、SciPy 和 Stim；依赖文件固定原实验版本。仓库根目录的通用 requirements 不能替代本案例锁定版本。每次入口运行创建新的临时计算目录并打印位置，包含 `run-check.json`；不会覆盖冻结数据。

| mode | 实际执行内容 | 不代表什么 |
|---|---|---|
| `quick` | 五组码精确二元检查，以及 54 码一个原参数点的 frame MAP/MLE 接受率 | 全部噪声曲线或完整魔态 fidelity |
| `algebra` | 重跑原码构造与逻辑态代数程序 | 有噪工厂正确率 |
| `preparation` | 重跑 44 配置、96 顺序对照、400 万 gate-level 样本 | 更广 320 顺序扫描、所有逻辑错误计数 |
| `verify` | 对 44 行冻结分布重新求接受率，并核对保存的线路散列 | 新的独立科学验收 |
| `render` | 用冻结生成数据重画接受率图 | 新数值生成或新的原图像素分数 |

完整 `preparation` 历史墙时 1468.8 秒，不能承诺其他机器相同。源图数据不进入生成。

## 已固定的约定

- $`p`$ 是各指定 SD6 通道的总概率；CCZ 单 pair 边缘采用 $`16p_{CCZ}/21`$ 的均匀非平凡 Pauli 参数。
- `fresh_aligned` 与 `baseline` 是声明的独立调度变体，未认定为作者程序。
- R+H 与 H+M 保留；门序和 idle 噪声由具体线路决定。
- 每次尝试均计入接受率分母；最终 quad readout 不参与 acceptance mask。
- MAP 对 frame 类求概率和；MLE 对独立 DEM 机制做加权 XOR 最短路。
- 所有相位诊断与完整输出魔态误差分别标注。

[模型](../code/preparation/config/models.json)、[实验配置](../code/preparation/config/experiment.json)、[保存线路](../outputs/data/preparation/programs.json)、[概率表](../outputs/data/preparation/tables.npz)。

## 其他已保存的计算

`code/base` 保留代数、距离、故障与存储等原有科学实现和配置。它们不都由默认入口批量执行；某些历史诊断需要对应的历史生成输入，不能把缺输入的命令当作已验证运行入口。主报告核心接受率与代数计算有自包含入口。`code/preparation/src/tri_order_scan.py` 和 `fault_audit.py` 可在新的 preparation 副本中运行，分别输出 `tri-scan` 和 `fault-audit`，使用随包配置。

公开导出仅改写原本的本地目录前缀，不修改科学算法和已计算数值。每个复制资产的源/公开 SHA256 与变换类型见[provenance](../outputs/checks/publication_provenance.json)。公开入口检查与旧原生实验收据是不同证据，不能相互冒充。
