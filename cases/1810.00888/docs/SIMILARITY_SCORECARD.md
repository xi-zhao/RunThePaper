# Similarity scorecard

主指标是九个预声明科学理论区域内的前景灰度逐像素相似度，均值 45.928/100。该指标只在数值数据冻结后计算，不能反向调整物理参数或数组。

包含背景的同区域全灰度相似度均值为 89.408/100，仅反映画幅和留白等排版因素，不作为主像素结论。

Harness 综合分为 80.33/100，等级 numerical_feature_reproduction：公式、参数、科学目标和范围均通过；图形前景仍存在字体、点密度、标签与绘制细节差异。完整逐目标数据见 outputs/checks/similarity_scorecard.json 和 pixel_evidence.json。
