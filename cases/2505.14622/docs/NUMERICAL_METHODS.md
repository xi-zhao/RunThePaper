# 复算与证据范围 / Rerun and evidence

从仓库根目录安装依赖，然后运行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2505.14622/code/requirements.txt
python cases/2505.14622/code/scripts/run_reproduction.py
```

程序创建新的临时目录，打印其路径，重新生成原尺寸数组，以不同数学表示核验，并与公开冻结数组比较。也可用 `--output NEW_DIRECTORY` 指定尚不存在的输出目录。原公开数据不会被覆盖。锁定环境来自 Python 3.13.2；NumPy、SciPy、Matplotlib 等精确版本见依赖文件。

`code/model/generate.py` 与数值 audit 来自独立实现，仅适配公开目录；生成器不读取参考曲线。重新绘图使用新数组，少量标注引用固定参数下已核验的摘要。Skin effect 额外重算 20 组稳态控制。图形读数提取与长度候选比较的原始运行结果已归档；公开复算不重新读取作者 EPS、PNG 或数字化参考点。

Public commands generate fresh full-size arrays, run a distinct numerical formulation, compare every array with frozen independently generated data, and render new figures. The existing published arrays and checks remain unchanged. Source extraction is not rerun; obtain paper assets from official sources for a new source-comparison audit.

## 证据入口

- [原始核验摘要](../outputs/checks/numerical-checks.json)
- [不同方法的数值 audit](../outputs/checks/distinct-method-audit.json)
- [声明范围与原生状态投影](../outputs/checks/completion_assessment.json)
- [文件来源和哈希](../outputs/checks/publication_provenance.json)

原生任务状态 concluded 表示声明研究目标已有明确结论，原文一致性另列。旧目录的 complete 布尔值只对应同名 complete 状态，不能把它当作数值子图完成率。本次没有把 Run、子图、内部曲线重复计数，也没有把独立实现、同一 Agent 核验与独立评审混为一谈。

原论文 PDF、EPS、作者 notebook、数字化原图坐标和私人运行记录不在本公开包中。必要对照图单独归属原作者，其参考内容不适用本仓库开放内容许可。公开包检查只验证文件、来源与导航完整性。

公开生成图不读取论文参考坐标；有限的参考对照独立标注其来源和精度边界。
