"""Open-chain second-order Trotter control, with an independent dense path."""
import numpy as np

X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1, -1])
I = np.eye(2)


def step_dense(state, n, dt):
    half = np.cos(dt/2)*I - 1j*np.sin(dt/2)*X
    # Build the bond phases using bit parity directly.
    indices = np.arange(2**n)[:,None]
    bond_odd = ((indices >> np.arange(n-1)) ^ (indices >> np.arange(1,n))) & 1
    diagonal = np.exp(1j*dt*np.sum(1-2*bond_odd,axis=1))
    def x_layer(v):
        for i in range(n):
            t = np.moveaxis(v.reshape((2,)*n), i, 0)
            v = np.moveaxis((half @ t.reshape(2,-1)).reshape(t.shape), 0, i).ravel()
        return v
    return x_layer(diagonal*x_layer(state))


def contract(mps, site, op):
    accumulator = np.ones((1,1),complex)
    for i, a in enumerate(mps):
        matrix = op if i==site else I
        accumulator = np.einsum("ab,asi,st,btj->ij",accumulator,a.conj(),matrix,a,optimize=True)
    return float(accumulator[0,0].real)


def dense_magnetization(state, n, op):
    t=state.reshape((2,)*n)
    return float(np.mean([np.vdot(ti,op @ ti).real
                          for i in range(n) for ti in [np.moveaxis(t,i,0).reshape(2,-1)]]))


def right_canonicalize(mps):
    for i in range(len(mps)-1,0,-1):
        a,b,c=mps[i].shape
        q,r=np.linalg.qr(mps[i].reshape(a,b*c).T)
        mps[i]=q.T.reshape(q.shape[1],b,c)
        mps[i-1]=mps[i-1] @ r.T


def trajectory(n, steps, dt, chi):
    mps=[np.array([1.,0.],complex).reshape(1,2,1) for _ in range(n)]
    half=np.cos(dt/2)*I-1j*np.sin(dt/2)*X
    zz=np.exp(1j*dt*np.array([[1.,-1.],[-1.,1.]]))
    values=[]
    discarded=0.
    max_bond=1
    for k in range(steps+1):
        norm=contract(mps,-1,I)
        values.append([np.mean([contract(mps,i,op) for i in range(n)])/norm for op in (Z,Y)])
        if k==steps:
            break
        mps=[np.einsum("st,atb->asb",half,a) for a in mps]
        right_canonicalize(mps)
        for i in range(n-1):
            a=mps[i]
            b=mps[i+1]
            theta=np.einsum("asb,btc,st->astc",a,b,zz,optimize=True)
            m,s,v=np.linalg.svd(theta.reshape(a.shape[0]*2,b.shape[2]*2),full_matrices=False)
            rank=min(chi,max(1,int(np.count_nonzero(s>1e-12))))
            discarded+=float(s[rank:] @ s[rank:])
            max_bond=max(max_bond,rank)
            mps[i]=m[:,:rank].reshape(a.shape[0],2,rank)
            mps[i+1]=(s[:rank,None]*v[:rank]).reshape(rank,2,b.shape[2])
        mps=[np.einsum("st,atb->asb",half,a) for a in mps]
    return dict(values=np.array(values).tolist(),discarded_norm_squared=discarded,max_bond=max_bond)
