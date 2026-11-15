"""Cover all local/global threshold cells using monotone high-weight counts."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from pauli_thresholds import components


def weight_bounds(groups, weight, alpha, target):
    k = len(groups)-1
    pieces = []
    for a in range(max(1, weight-k), min(k, weight-1)+1):
        x, y = groups[a], groups[weight-a]
        x = x[x > alpha]
        y = y[y > alpha]
        if len(x) and len(y):
            pieces.append((x[:, None]*y[None, :]/32).ravel())
    values = np.concatenate(pieces) if pieces else np.empty(0)
    size = len(values)
    if size < target:
        return (0., 0.)
    if target == 0:
        return (float(values.max(initial=0)), None)
    low = size-target-1
    high = size-target
    chosen = np.partition(values, [max(0, low), high])
    return (0. if low < 0 else float(chosen[low]), float(chosen[high]))


def solve(k):
    start = time.monotonic()
    _, groups = components(k, "projected_position")
    table = np.loadtxt("config/pauli-histogram-targets.csv", delimiter=",", skiprows=1, dtype=int)
    raw = table[table[:, 0] == k, 2]
    assert np.all(raw[k+1:] % 3 == 0)
    target = {w: int(raw[w]//3) for w in range(k+1, 2*k+1)}
    alphas = np.unique(np.r_[0., np.concatenate(groups[1:])])
    cache = {}
    def bounds(index):
        if index not in cache:
            cache[index] = {w: weight_bounds(groups, w, alphas[index], n) for w, n in target.items()}
        return cache[index]
    nodes = [dict(lo=0, hi=len(alphas)-1)]
    todo = [0]
    possible = []
    while todo:
        i = todo.pop()
        row = nodes[i]
        lo, hi = row["lo"], row["hi"]
        upper = bounds(lo)
        lower = bounds(hi)
        w_lower = max(target, key=lambda w: lower[w][0])
        w_upper = min(target, key=lambda w: float("inf") if upper[w][1] is None else upper[w][1])
        b_low, b_high = lower[w_lower][0], upper[w_upper][1]
        row.update(lower_weight=w_lower, upper_weight=w_upper, b_low=b_low, b_high=b_high)
        if b_high is not None and b_low >= b_high:
            row["status"] = "excluded"
        elif lo == hi:
            row["status"] = "possible"
            possible.append(i)
        else:
            middle = (lo+hi)//2
            children = [len(nodes), len(nodes)+1]
            nodes.extend([dict(lo=lo, hi=middle), dict(lo=middle+1, hi=hi)])
            row.update(status="split", children=children)
            todo.extend(reversed(children))
    return dict(k=k, local_groups=[g.tolist() for g in groups], alphas=alphas.tolist(),
                target=target, nodes=nodes, possible=possible, evaluated_alpha_cells=len(cache),
                seconds=time.monotonic()-start, high_weights_incompatible=not possible)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("k", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = solve(args.k)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(args.k, "possible", len(result["possible"]), "nodes", len(result["nodes"]),
          "seconds", result["seconds"], flush=True)


if __name__ == "__main__":
    main()
