"""Reconstruct the binary register mixer and check encoding costs."""

from itertools import permutations
import json
from math import ceil, factorial, lgamma, log, log2
from pathlib import Path

import numpy as np


def batcher(n):
    """Odd-even mergesort comparators for a power of two."""
    result = []
    def merge(lo, count, stride):
        step = 2*stride
        if step < count:
            merge(lo,count,step)
            merge(lo+stride,count,step)
            result.extend((j,j+stride) for j in range(lo+stride,lo+count-stride,step))
        else:
            result.append((lo,lo+stride))
    def sort(lo,count):
        if count>1:
            half = count//2
            sort(lo,half)
            sort(lo+half,half)
            merge(lo,count,1)
    sort(0,n)
    layers = [0]*n
    for a,b in result:
        layers[a]=layers[b]=1+max(layers[a],layers[b])
    return result,max(layers)


def support(n):
    pairs,_ = batcher(n)
    states = np.array(list(permutations(range(n))))
    lookup = {tuple(s):i for i,s in enumerate(states)}
    counts = np.zeros((len(states),len(pairs)+1),np.int64)
    counts[0,0] = 1
    for a,b in pairs:
        swapped = states.copy()
        swapped[:,[a,b]] = swapped[:,[b,a]]
        mapping = np.fromiter((lookup[tuple(s)] for s in swapped),dtype=int,count=len(states))
        current = counts.copy()
        current[:,1:] += counts[mapping,:-1]
        counts = current
    # At beta=pi/4 all terms have the same overall scalar.
    weights = (-1j)**np.arange(counts.shape[1])
    probability = abs(counts@weights)**2 / 2**len(pairs)
    assert abs(probability.sum()-1)<1e-12
    return dict(n=n,pairs=pairs,terms=int(counts.sum()),reached=int(np.any(counts>0,axis=1).sum()),
                zero_at_pi_over_4=int(np.sum(probability==0)),
                max_probability=float(probability.max()))


def ancilla_mixer(width,t):
    d = 2**(2*width)
    low = 2**width-1
    s = np.arange(d)
    p = ((s&low)<<width)+(s>>width)
    swap = np.eye(d)[p]
    control = np.block([[np.eye(d),np.zeros((d,d))],[np.zeros((d,d)),swap]])
    had = np.kron(np.array([[1,1],[1,-1]])/np.sqrt(2),np.eye(d))
    rotation = np.kron(np.cos(t)*np.eye(2)-1j*np.sin(t)*np.array([[0,1],[1,0]]),np.eye(d))
    u = had @ control @ rotation @ control @ had
    exact = np.cos(t)*np.eye(d)-1j*np.sin(t)*swap
    return float(np.max(abs(u[:d,:d]-exact))),float(np.max(abs(u[d:,:d])))


def walsh(values):
    a = np.asarray(values,dtype=float).copy()
    length = 1
    while length<len(a):
        view = a.reshape(-1,2*length)
        x,y = view[:,:length].copy(),view[:,length:].copy()
        view[:,:length],view[:,length:] = x+y,x-y
        length*=2
    return a


def encodings():
    rows = []
    for n in (4,10,16,100,128):
        w = ceil(log2(n))
        rows.append(dict(n=n,bits=w,feasible_permutation_fraction_log10=
                         lgamma(n+1)/log(10)-n*w*log(2)/log(10)))
    V,C,n = 7,20,100
    slots = V*C
    p = [1]+[0]*n
    for _ in range(V):
        p = [sum(p[max(0,i-C):i+1]) for i in range(n+1)]
    gapped = factorial(slots)//factorial(slots-n)
    compact = factorial(n)*p[n]
    rng = np.random.default_rng(190219)
    values = rng.uniform(0,10,2**14)
    coefs = walsh(values)/len(values)
    assert np.max(abs(walsh(coefs)-values))<1e-12
    full = dict(slots=slots,customers=n,customer_bits=ceil(log2(n+1)),
                with_dummy_128_bits=ceil(log2(129)),gapped_count=str(gapped),compact_count=str(compact),
                vehicle_length_combinations=p[n],table_width=14,table_terms=int(np.count_nonzero(coefs)),
                max_locality=max(i.bit_count() for i in np.flatnonzero(coefs).tolist()),
                parity_cnot_upper_bound=sum(2*max(0,i.bit_count()-1) for i in range(len(coefs))))
    return rows,full


def main():
    small = [support(n) for n in (4,8)]
    assert [d["reached"] for d in small] == [24,40320]
    mixers = [dict(width=w,error=e,leakage=l) for w in (1,2,3)
              for e,l in [ancilla_mixer(w,.392)]]
    assert max(r["error"]+r["leakage"] for r in mixers)<1e-12
    resources = []
    for n in (4,8,16,32,64,128):
        w = int(log2(n))
        seq,d = batcher(n)
        resources.append(dict(n=n,w=w,comparators=len(seq),comparator_depth=d,
                              two_register_fredkin_upper=2*w,
                              fredkin_count=2*w*len(seq),
                              logical_width_with_parallel_ancilla=n*w+n//2))
    perm,slots = encodings()
    # A register swap preserves the permutation but can violate load capacity.
    demand = [2,1,2,1]
    order = [0,1,2,3]
    after = [0,2,1,3]
    loads = lambda p:[sum(demand[k] for k in p[:2]),sum(demand[k] for k in p[2:])]
    out = dict(support=small,ancilla_mixers=mixers,sorting_resources=resources,permutation_spaces=perm,
        padded_slots=slots,weighted_capacity=dict(capacity=3,before=loads(order),after=loads(after),
                                                 labels_before=order,labels_after=after,demands=demand))
    Path("results/permutation-followup.json").write_text(json.dumps(out,allow_nan=False,indent=2)+"\n")
    print(small,resources[-1],slots["vehicle_length_combinations"],flush=True)


if __name__=="__main__":
    main()
