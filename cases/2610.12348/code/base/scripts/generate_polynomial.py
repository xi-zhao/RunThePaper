"""Exact rational checks of the paper's translation-invariant polynomials."""
from fractions import Fraction as F
from collections import defaultdict
from itertools import product
import math,json
from pathlib import Path
import numpy as np
from generate_statics import basis,matrix

def add(a,b,scale=1):
    c=defaultdict(F,a)
    for p,v in b.items():c[p]+=scale*v
    return {p:v for p,v in c.items() if v}
def mul(a,b):
    c=defaultdict(F)
    for p,u in a.items():
        for q,v in b.items():c[tuple(x+y for x,y in zip(p,q))]+=u*v
    return {p:v for p,v in c.items() if v}
def power(a,r,N):
    out={(0,)*N:F(1)}
    for _ in range(r):out=mul(out,a)
    return out
def centered(N,r):
    out={}
    for i in range(N):
        term={tuple(int(j==k) for j in range(N)):F(int(k==i))-F(1,N) for k in range(N)}
        out=add(out,power(term,r,N))
    return out
def derivative_sum(a):
    out=defaultdict(F)
    for p,v in a.items():
        for i,n in enumerate(p):
            if n:q=list(p);q[i]-=1;out[tuple(q)]+=n*v
    return {p:v for p,v in out.items() if v}
def main():
    checks=[]
    for N in range(2,6):
        for r in range(2,7):
            q=centered(N,r);bad=[]
            for nu in product(range(r+1),repeat=N):
                if sum(nu)!=r:continue
                parts=[x for x in nu if x]
                predicted=F((-1)**r,N**r)*F(math.factorial(r),math.prod(math.factorial(x) for x in nu))*(sum((1-N)**x for x in parts)+N-len(parts))
                if q.get(nu,0)!=predicted:bad.append(nu)
            checks.append({'N':N,'r':r,'coefficient_mismatches':len(bad),'translation_derivative_terms':len(derivative_sum(q))})
    N,L=4,3;q2=centered(N,2);q4=centered(N,4);S=add({p:7*v for p,v in mul(q2,q2).items()},q4,-12)
    occ=basis(L,N,'boson');v=np.zeros(len(occ));seen=set()
    for nu,c in S.items():
        partition=tuple(sorted(nu,reverse=True))
        if partition in seen:continue
        seen.add(partition);n=tuple(partition.count(j) for j in range(L))
        v[occ.index(n)]=float(c)*math.prod(math.factorial(x) for x in partition)/math.sqrt(math.prod(math.factorial(x) for x in n))
    v/=np.linalg.norm(v)
    O=matrix(occ,occ,[(1,[(j+1,-1),(j,1)]) for j in range(L-1)],'boson')
    result={'q_r_decomposition_checks':checks,'degree_bound_counterexample':{'N':N,'L':L,'expression':'7 q_2^2 - 12 q_4','total_degree':4,'maximum_individual_degree':max(max(p) for p in S),'translation_derivative_exactly_zero':not derivative_sum(S),'nonzero_monomials':len(S),'O_state_residual':float(np.linalg.norm(O@v)),'occupation_basis':occ,'normalized_fock_amplitudes':v.tolist(),'coefficients':[{'powers':p,'coefficient':str(c)} for p,c in sorted(S.items())],'interpretation':'Total d <= L-1 is sufficient for a single invariant product, not necessary for a linear combination to fit the finite lattice. The source wording as a necessary condition is overrestrictive.'}}
    out=Path('outputs/data');out.mkdir(parents=True,exist_ok=True);(out/'polynomial.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
