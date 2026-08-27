# Paper Map

## Identity

- Paper ID: `2607.08767`
- Title: *Plaquette: A hardware-aware design platform for fault-tolerant quantum computers*
- Source: <https://arxiv.org/abs/2607.08767>
- Local paper inputs: `raw/paper.pdf`, `raw/paper.txt`

## Numeric Inventory

| Paper object | Scientific role | Decision | Local target / blocker |
| --- | --- | --- | --- |
| Table III | generalized-Pauli transition/error weights | exact target | `T_TABLE3`, Eq. (12) |
| Fig. 5(a) | coherent vs Clifford logical error | proxy only | `F5A_PROXY`; declared proxy reproduces only the scientific direction |
| Fig. 5(b) | sector-aware leakage | uncovered | `T_FIG5B`; independent circuit, sampler and decoder not implemented |
| Fig. 6(a) | distance-three transmon sampler comparison | uncovered | `T_FIG6A`; channel-to-QEC scan not implemented |
| Fig. 6(b) | distance-nine transmon sampler comparison | uncovered | `T_FIG6B`; larger-code scan and convergence not implemented |
| Fig. 7 | transmon threshold fits | uncovered | `T_FIG7`; finite-size simulation and fit not implemented |
| Fig. 8 | neutral-atom threshold surface | uncovered | `T_FIG8`; Rydberg channel/scan/fit not implemented; exact 15 rays unprinted |
| Fig. 10 | thermal transition matrix | exact target | `T_FIG10`, Eqs. (20)–(21) |
| Fig. 11 | ion-trap logical errors | uncovered | `T_FIG11`; sector-history QEC and threshold fit not implemented |

Figures 1–4 and 9 and Tables I–II are schematics or qualitative inventories, not
numeric reproduction targets.

## Claim Boundary

The paper-exact targets use only equations and parameters printed in the paper.
The Fig. 5(a) proxy uses the printed error channel but an independently declared
three-qubit memory circuit, so its numerical distance from the paper cannot be
used to judge the paper. No source pixels, author arrays or author code are
scientific inputs. Missing author arrays or commercial Plaquette access are not
treated as prerequisites: the six uncovered targets require independent
implementations first, after which any genuinely unpublished convention can be
adjudicated as a narrower external boundary.
