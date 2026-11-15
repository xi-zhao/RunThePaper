"""Rebuild the Fig. 3 gate list and exact CVRP permutation encoding."""
from itertools import permutations
import json
import math
from pathlib import Path

import numpy as np


def u(theta,phi,lam):
    a=np.cos(theta/2)
    b=np.sin(theta/2)
    return np.array([[a,-np.exp(1j*lam)*b],[np.exp(1j*phi)*b,np.exp(1j*(phi+lam))*a]])


def circuit(theta,t,c):
    pi=np.pi
    cx=np.eye(4)[[0,1,3,2]]
    i=np.eye(2)
    before=np.kron(u(0,-pi/2,theta*c[0]),u(-pi/2,theta*c[1],0))[:,0]
    for g in [u(0,-pi/2,theta*c[2]),u(-pi/2,pi+t,0),u(-pi/2,-pi/2,t+pi/2)]:
        before=np.kron(i,g)@cx@before
    out=np.kron(u(pi/2,-pi/2,pi/2),u(pi/2,0,pi))@cx@before
    return abs(out)**2


def main():
    rng=np.random.default_rng(1903)
    errors=[]
    validity=[]
    for _ in range(256):
        theta,t=rng.normal(size=2)
        c=rng.normal(size=3)
        p=circuit(theta,t,c)
        w=np.sin(2*t)*np.cos(theta*(c[1]+c[2]))
        expected=.25*(1+np.array([1,-1,1,-1])*w)
        errors.append(float(abs(expected-p).max()))
        validity.append(float(p[1]+p[2]))
    assert max(errors)<2e-14 and max(abs(np.array(validity)-.5))<2e-14
    # Two routes can be read using just the lower output bit with a supplied
    # decoding; the upper output bit is uniformly random for all angles.
    extreme=[circuit(0,t,[1,2,3]).tolist() for t in (-np.pi/4,np.pi/4)]
    cost=rng.integers(1,20,size=(5,5))
    np.fill_diagonal(cost,0)
    classical=[]
    binary=[]
    def tour(route):
        return sum(int(cost[a,b]) for a,b in zip((0,*route),(*route,0)))
    for order in permutations(range(1,5)):
        classic=tour(order[:2])+tour(order[2:])
        classical.append(classic)
    # Four customer labels stored in four two-bit slots.
    for x in range(256):
        route=tuple(1+((x>>(2*i))&3) for i in range(4))
        if len(set(route))==4:
            binary.append(tour(route[:2])+tour(route[2:]))
    assert sorted(classical)==sorted(binary)
    size=[dict(passengers=n,one_hot=140*n,binary=140*math.ceil(math.log2(n)),feasible=n<=140) for n in range(2,141)]
    answer=dict(circuit=dict(CNOT_count=4,probability_formula_max_abs=max(errors),
       literal_01_or_10_total=float(np.mean(validity)),lower_bit_extremes=extreme),
       count_100=size[98],scaling=size,
       classical_example=dict(cost=cost.tolist(),feasible=len(classical),binary_space=256,min_cost=min(classical)),
       fig4_rounded=dict(success_ratios=[.97/.43,.46/.43],error_reductions=[.57/.03,.57/.54],
        nearest_percent_error_ratio_interval=[.565/.035,.575/.025]))
    Path("results/routing.json").write_text(json.dumps(answer,allow_nan=False)+"\n")


if __name__=="__main__": main()
