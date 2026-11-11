# 97篇归档证据提取报告

**这是归档目录与字节完整性结果，尚未形成新的科学一致性判断。**

固定来源为 RunThePaper `43a64cd03824edb136b549f352412e8d263d9361`。提取器仅通过 Git 对象读取原有材料，未导入案例代码，未运行旧求解器、测试或科学检查器。

| 观察项 | 数量 | 含义 |
|---|---:|---|
| 固定历史论文 | 97 | 原100篇中预先登记纳入本分析的97篇 |
| 原归档对象条目 | 3666 | 原清单的粒度不同，不能作为统一成果分母 |
| 清单未映射的历史目标 | 261 | 单独保留以供补核对，不增加独立结果数 |
| 当前证据记录 | 3927 | 对象条目加未映射目标；不是科学成果数 |
| 已读取并哈希的来源文件 | 1721 | 能复核提取输入的字节与Git对象 |
| 有可定位公共工件的记录 | 2767 | 文件存在，不代表其科学内容正确 |
| 有公共引用缺口的记录 | 2444 | 与上一行可重叠；不推断私有档案也缺失 |
| 新科学执行 / 新验收结论 | 0 / 0 | 无旧案例重跑，无新成功率 |

模型、人工干预、实际物理条件和逐值比较仍为未知。历史标签保存在独立字段，不能由 `paper_exact`、`passed`、旧混合分或文件数量推导新结论。

## 每篇的核对入口

以下所有行的原文语义核对状态均为 `not_rechecked`。对象数不齐或粒度不同必须回到原文核齐后再决定分母。

