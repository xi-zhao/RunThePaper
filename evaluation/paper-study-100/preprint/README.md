# PRAgent 技术预印本

**定位：适合公开阅读、引用与个人成果展示的科研技术报告。** 主线是研究方法、系统设计与具体科学实现，不以档案审计作为主贡献；不依赖期刊投稿来成立。

- [10页英文技术报告](PRAgent_Technical_Report.pdf)
- [可编辑正文](report.md)、[独立LaTeX源文件](main.tex)
- [arXiv草稿源包](arxiv_source_draft.zip)
- [中文摘要与阅读说明](中文说明.md)
- [提交说明](ARXIV_SUBMISSION.md)、[待填写的提交元数据](submission_metadata.json)

4张主图分别展示研究工作流、哈密顿模拟资源估算、量子游走和量子关联。报告统一保留100篇项目队列。原[档案审计稿](../manuscript/paper.md)保留为补充分析，不再作为当前对外主稿。

## 可复算成果

Figure 1为重新设计并逐项核对的概念架构图；Figures 2-4由固定公开版本的数值数组重绘，没有运行原案例求解器，也没有复制作者原图。`build_evidence.py`读取公开Git对象，复算量子游走粒子数守恒残差和资源比例，保存输入哈希及结果摘要。物理模型、原始理论与源论文作者明确归属；报告贡献为实现、工作流与科研工件组织。

```bash
python build_evidence.py
bash build_report.sh
python package_arxiv.py
```

数值图环境沿用 `../manuscript/requirements.txt`。Figure 1保留已审阅的设计图；`build_figure1.py`使用 `reportlab==4.4.9`将原PNG无像素修改地封装为PDF。执行数据复算不会覆盖该设计。排版使用Pandoc和标准PDFLaTeX，没有本机系统字体、绝对文件路径或非标准期刊类依赖。打包工具在干净目录中解包并执行两次PDFLaTeX，检查每张引用图和100个队列身份。

## 尚待作者提供

英文作者姓名、顺序和单位尚未填写。`authors.tex`在预览稿中明确标出这一点，提交元数据与源包也保持草稿状态。用户补齐后重新构建即可。arXiv授权许可、账号与分类endorsement需在实际提交时确认；本目录不代表已提交或已公告。
