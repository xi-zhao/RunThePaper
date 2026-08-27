# Target ledger

| Target | Item count | Observable | Scientific acceptance | W1 coverage |
| --- | ---: | --- | --- | --- |
| T001 | 3 | two-level `theta,k,Q` | closed form equals tilted `4x4` Liouvillian; `theta(0)=0`, `Q=-2/3` | covered |
| T002 | 2 | two-level rate function | numerical Legendre transform equals printed closed form and minimum at `k=2/3` | covered |
| T003 | 3 | two-level event rasters | seeded clean-room jump records have rates `2`, `2/3`, `2/9` within finite-time tolerance | covered |
| T004 | 2 | three-level `theta` | direct tilted `9x9` Liouvillian, physical zero at `s=0`, active-side two-level approach | covered |
| T005 | 3 | three-level `k,Q` | derivatives/eigenvalue perturbation agree; active/inactive limits and positive crossover peak | covered |
| T006 | 2 | three-level rate function | Legendre duality, minimum at physical activity, asymmetric tails versus Poisson | covered |
| T007 | 2 | blinking event rasters | postselected seeded physical quantum-jump windows realize inactive and active rates | covered |
| T008 | 2 | micromaser `alpha=1.2pi` | tridiagonal tilted generator, convergence in photon cutoff, transition at negative `s` | covered; reconstructed parameters |
| T009 | 2 | micromaser `alpha=2pi` | cutoff convergence and first-order activity jump at/near `s=0` | covered; reconstructed parameters |
| T010 | 3 | micromaser biased distributions | nonnegative normalized dominant right eigenvectors; active distribution at larger photon number | covered; reconstructed parameters |
| T011 | 2 | general Doob map and two-level mapped rate | transformed jumps are trace preserving and two-level rates rescale by `exp(-s/3)` | covered |
| T012 | 1 | three-level inactive-side mapped realization | mapped Hamiltonian contains the claimed `|1>-|2>` drive/effective detuning and suppresses emission | covered; fresh review pending |

`T012` 现已从正文三能级模型和 Doob 公式独立实现。显式映射算符与超算符相似
变换的最大残差为 `1.53e-13`；在 `s=0.5`，新增 `|1~>-|2~>` 耦合为原始
`Omega_2` 的 `5.56` 倍，发射率降至无偏系统的 `1.96%`。隔离运行
`0911.0556-t012-doob-v2-20260824` 已通过且未访问 `raw/` 或原图；剩余边界仅是
新 artifact 尚未经过 fresh-context 独立评审。
