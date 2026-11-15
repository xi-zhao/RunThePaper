"""Branch on binary edge parities and retain rational proof leaves."""
import json
from pathlib import Path
import time
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from maxcut_signed_cycles import signed_separator


def consistent(n, edges, fixed):
    adjacent = [[] for _ in range(n)]
    for e, z in fixed.items():
        a, b = edges[e]
        adjacent[a].append((b, 1-z))
        adjacent[b].append((a, 1-z))
    labels = {}
    for v in range(n):
        if v in labels:
            continue
        labels[v] = 0
        todo = [v]
        while todo:
            a = todo.pop()
            for b, parity in adjacent[a]:
                expected = labels[a] ^ parity
                if b in labels:
                    if labels[b] != expected:
                        return False
                else:
                    labels[b] = expected
                    todo.append(b)
    return True


def main():
    start = time.monotonic()
    graph, = [g for g in json.loads(Path("config/graphs.json").read_text())["cases"]
              if (g["n"], g["k"]) == (156, 5)]
    edges = graph["edges"]
    seed = json.loads(Path("config/cycle-seed.json").read_text())
    cuts = {(tuple(c["positive"]), tuple(c["negative"])): c["vertices"] for c in seed["cycles"]}
    nodes = [dict(parent=None, fixed={})]
    pending = [0]
    while pending and len(nodes) < 511 and time.monotonic()-start < 150:
        node_id = pending.pop()
        node = nodes[node_id]
        fixed = {int(k): v for k, v in node["fixed"].items()}
        if not consistent(graph["n"], edges, fixed):
            node["status"] = "parity_contradiction"
            continue
        for iteration in range(80):
            keys = list(cuts)
            rows, columns, weights = [], [], []
            for j, (positive, negative) in enumerate(keys):
                rows.extend([j]*(len(positive)+len(negative)))
                columns.extend(positive+negative)
                weights.extend([1]*len(positive)+[-1]*len(negative))
            matrix = csr_matrix((weights, (rows, columns)), shape=(len(keys), len(edges)))
            rhs = np.array([1-len(negative) for _, negative in keys])
            bounds = [(fixed[e], fixed[e]) if e in fixed else (0, 1) for e in range(len(edges))]
            fit = linprog(np.ones(len(edges)), A_ub=-matrix, b_ub=-rhs, bounds=bounds, method="highs")
            assert fit.success, fit.message
            if fit.fun > 65.00001:
                break
            added = {k: v for k, v in signed_separator(graph["n"], edges, fit.x).items() if k not in cuts}
            if not added:
                break
            cuts.update(added)
        denominator = 10**8
        numerators = np.floor(np.maximum(0., -fit.ineqlin.marginals)*denominator).astype(np.int64)
        load = np.asarray(matrix.T@numerators).ravel().astype(np.int64)
        total = sum(int(a)*int(b) for a, b in zip(numerators, rhs))
        total += sum((denominator-int(load[e]))*v for e, v in fixed.items())
        total -= sum(max(0, int(load[e])-denominator) for e in range(len(edges)) if e not in fixed)
        upper = len(edges)-(total+denominator-1)//denominator
        node.update(upper=upper, uncut_lower_numerator=total, denominator=denominator,
                    certificate=[dict(positive=list(p), negative=list(q), vertices=cuts[p, q], numerator=int(a))
                                 for (p, q), a in zip(keys, numerators) if a > 0])
        if upper <= 324:
            node["status"] = "bounded"
        else:
            free = [e for e in range(len(edges)) if e not in fixed and 1e-6 < fit.x[e] < 1-1e-6]
            if not free:
                node["status"] = "integral_candidate"
                node["edge_values"] = np.rint(fit.x).astype(int).tolist()
                break
            split = min(free, key=lambda e: abs(fit.x[e]-.5))
            children = []
            for value in (0, 1):
                children.append(len(nodes))
                nodes.append(dict(parent=node_id, fixed={**fixed, split: value}))
            node.update(status="split", split=split, children=children)
            pending.extend(reversed(children))
        print(node_id, node["status"], upper, "pending", len(pending), "seconds", round(time.monotonic()-start, 1), flush=True)
    output = dict(n=156, degree=5, nodes=nodes, pending=pending,
                  completed=not pending and all(n.get("status") in {"split", "bounded", "parity_contradiction"} for n in nodes),
                  seconds=time.monotonic()-start)
    Path("results/maxcut-branch.json").write_text(json.dumps(output, separators=(",", ":"))+"\n")
    print("complete", output["completed"], "nodes", len(nodes), output["seconds"], flush=True)


if __name__ == "__main__":
    main()
