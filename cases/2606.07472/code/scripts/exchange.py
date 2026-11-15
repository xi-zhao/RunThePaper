"""Exchange-only control with independent filter and logical-spin formulations."""
from functools import lru_cache
import itertools
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq, minimize_scalar, curve_fit
from numpy.polynomial.legendre import leggauss

C=np.array([.1,.03,.03,.03])
TAU=np.array([4.,50.,200.,1000.])
I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1.,-1.])
N=(-np.sqrt(3)*X-Z)/2


@lru_cache(maxsize=24)
def quadrature(order):
    return leggauss(order)


def schedule(timing,gamma):
    return [(length,level) for length,level in zip(timing,(1.,0.,-gamma,0.)) if length]


def filtered_nodes(timing,gamma,repeats,order=20):
    """The normalized voltage at quadrature nodes, with exact memory updates."""
    nodes,weights=quadrature(order)
    memory=np.zeros(4)
    trace=[]
    pieces=schedule(timing,gamma)
    w=[]
    for length,_ in pieces:
        w.extend(weights*length/2)
    for _ in range(repeats):
        row=[]
        for length,u in pieces:
            t=(nodes+1)*length/2
            row.extend(u+np.exp(-t[:,None]/TAU)@(C*(memory-u)))
            memory=u+(memory-u)*np.exp(-length/TAU)
        trace.append(row)
    return np.array(trace),np.array(w)


def step_sum(timing,gamma,repeats,order):
    """Duhamel sum over segment boundaries, separate from memory propagation."""
    nodes,_=quadrature(order)
    pieces=schedule(timing,gamma)*repeats
    time=np.r_[0.,np.cumsum([a for a,_ in pieces])]
    levels=np.array([b for _,b in pieces])
    jumps=np.diff(np.r_[0.,levels])
    out=[]
    for j,(length,_) in enumerate(pieces):
        elapsed=time[j]+(nodes+1)*length/2
        kernels=1-np.exp(-(elapsed[:,None,None]-time[None,:j+1,None])/TAU)@C
        out.extend(kernels@jumps[:j+1])
    return np.asarray(out).reshape(repeats,-1)


def integrated_exchange(x,beta,z,w):
    return np.cumsum(np.exp(beta*(np.asarray(x)[...,None,None]*z-1))@w,axis=-1)


def centers(timing,gamma,beta,n=25,order=20):
    z,w=filtered_nodes(timing,gamma,n,order)
    ref,rw=filtered_nodes(timing,0,n,order)
    base=float(integrated_exchange(1.,beta,ref,rw)[-1]/n)
    target=np.arange(1,n+1)*base
    lo=np.full(n,.8)
    hi=np.full(n,1.2)
    zz=z[None,:,:]
    for _ in range(34):
        center=(hi+lo)/2
        phase=integrated_exchange(center,beta,zz[0],w).diagonal()
        upper=phase>target
        hi=np.where(upper,center,hi)
        lo=np.where(upper,lo,center)
    root=(hi+lo)/2
    assert np.max(abs(integrated_exchange(root,beta,z,w).diagonal()/target-1))<1e-8
    return root,base


def survival(angle):
    return 1-.75*np.sin(angle/2)**2


def rotation(axis,angle):
    return np.cos(angle/2)*I+1j*np.sin(angle/2)*axis


def up_sector():
    """Basis: single down spin at dots 1,2,3, then the encoded states and quartet."""
    u=np.array([-1.,1.,0.])/np.sqrt(2)
    v=np.array([-1.,-1.,2.])/np.sqrt(6)
    q=np.ones(3)/np.sqrt(3)
    basis=np.stack((u,v,q),axis=1)
    hs=[]
    for i,j in ((0,1),(1,2)):
        p=np.eye(3)
        p[:,[i,j]]=p[:,[j,i]]
        hs.append(basis.T@(p/2-np.eye(3)/4)@basis)
    return hs


