"""Paper-scale independent Fock-space calculation, no author data inputs.

Exploit exact particle number and center-of-mass sectors. Find ker O by SVD,
resolve K+K- within it, and compute basis-invariant mixed-sector observables.
Entropy and displayed standard deviations use a declared independent Haar basis.
"""
import itertools as it
import json
import math
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.linalg import null_space, eigh
from scipy.sparse import coo_matrix


@lru_cache(None)
def basis(L,N,statistics):
    rows=[]
    iterator = it.combinations(range(L),N) if statistics=='fermion' else it.combinations_with_replacement(range(L),N)
    for pos in iterator:
        n=[0]*L
        for j in pos:n[j]+=1
        rows.append(tuple(n))
    return rows


def sector(L,N,statistics,X):
    return [n for n in basis(L,N,statistics) if sum((j+1)*v for j,v in enumerate(n))==X]


def act(n,ops,statistics):
    """ops in application order (rightmost operator first)."""
    n=list(n);a=1.0
    for j,change in ops:
        if change==-1:
            if n[j]==0:return None,0.0
            if statistics=='fermion':a*=(-1)**sum(n[:j])
            else:a*=math.sqrt(n[j])
            n[j]-=1
        else:
            if statistics=='fermion':
                if n[j]:return None,0.0
                a*=(-1)**sum(n[:j])
            else:a*=math.sqrt(n[j]+1)
            n[j]+=1
    return tuple(n),a


def matrix(src,dst,terms,statistics):
    ix={n:i for i,n in enumerate(dst)};rr=[];cc=[];vv=[]
    for j,n in enumerate(src):
        for coefficient,ops in terms:
            m,a=act(n,ops,statistics)
            if a and m in ix:rr.append(ix[m]);cc.append(j);vv.append(a*coefficient)
    return coo_matrix((vv,(rr,cc)),shape=(len(dst),len(src))).tocsr()


def qbinom(n,k):
    polys={(0,0):[1]}
    for nn in range(1,n+1):
        for kk in range(min(k,nn)+1):
            a=polys.get((nn-1,kk),[]);b=polys.get((nn-1,kk-1),[])
            out=[0]*max(len(a),len(b)+nn-kk)
            for j,v in enumerate(a):out[j]+=v
            for j,v in enumerate(b):out[j+nn-kk]+=v
            while len(out)>1 and out[-1]==0:out.pop()
            polys[nn,kk]=out
    return polys[n,k]


def schmidt_maps(states,L):
    cuts=[]
    for cut in range(1,L):
        buckets=defaultdict(list)
        for idx,n in enumerate(states):
            left=n[:cut];right=n[cut:]
            label=(sum(left),sum((j+1)*v for j,v in enumerate(left)))
            buckets[label].append((idx,left,right))
        maps=[]
        for rows in buckets.values():
            li={x:i for i,x in enumerate(sorted({r[1] for r in rows}))}
            ri={x:i for i,x in enumerate(sorted({r[2] for r in rows}))}
            maps.append((len(li),len(ri),np.array([r[0] for r in rows]),
                         np.array([li[r[1]] for r in rows]),np.array([ri[r[2]] for r in rows])))
        cuts.append(maps)
    return cuts


def entropies(vectors,maps):
    result=np.zeros((vectors.shape[1],len(maps)))
    for c,groups in enumerate(maps):
        for n,m,ind,ii,jj in groups:
            for k in range(vectors.shape[1]):
                a=np.zeros((n,m),complex);a[ii,jj]=vectors[ind,k]
                p=np.linalg.svd(a,compute_uv=False)**2
                p=p[p>1e-15]
                result[k,c]-=np.sum(p*np.log(p))
    return result


