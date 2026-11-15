"""QFT synthesis on a line, plus independent Fourier and bitwise references."""
import numpy as np

H=np.array([[1.,1.],[1.,-1.]])/np.sqrt(2)
SX=np.array([[1+1j,1-1j],[1-1j,1+1j]])/2
CX=np.eye(4)[[0,1,3,2]]
SWAP=np.eye(4)[[0,2,1,3]]


def rz(angle):
    return np.diag(np.exp(-.5j*angle*np.array([1.,-1.])))


def cx(i):
    return ("cx",i,i+1)


def wires(op):
    return op[1:3] if op[0] in ("cx","cz","cp","zz") else op[1:2]


def phase(k):
    return np.ldexp(np.pi,-k)


def textbook(n,d,compensated=True):
    ops=[]
    for i in range(n):
        ops.append(("h",i))
        for j in range(i+1,n):
            theta=phase(j-i)
            if j-i<=d:
                ops.append(("cp",i,j,theta))
            elif compensated:
                ops.extend((("rz",i,theta/2),("rz",j,theta/2)))
    return ops


def prefix(n,low):
    ops=[("h",0)]
    for j in range(1,n):
        angle=sum(phase(k)/2 for k in range(1,j+1))
        if low and j<n-1:
            angle+=np.pi/2
        ops.append(("rz",j,angle))
    return ops


def suffix(n,low):
    ops=[("h",n-1)]
    for i in range(n-1):
        angle=sum(phase(k)/2 for k in range(1,n-i))
        if low and i>0:
            angle+=np.pi/2
        ops.append(("rz",i,angle))
    return ops


def body(n,d,low):
    ops=[]
    for i in range(n-1):
        radius=min(d,n-1-i)
        parity=[cx(j) for j in range(i+1,i+radius)]
        ops.extend(parity)
        ops.extend(("rz",i+j,-phase(j)/2) for j in range(1,radius+1))
        if low and i<n-2:
            assert parity
            ops.extend(reversed(parity[1:]))
            ops.extend((("sx",i+1),parity[0],cx(i)))
        else:
            ops.extend(reversed(parity))
            ops.append(cx(i))
            if i<n-2:
                ops.extend((cx(i+1),("h",i+1),cx(i+1)))
    return ops


def linear(n,d,low=True):
    assert n>=2 and 1<=d<n
    if low and d==1:
        # Direct two-CX synthesis because all retained ZZ terms are nearest neighbors.
        ops=[]
        for op in textbook(n,d):
            if op[0]!="cp":
                ops.append(op)
                continue
            _,i,j,theta=op
            ops.extend((("rz",i,theta/2),("rz",j,theta/2),cx(i),("rz",j,-theta/2),cx(i)))
        return ops
    return prefix(n,low)+[cx(i) for i in reversed(range(n-1))]+body(n,d,low)+suffix(n,low)


def convolution(n,d):
    assert n>=3 and 2<=d<n
    prep=[(g[0],g[1]+1,*g[2:]) for g in prefix(n,True)]
    # Input order a,x0,...,x[n-1]. The reverse ladder implements the initial
    # cyclic shift followed by the downward parity ladder on this subspace.
    reverse=[("cx",j+1,j) for j in range(n)]
    unscheduled=prep+reverse+body(n,d,True)+[cx(n-1)]+suffix(n,True)
    return as_late_as_possible(n+1,unscheduled)


def as_late_as_possible(n,ops):
    latest=np.zeros(n,int)
    schedule=[]
    for index in reversed(range(len(ops))):
        op=ops[index]
        qs=list(wires(op))
        t=int(latest[qs].min())-1
        latest[qs]=t
        schedule.append((t,index,op))
    return [op for _,_,op in sorted(schedule)]


def gate(op):
    name=op[0]
    if name=="h":
        return H
    if name=="sx":
        return SX
    if name=="rz":
        return rz(op[2])
    if name=="cp":
        return np.diag([1.,1.,1.,np.exp(1j*op[3])])
    if name=="cx":
        return CX
    if name=="cz":
        return np.diag([1.,1.,1.,-1.])
    raise ValueError(op)


