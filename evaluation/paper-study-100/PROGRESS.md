# 研究执行进度

2026-09-21。**当前主稿已调整为面向arXiv的科研技术报告。** 用户目标是通过正式、可引用的技术成果展示科研与实现能力，不以期刊录用为前提。10页英文稿包含4张主图和100篇附图，来源为实际公开实现和已有数组的只读重分析。

arXiv草稿源包已通过干净目录中的两遍PDFLaTeX编译；署名、作者顺序和单位尚待作者提供，未提交arXiv。主入口：[技术报告](preprint/PRAgent_Technical_Report.pdf)、[源码包与提交说明](preprint/ARXIV_SUBMISSION.md)。此前档案审计稿保留为补充研究记录。

| 环节 | 已交付 | 尚待完成 |
|---|---|---|
| 公开证据整理 | 统一100篇身份；可提取记录包含3,927条证据、1,721份输入哈希及逐篇核查队列 | 原文逐对象核对、实际物理条件和数值一致性审阅 |
| 生产case准备 | 来源、推导、责任清单、独立实现、运行合同；22项软件测试和开发诊断 | 正式生产入口返回isolation_unavailable，未执行；独立科学验收未开始 |
| 公开投影 | 保持既有归档不变 | 由PRAgent生成适用公开清单后投影 |
| 完整稿件 | 10页英文PDF；3张主图与100篇附图；8条参考文献；中文摘要、证据索引、图表复算脚本 | 科学比较结果、作者与单位、投稿声明及针对目标期刊的定稿 |

## 当前入口

- [完整论文PDF](manuscript/PRAgent_100_Papers_Manuscript.pdf)、[可编辑正文](manuscript/paper.md)、[中文读稿说明](manuscript/读稿说明.md)。
- [统一100篇附表](manuscript/cohort_100.csv)、[图表统计](manuscript/figure_data.json)、[陈述依据](manuscript/claim_evidence.csv)。
- [公开档案报告](analysis/ARCHIVE_REPORT.md)、[逐结果证据](data/results.jsonl)、[输入哈希](data/inputs.jsonl)、[语义核对队列](analysis/semantic_review_queue.csv)。

当前稿件按一个100篇队列组织，未评估的测量保持未知，不按来源设置研究组别。`cohort.json` 和原始选题记录保留冻结历史；其中旧分组策略不再用于正文，not_started也不是最新开发状态。

## 分支、提交与责任

RunThePaper使用PR #19原分支 `c/paper-study-100-plan-20260920`；先前证据整理提交 `6d680eecd08938e996af5ee0484d3daa231f2e83` 已推送。当前稿件改动在该分支继续提交；后续是否推送以实际Git记录为准。

PRAgent使用 `c/paper-study-100-production-20260921`，实现提交 `13238275a0d10370dad7ebf1f87d9c3f9ed5dbc8` 已推送。开发入口为该仓库 `docs/paper-study-100/README.md`。用户选择沿用生产case流程，保留未就绪的运行阶段；本次写作不修改生产case或运行状态。

普通工作区诊断不能替代隔离证明，软件测试不等于科学验收。原始材料、开发诊断和内部检查保存在PRAgent，本次稿件只使用公开档案统计和有引用的原文数学示例，没有将私有诊断投影为公共科研成绩。
