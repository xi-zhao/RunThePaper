# 运行、范围与证据

核对版本：1902.10958v2，含完整附录。正式论文：[Phys. Rev. Lett. 123, 066404 (2019)](https://doi.org/10.1103/PhysRevLett.123.066404)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/1902.10958-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

冻结执行：Run `a12a926a-4474-4483-98c0-b5e31e7365ff`，版本 12。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：这仅核验带符号结果，不等于原图标签已对齐；降阶点和其余能带/环路比较仍保留。；Three complexR-loop geometry comparisons are now computed as source-only diagnostics; full original band, auxiliary-root and Lee spectrum comparisons remain.

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
