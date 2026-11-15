"""Open-chain Fermi-Hubbard independent controls in fixed spin sectors."""
import os
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")

from itertools import combinations
import numpy as np
from scipy.linalg import eigh,expm
from scipy.sparse import coo_matrix,eye,diags,kron
from scipy.sparse.linalg import expm_multiply


def initial(L, vacancy=None, up_even=True):
    n=np.zeros((L,2),int)
    n[np.arange(L),(np.arange(L)+int(not up_even))%2]=1
    if vacancy is not None:
        n[vacancy]=0
    return n


def physical_bits(n):
    # Input wire order: (down, up), (up, down), ...
    return np.concatenate([row[::-1] if i%2==0 else row for i,row in enumerate(n)])


def two_gates(dt,U):
    hop=np.eye(4,dtype=complex)
    hop[1:3,1:3]=np.cos(dt)*np.eye(2)+1j*np.sin(dt)*np.array([[0.,1.],[1.,0.]])
    exchange=np.eye(4,dtype=complex)
    exchange[1:3,1:3]=np.array([[0.,1.],[1.,0.]])
    exchange[3,3]=-np.exp(-1j*U*dt)
    return hop,exchange


def dense_apply(v,q,n,g):
    a=np.moveaxis(v.reshape((2,)*n),(q,q+1),(0,1))
    b=(g@a.reshape(4,-1)).reshape(a.shape)
    return np.moveaxis(b,(0,1),(q,q+1)).ravel()


def dense_steps(occ,U,dt,steps):
    L=len(occ)
    v=np.zeros(2**(2*L),complex)
    v[int("".join(map(str,physical_bits(occ))),2)]=1
    hop,onsite=two_gates(dt,U)
    b=((np.arange(len(v))[:,None] >> np.arange(2*L-1,-1,-1))&1).reshape(len(v),L,2)
    out=[]
    for k in range(steps+1):
        logical=b.copy()
        for j in range(L):
            if (j+k)%2==0:
                logical[:,j,:]=logical[:,j,::-1]
        p=abs(v)**2
        obs=np.einsum("i,ijs->js",p,logical)
        out.append(obs)
        if k==steps:
            break
        for layer,g in ((range(1,2*L-1,2),hop),(range(0,2*L,2),onsite),(range(1,2*L-1,2),hop)):
            for q in layer:
                v=dense_apply(v,q,2*L,g)
    return np.array(out)


class Sector:
    def __init__(self,L,occ):
        self.L=L
        self.occupied=[]
        self.pairs=[]
        self.index=[]
        hs=[]
        for spin in range(2):
            states=sorted(sum(1<<i for i in c) for c in combinations(range(L),int(occ[:,spin].sum())))
            ix={b:i for i,b in enumerate(states)}
            table=np.asarray(states)
            self.occupied.append((table[:,None]>>np.arange(L))&1)
            self.index.append(ix[sum(int(x)<<i for i,x in enumerate(occ[:,spin]))])
            pairs=[]
            for i in range(L-1):
                left=np.flatnonzero((table&(3<<i))==(1<<i))
                right=np.array([ix[table[j]^(3<<i)] for j in left],dtype=int)
                pairs.append((left,right))
            self.pairs.append(pairs)
            a=np.concatenate([u for pair in pairs for u in pair])
            b=np.concatenate([u for pair in pairs for u in reversed(pair)])
            hs.append(coo_matrix((-np.ones(len(a)),(a,b)),shape=(len(states),len(states))).tocsr())
        self.shape=tuple(len(a) for a in self.occupied)
        self.double=self.occupied[0]@self.occupied[1].T
        self.kinetic=kron(hs[0],eye(self.shape[1]),format="csr")+kron(eye(self.shape[0]),hs[1],format="csr")
        self.v0=np.zeros(self.shape,complex)
        self.v0[tuple(self.index)]=1

    def stats(self,state):
        p=(abs(state.reshape(self.shape))**2)
        up=p.sum(axis=1)@self.occupied[0]
        dn=p.sum(axis=0)@self.occupied[1]
        return np.stack((up,dn),axis=-1)

    def exact(self,U,dt,count):
        h=self.kinetic+diags((U*self.double).ravel(),format="csr")
        v=expm_multiply(-1j*h,self.v0.ravel(),start=0,stop=dt*count,num=count+1,
                        traceA=-1j*U*float(self.double.sum()))
        return np.stack([self.stats(x) for x in v])

    def trotter(self,U,dt,count,mirror=True):
        v=self.v0.copy()
        obs=[self.stats(v)]
        c,s=np.cos(dt),1j*np.sin(dt)
        interaction=np.exp(-1j*U*dt*self.double)
        def kinetic(which):
            for i in range(self.L-1):
                spin=(i+which)%2
                left,right=self.pairs[spin][i]
                w=v if spin==0 else v.T
                a,b=w[left,:].copy(),w[right,:].copy()
                w[left,:],w[right,:]=c*a+s*b,s*a+c*b
        for step in range(count):
            first=step%2 if mirror else 0
            kinetic(first)
            v*=interaction
            kinetic(1-first)
            obs.append(self.stats(v))
        return np.stack(obs)


