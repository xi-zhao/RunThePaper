"""Independent Jordan-Wigner/Slater implementation; no reference ordinates.
Units J=hbar=a=1. rho[i,j]=<b_i^dagger b_j>.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
import numpy as np
from numba import njit, prange, set_num_threads
from scipy.linalg import eigh_tridiagonal
from scipy.optimize import root
from scipy.special import expit
set_num_threads(4)


def free_modes(L):
    x=np.arange(1,L+1)[:,None]; m=np.arange(1,L+1)[None,:]
    U=np.sqrt(2/(L+1))*np.sin(np.pi*x*m/(L+1))
    return -2*np.cos(np.pi*np.arange(1,L+1)/(L+1)),U


def initial_box(L,N,Lin):
    _,v=free_modes(Lin)
    P=np.zeros((L,N)); start=(L-Lin)//2
    P[start:start+Lin]=v[:,:N]
    return P


def initial_super(L,N,A=8,phase=0):
    e,U=eigh_tridiagonal(A*np.cos(np.pi/2*(np.arange(1,L+1)+phase)), -np.ones(L-1))
    return U[:,:N]


@njit(parallel=True)
def pure_rho_direct(P):
    L,N=P.shape; rho=np.zeros((L,L),np.complex128)
    for i in prange(L):
        rho[i,i]=np.sum(np.abs(P[i])**2)
        A=np.eye(N,dtype=np.complex128)
        B=np.zeros((N+1,N+1),np.complex128)
        for j in range(i+1,L):
            B[:N,:N]=A
            B[:N,N]=np.conj(P[i]); B[N,:N]=P[j]
            rho[i,j]=-np.linalg.det(B)
            for a in range(N):
                for b in range(N):
                    A[a,b]-=2*np.conj(P[j,a])*P[j,b]
    return rho+rho.conj().T-np.diag(np.diag(rho))


@njit(parallel=True)
def pure_rho(P,reset=24):
    L,N=P.shape; rho=np.zeros((L,L),np.complex128)
    for i in prange(L):
        rho[i,i]=np.sum(np.abs(P[i])**2)
        A=np.eye(N,dtype=np.complex128)
        inv=A.copy(); det=1.+0j
        bad=False
        for j in range(i+1,L):
            if (j-i-1)%reset==0 or bad:
                det=np.linalg.det(A)
                if abs(det)>1e-13:
                    inv=np.linalg.inv(A); bad=False
                else: bad=True
            if bad:
                B=np.zeros((N+1,N+1),np.complex128)
                B[:N,:N]=A; B[:N,N]=np.conj(P[i]); B[N,:N]=P[j]
                rho[i,j]=-np.linalg.det(B)
            else:
                u=inv@np.conj(P[i]); rho[i,j]=det*np.dot(P[j],u)
            # Grow the parity interval to include site j.
            if not bad:
                u=inv@np.conj(P[j]); v=P[j]@inv
                denom=1-2*np.dot(P[j],u)
                if abs(denom)<1e-7: bad=True
                else:
                    inv+=2*np.outer(u,v)/denom; det*=denom
            for a in range(N):
                for b in range(N):
                    A[a,b]-=2*np.conj(P[j,a])*P[j,b]
    return rho+rho.conj().T-np.diag(np.diag(rho))


@njit(parallel=True)
def gaussian_real_rho(C,cutoff=160):
    """Wick parity string by growing Schur complement; real Gaussian C.
    Correlations beyond cutoff omitted; compare increased cutoff explicitly.
    """
    L=C.shape[0]; rho=np.zeros((L,L))
    for i in prange(L):
        rho[i,i]=C[i,i]
        inv=np.zeros((cutoff,cutoff)); det=1.
        for j in range(i+1,min(L,i+cutoff+1)):
            d=j-i-1
            q=np.zeros(d)
            for a in range(d):
                for b in range(d): q[a]+=inv[a,b]*C[i+1+b,j]
            val=C[i,j]
            for a in range(d): val+=2*C[i,i+1+a]*q[a]
            rho[i,j]=det*val
            if d+1==cutoff: continue
            schur=1-2*C[j,j]
            for a in range(d): schur-=4*C[j,i+1+a]*q[a]
            if abs(schur)<1e-12:
                # Generic determinant fallback at rare singular intermediate blocks.
                for jj in range(j+1,min(L,i+cutoff+1)):
                    G=2*C[i:jj,i+1:jj+1].copy()
                    for a in range(jj-i-1): G[a+1,a]-=1
                    rho[i,jj]=.5*np.linalg.det(G)
                break
            for a in range(d):
                for b in range(d): inv[a,b]+=4*q[a]*q[b]/schur
                inv[a,d]=2*q[a]/schur; inv[d,a]=inv[a,d]
            inv[d,d]=1/schur; det*=schur
    return rho+rho.T-np.diag(np.diag(rho))


def momentum(rho,k=None):
    L=len(rho)
    if k is None:k=np.arange(-L//2,L//2)
    diag=np.array([np.diagonal(rho,offset=d).sum() for d in range(L)])
    return (diag[0].real+2*(np.exp(-2j*np.pi*np.outer(k,np.arange(1,L))/L)@diag[1:]).real)/L


def occupations(U,P):
    Q=U.T@P
    return np.sum(np.abs(Q)**2,axis=1),Q


def thermal(e,n):
    N=n.sum(); E=e@n
    def fun(z):
        f=expit(-z[0]-z[1]*e)
        return [f.sum()-N, e@f-E]
    sol=root(fun,[3.,1.])
    if not sol.success or np.max(np.abs(fun(sol.x)))>1e-8: raise RuntimeError(str(sol))
    return expit(-sol.x[0]-sol.x[1]*e),sol.x
