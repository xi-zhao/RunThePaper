# 运行、范围与证据

核对版本：cond-mat/9603165v1。正式论文：[Phys. Rev. Lett. 77, 570 (1996)](https://doi.org/10.1103/PhysRevLett.77.570)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/cond-mat-9603165-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

补充计算位于 `code/model/alignment-v3-20261022/`。可用 `--experiment alignment-v3-20261022/文件名.py` 逐项执行。贝叶斯变体、状态重置和不充分截断均明确属于诊断控制；不能代替原模型。Gauss检查自带六条真实生成记录的选择配置。

冻结执行：Run `691ad28a-b3b8-4836-9169-90677d9d1e31`，版本 16。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：空间宽度原坐标定义下，原尺度100组无序集合支持余差统计相容；新诊断尚未更新原始对象验收，需保持完整来源对照的明确口径。作者精确种子或代码身份不作为额外完成要求。

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
