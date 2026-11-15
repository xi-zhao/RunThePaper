"""Separate odd-cycle inequalities and export a rational covering certificate."""
import argparse
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra


def odd_part(walk):
    stack, position = [], {}
    for v in walk:
        if v in position:
            start = position[v]
            cycle = stack[start:]
            if len(cycle) % 2:
                return cycle
            for removed in stack[start+1:]:
                del position[removed]
            stack = stack[:start+1]
        else:
            position[v] = len(stack)
            stack.append(v)
    raise ValueError("odd closed walk did not contain an odd simple cycle")


def separate(n, edges, weights):
    rows, cols, values = [], [], []
    edge_ids = {tuple(sorted(e)): j for j, e in enumerate(edges)}
    for j, (a, b) in enumerate(edges):
        for parity in (0, 1):
            u, v = 2*a+parity, 2*b+1-parity
            rows += [u, v]
            cols += [v, u]
            values += [max(0., weights[j])]*2
    graph = csr_matrix((values, (rows, cols)), shape=(2*n, 2*n))
    distances, parents = dijkstra(graph, directed=True, indices=2*np.arange(n), return_predecessors=True)
    found = {}
    for v in range(n):
        if distances[v, 2*v+1] >= 1-1e-8:
            continue
        path = [2*v+1]
        while path[-1] != 2*v:
            parent = int(parents[v, path[-1]])
            assert parent >= 0 and len(path) <= 2*n
            path.append(parent)
        cycle = odd_part([p//2 for p in reversed(path)])
        ids = tuple(sorted(edge_ids[tuple(sorted((a, b)))] for a, b in zip(cycle, cycle[1:]+cycle[:1])))
        found[ids] = cycle
    return found


def solve(graph):
    start = time.monotonic()
    n, edges = graph["n"], graph["edges"]
    m = len(edges)
    cycles = separate(n, edges, np.zeros(m))
    history = []
    for iteration in range(250):
        ids = list(cycles)
        rows = np.concatenate([np.full(len(c), j) for j, c in enumerate(ids)])
        cols = np.concatenate(ids)
        matrix = csr_matrix((-np.ones(len(rows)), (rows, cols)), shape=(len(ids), m))
        fitted = linprog(np.ones(m), A_ub=matrix, b_ub=-np.ones(len(ids)), bounds=(0., 1.),
                         method="highs", options={"dual_feasibility_tolerance": 1e-8,
                                                  "primal_feasibility_tolerance": 1e-8})
        assert fitted.success, fitted.message
        more = separate(n, edges, fitted.x)
        added = {k: v for k, v in more.items() if k not in cycles}
        history.append(dict(iteration=iteration, cycles=len(cycles), uncut_lower=float(fitted.fun),
                            new_violations=len(added)))
        if not added:
            break
        cycles.update(added)
    denominator = 10**8
    dual = np.maximum(0., -fitted.ineqlin.marginals)
    numerators = np.floor(dual*denominator).astype(np.int64)
    load = np.asarray((-matrix).T @ numerators).ravel().astype(np.int64)
    denominator = max(denominator, int(load.max()))
    certificate = [dict(edges=list(c), vertices=cycles[c], numerator=int(a))
                   for c, a in zip(ids, numerators) if a > 0]
    total = sum(c["numerator"] for c in certificate)
    return dict(n=n, degree=graph["k"], seed=graph["seed"], edge_count=m,
                denominator=denominator, uncut_lower_numerator=total,
                cut_upper=m-(total+denominator-1)//denominator, cycles=certificate,
                rounds=history, seconds=time.monotonic()-start,
                final_lp_uncut_lower=float(fitted.fun), separation_closed=not added)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("degree", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    graph, = [g for g in json.loads(Path("config/graphs.json").read_text())["cases"]
              if (g["n"], g["k"]) == (156, args.degree)]
    result = solve(graph)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(args.degree, result["cut_upper"], len(result["rounds"]), result["seconds"], flush=True)


if __name__ == "__main__":
    main()