def run_model(model,cfg,arrays):
    L,N,stats=model['L'],model['N'],model['statistics']
    rows=[];rng=np.random.default_rng(cfg['seed']+(stats=='boson'))
    nn=L if stats=='fermion' else L+N-1
    coeff=qbinom(nn,N)
    count_formula=coeff[(N*(L-N) if stats=='fermion' else N*(L-1))//2]
    shift=N*(N+1)//2 if stats=='fermion' else N
    for X in model['X']:
        states=sector(L,N,stats,X);lower=sector(L,N,stats,X-1)
        hops=[matrix(states,lower,[(1,[(j+1,-1),(j,1)])],stats) for j in range(L-1)]
        O=sum(hops)
        U=null_space(O.toarray(),rcond=cfg['null_rcond'])
        d=X-shift;expected=coeff[d]-(coeff[d-1] if d else 0)
        pair_states=sector(L,N-2,stats,X-(L+1))
        pair_hops=[]
        for j in range((L+1)//2):
            c=(-1)**j*(0.5 if j==L-1-j else 1)
            pair_hops.append(matrix(states,pair_states,[(c,[(j,-1),(L-1-j,-1)])],stats))
        K=sum(pair_hops);KU=K@U
        ev,R=eigh(KU.T@KU)
        projected=U@R
        unique=[]
        for Np in range(N//2+1):
            target=Np*(Np+1) if stats=='fermion' else Np*(N+L/2-Np-1)
            inds=np.flatnonzero(np.abs(ev-target)<cfg['pair_eigenvalue_tolerance'])
            if not len(inds):continue
            V=projected[:,inds];ns=V.shape[1];unique.extend(inds.tolist())
            z=rng.normal(size=(ns,ns))+1j*rng.normal(size=(ns,ns))
            Q,Rh=np.linalg.qr(z);diag=np.diag(Rh);Q*=diag.conj()/np.abs(diag)
            random_basis=V@Q
            density_each=(np.abs(random_basis)**2).T@np.array(states)
            density=np.mean(density_each,axis=0)
            moved=np.stack([h@V for h in hops])
            kinetic=np.einsum('iak,jak->ij',moved.conj(),moved).real/ns
            paired=np.stack([h@V for h in pair_hops])
            pairing=np.einsum('iak,jak->ij',paired.conj(),paired).real/ns
            entropy=entropies(random_basis,schmidt_maps(states,L))
            pair_res=np.linalg.norm(K.T@(K@V)-target*V)
            row={'statistics':stats,'L':L,'N':N,'X':X,'Np':Np,'Ns':ns,
                 'X_sector_dimension':len(states),'null_dimension':U.shape[1],
                 'qbinomial_null_dimension':int(expected),'total_null_dimension_formula':int(count_formula),
                 'null_residual_fro':float(np.linalg.norm(O@V)),
                 'pair_residual_fro':float(pair_res),
                 'orthonormality_residual':float(np.linalg.norm(V.T@V-np.eye(ns))),
                 'density_particle_sum':float(density.sum()),
                 'density_position_sum':float(density@np.arange(1,L+1)),
                 'kinetic_sum':float(kinetic.sum()),'pairing_sum':float(pairing.sum()),
                 'expected_pairing_sum':float(target),
                 'density':density.tolist(),'density_basis_std':density_each.std(0).tolist(),
                 'entropy_mean':entropy.mean(0).tolist(),'entropy_basis_std':entropy.std(0).tolist()}
            key=f'{stats}_X{X}_Np{Np}'
            arrays[key+'_states']=np.array(states,dtype=np.int16)
            arrays[key+'_kernel']=V
            arrays[key+'_kinetic']=kinetic;arrays[key+'_pairing']=pairing
            arrays[key+'_density']=density
            arrays[key+'_entropy_samples']=entropy
            rows.append(row)
            print(stats,X,Np,ns,'residual',row['null_residual_fro'],flush=True)
        if sorted(unique)!=list(range(len(ev))):raise ValueError(('unclassified pair eigenvalues',ev))
        if U.shape[1]!=expected:raise ValueError(('kernel multiplicity',X,U.shape,expected))
    return rows


def main():
    t=time.monotonic();cfg=json.loads(Path('config/model.json').read_text())
    arrays={};rows=[]
    for model in cfg['models']:rows.extend(run_model(model,cfg,arrays))
    out=Path('outputs/data');out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'statics.npz',**arrays)
    (out/'statics.json').write_text(json.dumps({'sectors':rows,'elapsed_seconds':time.monotonic()-t,
       'basis':'One independent complex Haar basis per (X,Np); linear observable means are basis invariant.',
       'limitations':'Finite-size entanglement profiles do not by themselves prove asymptotic volume-law scaling. No dissipative dynamics included.'},indent=2)+'\n')


if __name__=='__main__':main()
