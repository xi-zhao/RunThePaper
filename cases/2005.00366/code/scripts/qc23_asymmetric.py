"""Check the time-order term of asymmetric sideband detuning against lab-frame integration."""
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
from scipy.special import roots_legendre

THETA=8*np.pi
STRENGTH=np.pi
SEGMENT_SIGN=[1,-1,-1,1]
SPINS=np.array([2,0,0,-2])
IDENTITY=np.eye(2)
X=np.array([[0,1],[1,0]])
Y=np.array([[0,-1j],[1j,0]])
Z=np.diag([1,-1])
ZSUM=np.kron(X,IDENTITY)+np.kron(IDENTITY,X)
YSUM=-(np.kron(Y,IDENTITY)+np.kron(IDENTITY,Y))
XSUM=np.diag(SPINS)


def prefix(t,theta):
    displacement=0j
    phase=0.
    first=0j
    for i,sign in enumerate(SEGMENT_SIGN):
        a=i/4
        length=max(0,min(t-a,0.25))
        start=STRENGTH*sign*np.exp(1j*theta*a)
        z=1j*theta*length
        step=start*np.expm1(z)/(1j*theta)
        first+=a*step+start*((z-1)*np.expm1(z)+z)/(1j*theta)**2
        phase+=(step*displacement.conjugate()).imag
        phase+=STRENGTH**2*(theta*length-np.sin(theta*length))/theta**2
        displacement+=step
    return displacement,phase,first


def osc(n):
    a=np.diag(np.sqrt(np.arange(1,n)),1)
    return a,a.T


def common(t,theta,n):
    a,adag=osc(n)
    alpha,phase,_=prefix(t,theta)
    blocks=[np.exp(1j*phase*s*s)*expm(s*(alpha*adag-alpha.conjugate()*a)) for s in SPINS]
    full=np.zeros((4*n,4*n),complex)
    for j,block in enumerate(blocks):
        full[j*n:(j+1)*n,j*n:(j+1)*n]=block
    return full


def apply(m,v):
    return np.einsum("ij,jk->ik",m,v)


def rotation_derivative(n,order):
    z=np.kron(ZSUM,np.eye(n))
    x,w=roots_legendre(order)
    integrated=np.zeros((4*n,4),complex)
    columns=np.arange(4)*n
    for i in range(4):
        for point,weight in zip(x,w):
            u=common((i+(point+1)/2)/4,THETA,n)
            integrated+=weight*apply(u.conj().T,apply(z,u[:,columns]))/8
    u=common(1.,THETA,n)
    rotating=(apply(u,integrated)-apply(z,u[:,columns]))*0.25j
    return rotating


def lab(epsilon,phase_error,n):
    a,adag=osc(n)
    psi=np.eye(4*n,dtype=complex)[:,::n].copy()
    for i,sign in enumerate(SEGMENT_SIGN):
        def rhs(t,v):
            angle=(epsilon*t-phase_error)/2
            spin=np.cos(angle)*XSUM+np.sin(angle)*YSUM
            beta=STRENGTH*sign*np.exp(1j*(THETA*t+angle))
            mot=beta*adag-beta.conjugate()*a
            return np.einsum("ij,ab,jbc->iac",spin,mot,v.reshape(4,n,4)).ravel()
        res=solve_ivp(rhs,(i/4,(i+1)/4),psi.ravel(),method="DOP853",rtol=2e-11,atol=2e-13)
        assert res.success
        psi=res.y[:,-1].reshape(4*n,4)
    return psi


def norm(x):
    return float(np.linalg.norm(x))


def run(n):
    u=common(1.,THETA,n)[:,::n]
    d24=rotation_derivative(n,24)
    d16=rotation_derivative(n,16)
    x,_,m=prefix(1.,THETA)
    assert abs(x)<1e-13 and abs(m)<1e-13
    rows=[]
    for step in (2e-3,1e-3,5e-4):
        plus,minus=lab(step,0.,n),lab(-step,0.,n)
        common_plus=common(1.,THETA+step/2,n)[:,::n]
        common_minus=common(1.,THETA-step/2,n)[:,::n]
        common_deriv=(common_plus-common_minus)/(2*step)
        fd=(plus-minus)/(2*step)
        rot=fd-common_deriv
        rows.append(dict(epsilon=step,full_derivative_norm=norm(fd),common_derivative_norm=norm(common_deriv),
                         omitted_rotation_norm=norm(rot),rotation_error=norm(rot-d24),
                         first_order_model_error=norm(plus-u-step*(d24+common_deriv))))
    z=np.kron(ZSUM,np.eye(n))
    phase_deriv=0.25j*(apply(z,u)-apply(common(1.,THETA,n),z[:,::n]))
    step=1e-3
    phase_fd=(lab(0.,step,n)-lab(0.,-step,n))/(2*step)
    return dict(n=n,displacement=abs(x),first_moment=abs(m),ideal_pair_phase=2*prefix(1.,THETA)[1],
                quadrature_error=norm(d24-d16),rotation_norm=norm(d24),
                rotation_outside_vacuum=norm(d24.reshape(4,n,4)[:,1:,:]),
                phase_offset_derivative_error=norm(phase_fd-phase_deriv),rows=rows)


def main():
    outputs=[run(n) for n in (12,20)]
    assert abs(outputs[0]["rotation_norm"]-outputs[1]["rotation_norm"])<1e-8
    assert abs(outputs[0]["rotation_outside_vacuum"]-outputs[1]["rotation_outside_vacuum"])<1e-8
    for d in outputs:
        assert d["quadrature_error"]<1e-8 and d["rows"][-1]["rotation_error"]<1e-6
        assert d["phase_offset_derivative_error"]<1e-6
        assert d["rotation_norm"]>0.1 and d["rotation_outside_vacuum"]>0.01
    Path("results/asymmetric-detuning.json").write_text(json.dumps(outputs,indent=2)+"\n")


if __name__=="__main__":
    main()
