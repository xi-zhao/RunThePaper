# 复算方法 / Numerical methods

## 环境与入口

建议 Python 3.12，在仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2610.12348/code/requirements.txt
python cases/2610.12348/code/scripts/run_reproduction.py --mode quick
```

核心库为 NumPy、SciPy、Matplotlib，文件固定原实验依赖版本。每次运行创建新临时目录并打印位置，保留冻结输出。

| mode | 实际执行内容 | 边界 |
|---|---|---|
| `quick` | 两种统计的小系统零空间与共四条量子轨迹 | 安装与算法通路检查，不是原尺寸收敛 |
| `statics` | 原尺寸 23 个静态扇区的密度、关联与熵 | 一组 Haar 基，不是 512 基统计或耗散动力学 |
| `h3` | 704 条原文参数轨迹与 576 次压力检查，共 1280 次 | 已完成 v2 配置；不重启 v3 大样本任务 |
| `verify` | 从逐轨道数组重算均值及 raw 恒等式 | 不含作者原数组或严格截断界 |
| `render` | 从冻结数组重画 12 个初态的两种熵 | 新版展示，没有新像素分数 |

## H3 参数

原文组使用 $`N=8`$、fermion $`L=16`$、boson $`L=9`$，$`\delta/g=5`$、$`\Gamma/g=10`$、$`tg=250`$、photon cutoff 8，`rtol=1e-9`、`atol=1e-11`。初始腔真空和 photon-counting unraveling 是本案明确声明的条件。实际样本数取外层 `cohort.samples`；嵌套 `initial.samples` 是未参与计算的旧元数据。生成配置保留原值，避免改写历史。

压力组为 fermion L8N4、boson L5N4，各取 GS 及两个 Fock 初态；$`(\delta/g,\Gamma/g,tg)`$ 取 (0,10,50)、(5,10,50)、(10,10,50)、(5,5,50)、(5,20,50)、(5,10,250)。每组 16 条随机流，跨参数配对；原文没有这些参数曲线，因此不能计作新增原图复现。

[配置](../code/h3/config.json)、[生成器](../code/h3/generate.py)、[数组](../outputs/data/h3/samples.npz)、[运行汇总](../outputs/data/h3/results.json)。主生成历史墙时 1447.9 秒，仅供估计。

## 统计含义

SVD 得到 Schmidt 值后归一化计算物理熵。raw 诊断从每条轨迹的真实末段范数构造；均值与 SE 逐 cohort 保存。比较使用 2000 次整轨道 bootstrap，保留 bond 间相关性。0.02/0.04/0.08 nats 加两倍经验 SE 的窗口是读图敏感性，既不是作者 CI，也不是可自动用于全部原图的验收阈值。

## 可重复范围

核心静态与 H3 生成有自包含入口。`code/base` 保留先前动力学、H1 和 H2 科学算法；它们部分需要对应历史输入或采用不同 cohort。冻结数据与各自配置分列，禁止把相干 GS、去相干 GS、不同 cutoff 的数组混合作为同一独立样本集。

v3 的 9216 次计划求解未提供完成收据，退出原因未知；本包不含其未完成样本。公开封装检查不等于原生科学验收。资产变换与散列见[provenance](../outputs/checks/publication_provenance.json)。
