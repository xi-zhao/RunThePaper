# arXiv提交准备

核对日期：2026-09-21。当前已准备技术报告正文、图表及可独立编译的草稿源包；尚未向arXiv提交。

## 文件与编译

上传源文件包 `arxiv_source_draft.zip`，顶层文件为 `main.tex`，处理器选择PDFLaTeX。包内包括 `authors.tex`、6张实际使用的PDF图和19个ancillary数据文件。主PDF不混入源文件包；无需本机字体、绝对路径或shell escape。

arXiv要求由TeX生成的文章提供源文件，图表必须一并包含；提交时仍需查看arXiv服务器生成的PDF。来源：[Submission Overview](https://info.arxiv.org/help/submit/index.html)、[Submit TeX/LaTeX](https://info.arxiv.org/help/submit_tex.html)。

## 投稿字段

标题、英文摘要和comments草稿见 `submission_metadata.json`。作者姓名、作者顺序、单位及分发许可保持未填，不能从GitHub用户名推断。作者信息补齐后更新 `authors.tex` 并重建，移除预览页中的待填提示。

**建议主分类：physics.comp-ph。** 这是根据本稿主要内容作出的编辑判断：核心是用于物理问题的计算方法与科研工作流，官方该分类覆盖应用于物理的计算科学。可再考虑quant-ph交叉分类，最终分类由作者选择并经审核。来源：[Category Taxonomy](https://arxiv.org/category_taxonomy)。

arXiv进行内容与主题审核，准备好稿件不保证被收录。首次在某分类提交可能需要endorsement，具体以账号页面为准。来源：[Moderation](https://info.arxiv.org/help/moderation/index.html)、[Endorsement](https://info.arxiv.org/help/endorsement.html)。这份技术报告无需先取得期刊录用；但仍应是一份可评议的科学或技术贡献，不以个人介绍替代方法和结果。

## 当前提交前缺项

1. 作者提供英文署名、作者顺序、单位，以及真实的贡献与责任确认。
2. 作者选择arXiv分发许可，并检查自己的账号和对应分类资格。
3. 在署名补齐版本上确认最终正文和图表，再上传并检查平台编译结果。

上述步骤尚未执行。当前源包包含明确的作者待填标识，不应直接作为最终稿提交。`submission_metadata.json`中的 `ready_for_submission` 为false。
