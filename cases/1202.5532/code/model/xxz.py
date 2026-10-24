"""Independent XXZ calculation from arXiv:1202.5532v2 Eqs. 1-2.

Open chain, spin one-half, J_perp=1, hbar=1. Entropy returned in nats.
No paper curves or external code are read by this generator.
"""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
import numpy as np
from scipy.linalg import eigh
from functools import lru_cache

@lru_cache(None)
def sector(L, N):
    basis=np.array([s for s in range(1<<L) if s.bit_count()==N],dtype=np.int64)
    idx={int(s):i for i,s in enumerate(basis)}
    bits=((basis[:,None]>>np.arange(L))&1)
    z=bits-.5
    hop=np.zeros((len(basis),len(basis)))
    for k,s in enumerate(basis):
        for i in range(L-1):
            if ((s>>i)&1)!=((s>>(i+1))&1):
                hop[idx[int(s^(3<<i))],k]=.5
    iz=(z[:,:-1]*z[:,1:]).sum(axis=1)
    half=L//2; blocks=[]
    for q in range(half+1):
        aa=[x for x in range(1<<half) if x.bit_count()==q]
        bb=[x for x in range(1<<(L-half)) if x.bit_count()==N-q]
        if aa and bb:
            blocks.append(np.array([[idx[a+(b<<half)] for b in bb] for a in aa]))
    return basis,idx,z,hop,iz,bits[:,:half].sum(axis=1),blocks

def hamiltonian(L,N,h,Jz):
    basis,idx,z,hop,iz,na,blocks=sector(L,N)
    H=hop.copy(); H.flat[::len(H)+1]=z@h+Jz*iz
    return H

def observables(psi,L,N):
    # psi columns are times; charge block Schmidt decomposition.
    basis,idx,z,hop,iz,na,blocks=sector(L,N)
    nt=psi.shape[1]; S=np.zeros(nt)
    for ids in blocks:
        c=psi[ids,:].transpose(2,0,1)
        p=np.linalg.svd(c,compute_uv=False)**2
        S-=np.sum(p*np.log(np.maximum(p,1e-300)),axis=1)
    prob=np.abs(psi)**2
    mean=na@prob
    var=(na**2)@prob-mean**2
    return S,var

def evolve(L,h,Jz,state,times,driver='evr',return_state=False):
    N=int(state).bit_count();basis,idx,*_=sector(L,N)
    H=hamiltonian(L,N,h,Jz)
    e,v=eigh(H,driver=driver,check_finite=False)
    # Remove an irrelevant common phase before long-time exponentiation.
    phase=np.exp(-1j*np.outer(e-e.mean(),times))
    psi=v@(v[idx[int(state)],:,None]*phase)
    S,var=observables(psi,L,N)
    if return_state: return S,var,psi,e,v,H
    return S,var

def free_evolve(L,h,state,times):
    one=np.diag(h)+.5*(np.eye(L,k=1)+np.eye(L,k=-1))
    e,v=eigh(one)
    occupied=[j for j in range(L) if (int(state)>>j)&1]
    S=[];V=[]
    for t in times:
        orb=(v*np.exp(-1j*e*t))@v[occupied,:].T
        C=orb[:L//2]@orb[:L//2].conj().T
        f=np.clip(np.linalg.eigvalsh(C),0,1)
        S.append(-np.sum(f*np.log(np.maximum(f,1e-300))+(1-f)*np.log(np.maximum(1-f,1e-300))))
        V.append(np.sum(f*(1-f)))
    return np.array(S),np.array(V)
