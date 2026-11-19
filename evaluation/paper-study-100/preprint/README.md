# PRAgent 技术预印本

**定位：用具体实现和证据链展示PRAgent的科研复现能力。** 能力指人工指导工作流中已有实现和记录支持的能力。

- [英文技术报告](PRAgent_Technical_Report.pdf)、[可编辑正文](report.md)
- [arXiv草稿源包](arxiv_source_draft.zip)、[独立LaTeX源文件](main.tex)
- [中文摘要与阅读说明](中文说明.md)、[本轮证据审计修订说明](证据审计修订说明.md)
- [提交说明](ARXIV_SUBMISSION.md)、[待填写的提交元数据](submission_metadata.json)

正文先介绍工作流和一个真实的代理模型评估链，再用三个案例展示精度处理、守恒子空间和系综计算。统一100篇的总体图保留历史检查标签并显式显示状态冲突；逐结果证据台账补充可检查的比较范围。原[档案审计稿](../manuscript/paper.md)保留为补充记录。

## 图表与审计重建

Figure 1是已审阅的概念工作流图。Figure 2展示存储资源曲线与相邻整数的精度要求；Figures 3–4重绘量子游走和量子关联数组；Figure 5展示历史检查标签及摘要/详单一致性。Table 1展示局部检查通过但原目标未接纳的真实记录，Table 2展示联合状态。

```bash
python build_evidence.py
python build_overview.py
python build_evidence_audit.py
python build_reason_audit.py
python build_diagnostic_followup.py
python build_obstacle_examples.py
bash build_report.sh
python package_arxiv.py
```

数值图依赖见 `../manuscript/requirements.txt`。脚本只读冻结Git对象和派生台账，保留输入哈希，不执行案例代码。Figure 1不在上述再分析中重画；`build_figure1.py`使用 `reportlab==4.4.9`将已审阅PNG封装为PDF。排版使用Pandoc和PDFLaTeX。打包工具在干净目录编译两遍，核对PDF文本、100个身份、数值、对象与联合状态的一致性。

## 指标解释

40.9%和57.8%是关联检查中历史“reproduced”标签的平均比例，分别按结论和按有测量论文等权。它们包含辅助/共享检查，不能解释为科学复现程度。3篇缺测保留缺失。Figure 5c使用摘要与详单一致性，不把冲突状态强行合并；两个26篇集合交集为零，详见正文Table 2。

`anc/audit_*`新增10份公开证据审计文件，包含100篇联合状态、3,241个结果对象、记录冲突、阻塞项、检查拆分敏感性、整数精度检查和具体系统链。对象分类描述声明的比较条件，不认证数值参考或科学结论。源包共6张图、26份ancillary文件及TeX来源。

## 障碍分析与科学边界

论文、Agent、算力、实验设备作为四个排查方向，不作为责任原因的数量结论。三例诊断交代来源可辨识性、缺失科学实现和实测资源依据；均未重跑底层实验。`anc/obstacle_examples.json`保存原始记录及来源；`anc/reason_*`与`anc/diagnostic_followup_*`保留旧标签历史。

旧责任计数位于 `qa/exploratory_attribution/`，明确撤下，不进入论文与源包。[八案复查](诊断复查说明.md)和[四类排查说明](四类归因说明.md)保留为解释材料。新审计不修改公开case或PRAgent权威状态，也不将缺审查当作科学证伪。

## 尚待作者提供

英文作者姓名、顺序、单位与许可尚未填写。稿件和元数据均保留草稿标识，尚未提交arXiv。标题和摘要从同一正文生成，避免不同文件漂移。