def mapping_control(U):
    L,n=3,6
    indices=np.arange(2**n)
    ann=[]
    for i in range(n):
        shift=1<<(n-1-i)
        matrix=np.zeros((2**n,2**n))
        for state in indices[(indices&shift)!=0]:
            matrix[state^shift,state]=(-1)**int(state>>(n-i)).bit_count()
        ann.append(matrix)
    hs=np.zeros_like(ann[0])
    hl=hs.copy()
    for i in range(L-1):
        for a,b,target in ((2*i+1,2*i+2,hs),(2*i,2*i+3,hl)):
            m=ann[a].T@ann[b]
            target-=m+m.T
    occupation=((indices[:,None]>>np.arange(n-1,-1,-1))&1).reshape(-1,L,2)
    uv=np.diag(U*np.sum(occupation[:,:,0]*occupation[:,:,1],axis=1))
    _,exchange=two_gates(0.,0.)
    f=np.column_stack([np.eye(2**n)[:,j] for j in indices]).astype(complex)
    for q in range(0,n,2):
        f=np.column_stack([dense_apply(v,q,n,exchange) for v in f.T])
    e,v=eigh(hs+hl+uv)
    steps=[]
    for dt in (.1,.05,.025,.0125):
        t=expm(-1j*hs*dt)
        o=f@t@f@np.diag(np.exp(-1j*dt*np.diag(uv)))@t
        mirror=t@np.diag(np.exp(-1j*dt*np.diag(uv)))@f@t@f
        physical=t@f@np.diag(np.exp(-1j*dt*np.diag(uv)))@t
        target=lambda d:(v*np.exp(-1j*d*e))@v.T
        steps.append(dict(dt=dt,odd_error=float(np.linalg.norm(o-target(dt),2)),
                          paired_error=float(np.linalg.norm(mirror@o-target(2*dt),2)),
                          gauge_error=float(np.max(abs(f@physical-o))),
                          physical_pair_error=float(np.max(abs(physical@physical-mirror@o)))))
    return dict(exchange_max_error=float(np.max(abs(f@hs@f-hl))),steps=steps)


def free(L,occ,t,center):
    h=-np.eye(L,k=1)-np.eye(L,k=-1)
    e,v=eigh(h)
    density=[]
    spin=[]
    charge=[]
    for time in t:
        prop=(v*np.exp(-1j*time*e))@v.T
        matrices=[(prop*occ[:,s])@prop.conj().T for s in range(2)]
        n=np.stack([g.diagonal().real for g in matrices],axis=1)
        c=-sum(abs(g[:,center])**2 for g in matrices)
        c[center]+=n[center].sum()
        density.append(n.tolist())
        spin.append(c.tolist())
        charge.append((n.sum(axis=1)-occ.sum(axis=1)).tolist())
    return dict(density=density,charge=charge,spin=spin)
