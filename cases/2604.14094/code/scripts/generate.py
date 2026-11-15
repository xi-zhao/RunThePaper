"""Independent SU(2) matrix-model spectra, cutoff dynamics and Trotter controls."""
import os
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")

import json
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.linalg import eigh


def oscillator(d, prescription="normal_ordered"):
    # Matrix powers are taken with padding then projected. This implements
    # the source's normal-order-before-truncation prescription.
    size=d+4 if prescription=="normal_ordered" else d
    x=np.diag(np.sqrt(np.arange(1,size)/2),1)
    x=x+x.T
    x2=x@x
    return x2[:d,:d].copy(),(x2@x2)[:d,:d].copy()


def radial(lam, n):
    indices=np.arange(1,2*n,2)
    _,x4=oscillator(2*n)
    h=np.diag(indices+.5)+lam/64*x4[np.ix_(indices,indices)]
    e,v=eigh(h)
    return e,v


def echo(e,w,t):
    return abs(np.exp(-1j*np.asarray(t)[:,None]*(e-e[0]))@w)**2


def transform(t,m):
    a=np.fft.rfft(m)
    w=2*np.pi*np.fft.rfftfreq(len(t),t[1]-t[0])
    # Retain all bins, including the Nyquist bin, for checker-side convention tests.
    return np.stack((w,abs(a)),axis=1).tolist()


def radial_curves(evec):
    z=np.linspace(0,.999,1201)
    x=3*np.arctanh(z)
    p0=np.exp(-x*x/2)/np.pi**.25
    p1=np.sqrt(2)*x*p0
    odd=[p1]
    for k in range(2,2*len(evec)):
        p0,p1=p1,np.sqrt(2/k)*x*p1-np.sqrt((k-1)/k)*p0
        if k%2:
            odd.append(p1)
    u=np.sqrt(2)*np.stack(odd,axis=1)@evec[:,:6]
    return dict(z=z.tolist(),u=u.tolist())


def add_modes(local):
    identity=np.eye(len(local))
    return sum(np.kron(np.kron(local if i==0 else identity,local if i==1 else identity),
                       local if i==2 else identity) for i in range(3))


def cube_h(k,lam,even,prescription="normal_ordered"):
    d=2**k
    x2,x4=oscillator(d,prescription)
    occupations=np.arange(d)
    if even:
        x2,x4=x2[::2,::2],x4[::2,::2]
        occupations=occupations[::2]
    identity=np.eye(len(x2))
    h0=add_modes(np.diag(occupations+.5))
    pairs=(np.kron(np.kron(x2,x2),identity)+np.kron(np.kron(x2,identity),x2)+
           np.kron(np.kron(identity,x2),x2))
    hint=lam/64*(add_modes(x4)+2*pairs)
    return h0,hint


def walsh(v):
    v=v.copy()
    k=1
    while k<len(v):
        rows=v.reshape(-1,2*k)
        a=rows[:,:k].copy()
        b=rows[:,k:].copy()
        rows[:,:k]=a+b
        rows[:,k:]=a-b
        k*=2
    return v


