# Derivation of the SABRE reproduction

This case reconstructs the routing algorithm from the paper's problem
definition, equations, pseudocode and examples. It does not use the authors'
implementation as a numerical input.

## Routing state

Let \(\pi(q)\) map logical qubit \(q\) to a vertex of the hardware coupling
graph. Two-qubit gates form a dependency DAG. The front layer \(F\) contains
the gates whose predecessors have executed. A gate \((q_i,q_j)\) is executable
exactly when \(\pi(q_i)\) and \(\pi(q_j)\) are adjacent in the coupling graph.

When no front-layer gate is executable, candidate SWAPs are restricted to
hardware edges incident on a physical qubit occupied by a logical qubit in
\(F\). Applying a SWAP updates \(\pi\), after which newly executable gates are
removed and the front layer is advanced.

## Distance objective

All-pairs shortest-path distances \(D[u,v]\) are computed on the coupling
graph. The basic routing cost is

\[
H_{\mathrm{basic}}(\pi)=
\frac{1}{|F|}\sum_{g\in F}
D\!\left[\pi(g.q_1),\pi(g.q_2)\right].
\]

The look-ahead extension adds an analogous average over a bounded successor
set \(E\), weighted by the paper's parameter \(W\). The decay variant multiplies
the total by the larger recent-use penalty on the two physical endpoints of a
candidate SWAP. This trades a small increase in gate count for more parallel
SWAP placement and lower circuit depth.

## Initial mapping

The reverse-traversal procedure starts from a temporary mapping, routes the
forward circuit, reverses the circuit and routes from the forward final
mapping. The reverse final mapping becomes the initial mapping for the final
forward traversal. The reproduced benchmark checks whether this process
improves or preserves both additional-gate count and depth.

## Observable reconstruction

For every routed circuit the implementation records inserted SWAPs,
three-CNOT-equivalent overhead per SWAP, routed depth, runtime and a final
hardware-legality check. Table II comparisons use the published circuit and
coupling-graph identities. Exact optimized row values remain conditional on
unpublished random seeds, tie breaking and baseline post-processing; those
missing choices are reported as a publication boundary rather than inferred
from the table values.
