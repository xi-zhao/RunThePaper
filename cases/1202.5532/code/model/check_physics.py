"""Distinct full Pauli/expm, correlation matrix, and analytic controls."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
import json,time
from pathlib import Path
from functools import reduce
import numpy as np
from scipy.linalg import expm
from threadpoolctl import threadpool_limits
from xxz import evolve,free_evolve,sector

def kron_ops(L,ops):
    return reduce(np.kron,[ops.get(i,np.eye(2)) for i in reversed(range(L))])
def full_h(L,h,j,periodic=False):
    sx=np.array([[0,1],[1,0]])/2;sy=np.array([[0,1j],[-1j,0]])/2;sz=np.diag([-.5,.5])
    H=sum(h[i]*kron_ops(L,{i:sz}) for i in range(L)).astype(complex)
    for i in range(L if periodic else L-1):
        k=(i+1)%L
        H+=kron_ops(L,{i:sx,k:sx})+kron_ops(L,{i:sy,k:sy})+j*kron_ops(L,{i:sz,k:sz})
    return H
def full_observables(psi,L):
    c=psi.reshape(1<<(L-L//2),1<<(L//2));ra=c.conj().T@c;rb=c@c.conj().T
    p=np.linalg.eigvalsh(ra);q=np.linalg.eigvalsh(rb)
    entropy=lambda p:-sum(x*np.log(x) for x in p if x>1e-16)
    prob=abs(psi)**2;na=np.array([(i&((1<<(L//2))-1)).bit_count() for i in range(1<<L)])
    return entropy(p),na**2@prob-(na@prob)**2,abs(entropy(p)-entropy(q))

def main():
    rng=np.random.default_rng(12025532);out={'checks':[]};ts=time.monotonic()
    with threadpool_limits(limits=1):
        for L in [4,6,8]:
            for Jz in [0,.01,.2]:
                h=rng.uniform(-5,5,L);state=int(rng.integers(0,1<<L));times=[0,.1,1,10,100]
                s,v,psi,e,U,H=evolve(L,h,Jz,state,times,return_state=True)
                hf=full_h(L,h,Jz);basis=sector(L,state.bit_count())[0]
                residual=float(np.max(abs(hf[np.ix_(basis,basis)]-H)))
                ini=np.zeros(1<<L);ini[state]=1;errs=[];ab=0
                for k,t in enumerate(times):
                    f=expm(-1j*t*hf)@ini;a,b,c=full_observables(f,L);errs.extend([abs(a-s[k]),abs(b-v[k])]);ab=max(ab,c)
                nerr=float(np.max(abs((abs(psi)**2).sum(0)-1)))
                eerr=float(np.max(abs(np.sum(psi.conj()*(H@psi),axis=0)-H[sector(L,state.bit_count())[1][state],sector(L,state.bit_count())[1][state]])))
                out['checks'].append({'kind':'full_tensor_expm','L':L,'Jz':Jz,'H_error':residual,'observable_error':float(max(errs)),'norm_error':nerr,'energy_error':eerr,'S_A_minus_S_B':ab})
        for L in [4,6,10,12]:
            state=sum(1<<i for i in range(0,L,2));h=rng.uniform(-5,5,L)
            times=np.array([0,.05,1,100,1e3,1e6,1e9,1e10]);a=evolve(L,h,0,state,times);b=free_evolve(L,h,state,times)
            out['checks'].append({'kind':'free_correlation_vs_ED','L':L,'times':times.tolist(),'entropy_error':abs(a[0]-b[0]).tolist(),'variance_error':abs(a[1]-b[1]).tolist()})
            a=evolve(L,h,.1,state,times,driver='evr');b=evolve(L,h,.1,state,times,driver='evd')
            out['checks'].append({'kind':'LAPACK_phase_sensitivity','L':L,'times':times.tolist(),'entropy_error':abs(a[0]-b[0]).tolist(),'variance_error':abs(a[1]-b[1]).tolist()})
        # No hopping: all product z eigenstates remain product eigenstates.
        # Analytic two-spin longitudinal interaction on |+x,+x>.
        sz=np.diag([-.5,.5]);ini=np.ones(4)/2
        for t in [0,.2,np.pi,2*np.pi]:
            a,b,c=full_observables(expm(-1j*t*np.kron(sz,sz))@ini,2)
            lam=np.array([(1+abs(np.cos(t/2)))/2,(1-abs(np.cos(t/2)))/2]);expected=-sum(x*np.log(x) for x in lam if x>1e-16)
            out['checks'].append({'kind':'commuting_Ising_analytic','t':t,'entropy':a,'expected':expected,'variance':b,'error':abs(a-expected)})
    out['wall_seconds']=time.monotonic()-ts
    Path('checks/physics_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
