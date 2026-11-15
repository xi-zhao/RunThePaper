"""Bounded MPS realization of the source's short-hop/fSWAP circuit."""
import time
import numpy as np
from scipy.linalg import qr,svd

from hubbard import physical_bits,two_gates


def left(env,a,state=None):
    if state is not None:
        v=a[:,state,:]
        return v.conj().T@env@v
    return sum(a[:,s,:].conj().T@env@a[:,s,:] for s in (0,1))


def right(env,a,state=None):
    if state is not None:
        v=a[:,state,:]
        return v@env@v.conj().T
    return sum(a[:,s,:]@env@a[:,s,:].conj().T for s in (0,1))


def link(l,r):
    return float(np.einsum("ij,ji",l,r).real)


class Chain:
    def __init__(self,bits,chi,cutoff):
        self.a=[np.eye(2,dtype=complex)[b].reshape(1,2,1) for b in bits]
        self.chi=chi
        self.cutoff=cutoff
        self.direction=1
        self.loss=0.
        self.max_rank=1

    def layer(self,bonds,g):
        a=self.a
        forward=self.direction==1
        for i in (range(len(a)-1) if forward else reversed(range(len(a)-1))):
            dl,_,mid=a[i].shape
            dr=a[i+1].shape[2]
            if i in bonds:
                theta=(a[i].reshape(2*dl,mid)@a[i+1].reshape(mid,2*dr)).reshape(dl,4,dr)
                theta=(g@theta).reshape(2*dl,2*dr)
                u,s,vh=svd(theta,full_matrices=False,check_finite=False,lapack_driver="gesdd")
                k=min(self.chi,max(1,int(np.count_nonzero(s>self.cutoff))))
                self.max_rank=max(self.max_rank,k)
                self.loss+=float(s[k:]@s[k:])
                s=s[:k]/np.linalg.norm(s[:k])
                a[i]=(u[:,:k] if forward else u[:,:k]*s).reshape(dl,2,k)
                a[i+1]=(s[:,None]*vh[:k] if forward else vh[:k]).reshape(k,2,dr)
            elif forward:
                q,r=qr(a[i].reshape(2*dl,mid),mode="economic",check_finite=False)
                a[i]=q.reshape(dl,2,q.shape[1])
                a[i+1]=(r@a[i+1].reshape(mid,2*dr)).reshape(q.shape[1],2,dr)
            else:
                q,r=qr(a[i+1].reshape(mid,2*dr).T,mode="economic",check_finite=False)
                a[i+1]=q.T.reshape(q.shape[1],2,dr)
                a[i]=(a[i].reshape(2*dl,mid)@r.T).reshape(dl,2,q.shape[1])
        self.direction=-self.direction

    def measure(self,centers):
        a=self.a
        n=len(a)
        l=[np.ones((1,1),complex)]
        r=[None]*n+[np.ones((1,1),complex)]
        for t in a:
            l.append(left(l[-1],t))
        for i in range(n-1,-1,-1):
            r[i]=right(r[i+1],a[i])
        norm=float(l[-1][0,0].real)
        p=np.array([link(left(l[i],a[i],1),r[i+1])/norm for i in range(n)])
        correlations=[]
        for c in centers:
            x=np.empty(n)
            x[c]=p[c]
            e=left(l[c],a[c],1)
            for i in range(c+1,n):
                x[i]=link(left(e,a[i],1),r[i+1])/norm
                e=left(e,a[i])
            e=right(r[c+1],a[c],1)
            for i in range(c-1,-1,-1):
                x[i]=link(l[i],right(e,a[i],1))/norm
                e=right(e,a[i])
            correlations.append(x-p[c]*p)
        return p,correlations,norm


def trajectory(occ,U,dt,steps,chi,cutoff,center=None):
    a=Chain(physical_bits(occ),chi,cutoff)
    hop,onsite=two_gates(dt,U)
    L=len(occ)
    short=set(range(1,2*L-1,2))
    intra=set(range(0,2*L,2))
    out=[]; charge=[]; spin=[]; loss=[]; norms=[]
    start=time.perf_counter()
    for t in range(steps+1):
        p,cor,norm=a.measure(()) if center is None else a.measure((2*center,2*center+1))
        order=np.stack([np.arange(L)*2+((np.arange(L)+t+1)%2),
                        np.arange(L)*2+((np.arange(L)+t)%2)],axis=1)
        out.append(p[order].tolist())
        norms.append(norm)
        charge.append((p.reshape(L,2).sum(axis=1)-occ.sum(axis=1)).tolist())
        if center is not None:
            c=(cor[0]-cor[1]).reshape(L,2)
            spin.append(((c[:,0]-c[:,1])*(-1)**(np.arange(L)+center)).tolist())
        loss.append(a.loss)
        if t==steps:
            break
        a.layer(short,hop)
        a.layer(intra,onsite)
        a.layer(short,hop)
    return dict(t=(np.arange(steps+1)*dt).tolist(),density=out,charge=charge,spin=spin,
                max_rank=a.max_rank,cumulative_discarded_weight=loss,norms=norms,seconds=time.perf_counter()-start)
