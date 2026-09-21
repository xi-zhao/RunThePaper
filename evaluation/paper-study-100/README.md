# PRAgent：100篇物理论文研究

**当前对外主稿为面向arXiv的技术报告，按统一的100篇项目队列组织。** 正文以科研工作流、具体数值实现和代表性结果展示项目能力。原档案审计稿保留为补充分析。

阅读入口：[技术报告PDF](preprint/PRAgent_Technical_Report.pdf)、[可编辑正文](preprint/report.md)、[中文说明](preprint/中文说明.md)、[arXiv提交准备](preprint/ARXIV_SUBMISSION.md)、[统一100篇附表](manuscript/cohort_100.csv)。实际状态见 [PROGRESS.md](PROGRESS.md)。

已制作并在干净目录验证arXiv草稿源包；英文署名、顺序和单位尚待作者提供，尚未提交arXiv。4张主图包含流程、资源估算、量子游走和量子关联。此前的审计结果及图表仍保存在 `manuscript/`，其边界不被新报告改写。

## 研究问题

论文讨论AI辅助物理复现如何从原文对象、物理条件、实际产物与独立核查建立可追踪的证据链。正文统一分析100篇身份，每项测量分别披露可用性；不按历史来源划分研究组别，不把“100”写成完整复现或成功数量。

主稿包含引言、相关工作、方法、结果、物理验证案例、讨论、结论和参考文献。3张主图展示证据流程、可用性与引用缺口、清单颗粒度与条件声明；补充附图逐篇展示100个身份。统计、输入哈希和关键陈述依据分别见 [figure_data.json](manuscript/figure_data.json) 与 [claim_evidence.csv](manuscript/claim_evidence.csv)。

## 证据与选择历史

当前标准化公开提取覆盖97个队列身份，包含3,666条原清单记录与261条未映射目标恢复记录，共3,927条证据记录；1,721份输入有完整性信息。未提取的测量保持未知。证据记录不是独立科研结果，现有顶层状态、文件数和像素相似度均不作为新的科学成绩。

[cohort.json](cohort.json) 保留2026-09-20冻结的选择记录，包括来源、全部身份与排除理由。它涉及103个身份的选择历史，形成当前100篇队列。选择具有事后性和可行性偏好，不能用于总体成功率或统一预算性能推断。原清单中的分组报告策略已经由后续用户要求改为统一队列呈现；历史文件本身不改写。

固定公开来源为 `43a64cd03824edb136b549f352412e8d263d9361`。原始归档与旧审计保持不变，缺失、失败和未完成项不因当前写稿而删除。每篇的证据入口见[归档报告](analysis/ARCHIVE_REPORT.md)，逐结果记录见[data/results.jsonl](data/results.jsonl)。

## 执行与公开边界

已有归档仅作只读分析，不运行求解器、Notebook、训练、案例测试或科学检查器，不修复旧案例代码。允许检查原文和已存文件、核对版本、比较已有数值及绘图；未知的模型版本、资源和人工介入不填成0。

当前需要开发的生产case由PRAgent管理，来源、合同、代码、诊断和运行记录保存在PRAgent。公开案例必须通过其 `publish_manifest.json` 投影，本稿不手建公共case、不复制私有开发材料。原文导出的部分转置、态传输和离散陈数验证责任写入正文，均没有冒充新的数值实验结果。具体来源与责任记录仍可查 [NEW_PAPERS.md](NEW_PAPERS.md)。

## 继续完善科学结果

1. 沿统一队列核对原文对象、物理条件、数组、比较值与单位，记录证据充分性和未知项。
2. 需要正式执行的case使用受支持且通过核验的生产后端，保留执行失败与受阻状态。
3. 独立审阅每项科学判断，区分自身实现缺陷、原文约定不明、版本差异与候选源文问题。
4. 在相应证据成立后补充科学比较图表和主结论；作者、单位及投稿声明另行据实填写。

## 复算与校验

```bash
python evaluation/paper-study-100/validate_plan.py
python evaluation/paper-study-100/validate_archive_evidence.py
python -m unittest discover -s evaluation/paper-study-100 -p 'test_*.py' -v
python evaluation/paper-study-100/build_archive_evidence.py --repository-root .
python evaluation/paper-study-100/build_archive_report.py
```

以上工具只读取固定公共记录，不执行案例。论文图表与PDF的复算方法见[稿件目录说明](manuscript/README.md)。校验通过表示数据、计数和文件关系符合记录，不表示科学验收通过。