def pauli_local(h,zero):
    d=len(h)
    ind=np.arange(d)
    band=h.nonzero()
    flips=np.unique(band[0]^band[1])
    result={}
    for x in flips:
        w=walsh(h[ind^x,ind])/d
        for z in np.flatnonzero(abs(w)>zero):
            count=int(x&z).bit_count()
            if not count%2:
                result[(int(x),int(z))]=float(w[z]*(-1)**(count//2))
    return result


def weight_hist(k,zero,prescription="normal_ordered"):
    x2,x4=oscillator(2**k,prescription)
    n=np.diag(np.arange(2**k)+.5)
    q2=pauli_local(x2,zero)
    singles=pauli_local(n+(x4+4*np.trace(x2)/len(x2)*x2)/64,zero)
    def count(terms):
        out=np.zeros(k+1,np.int64)
        for x,z in terms:
            if x or z:
                out[(x|z).bit_count()]+=1
        return out
    counts=3*np.convolve(count(q2),count(q2))
    counts[:k+1]+=3*count(singles)
    counts[0]=1
    return counts.tolist()


def pauli_terms(h,zero=1e-12):
    data=pauli_local(h,zero)
    return [(x,z,data[x,z]) for x,z in sorted(data) if (x,z)!=(0,0)]


def masks(d,x,z):
    src=np.arange(d)^x
    phase=(1j)**(x&z).bit_count()*np.array([(-1)**int(i&z).bit_count() for i in src])
    return src,phase


def native_factor_step(terms,d,dt):
    u=np.eye(d,dtype=complex)
    for x,z,c in terms:
        perm,phase=masks(d,x,z)
        u=np.cos(c*dt)*u-1j*np.sin(c*dt)*phase[:,None]*u[perm,:]
    return u


def circuit_controls(lam,dt,n,prescription="normal_ordered"):
    h0,hint=cube_h(2,lam,False,prescription)
    h=h0+hint
    e,v=eigh(h)
    times=np.arange(n+1)*dt
    occ=np.diag(h0)-1.5
    def trace(step):
        v=np.zeros(len(h),complex)
        v[0]=1
        result=[]
        for _ in times:
            p=abs(v)**2
            result.append([p[0],p@occ,p[(occ.astype(int)%2)==1].sum(),p.sum()])
            v=step@v
        return result
    full=pauli_terms(h)
    inter=pauli_terms(hint)
    def label(term):
        x,z,_=term
        return tuple(((z>>bit)&1) if not ((x>>bit)&1) else 2+((z>>bit)&1)
                     for bit in reversed(range(6)))
    lex=sorted(full,key=label)
    phase=np.exp(-1j*dt*np.diag(h0))
    only=native_factor_step(inter,len(h),dt)
    t=native_factor_step(full,len(h),dt)
    rev=native_factor_step(reversed(full),len(h),dt)
    exact=(v*np.exp(-1j*dt*e))@v.T
    bound_ladder=sum(2*max(0,(x|z).bit_count()-1) for x,z,_ in full)
    scale=[]
    for f in (.001,.002,.004,.008):
        z,w=eigh(h0+f*hint)
        target=(w*np.exp(-1j*.0125*z))@w.T
        approximate=native_factor_step(pauli_terms(h0+f*hint),len(h),.0125)
        # Reinsert the identity part omitted in the circuit, so norm is phase-sensitive.
        approximate*=np.exp(-1j*.0125*np.trace(h0+f*hint)/len(h))
        scale.append(float(np.linalg.norm(target-approximate,ord=2)))
    return dict(t=times.tolist(),exact=trace(exact),full=trace(t),reversed=trace(rev),
                split=trace(only*phase[None,:]),interaction_only=trace(only),
                lexical=trace(native_factor_step(lex,len(h),dt)),
                scale=scale,term_count=len(full),ladder_2q_count=bound_ladder,
                exact_echo=echo(e,abs(v[0])**2,times).tolist())


def gauge_controls():
    d=4
    a=np.diag(np.sqrt(np.arange(1,d)),1)
    x=np.kron(np.kron(a,np.eye(d)),np.eye(d))
    y=np.kron(np.kron(np.eye(d),a),np.eye(d))
    z=np.kron(np.kron(np.eye(d),np.eye(d)),a)
    g=[1j*(u.T@v-v.T@u) for u,v in ((y,z),(z,x),(x,y))]
    c=sum(s@s for s in g)
    h0,hint=cube_h(2,20,False)
    e,w=eigh(h0+hint)
    times=np.arange(6)*.1
    states=(np.exp(-1j*times[:,None]*e)*w[0])@w.T
    charges=np.einsum("ni,ij,nj->n",states.conj(),c,states).real
    occupation=np.stack(np.unravel_index(np.arange(d**3),(d,d,d)),axis=1)
    bad=np.any(occupation%2,axis=1)
    return dict(casimir_200=float(c[2*d*d,2*d*d].real),expectations=charges.tolist(),
                odd_probability=(abs(states[:,bad])**2).sum(axis=1).tolist())


def main():
    c=json.loads(Path("config/protocol.json").read_text())
    t=np.linspace(0,c["echo_window"],c["echo_samples"])
    t3=np.arange(round(c["cutoff_window"]/c["cutoff_dt"])+1)*c["cutoff_dt"]
    details={}
    for lam in c["radial_lambda"]:
        e,v=radial(lam,c["radial_levels"])
        coarse,_=radial(lam,c["radial_cutoff_check"])
        details[str(lam)]=dict(energy=e[:12].tolist(),weights=(v[0,:12]**2).tolist(),
           convergence=float(np.max(abs(e[:12]-coarse[:12]))),total_weight=float(np.sum(v[0]**2)),
           vacuum_echo=dict(t=t.tolist(),m=echo(e,v[0]**2,t).tolist()) if lam==c["echo_lambda"] else None)
        if lam==c["echo_lambda"]:
            details[str(lam)]["fft"]=transform(t,echo(e,v[0]**2,t))
        if lam==c["cutoff_lambda"]:
            spectral=echo(e,v[0]**2,t3)
        if lam==10:
            functions=radial_curves(v)
    spectrum=[]
    for lam in np.linspace(.02,20,100):
        e,_=radial(lam,c["radial_cutoff_check"])
        spectrum.append([float(lam),*e[:6].tolist()])
    cutoff={}
    pauli={}
    circuit={}
    for order in ("normal_ordered","projected_position"):
        cutoff[order]={}
        for k in c["cutoff_K"]:
            h0,v=cube_h(k,c["cutoff_lambda"],True,order)
            e,u=eigh(h0+v)
            w=u[0]**2
            m=echo(e,w,t3)
            cutoff[order][str(k)]=dict(e=e[:12].tolist(),w=w[:12].tolist(),m=m.tolist(),
                fft=transform(t3,m),mae=float(np.mean(abs(m-spectral))))
        pauli[order]={str(k):weight_hist(k,c["pauli_zero_abs_tolerance"],order) for k in c["pauli_K"]}
        circuit[order]={str(lam):circuit_controls(lam,c["circuit_dt"],c["circuit_steps"],order)
                        for lam in c["circuit_lambda"]}
    obj=dict(radial=details,energies=spectrum,eigenfunctions=functions,
             cutoff=dict(t=t3.tolist(),spectral=spectral.tolist(),fft=transform(t3,spectral),truncated=cutoff),
             pauli=pauli,circuit=circuit,
             gauge=gauge_controls())
    Path("results/independent.json").write_text(json.dumps(obj,separators=(",",":"),allow_nan=False)+"\n")


if __name__=="__main__":
    main()
