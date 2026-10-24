"""Dense wavefunction/Born and density-matrix channel for A1/A2; base-2 Rényi."""
import os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'scratch/mpl')
import numpy as np
from threadpoolctl import threadpool_limits
threadpool_limits(1)

def haar(rng):
    z=rng.normal(size=(4,4))+1j*rng.normal(size=(4,4))
    q,r=np.linalg.qr(z);d=np.diag(r);return q*(d/abs(d)).conj()[None,:]

def local(psi,u,q,L):
    x=psi.reshape(2**q,4,2**(L-q-2))
    return np.einsum('ij,ajb->aib',u,x,optimize=False).reshape(-1)

def ent(psi,a,L):
    if a==0 or a==L:return 0.0
    mat=psi.reshape(2**a,-1)
    rho=mat@mat.conj().T if mat.shape[0]<=mat.shape[1] else mat.conj().T@mat
    return -np.log2(np.sum(abs(rho)**2))

def trajectory(job):
    L,model,seed,steps=job;rng=np.random.default_rng(seed);psi=np.ones(2**L,dtype=complex)/np.sqrt(2**L)
    sample=[];mid=[]
    for t in range(1,steps+1):
        for q in range((t-1)%2,L-1,2):
            x=psi.reshape(2**q,4,2**(L-q-2)).copy()
            probs=np.sum(abs(x)**2,axis=(0,2))
            if model==1:
                a=rng.choice(4,p=probs/probs.sum());x[:,np.arange(4)!=a,:]=0;x/=np.sqrt(probs[a])
            else:
                pp=np.array([probs[0]+probs[3],probs[1]+probs[2]])
                a=rng.choice(2,p=pp/pp.sum());mask=np.array([0,1,1,0])!=a;x[:,mask,:]=0;x/=np.sqrt(pp[a])
            psi=np.einsum('ij,ajb->aib',haar(rng),x,optimize=False).reshape(-1)
        if t in [20,40,80,120,160,199,200]:mid.append([t,ent(psi,L//2,L)])
        if t>=steps-1:sample.append([ent(psi,a,L) for a in range(L+1)])
    return {'cuts':sample,'mid':mid,'norm_error':float(abs(np.vdot(psi,psi).real-1))}

def channel(job):
    L,model,seed,steps=job;rng=np.random.default_rng(seed);D=2**L;rho=np.ones((D,D),complex)/D;idx=np.arange(D);history=[]
    for t in range(1,steps+1):
        for q in range((t-1)%2,L-1,2):
            a=(idx>>(L-q-1))&1;b=(idx>>(L-q-2))&1;labels=(2*a+b) if model==1 else (a^b)
            rho*=labels[:,None]==labels[None,:]
            u=haar(rng)
            x=rho.reshape(2**q,4,2**(L-q-2),D)
            rho=np.einsum('ij,ajbc->aibc',u,x,optimize=False).reshape(D,D)
            x=rho.T.reshape(2**q,4,2**(L-q-2),D)
            rho=np.einsum('ij,ajbc->aibc',u.conj(),x,optimize=False).reshape(D,D).T.copy()
        purity=float(np.sum(abs(rho)**2));s=-np.log2(purity);history.append([t,s])
        if L-s<1e-11:break
    return {'L':L,'model':model,'seed':seed,'history':history,'S_final':s,'entropy_deficit':L-s,'trace_error':float(abs(np.trace(rho)-1)),'hermiticity_error':float(np.max(abs(rho-rho.conj().T)))}
