"""Depth-four tricycle edge coloring with alternating block matchings.
This schedule is independently constructed, not an author schedule.
"""
import itertools
import numpy as np
from generate_algebra import regular,construct

def structured_tri(model,order=(0,1,2,3),flips=(0,0,0)):
    blocks={(0,0):2,(0,2):0,(1,1):2,(1,2):1,(2,0):1,(2,1):0}
    ng=int(np.prod(model['group']));matchings=[[(0,0),(1,2),(2,1)],[(0,2),(1,1),(2,0)]]
    layers=[]
    for monomial in range(2):
        for pairs in matchings:
            edges=[]
            for r,c in pairs:
                factor=blocks[r,c];term=model['polynomials'][factor][monomial^flips[factor]]
                p=regular(model['group'],[term])
                edges.extend((int(r*ng+i),int(c*ng+j)) for i,j in zip(*np.nonzero(p)))
            assert len({x for x,y in edges})==len(edges)
            assert len({y for x,y in edges})==len(edges)
            layers.append(edges)
    result=[layers[i] for i in order];tz=construct(model)[-1];check=np.zeros_like(tz)
    for layer in result:
        for i,j in layer:check[i,j]+=1
    assert np.array_equal(tz,check)
    return result
