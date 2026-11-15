"""Finite motif tables and hash joins for unlabeled undirected graphs."""
from collections import defaultdict
from itertools import combinations, pairwise
import json
from pathlib import Path
import random


def edge(u, v):
    return (min(u, v), max(u, v))


def join(left, left_vars, right, right_vars):
    shared = tuple(v for v in left_vars if v in right_vars)
    right_new = tuple(v for v in right_vars if v not in shared)
    li = tuple(left_vars.index(v) for v in shared)
    ri = tuple(right_vars.index(v) for v in shared)
    ni = tuple(right_vars.index(v) for v in right_new)
    indexed = defaultdict(list)
    for row in right:
        indexed[tuple(row[i] for i in ri)].append(tuple(row[i] for i in ni))
    result = set()
    candidates = 0
    for row in left:
        for tail in indexed[tuple(row[i] for i in li)]:
            candidates += 1
            merged = row + tail
            if len(set(merged)) == len(merged):
                result.add(merged)
    return result, left_vars + right_new, candidates


def path_tables(data, largest):
    directed = {(u, v) for a, b in data for u, v in [(a, b), (b, a)]}
    rows = {2: directed}
    for size in range(3, largest+1):
        rows[size], _, _ = join(rows[size-1], tuple(range(size-1)),
                                directed, (size-2, size-1))
    return rows


def decompose(pattern, width):
    """Cover all edges with paths of up to width vertices."""
    unused = set(pattern)
    paths = []
    while unused:
        seen = {v for path in paths for v in path}
        initial = min(unused, key=lambda e: (not bool(set(e) & seen), e))
        path = list(initial)
        unused.remove(initial)
        while len(path) < width:
            choices = sorted(v for v in range(max(max(e) for e in pattern)+1)
                             if v not in path and edge(path[-1], v) in unused)
            if not choices:
                break
            next_vertex = choices[0]
            unused.remove(edge(path[-1], next_vertex))
            path.append(next_vertex)
        paths.append(path)
    return paths


def solve(data, pattern, paths, tables):
    rows, columns = {()}, ()
    work = []
    for path in paths:
        rows, columns, candidates = join(rows, columns, tables[len(path)], tuple(path))
        work.append([candidates, len(rows)])
    order = sorted(columns)
    nonedges = [e for e in combinations(order, 2) if e not in pattern]
    rows = {tuple(row[columns.index(v)] for v in order) for row in rows}
    induced = {row for row in rows
               if all(edge(row[u], row[v]) not in data for u, v in nonedges)}
    return dict(noninduced=sorted(rows), induced=sorted(induced), work=work)


def random_graph(rng, size, p):
    tree = {edge(v, rng.randrange(v)) for v in range(1, size)}
    return tree | {e for e in combinations(range(size),2) if rng.random()<p}


def main():
    config = json.loads(Path("config/cases.json").read_text())
    rng = random.Random(config["seed"])
    cases = [
        ("figure2", 7, 6, set(map(tuple,config["fig2_edges"])), set(map(tuple,config["fig2_pattern"]))),
        ("path-in-triangle", 3, 3, {(0,1),(0,2),(1,2)}, {(0,1),(1,2)}),
    ]
    for k in range(config["count"]):
        n, m = rng.randrange(5,9), rng.randrange(2,6)
        cases.append((f"random-{k:03}", n,m,random_graph(rng,n,rng.uniform(.04,.60)),
                      random_graph(rng,m,rng.uniform(.04,.70))))
    result = []
    for name, n, m, data, pattern in cases:
        tables = path_tables(data,4)
        paths = config["fig2_slices"] if name=="figure2" else decompose(pattern,4)
        small = solve(data,pattern,decompose(pattern,2),tables)
        large = solve(data,pattern,paths,tables)
        assert small["noninduced"]==large["noninduced"] and small["induced"]==large["induced"]
        result.append(dict(name=name,n=n,m=m,data=sorted(data),pattern=sorted(pattern),
                           path_counts={k:len(v) for k,v in tables.items()},large_paths=paths,
                           edge_join_work=small["work"],**large))
    Path("results/counts.json").write_text(json.dumps(result,separators=(",",":"))+"\n")


if __name__=="__main__":
    main()
