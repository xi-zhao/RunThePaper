# 运行、范围与证据

核对版本：PRL 61,2015–2018 (1988)，出版社全文提取。正式论文：[Phys. Rev. Lett. 61, 2015 (1988)](https://doi.org/10.1103/PhysRevLett.61.2015)。

在本案例目录，使用Python 3.13和固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r code/requirements.txt
python code/scripts/run_reproduction.py --output /tmp/PhysRevLett.61.2015-fresh-result
```

输出路径必须不存在；程序重新计算主模型，运行其内置数值检查，并逐数组对照冻结结果（atol=rtol=1e-8）。这项检验验证公开代码的复算能力，不等于原文全部条件通过。

冻结执行：Run `e2be64b2-4a90-47ba-9a84-526938c547fe`，版本 8。任务状态 `unfinished`；原文支持、未决对象与计算可靠性分别保存在 `outputs/checks/completion_assessment.json`。本报告来自同一研究Agent的计算和不同数值方法交叉核验，不是严格独立审查或形式化物理证明。

当前边界：箭头与带符号Hall约定的视觉确认仍未完成；这是具体来源获取限制，不是作者未说明的证据。

本地原始论文、参考点集、插件运行库及完整原生记录未包含在公开包。主要结果数组及生成程序已包含；含源标记的必要对比图单独注明归属。