| 论文 | 原对象 | 未映射目标 | 有工件的记录 | 有引用缺口的记录 |
|---|---:|---:|---:|---:|
| [0709.0548](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/0709.0548) | 47 | 0 | 44 | 44 |
| [0911.0556](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/0911.0556) | 27 | 2 | 26 | 26 |
| [10.1007-s11433-024-2478-8](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1007-s11433-024-2478-8) | 38 | 0 | 34 | 34 |
| [10.1038-s41467-025-67768-4](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1038-s41467-025-67768-4) | 47 | 0 | 16 | 16 |
| [10.1038-s41586-024-08262-7](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1038-s41586-024-08262-7) | 7 | 1 | 3 | 2 |
| [10.1038-s41586-026-10720-3](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1038-s41586-026-10720-3) | 28 | 0 | 13 | 11 |
| [10.1103-PRXQuantum.6.010331](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1103-PRXQuantum.6.010331) | 41 | 0 | 22 | 22 |
| [10.1103-PhysRevB.91.085420](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1103-PhysRevB.91.085420) | 6 | 0 | 6 | 6 |
| [10.1103-PhysRevLett.124.113601](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1103-PhysRevLett.124.113601) | 15 | 0 | 14 | 14 |
| [10.1126-science.aaw1611](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1126-science.aaw1611) | 92 | 0 | 38 | 38 |
| [10.1145-3297858.3304023](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/10.1145-3297858.3304023) | 14 | 0 | 7 | 0 |
| [1004.0190](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1004.0190) | 1 | 10 | 10 | 10 |
| [1106.2978](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1106.2978) | 25 | 0 | 24 | 24 |
| [1206.2505](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1206.2505) | 15 | 0 | 15 | 15 |
| [1212.3324](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1212.3324) | 15 | 1 | 9 | 9 |
| [1302.5069](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1302.5069) | 27 | 0 | 27 | 27 |
| [1508.03344](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1508.03344) | 6 | 1 | 7 | 7 |
| [1608.02589](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1608.02589) | 137 | 3 | 139 | 74 |
| [1706.07435](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1706.07435) | 17 | 0 | 15 | 0 |
| [1708.05014](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1708.05014) | 72 | 1 | 68 | 67 |
| [1709.03478](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1709.03478) | 20 | 0 | 13 | 13 |
| [1710.10890](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1710.10890) | 44 | 4 | 21 | 23 |
| [1711.03528](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1711.03528) | 10 | 0 | 10 | 0 |
| [1711.08863](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1711.08863) | 28 | 3 | 4 | 3 |
| [1711.09418](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1711.09418) | 20 | 5 | 22 | 4 |
| [1803.01876](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1803.01876) | 23 | 3 | 25 | 25 |
| [1803.07128](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1803.07128) | 22 | 1 | 15 | 15 |
| [1804.03151](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1804.03151) | 17 | 0 | 13 | 13 |
| [1804.04672](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1804.04672) | 65 | 1 | 64 | 64 |
| [1805.00931](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1805.00931) | 38 | 1 | 37 | 7 |
| [1807.01815](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1807.01815) | 17 | 0 | 15 | 15 |
| [1807.02414](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1807.02414) | 9 | 4 | 10 | 9 |
| [1807.03311](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1807.03311) | 24 | 0 | 16 | 16 |
| [1807.10084](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1807.10084) | 65 | 0 | 62 | 61 |
| [1807.10676](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1807.10676) | 88 | 3 | 77 | 77 |
| [1810.00888](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1810.00888) | 89 | 14 | 103 | 103 |
| [1811.08017](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1811.08017) | 10 | 0 | 6 | 0 |
| [1812.05561](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1812.05561) | 75 | 1 | 76 | 76 |
| [1903.05124](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1903.05124) | 55 | 0 | 45 | 45 |
| [1904.10246](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1904.10246) | 15 | 0 | 9 | 9 |
| [1905.09460](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1905.09460) | 38 | 1 | 33 | 37 |
| [1910.00020](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1910.00020) | 12 | 0 | 11 | 0 |
| [1910.08980](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/1910.08980) | 6 | 5 | 4 | 9 |
| [2005.09722](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2005.09722) | 134 | 5 | 137 | 5 |
| [2005.12667](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2005.12667) | 135 | 9 | 101 | 101 |
| [2103.03074](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2103.03074) | 33 | 10 | 36 | 36 |
| [2105.08076](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2105.08076) | 11 | 0 | 9 | 9 |
| [2305.15556](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2305.15556) | 8 | 0 | 7 | 7 |
| [2401.05830](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2401.05830) | 39 | 2 | 29 | 29 |
| [2401.08523](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2401.08523) | 7 | 0 | 7 | 7 |
| [2402.14814](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2402.14814) | 73 | 13 | 38 | 38 |
| [2404.08378](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2404.08378) | 57 | 11 | 38 | 41 |
| [2406.13410](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2406.13410) | 50 | 1 | 26 | 26 |
| [2407.01296](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2407.01296) | 87 | 5 | 70 | 59 |
| [2409.18176](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2409.18176) | 41 | 0 | 30 | 30 |
| [2412.14271](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2412.14271) | 34 | 0 | 31 | 2 |
| [2502.20558](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2502.20558) | 305 | 10 | 30 | 267 |
| [2504.08598](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2504.08598) | 11 | 0 | 5 | 2 |
| [2506.06669](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2506.06669) | 118 | 7 | 63 | 17 |
| [2507.09447](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2507.09447) | 24 | 0 | 21 | 21 |
| [2510.12880](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2510.12880) | 13 | 7 | 9 | 8 |
| [2510.26761](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2510.26761) | 7 | 3 | 9 | 9 |
| [2511.11394](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2511.11394) | 21 | 0 | 21 | 17 |
| [2512.08279](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2512.08279) | 8 | 9 | 13 | 13 |
| [2512.23799](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2512.23799) | 13 | 1 | 4 | 4 |
| [2602.12212](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2602.12212) | 65 | 0 | 65 | 65 |
| [2604.08669](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2604.08669) | 23 | 0 | 19 | 19 |
| [2605.02873](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2605.02873) | 8 | 0 | 8 | 0 |
| [2605.25398](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2605.25398) | 37 | 0 | 20 | 20 |
| [2605.25594](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2605.25594) | 73 | 2 | 58 | 16 |
| [2606.30255](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2606.30255) | 18 | 0 | 8 | 8 |
| [2607.00718](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.00718) | 25 | 0 | 23 | 19 |
| [2607.02157](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.02157) | 46 | 0 | 43 | 43 |
| [2607.08212](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.08212) | 45 | 1 | 41 | 40 |
| [2607.08767](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.08767) | 16 | 0 | 9 | 7 |
| [2607.15070](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.15070) | 13 | 0 | 12 | 0 |
| [2607.15597](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.15597) | 109 | 6 | 92 | 68 |
| [2607.22976](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.22976) | 23 | 0 | 17 | 0 |
| [2607.23978](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.23978) | 79 | 1 | 39 | 17 |
| [2607.27060](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.27060) | 18 | 0 | 12 | 12 |
| [2607.28795](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2607.28795) | 85 | 9 | 61 | 61 |
| [2608.03987](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2608.03987) | 33 | 0 | 6 | 3 |
| [2608.05312](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/2608.05312) | 74 | 0 | 72 | 72 |
| [PhysRevA.47.5138](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/PhysRevA.47.5138) | 10 | 0 | 7 | 7 |
| [PhysRevB.14.2239](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/PhysRevB.14.2239) | 8 | 3 | 11 | 11 |
| [PhysRevLett.132.113001](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/PhysRevLett.132.113001) | 33 | 6 | 13 | 8 |
| [PhysRevLett.133.191801](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/PhysRevLett.133.191801) | 17 | 0 | 5 | 5 |
| [cond-mat-0411737](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/cond-mat-0411737) | 17 | 19 | 20 | 30 |
| [cond-mat-0503511](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/cond-mat-0503511) | 45 | 2 | 47 | 2 |
| [cond-mat-0509490](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/cond-mat-0509490) | 1 | 5 | 5 | 5 |
| [cond-mat-0610854](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/cond-mat-0610854) | 4 | 0 | 4 | 4 |
| [physics-0206018](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/physics-0206018) | 7 | 0 | 3 | 0 |
| [physics-9712001](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/physics-9712001) | 7 | 22 | 28 | 28 |
| [quant-ph-0211074](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/quant-ph-0211074) | 6 | 16 | 22 | 21 |
| [quant-ph-0403025](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/quant-ph-0403025) | 5 | 0 | 4 | 4 |
| [quant-ph-0507004](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/quant-ph-0507004) | 20 | 0 | 20 | 20 |
| [quant-ph-9709029](https://github.com/xi-zhao/RunThePaper/tree/43a64cd03824edb136b549f352412e8d263d9361/cases/quant-ph-9709029) | 0 | 11 | 11 | 11 |

## 复算与接续

`build_archive_evidence.py` 从固定Git版本重建 data；`validate_archive_evidence.py` 校验身份、计数和证据索引；`build_archive_report.py` 重建本报告、描述计数和核对队列。所有工具仅处理归档资料。

后续逐结果核对应另行追加可定位的审阅记录，保留本次提取快照。先确认原文版本、原始对象、条件和数据字段，再写有单位的比较值。原文未核齐时不得报告整篇覆盖率。
