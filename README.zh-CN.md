<h1 align="center">RunThePaper</h1>

<p align="center"><strong>读懂一篇论文，亲手跑出结果。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

<p align="center">
  <a href="#浏览论文">浏览论文</a> ·
  <a href="#运行这个示例">运行示例</a> ·
  <a href="#如何看待复现结果">查看证据</a> ·
  <a href="#参与项目">参与项目</a>
</p>

**RunThePaper 是一个开放的物理论文复现库。** 每个案例把推导、可运行代码、
生成的数据与图、验证结果和未解决的问题放在一起，并提供中英文讲义。

你可以用它理解一种方法、核验论文中的一个结果，或者修改参数开始新的计算，
省去从 PDF 重新搭建整套研究过程的工作。

## 从一个具体结果开始

模拟分子哈密顿量需要多少量子门？[qDRIFT 案例](cases/1811.08017/README.md)
从 *A random compiler for fast Hamiltonian simulation* 的公式出发，
重新计算三种分子的资源需求，比较 qDRIFT 与 Trotter 方法的量子门数。

![独立生成的 Fig. 2：丙烷、二氧化碳和乙烷的 qDRIFT 与 Trotter 量子门数上界](cases/1811.08017/outputs/figures/fig2_gate_counts_reproduction.png)

*独立生成的 Fig. 2 复现图。* 你可以顺着[讲义](cases/1811.08017/note/reproduction-note.zh-CN.md)
看推导，打开 [CSV 数据](cases/1811.08017/outputs/data/fig2_gate_counts.csv)，
或检查[数值验证结果](cases/1811.08017/outputs/checks/target_checks.json)。
这个案例目前[仍待独立评审](cases/1811.08017/outputs/checks/completion_assessment.json)。

## 运行这个示例

qDRIFT 示例使用 Python 3.11 或以上版本，在本地 CPU 上即可运行。
以下命令适用于 macOS 或 Linux：

```bash
git clone https://github.com/xi-zhao/runthepaper.git
cd runthepaper
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd cases/1811.08017/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

它会重新计算 Fig. 2 和 Fig. 4 背后的数值结果，并写入：

- `cases/1811.08017/outputs/data/fig2_gate_counts.csv`
- `cases/1811.08017/outputs/data/fig4_phase_estimation_counts.csv`
- `cases/1811.08017/outputs/checks/target_checks.json`

数值检查通过时，检查文件会报告 `"status": "passed"`。
绘制好的图片已随仓库提供；这条命令重新生成的是数据和检查结果。
计算范围与待完成的评审请看[案例运行说明](cases/1811.08017/code/README.md)。

## 浏览论文

<!-- case-catalog:start -->
**100 篇公开论文案例**，包含部分复现和受阻的尝试。
按主题进入[完整目录](CASES.md)，查看论文来源、已记录状态、中英文讲义、代码和证据。

[选择学习路径](LEARNING_PATHS.md) · [查看案例增量更新](UPDATES.md)

| 研究主题 | 案例数 |
| --- | ---: |
| [量子计算、算法与纠错](CASES.md#collection-quantum-computing) | 25 |
| [量子信息、基础问题与精密测量](CASES.md#collection-quantum-information) | 18 |
| [多体物理、相变与非平衡动力学](CASES.md#collection-many-body) | 27 |
| [拓扑、非厄米、材料与输运](CASES.md#collection-topology-materials) | 21 |
| [原子、光学、光子学与场论](CASES.md#collection-amo-field) | 9 |
<!-- case-catalog:end -->

也可以从[非厄米边界态](cases/1803.01876/README.md)或
[无序系统的 Lyapunov 能带理论](cases/2507.09447/README.md)开始。
案例页面集中提供论文来源、推导、结果和当前限制。

## 如何看待复现结果

使用一个复现案例时，先看三个问题：

| 问题 | 在哪里看 |
| --- | --- |
| **复现了什么？** | 案例简介列明覆盖的图或科学主张、使用的参数，以及缺失输入或算力限制。 |
| **结果是否一致？** | 生成数据和科学检查记录数值一致性、差异与容差；图像相似度单独记录。 |
| **还有什么没完成？** | 完成情况记录列出未解决的目标和独立评审状态。一次运行通过，只说明这次运行的检查通过。 |

部分结果和未成功的尝试也会连同证据保留。标记为“论文错误候选”的发现仍需核验，
不能直接当作对原论文的定论。

[固定 100 篇论文的审计](evaluation/claim-first-100/README.md)将 3,933 项检查
对应到 1,427 条科学主张。对每条数值主张赋予相同权重后，结果为：

| 结果 | 占比 |
| --- | ---: |
| 成功复现 | 40.55% |
| 受有证据支持的外部条件阻塞 | 21.93% |
| 已尝试但未复现 | 37.52% |

这些比例描述主张层面的结果，不是整篇论文的成功率。
完整台账、计算方法、保真度证据及其限制见[评测说明](evaluation/claim-first-100/README.md)。

## 案例怎样产生

我们使用自研论文复现系统 **PRAgent**，组织论文理解、推导、代码实现、数值运行、
检查和独立评审。RunThePaper 公开这项工作产生的科研材料及其已记录的边界。
PRAgent 执行系统在独立项目中开发，当前未随本仓库提供。

我们希望每次复现都能成为下一位研究者的起点：重新运行一个结果，追查一处差异，
或修改一个假设，继续提出新问题。后续工作见[路线图](ROADMAP.md)。

## 参与项目

- **推荐论文：** [提交 issue](https://github.com/xi-zhao/runthepaper/issues/new)，
  附上 DOI 或 arXiv 编号，以及最关心的图或科学主张。
- **反馈运行结果或差异：** 提供案例、运行命令、环境和观察到的结果，方便他人核验。
- **复核或扩展案例：** 检查推导、补充输入、修正错误或增加新结果，具体流程见
  [贡献指南](CONTRIBUTING.md)。

在研究中使用案例时，请引用原论文，并链接到你使用的案例提交版本，
让读者能够检查同一份材料。

## 许可

代码采用 [MIT](LICENSE-CODE)；讲义、生成数据和生成图片采用
[CC BY 4.0](LICENSE-CONTENT)，个别案例另有说明的除外。
第三方材料及对照面板中注明来源的论文节选仍适用原权利人的条款，见 [NOTICE.md](NOTICE.md)。
