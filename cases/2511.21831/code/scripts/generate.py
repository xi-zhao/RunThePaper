"""Compute controlled-pulse, synthesis, QFT and Ising controls."""
import json
from itertools import product
from pathlib import Path
import os
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")

import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares

from ising import I,X,Y,Z,trajectory
from tomography import controlled,run as tomography,su2

XX, YY, ZZ = [np.kron(p,p) for p in (X,Y,Z)]
Q=np.array([[1,0,0,1j],[0,1j,1,0],[0,1j,-1,0],[1,0,0,-1j]],complex)/np.sqrt(2)


def rot(axis, angle):
    return np.cos(angle/2)*I - 1j*np.sin(angle/2)*axis


def cartan(x,y=0.,z=0.):
    return expm(-.5j*(x*XX+y*YY+z*ZZ))


def invariants(u):
    ub=Q.conj().T@u@Q
    m=ub.T@ub
    tr=np.trace(m)
    return np.array([tr.real/4,tr.imag/4,((tr*tr-np.trace(m@m))/4).real])


def cr_checks():
    records=[]
    for pair,coeffs,offset in json.loads(Path("config/cr-coefficients.json").read_text())["rows"]:
        zx,zy,zz,ix,iy,iz,zi=coeffs
        z=np.array([zx,zy,zz])
        single=np.array([ix,iy,iz])
        H=sum((v*np.kron(a,b)/2 for v,a,b in
               [(zx,Z,X),(zy,Z,Y),(zz,Z,Z),(ix,I,X),(iy,I,Y),(iz,I,Z),(zi,Z,I)]))
        full=expm(-1j*H)
        correct=controlled(su2((single+z)/2),su2((single-z)/2),zi/2)
        printed=controlled(su2(z+single),su2(z-single),zi)
        c=lambda u:float(np.arccos(np.clip(abs(np.trace(u[:2,:2].conj().T@u[2:,2:])/2),0,1)))
        records.append(dict(pair=pair,correct=c(correct),direct=c(full),printed=c(printed),
               original=np.pi/4+offset,correct_unitary_error=float(np.max(abs(correct-full))),
               printed_unitary_error=float(np.max(abs(printed-full)))))
    return records


def local_z(a,b):
    return np.kron(rot(Z,(a+b)/2),rot(Z,(a-b)/2))


def pair_parts(a,b,x,y):
    l,r,t=[],[],[]
    for angle in (x-y,x+y):
        c=(np.cos(a)*np.cos(b)-np.cos(angle))/(np.sin(a)*np.sin(b))
        assert -1-1e-10<=c<=1+1e-10
        az=np.arccos(np.clip(c,-1,1))
        mid=rot(X,a) @ rot(Z,az) @ rot(X,b)
        ap=np.angle(mid[0,0])
        bp=np.angle(mid[0,1])+np.pi/2
        l.append(ap+bp)
        r.append(ap-bp)
        t.append(az)
    return local_z(*l)@cartan(a)@local_z(*t), cartan(b)@local_z(*r), local_z(*r)


def synthesize(rng):
    two=[]; three=[]; decisions=0; excluded=[]; outside_midpoint=0
    gx=np.kron(rot(X,np.pi/2),rot(X,np.pi/2))
    for _ in range(1500):
        a,b,c=np.sort(rng.uniform(.18,.92,3))[::-1]
        small,big=np.sort(rng.uniform(a-b,a+b,2))
        x,y=(big+small)/2,(big-small)/2
        left,right,_=pair_parts(a,b,x,y)
        two.append(float(np.max(abs(left@right-cartan(x,y)))))
        x,y,z=np.sort(rng.uniform(.02,1.08,3))[::-1]
        lo=max(x+y-a,a-x+y,b-c+z)
        hi=b+c-z
        bounds=a+b+c>=x+y+z and -a+b+c>=-x+y+z and c>=z
        assert bounds==(lo<=hi)
        decisions+=1
        if bounds:
            strict_hi=min(hi,a+x-y)
            outside_midpoint+=int((lo+hi)/2>strict_hi)
            if lo>strict_hi:
                excluded.append(dict(pulses=[a,b,c],target=[x,y,z],lower=lo,upper=strict_hi))
                continue
            delta=(lo+strict_hi)/2
            left,_,tail=pair_parts(a,delta,x,y)
            p,q,_=pair_parts(b,c,delta,z)
            formed=left@gx@p@q@gx.conj().T@tail
            three.append(float(np.max(abs(formed-cartan(x,y,z)))))
    return dict(two=two,three=three,interval_decisions=decisions,
                outside_midpoint=outside_midpoint,excluded=excluded)


def haar(rng,n):
    a=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n))
    q,r=np.linalg.qr(a)
    q*=np.diag(r)/abs(np.diag(r))
    return q*np.exp(-1j*np.angle(np.linalg.det(q))/n)


def fit_generic(rng,count):
    records=[]
    for _ in range(count):
        p1,p2,p3=[haar(rng,4) for _ in range(3)]
        def matrix(x):
            a,b,c,d=[rot(Z,t[0])@rot(Y,t[1])@rot(Z,t[2]) for t in x.reshape(4,3)]
            return p1@np.kron(a,b)@p2@np.kron(c,d)@p3
        target=invariants(matrix(rng.uniform(-np.pi,np.pi,12)))
        losses=[]
        costs=[]
        for k in range(5):
            opt=least_squares(lambda x:invariants(matrix(x))-target,rng.uniform(-np.pi,np.pi,12),
                              max_nfev=100,ftol=1e-11,xtol=1e-11,gtol=1e-10)
            losses.append(float(opt.fun@opt.fun))
            costs.append(int(opt.nfev))
        records.append(dict(losses=losses,evaluations=costs))
    return records


def qft_controls():
    result=[]
    for n in range(10,27,2):
        for motif in ["0","1","01","10","0011"]:
            bits=(motif*n)[:n]
            target=int(bits,2)
            offsets=np.array([(target*2**j)%(2**n) for j in range(n)])
            phases=2*np.pi*offsets/(2**n)
            result.append(dict(n=n,bits=bits,phases=phases.tolist(),
                              probability=float(np.prod(abs((1+np.exp(1j*phases)*np.exp(-1j*phases))/2)**2))))
    return result


def main():
    cfg=json.loads(Path("config/protocol.json").read_text())
    rng=np.random.default_rng(cfg["seed"])
    result=dict(cr=cr_checks(),synthesis=synthesize(rng))
    print("pulse matrices and synthesis finished",flush=True)
    result["tomography"]=tomography(rng,cfg["tomography_trials"],cfg["shots"],cfg["iterations"],cfg["depolarizing"])
    print("controlled-pulse fit finished",flush=True)
    result["generic"]=fit_generic(rng,cfg["generic_trials"])
    print("generic invariant fit finished",flush=True)
    result["qft"]=qft_controls()
    dt=np.pi/15
    result["ising"]={str(chi):trajectory(cfg["nsites"],cfg["steps"],dt,chi) for chi in (24,48)}
    result["ising"]["small"]=trajectory(8,8,dt,24)
    Path("results/controls.json").write_text(json.dumps(result,separators=(",",":"))+"\n")


if __name__=="__main__":
    main()
