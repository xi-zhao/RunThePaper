"""Explicit Koszul/Kunneth representatives for the C4 x C19 search window.

The active CRT component is E_y=sum(y^j), t=x+1, t^4=0. This computes a
valid representative ceiling, not the author's particular representative
optimization. Nontriviality is checked in the 24-dimensional local complex.
"""
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from generate_algebra import construct, rank

PAIRS=list(itertools.combinations(range(4),2))
NATIVE_PAIRS=[(1,3),(0,3),(2,3),(1,2),(0,2),(0,1)]


def _mul(a,b):
    v=0
    for i in range(4):
        if b>>i&1:v^=a<<i
    return v&15


def coefficients(polys):
    out=[]
    for terms in polys:
        f=0
        for x,y in terms:
            for r in range(4):
                if x&r==r:f^=1<<r
        out.append(f)
    return out


def tmatrix(f):
    return np.array([[(_mul(f,1<<j)>>i)&1 for j in range(4)] for i in range(4)],np.uint8)


def boundary(f,k):
    lo=list(itertools.combinations(range(4),k-1));hi=list(itertools.combinations(range(4),k))
    return np.block([[tmatrix(f[next(iter(set(b)-set(a)))]) if set(a)<set(b) else np.zeros((4,4),np.uint8) for b in hi] for a in lo])


def representatives(f):
    val=[next((i for i in range(4) if a>>i&1),4) for a in f];v=min(val);j=val.index(v)
    A=np.eye(4,dtype=int)
    if v<4:
        inv=next(g for g in range(1,16,2) if _mul(f[j]>>v,g)==1)
        for i in range(4):
            if i!=j:
                A[j,i]=_mul(f[i]>>v,inv)&((1<<(4-v))-1)
                assert _mul(f[j],int(A[j,i]))==f[i]
    rows=[]
    for a,b in PAIRS:
        # A pair avoiding j represents R/(t^v); a pair containing j
        # is multiplied by Ann(t^v)=t^(4-v) R.
        for r in range(v):
            scale=1<<(r+(4-v if j in (a,b) else 0))
            p=[_mul(scale,_mul(int(A[x,a]),int(A[y,b]))^_mul(int(A[y,a]),int(A[x,b]))) for x,y in PAIRS]
            rows.append(p)
    return v,rows


def main():
    config=Path('config/stern-population-v2.json');cfg=json.loads(config.read_text());out=Path('outputs/kunneth-ceiling-v1');out.mkdir(parents=True,exist_ok=True)
    rows=[];full=[]
    for index,c in enumerate(cfg['candidates']):
        assert c['model']['group']==[4,19]
        f=coefficients(c['model']['polynomials']);v,reps=representatives(f)
        vectors=np.array([[(p>>i)&1 for p in row for i in range(4)] for row in reps],np.uint8)
        d2,d3=boundary(f,2),boundary(f,3)
        assert not np.any(d2@vectors.T%2)
        base=rank(d3.T);assert rank(np.vstack([d3.T,vectors]))-base==6*v
        assert 24-rank(d2)-base==6*v
        supports=[]
        for row in reps:
            support=[]
            for block,pair in enumerate(NATIVE_PAIRS):
                p=row[PAIRS.index(pair)];xp=0
                for r in range(4):
                    if p>>r&1:
                        for k in range(4):
                            if r&k==k:xp^=1<<k
                support.extend(block*76+x*19+y for x in range(4) if xp>>x&1 for y in range(19))
            supports.append(support)
        best=min(supports,key=len)
        if index<8 or (v>=3 and not any(a['v']==v for a in full)):
            hx,hz,*_=construct(c['model']);w=np.zeros(456,np.uint8);w[best]=1
            assert not np.any(hz@w%2) and rank(np.vstack([hx,w]))==rank(hx)+1
            full.append(dict(sample=c['sample'],v=v,nontrivial_full_code=True))
        rows.append(dict(sample=c['sample'],v=v,K_local=6*v,representatives=len(reps),distance_upper_bound=len(best),X_support=best))
    (out/'results.json').write_text(json.dumps(dict(config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),rows=rows,full_matrix_controls=full,
        construction='E_y=sum_{s=0}^{18}y^s; t=x+1. For minimal valuation v, use an invertible generator change f -> (t^v u,0,0,0). Degree-2 quotient and annihilator representatives give 6v classes.',
        limitations=['Only the C4 x C19 trivial-y-character component. Full K-only CRT audit must exclude other active components.',
                     'Representative basis minimum is an upper bound, not an exact Kunneth-optimized ceiling.',
                     'No general non-principal local-ring formula or author representative choice is inferred.']),separators=(',',':'))+'\n')
    print(json.dumps(dict(candidates=len(rows),full_matrix_controls=len(full),ceiling_weights=sorted(set(r['distance_upper_bound'] for r in rows)))))


if __name__=='__main__':main()
