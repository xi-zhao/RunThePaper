# Method Trace

1. `MTH_ED`：生成 open-boundary Anderson eigensystem；A100 优先、CPU/LAPACK fallback。
2. `MTH_REDUCE`：按谱中心 20% 选择外层状态，分块计算所有内层状态的矩阵元与核函数。
3. `MTH_SCALE`：输出 peak、finite-size、spectral、distribution 所需的不可逆 sufficient statistics。
4. `MTH_PHENO`：独立采样 broadened-Drude relaxation-rate 分布，检查 Lorentzian half-width 和 `2-zeta` 指数。

执行入口：`scripts/run_paper_scale.py`；完整参数：`config/paper_scale.json`；机器合同：`run_contract.paper_scale.json`。

RenderContract 在数值冻结之后才能访问原图，只允许优化画幅、轴、字体、线型、调色板和插值，不得修改任何数值数组或物理参数。
