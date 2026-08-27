# Method Trace

本 case 以公式链为主要证据，详细符号推导见 `DERIVATION_TRACE.md` 和
`EQUATION_CARDS.json`。本文件只记录数值算法边界。

## METHOD001：periodic-QR Lyapunov spectrum

- Source：arXiv v1 main text；正式 Science Bulletin supplement S6 仅作为方法佐证。
- Inputs：复能量 batch、无序序列、`LongRangeModel`。
- Outputs：升序四个 Lyapunov 指数。
- Steps：构造单格点 transfer matrix → 每格点 batched QR → 累计
  `log|diag(R)|` → 除以长度并排序。
- Code：`src/lyapunov_band.py::lyapunov_exponents`。
- Checks：clean beta limit、finite output、OBC/PBC finite-spectrum potential。
- Status：verified for exploratory numerical use。
- Open：论文 QR interval/transfer length 未公开。

## METHOD002：dual winding evaluation

- Source：论文 `nu=M-n_positive` 关系和 twisted-boundary 定义。
- Inputs：probe energy、LE spectrum 或 finite twisted Hamiltonian。
- Outputs：integer winding。
- Paths：positive-LE count；`arg det[H(theta)-E]` 的 phase unwrap。
- Code：`winding_from_lyapunov`、`direct_twist_winding`。
- Checks：4 个区域 4/4 一致；三个谱洞恢复 `-1,+1,-1`。
- Status：verified at `L=160` direct-check scale。

## METHOD003：spectral density from potential

- Source：二维 Poisson/Laplacian 关系。
- Inputs：复能量规则网格上的 Thouless potential。
- Outputs：归一化非负 density proxy。
- Steps：中心差分 Laplacian → clipped finite-grid density → 与 ED histogram
  使用相同网格平滑与归一化。
- Checks：OBC/PBC density overlap `0.923/0.934`。
- Status：feature-level verified；边界 stencil 不用于论文级精确密度声明。
