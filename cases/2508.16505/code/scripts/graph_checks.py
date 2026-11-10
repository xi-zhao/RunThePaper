"""Enumerate graph isomorphism/LC classes without paper graph arrays."""
import itertools as it
import json, math
from collections import deque
from pathlib import Path
from graph_small import representatives

def canonical(G):
    n=len(G)
    return min(tuple(int(G.has_edge(p[i],p[j])) for i in range(n) for j in range(i+1,n)) for p in it.permutations(range(n)))

def complement(G,v):
    H=G.copy()
    for a,b in it.combinations(list(G[v]),2):
        if H.has_edge(a,b): H.remove_edge(a,b)
        else: H.add_edge(a,b)
    return H

def pauli_orbit_size(n): return 2**n

def stabilizer(G):
    n=len(G); terms=[(0,0,0)]
    for i in range(n):
        x=1<<i;z=sum(1<<j for j in G[i])
        # Store i^phase X^x Z^z; stabilizer generators commute.
        terms += [(a^x,b^z,(p+2*(b&x).bit_count())%4) for a,b,p in terms.copy()]
    # Hermitian convention i^(x.z) XZ, sign bit.
    return tuple(sorted((x,z,((p-(x&z).bit_count())%4)//2) for x,z,p in terms))

def clifford_orbit(G):
    n=len(G); start=stabilizer(G); seen={start}; todo=deque([start])
    while todo:
        state=todo.popleft()
        for q in range(n):
            bit=1<<q
            for gate in ('H','S'):
                out=[]
                for x,z,s in state:
                    xb=bool(x&bit);zb=bool(z&bit)
                    sign=s^(xb and zb)
                    if gate=='H':
                        if xb!=zb: x^=bit;z^=bit
                    elif xb: z^=bit
                    out.append((x,z,int(sign)))
                dest=tuple(sorted(out))
                if dest not in seen:seen.add(dest);todo.append(dest)
    return len(seen)

def main():
    result={}
    for n in range(2,6):
        graphs=representatives(n,canonical)
        mapping={canonical(g):g for g in graphs}
        todo=set(mapping);classes=[]
        while todo:
            first=min(todo);seen={first};queue=[first]
            while queue:
                c=queue.pop()
                for v in range(n):
                    new=canonical(complement(mapping[c],v))
                    if new not in seen:seen.add(new);queue.append(new)
            todo-=seen
            representative=min((mapping[k] for k in seen),key=lambda g:g.number_of_edges())
            E=representative.number_of_edges()
            classes.append({'graphs':len(seen),'minimum_edges':E,
                'representative_edges':list(representative.edges()),
                'fusion_baseline':(3/16)**E*(1/2)**(2*E-n),
                'clifford_orbit':clifford_orbit(representative),
                'pauli_orbit':pauli_orbit_size(n)})
        result[n]={'connected_nonisomorphic':len(graphs),'classes':classes,
                   'stabilizer_states':2**n*math.prod(2**i+1 for i in range(1,n+1))}
    Path('results').mkdir(exist_ok=True)
    Path('results/graph_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

if __name__=='__main__':main()
