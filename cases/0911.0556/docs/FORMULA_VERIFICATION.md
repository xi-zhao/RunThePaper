# Formula Verification

机器结果：`outputs/checks/formula_verification.json`。

| Formula | 数值角色 | Gate | 核验方式 |
| --- | --- | --- | --- |
| EQ001 Lindblad 方程 | 物理生成元 | verified | 来源追踪、trace-preservation |
| EQ002 tilted operator | 轨迹生成函数 | verified | `s=0` 退化为物理生成元 |
| EQ003 SCGF/cumulants | T001/T004/T005/T008/T009 | verified | 闭式两能级导数交叉检查 |
| EQ004 两能级闭式 | T001–T003/T011 | verified | 通用 4x4 本征求解误差 `<2e-12` |
| EQ005 Legendre dual | T002/T006 | verified | 与解析 CMP rate function 对比 |
| EQ006 三能级模型 | T004–T007 | verified | trace 与随机轨迹检查 |
| EQ007 micromaser jumps | T008–T010 | verified | 光子数 birth/death 率推导 |
| EQ008 birth–death reduction | 稳定 micromaser solver | verified | 对称/非对称两种本征求解 |
| EQ009 Doob transform | T003/T007/T011 | verified | 左零模与精确 rate scaling |

EQ007 的公式本身可数值化，但原 Letter 未给 `N_ex` 和热占据数；这限制参数身份，不关闭公式 gate。
