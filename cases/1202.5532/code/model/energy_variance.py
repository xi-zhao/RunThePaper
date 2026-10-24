import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
import numpy as np
from pathlib import Path
import json,time
from concurrent.futures import ProcessPoolExecutor
from threadpoolctl import threadpool_limits
from xxz import sector,evolve
TIMES=np.r_[.1,1,10,100,1000,1e4,1e6,1e8,1e10]
def one(i):
    with threadpool_limits(limits=1):
        rng=np.random.default_rng(np.random.SeedSequence([2026102344,i]));L=10;h=rng.uniform(-5,5,L);state=sum(1<<int(k) for k in rng.choice(L,5,replace=False));basis,idx,z,_,_,_,_=sector(L,5)
        out=[]
        for J in [0,.01,.1,.2]:
            s,n,p,e,v,H=evolve(L,h,J,state,TIMES,return_state=True)
            ha=np.diag(z[:,:5]@h[:5]+J*(z[:,:4]*z[:,1:5]).sum(1))
            for a,b in enumerate(basis):
                for k in range(4):
                    if ((b>>k)&1)!=((b>>(k+1))&1):ha[idx[int(b^(3<<k))],a]=.5
            hp=ha@p;mean=np.sum(p.conj()*hp,0).real;var=np.sum(abs(hp)**2,0)-mean**2
            out.append(np.c_[s,n,var])
        return out
def main():
    t0=time.monotonic()
    with ProcessPoolExecutor(max_workers=2) as pool:a=np.array(list(pool.map(one,range(2000),chunksize=50)))
    np.savez_compressed('results/energy_variance.npz',values=a,times=TIMES,Jzs=[0,.01,.1,.2])
    Path('checks/energy_variance.json').write_text(json.dumps({'samples':len(a),'times':TIMES.tolist(),'Jzs':[0,.01,.1,.2],'means':a.mean(0).tolist(),'sem':(a.std(0,ddof=1)/len(a)**.5).tolist(),'seconds':time.monotonic()-t0,'definition':'H_A includes sites 0..4 fields and four internal bonds; cross-cut bond excluded; paper does not explicitly define boundary allocation'},indent=2))
if __name__=='__main__':main()