def apply(n,ops,v):
    shape=(2,)*n+v.shape[1:]
    s=v.reshape(shape)
    for op in ops:
        qs=wires(op)
        k=len(qs)
        local=np.moveaxis(s,qs,range(k))
        b=(gate(op)@local.reshape(2**k,-1)).reshape(local.shape)
        s=np.moveaxis(b,range(k),qs)
    return s.reshape(v.shape)


def bit_reverse(n):
    return np.array([int(f"{j:0{n}b}"[::-1],2) for j in range(2**n)])


def fourier(n):
    d=2**n
    k=np.arange(d)
    return np.exp(2j*np.pi*((bit_reverse(n)[:,None]*k)%d)/d)/np.sqrt(d)


def phase_error(got,ideal):
    phase=np.vdot(ideal,got)
    return float(np.max(abs(got-ideal*phase/abs(phase))))


def stats(n,ops):
    layer=np.zeros(n,int)
    times=[]
    for op in ops:
        idx=list(wires(op))
        layer[idx]=layer[idx].max()+int(op[0] in ("cx","cz"))
        if op[0] in ("cx","cz"):
            assert abs(op[1]-op[2])==1
            times.append(int(layer[idx[0]]))
    light=[]
    for j in range(n):
        seen={j}
        size=0
        for op in reversed(ops):
            q=set(wires(op))
            if seen & q:
                seen|=q
                size+=int(op[0] in ("cx","cz"))
        light.append(size)
    return dict(two_qubit=len(times),depth=int(layer.max()),lightcone=light)


def cz_native(ops):
    out=[]
    for op in ops:
        if op[0]=="cx":
            _,i,j=op
            out.extend((("h",j),("cz",i,j),("h",j)))
        else:
            out.append(op)
    return out


def target_bits(n,k):
    return np.array([(k>>i)&1 for i in range(n)])


def prepared(n,k):
    states=[]
    for j in range(n):
        period=1<<(j+1)
        angle=-2*np.pi*(k%period)/period
        states.append(np.array([1.,np.exp(1j*angle)])/np.sqrt(2))
    return states


def target_probability(n,d,k,compensated=True):
    bits=target_bits(n,k)
    correction=.5 if compensated else 0.
    first=phase(d+1)
    delta=0.
    probability=1.
    for j in range(n-d-1):
        delta=delta/2+first*(correction-bits[j])
        probability*=np.cos(delta/2)**2
    return float(probability)


def mps_probability(n,d,k,ops):
    # For the finite-width kernel, contract the actual circuit on its product input.
    # A local SVD only removes machine-level null singular values.
    q=[np.array([1.,0.],complex),*prepared(n,k)]
    chain=[v.reshape(1,2,1) for v in q]
    max_rank=1
    dropped=0.
    for op in ops:
        qs=wires(op)
        g=gate(op)
        if len(qs)==1:
            j=qs[0]
            chain[j]=np.einsum("ij,ajb->aib",g,chain[j])
            continue
        i,j=sorted(qs)
        assert j==i+1
        if qs[0]!=i:
            g=SWAP@g@SWAP
        l,_,mid=chain[i].shape
        _,_,r=chain[j].shape
        a=(chain[i].reshape(2*l,mid)@chain[j].reshape(mid,2*r)).reshape(l,4,r)
        b=(g@a).reshape(2*l,2*r)
        u,s,v=np.linalg.svd(b,full_matrices=False)
        keep=int(np.count_nonzero(s>1e-13))
        dropped+=float(np.sum(s[keep:]**2))
        assert 0<keep<=128, (i,keep,n,d)
        max_rank=max(max_rank,keep)
        chain[i]=u[:,:keep].reshape(l,2,keep)
        chain[j]=(s[:keep,None]*v[:keep]).reshape(keep,2,r)
    amplitude=np.ones(1,complex)
    norm=np.ones((1,1),complex)
    for t,j in zip(chain,[*target_bits(n,k),0]):
        amplitude=amplitude@t[:,j,:]
        norm=np.einsum("ab,apc,bpd->cd",norm,t,t.conj())
    return dict(probability=float(abs(amplitude[0])**2),norm=float(norm[0,0].real),
                max_rank=max_rank,local_discarded_weight=dropped)
