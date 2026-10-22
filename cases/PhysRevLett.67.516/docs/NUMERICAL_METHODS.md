# 运行、范围与证据

核对版本：PRL 67,516–519 (1991)，作者机构保存的出版扫描。正式论文：[Phys. Rev. Lett. 67, 516 (1991)](https://doi.org/10.1103/PhysRevLett.67.516)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/PhysRevLett.67.516-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

冻结执行：Run `fc3b5de8-f185-491b-b436-9cba6bf18bd3`，版本 13。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：两个驱动位置的重合标记无法分辨多重性；没有把其余长时间曲线和密度像素比较自动判为完成。

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
