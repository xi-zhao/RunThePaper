# 运行、范围与证据

核对版本：1002.4341v2；已核对公开EPAPS。正式论文：[Phys. Rev. Lett. 104, 183601 (2010)](https://doi.org/10.1103/PhysRevLett.104.183601)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/1002.4341-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

补充计算位于 `code/model/alignment-v3-20261022/`。可用 `--experiment alignment-v3-20261022/文件名.py` 逐项执行。贝叶斯变体、状态重置和不充分截断均明确属于诊断控制；不能代替原模型。Gauss检查自带六条真实生成记录的选择配置。

冻结执行：Run `7ffe4071-5a2f-4b12-9b7b-8735666602cc`，版本 22。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：三模完整源曲线、正文0.28与源图0.4522尚未统一；源条件收敛g2(0)=0.34699064724。线宽、驱动、截断和有限制备时间控制均未恢复整条曲线。；原正Gaussian曲线和高于已受控占据范围的原条件计算仍未完成；625点热图已经完成，不重复计作待做。

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
