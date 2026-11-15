"""Add every odd signed-cycle inequality via a parity-cover separator."""
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from maxcut_cycles import separate


def signed_separator(n, edges, z):
    rows, cols, weights = [], [], []
    index = {tuple(sorted(e)): j for j, e in enumerate(edges)}
    for j, (a, b) in enumerate(edges):
        for parity in (0, 1):
            for cross in (0, 1):
                u, v = 2*a+parity, 2*b+(parity ^ cross)
                rows.extend([u, v])
                cols.extend([v, u])
                weights.extend([np.clip(z[j] if cross else 1-z[j], 0., 1.)]*2)
    graph = csr_matrix((weights, (rows, cols)), shape=(2*n, 2*n))
    distance, predecessor = dijkstra(graph, directed=True, indices=2*np.arange(n), return_predecessors=True)
    cuts = {}
    for root in range(n):
        if distance[root, 2*root+1] >= 1-1e-8:
            continue
        path = [2*root+1]
        while path[-1] != 2*root:
            parent = int(predecessor[root, path[-1]])
            assert parent >= 0 and len(path) <= 2*n
            path.append(parent)
        stack, position = [], {}
        cycle = None
        for vertex in reversed(path):
            base = vertex//2
            if base in position:
                first = position[base]
                if stack[first] % 2 != vertex % 2:
                    cycle = stack[first:] + [vertex]
                    break
                for old in stack[first+1:]:
                    del position[old//2]
                stack = stack[:first+1]
            else:
                position[base] = len(stack)
                stack.append(vertex)
        assert cycle is not None and len(cycle) >= 4
        positive, negative = [], []
        for a, b in zip(cycle, cycle[1:]):
            e = index[tuple(sorted((a//2, b//2)))]
            (positive if a % 2 != b % 2 else negative).append(e)
        assert len(positive) % 2
        key = (tuple(sorted(positive)), tuple(sorted(negative)))
        cuts[key] = [v//2 for v in cycle[:-1]]
    return cuts


def main():
    start = time.monotonic()
    graph, = [g for g in json.loads(Path("config/graphs.json").read_text())["cases"]
              if (g["n"], g["k"]) == (156, 5)]
    n, edges = graph["n"], graph["edges"]
    cuts = {(k, ()): v for k, v in separate(n, edges, np.zeros(len(edges))).items()}
    history = []
    for step in range(250):
        keys = list(cuts)
        rows, cols, values = [], [], []
        for i, (positive, negative) in enumerate(keys):
            rows.extend([i]*(len(positive)+len(negative)))
            cols.extend(positive+negative)
            values.extend([1]*len(positive)+[-1]*len(negative))
        matrix = csr_matrix((values, (rows, cols)), shape=(len(keys), len(edges)))
        rhs = np.array([1-len(negative) for _, negative in keys])
        result = linprog(np.ones(len(edges)), A_ub=-matrix, b_ub=-rhs, bounds=(0., 1.),
                         method="highs", options={"dual_feasibility_tolerance": 1e-8,
                                                  "primal_feasibility_tolerance": 1e-8})
        assert result.success
        more = {k: v for k, v in signed_separator(n, edges, result.x).items() if k not in cuts}
        history.append(dict(iteration=step, cuts=len(keys), uncut_lower=float(result.fun), added=len(more)))
        if not more:
            break
        cuts.update(more)
    denominator = 10**8
    numerator = np.floor(np.maximum(0., -result.ineqlin.marginals)*denominator).astype(np.int64)
    load = np.asarray(matrix.T@numerator).ravel().astype(np.int64)
    penalty = int(np.maximum(0, load-denominator).sum())
    bound = sum(int(a)*int(b) for a, b in zip(numerator, rhs))-penalty
    certificate = [dict(positive=list(p), negative=list(q), vertices=cuts[p, q], numerator=int(a))
                   for (p, q), a in zip(keys, numerator) if a > 0]
    output = dict(n=n, degree=5, seed=graph["seed"], denominator=denominator,
                  numerator=bound, upper_bound_penalty=penalty,
                  cut_upper=len(edges)-(bound+denominator-1)//denominator,
                  cycles=certificate, rounds=history, seconds=time.monotonic()-start,
                  final_lp_uncut_lower=float(result.fun), separation_closed=not more)
    Path("results/maxcut-signed-k5.json").write_text(json.dumps(output, indent=2)+"\n")
    print(output["cut_upper"], result.fun, len(history), output["seconds"], flush=True)


if __name__ == "__main__":
    main()
