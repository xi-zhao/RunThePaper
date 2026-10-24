"""Independent U(1)-block Vidal TEBD; small-chain ED and Quimb are controls.

Second order, disjoint even/odd two-site gates. No reference curves read.
The generic installed Quimb TEBD was benchmarked, but its Python tensor overhead
was high for the requested disorder ensemble; this implementation uses Numba LAPACK.
"""
import os
from pathlib import Path
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
os.environ.setdefault('NUMBA_CACHE_DIR',str(Path.cwd()/'results/numba-cache'))
import numpy as np
from numba import njit
from numba.typed import List
from scipy.linalg import expm

@njit(cache=True)
def gate_update(gam,lam,charges,gate,i,max_bond,cutoff):
    dl=gam[i].shape[0];dm=gam[i].shape[2];dr=gam[i+1].shape[2]
    a=gam[i].copy();b=gam[i+1].copy()
    for l in range(dl):
        for n in range(2):
            for m in range(dm):a[l,n,m]*=lam[i][l]*lam[i+1][m]
    for m in range(dm):
        for n in range(2):
            for r in range(dr):b[m,n,r]*=lam[i+2][r]
    th=(a.reshape(dl*2,dm)@b.reshape(dm,2*dr)).reshape(dl,2,2,dr)
    tmp=np.empty((4,dl*dr),dtype=np.complex128)
    for l in range(dl):
        for n in range(2):
            for m in range(2):
                for r in range(dr):tmp[2*n+m,l*dr+r]=th[l,n,m,r]
    tmp=gate@tmp
    mat=np.empty((dl*2,2*dr),dtype=np.complex128)
    for l in range(dl):
        for n in range(2):
            for m in range(2):
                for r in range(dr):mat[2*l+n, m*dr+r]=tmp[2*n+m,l*dr+r]
    # Total particle number labels partition the Schmidt SVD exactly.
    fullrank=min(dl*2,dr*2)
    uu=np.zeros((dl*2,dl*2),np.complex128)
    vv=np.zeros((dl*2,dr*2),np.complex128)
    ss=np.zeros(dl*2); qs=np.zeros(dl*2,np.int64);rank=0
    for q in range(i+2):
        rows=np.array([r for r in range(dl*2) if charges[i][r//2]+r%2==q],np.int64)
        cols=np.array([c for c in range(dr*2) if charges[i+2][c%dr]-c//dr==q],np.int64)
        if len(rows)==0 or len(cols)==0:continue
        block=np.empty((len(rows),len(cols)),np.complex128)
        for a in range(len(rows)):
            for b in range(len(cols)):block[a,b]=mat[rows[a],cols[b]]
        ub,sb,vb=np.linalg.svd(block,full_matrices=False)
        for k in range(len(sb)):
            ss[rank]=sb[k];qs[rank]=q
            for a in range(len(rows)):uu[rows[a],rank]=ub[a,k]
            for b in range(len(cols)):vv[rank,cols[b]]=vb[k,b]
            rank+=1
    inds=np.argsort(ss[:rank])[::-1]
    s=ss[inds].copy();u=uu[:,inds].copy();v=vv[inds,:].copy();qnew=qs[inds].copy()
    total=np.sum(s*s);keep=len(s);discard=0.
    while keep>1 and discard+s[keep-1]**2<cutoff*total:
        keep-=1;discard+=s[keep]**2
    keep=min(keep,max_bond)
    discard=np.sum(s[keep:]**2)/total
    norm=np.sqrt(np.sum(s[:keep]**2))
    anew=np.empty((dl,2,keep),dtype=np.complex128);bnew=np.empty((keep,2,dr),dtype=np.complex128)
    for l in range(dl):
        for n in range(2):
            for m in range(keep):anew[l,n,m]=u[2*l+n,m]/lam[i][l]
    for m in range(keep):
        for n in range(2):
            for r in range(dr):bnew[m,n,r]=v[m,n*dr+r]/lam[i+2][r]
    gam[i]=anew;gam[i+1]=bnew;lam[i+1]=s[:keep].copy()/norm;charges[i+1]=qnew[:keep].copy()
    return discard,abs(total-1.)

@njit(cache=True)
def steps(gam,lam,charges,ge,go,count,max_bond,cutoff):
    dw=0.;normerr=0.;totaldw=0.
    for _ in range(count):
        for parity in [0,1,0]:
            for i in range(parity,len(gam)-1,2):
                d,n=gate_update(gam,lam,charges,go[i] if parity else ge[i],i,max_bond,cutoff)
                dw=max(dw,d);totaldw+=d;normerr=max(normerr,n)
    return dw,totaldw,normerr

def create(L,state):
    gam=List();lam=List();charges=List();charges.append(np.zeros(1,dtype=np.int64))
    for i in range(L):
        a=np.zeros((1,2,1),complex);a[0,(state>>i)&1,0]=1;gam.append(a);lam.append(np.ones(1));charges.append(np.array([(state&((1<<(i+1))-1)).bit_count()],dtype=np.int64))
    lam.append(np.ones(1));return gam,lam,charges

def gates(h,Jz,dt):
    L=len(h);sz=np.diag([-.5,.5]);sx=np.array([[0,1],[1,0]])/2;sy=np.array([[0,1j],[-1j,0]])/2
    base=np.kron(sx,sx)+np.kron(sy,sy)+Jz*np.kron(sz,sz);ge=List();go=List()
    for i in range(L-1):
        H=base+h[i]/(1 if i==0 else 2)*np.kron(sz,np.eye(2))+h[i+1]/(1 if i+1==L-1 else 2)*np.kron(np.eye(2),sz)
        ge.append(np.ascontiguousarray(expm(-1j*dt/2*H)));go.append(np.ascontiguousarray(expm(-1j*dt*H)))
    return ge,go

def observe(gam,lam):
    cut=len(gam)//2;p=lam[cut]**2;S=-np.sum(p*np.log(np.maximum(p,1e-300)))
    e0=np.ones((1,1),complex);e1=np.zeros((1,1),complex);e2=np.zeros((1,1),complex)
    for i in range(cut):
        a=gam[i]*lam[i][:,None,None]
        n0=np.zeros((a.shape[2],a.shape[2]),complex);n1=n0.copy();n2=n0.copy()
        for s in range(2):
            b=a[:,s,:];n0+=b.conj().T@e0@b;n1+=b.conj().T@(e1+s*e0)@b;n2+=b.conj().T@(e2+2*s*e1+s*e0)@b
        e0,e1,e2=n0,n1,n2
    norm=np.real(p@np.diag(e0));mu=np.real(p@np.diag(e1))/norm;v=np.real(p@np.diag(e2))/norm-mu**2
    return float(S),float(v),float(norm)

def full_vector(gam,lam):
    c=np.ones((1,1),complex)
    for i in range(len(gam)):
        a=lam[i][:,None,None]*gam[i];c=np.tensordot(c,a,axes=(-1,0)).reshape(-1,a.shape[2])
    # MPS site 0 is the most significant array index, ED uses bit 0.
    return c[:,0].reshape([2]*len(gam)).transpose(tuple(reversed(range(len(gam))))).reshape(-1)

def evolve_mps(L,h,Jz,state,times,dt=.05,max_bond=32,cutoff=1e-10):
    gam,lam,charges=create(L,state);ge,go=gates(h,Jz,dt);out=[];last=0;dw=0.;tdw=0.;ne=0
    for t in times:
        n=int(round(t/dt));assert abs(n*dt-t)<1e-8
        a,b,c=steps(gam,lam,charges,ge,go,n-last,max_bond,cutoff);last=n;dw=max(dw,a);tdw+=b;ne=max(ne,c)
        out.append(observe(gam,lam))
    return np.array(out),{'max_discarded_weight':dw,'sum_discarded_weight':tdw,'max_gate_norm_error':ne,'max_bond_final':max(len(x) for x in lam)},gam,lam