def gate_control():
    p=np.pi
    a=np.arctan(np.sqrt(8))
    b=p-np.arctan(np.sqrt(5)/2)
    c,d=np.radians([74.755,201.625])
    recipes=[
      ("I",(0,0,0,0)),("X",(0,p-a,a,p-a)),("Y",(p,p-a,a,p-a)),
      ("Z",(p,0,0,0)),("S",(1.5*p,0,0,0)),("D",(p/2,0,0,0)),
      ("SX",(0,c,b,d)),("DX",(0,d,b,c)),("H",((p-a)/2,p+a,(p-a)/2,0)),
      ("XH",((p+a)/2,p-a,(3*p+a)/2,0)),("YH",((p+a)/2,p-a,(p+a)/2,0)),
      ("ZH",((3*p+a)/2,p-a,(p+a)/2,0)),("SH",((p-a)/2,p+a,2*p-a/2,0)),
      ("HS",(2*p-a/2,p+a,(p-a)/2,0)),("DH",((3*p+a)/2,p-a,a/2,0)),
      ("HD",(a/2,p-a,(3*p+a)/2,0)),("HSH",(a/2,p-a,a/2,0)),
      ("HDH",(p+a/2,p-a,p+a/2,0)),("DHS",(p+a/2,p-a,a/2,0)),
      ("SHD",(a/2,p-a,p+a/2,0)),("HSX",(a/2,p-a,(p+a)/2,0)),
      ("DXH",((p+a)/2,p-a,a/2,0)),("HDX",(2*p-a/2,p+a,(3*p-a)/2,0)),
      ("SXH",((3*p-a)/2,p+a,2*p-a/2,0))]
    hs=up_sector()
    target=dict(I=I,X=X,Y=Y,Z=Z,H=(X+Z)/np.sqrt(2),S=np.diag([1,1j]),D=np.diag([1,-1j]))
    g,err,leak=[],{},[]
    for name,angles in recipes:
        physical=np.eye(3,dtype=complex)
        expected=I
        for k,theta in enumerate(angles):
            physical=expm(-1j*hs[k%2]*theta)@physical
            expected=rotation((Z,N)[k%2],theta)@expected
        assert 1-abs(np.trace(expected.conj().T@physical[:2,:2]))/2<1e-13
        ideal=I
        for letter in name:
            ideal=ideal@target[letter]
        err[name]=float(np.max(abs(expected-ideal*np.trace(ideal.conj().T@expected)/2)))
        leak.append(float(np.linalg.norm(physical[2,:2])))
        g.append(expected)
    paulis=[X,Y,Z]
    matrices=np.array([[[np.trace(a0@u@b0@u.conj().T).real/2 for b0 in paulis] for a0 in paulis] for u in g])
    signed=[]
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((-1,1),repeat=3):
            m=np.eye(3)[list(perm)]*np.array(signs)[:,None]
            if np.linalg.det(m)>0:
                signed.append(m)
    err_group=np.max(np.min(np.max(abs(matrices[:,None]-np.asarray(signed)[None,:]),axis=(2,3)),axis=1))
    return dict(errors=err,group_max_error=float(err_group),distinct=len(set(map(tuple,np.rint(matrices).reshape(24,9)))),
                max_leakage_amplitude=max(leak),mean_pulses=float(np.mean([np.count_nonzero(v) for _,v in recipes])),
                projection_error=float(max(np.max(abs(h[:2,:2]+I/4+axis/2)) for h,axis in zip(hs,(Z,N)))))


def rb_control():
    n=np.r_[0,2**np.arange(11)]
    A,B,D,p,q=.25,.46,.21,.005,.0017
    model=lambda x,a,b,r:a+b*(1-r)**x
    y0=A+B*(1-p)**n+D*(1-q)**n
    y1=A-B*(1-p)**n+D*(1-q)**n
    diff=curve_fit(model,n,(y0-y1)/2,p0=(0.,.4,.006),maxfev=2000)[0]
    total=curve_fit(model,n,(y0+y1)/2,p0=(.24,.22,.002),maxfev=2000)[0]
    error=float(diff[2]/2+total[1]*total[2]/(2*diff[1]))
    leakage=float(total[1]*total[2]/diff[1])
    return dict(fit_gate_error=error,fit_leakage=leakage,
                expected_error=p/2+D*q/(2*B),expected_leakage=D*q/B)


def gamma_fit(timing,beta):
    def measure(gamma):
        root,_=centers(timing,gamma,beta)
        return float(np.std(root))
    opt=minimize_scalar(measure,bounds=(0,1.2),method="bounded",options={"xatol":1e-5})
    return dict(timing=timing,beta=beta,gamma=float(opt.x),spread=float(opt.fun),
                reference=measure(0.),net=measure(1.),published_gamma=measure(.699))
