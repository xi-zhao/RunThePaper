# 运行、范围与证据

核对版本：0908.0238v2。正式论文：[Phys. Rev. Lett. 103, 210401 (2009)](https://doi.org/10.1103/PhysRevLett.103.210401)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/0908.0238-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

冻结执行：Run `335b1a88-336b-4b15-8821-b6a7b8c3bf14`，版本 13。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：网格投影与近似阶次的残差仍需区分，未将量化对比完成当作整图完全一致。

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
