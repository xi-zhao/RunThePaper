"""Distinct Hilbert-space and high-precision checks; not a second research agent."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
import json,time
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigsh
from model import all_correlations,concurrence_jets

def direct(N,l,gamma,r):
    dim=2**N
    states=np.arange(dim,dtype=np.int64)
    z=np.array([1-2*((states>>i)&1) for i in range(N)])
    rr=[states];cc=[states];vv=[-z.sum(0).astype(float)]
    for i in range(N):
        j=(i+1)%N
        rr.append(states^((1<<i)|(1<<j)));cc.append(states)
        vv.append(-l*(1+gamma)/2+l*(1-gamma)/2*z[i]*z[j])
    H=coo_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(dim,dim)).tocsr()
    # Deterministic even and odd initial sectors; take the actual lower eigenvalue.
    parity=np.prod(z,axis=0)
    cand=[]
    for p in [1,-1]:
        ids=np.where(parity==p)[0];hp=H[ids][:,ids]
        en,ve=eigsh(hp,k=1,which='SA',tol=2e-13,v0=np.sin(np.arange(len(ids))+.7))
        psi=np.zeros(dim);psi[ids]=ve[:,0];cand.append((en[0],psi,p))
    en,psi,p=min(cand,key=lambda x:x[0])
    residual=np.linalg.norm(H@psi-en*psi)
    rho=np.zeros((4,4))
    # Group spin 0 and spin r, with all other bit strings held equal.
    for rest in range(1<<(N-2)):
        base=0;j=0
        for i in range(N):
            if i not in (0,r):
                base|=((rest>>j)&1)<<i;j+=1
        ix=[base,base|(1<<r),base|1,base|1|(1<<r)]
        v=psi[ix];rho+=np.outer(v,v)
    X=np.array([[0,1],[1,0]]);Y=np.array([[0,-1j],[1j,0]]);Z=np.diag([1,-1]);I=np.eye(2)
    sf=np.kron(Y,Y)
    eig=np.sort(np.sqrt(np.maximum(0,np.linalg.eigvals(rho@sf@rho.conj()@sf).real)))[::-1]
    C=max(0,eig[0]-sum(eig[1:]))
    obs=[float(np.trace(rho@np.kron(X,X)).real),float(np.trace(rho@np.kron(Y,Y)).real),float(np.trace(rho@np.kron(Z,Z)).real),C]
    return {'energy':en,'sector':p,'parity_gap':abs(cand[0][0]-cand[1][0]),'residual':residual,
            'obs':obs,'mz':float(np.trace(rho@np.kron(Z,I)).real),'rho_min_eigenvalue':np.linalg.eigvalsh(rho).min()}

def main():
    t=time.time();out={'ed':[],'derivative_convergence':[],'dual_checks':[]}
    for N,l,g in [(7,.8,1),(7,1.,1),(7,1.1,1),(9,1.,1),(11,1.,1),(9,.8,.5),(9,1.,.5),(9,1.1,.5)]:
        mz,rows=all_correlations(l,g,N,3)
        for r in [1,2,3]:
            d=direct(N,l,g,r);ref=rows[r-1,[1,2,3,4]]
            out['ed'].append({'N':N,'lambda':l,'gamma':g,'r':r,**d,
                              'covariance':ref.tolist(),'max_error':float(max(abs(np.array(d['obs'])-ref))),
                              'magnetization_error':abs(mz-d['mz'])})
    for N,l,g,r in [(41,.93,1,1),(401,1.0001,1,1),(41,1.,1,2),(101,1.001,.5,1)]:
        j=concurrence_jets(l,g,N,r)
        for h in [1e-4,3e-5,1e-5,3e-6]:
            vals=[concurrence_jets(l+s*h,g,N,r)[0] for s in [-2,-1,0,1,2]]
            d1=(vals[0]-8*vals[1]+8*vals[3]-vals[4])/(12*h)
            d2=(-vals[0]+16*vals[1]-30*vals[2]+16*vals[3]-vals[4])/(12*h*h)
            out['derivative_convergence'].append({'N':N,'lambda':l,'gamma':g,'r':r,'h':h,
                                                   'd1_error':d1-j[1],'d2_error':d2-j[2]})
    for N in [7,11,41,101,None]:
        for l in [.7,.9,1.05,1.3]:
            c=concurrence_jets(l,N=N,r=2)[0];d=concurrence_jets(1/l,N=N,r=2)[0]
            out['dual_checks'].append({'N':N,'lambda':l,'C2':c,'inverse_C2':d,'difference':c-d})
    out['maximum_ed_error']=max(row['max_error'] for row in out['ed'])
    out['maximum_ed_residual']=max(row['residual'] for row in out['ed'])
    out['runtime_seconds']=time.time()-t
    Path('checks/direct-checks.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if not isinstance(v,list)},indent=2))

if __name__=='__main__':main()
