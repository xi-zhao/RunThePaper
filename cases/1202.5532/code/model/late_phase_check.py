"""Finite-time versus generic interacting-eigenphase ensemble.

The random-phase limit assumes no additional exact many-body frequency relations;
it is not used for Jz=0, where the free spectrum has known additive relations.
"""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
from pathlib import Path
import json,time
import numpy as np
from scipy.linalg import eigh
from concurrent.futures import ProcessPoolExecutor,as_completed
from threadpoolctl import threadpool_limits
from xxz import sector,hamiltonian,observables
JS=[.001,.01,.1,.2];TS=np.r_[np.geomspace(1e7,1e9,12),np.geomspace(1e9,1e11,12)]
def chunk(start):
    L=10;N=5;state=sum(1<<i for i in range(0,L,2));idx=sector(L,N)[1][state];a=np.empty((100,4,48,2))
    with threadpool_limits(limits=1):
        for k in range(100):
            rng=np.random.default_rng(np.random.SeedSequence([8765532,start+k]));h=rng.uniform(-5,5,L)
            theta=rng.uniform(-np.pi,np.pi,(252,24))
            for j,J in enumerate(JS):
                e,v=eigh(hamiltonian(L,N,h,J));phase=np.c_[np.exp(-1j*np.outer(e-e.mean(),TS)),np.exp(1j*theta)]
                psi=v@(v[idx,:,None]*phase);s,n=observables(psi,L,N);a[k,j,:,0]=s;a[k,j,:,1]=n
    return start,a
def main():
    t0=time.monotonic();n=3000;a=np.zeros((n,4,48,2))
    with ProcessPoolExecutor(max_workers=3) as pool:
        for f in as_completed([pool.submit(chunk,i) for i in range(0,n,100)]):
            i,b=f.result();a[i:i+100]=b;print(i+100,time.monotonic()-t0,flush=True)
    np.savez_compressed('results/late_phase.npz',values=a,Jzs=JS,times=TS)
    rows=[]
    for label,sl in [('t1e7_1e9',slice(0,12)),('t1e9_1e11',slice(12,24)),('independent_eigenphases',slice(24,48))]:
        b=a[:,:,sl,:].mean(2);d=b[:,3]-b[:,1]
        rows.append({'window':label,'means':b.mean(0).tolist(),'sem':(b.std(0,ddof=1)/np.sqrt(n)).tolist(),'J02_minus_J001':d.mean(0).tolist(),'paired_sem':(d.std(0,ddof=1)/np.sqrt(n)).tolist()})
    Path('checks/late_phase.json').write_text(json.dumps({'samples':n,'Jzs':JS,'rows':rows,'seconds':time.monotonic()-t0,'assumption':'Generic nonzero-interaction eigenfrequencies; not a rigorous nonresonance proof'},indent=2))
if __name__=='__main__':main()
