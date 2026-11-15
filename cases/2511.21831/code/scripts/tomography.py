"""Shot sampling and fitting for the controlled-unitary tomography model."""
import numpy as np
from scipy.optimize import least_squares, minimize_scalar
from scipy.spatial.transform import Rotation

from ising import I, X, Y, Z

PAULI = np.stack((X, Y, Z))


def su2(u):
    length = np.linalg.norm(u)
    return np.cos(length)*I-1j*np.sinc(length/np.pi)*np.einsum("i,ijk->jk",u,PAULI)


def haar_vector(rng):
    w=rng.normal(size=4)
    w/=np.linalg.norm(w)
    length=np.arctan2(np.linalg.norm(w[1:]),w[0])
    return length*w[1:]/np.linalg.norm(w[1:])


def block_model(vec, iters, attenuation):
    return Rotation.from_rotvec(2*iters[:,None]*vec).as_matrix()*attenuation[:,None,None]


def fit_block(rng, vec, samples, iters, attenuation):
    expected=block_model(vec,iters,attenuation)
    counts=rng.binomial(samples,np.clip((expected+1)/2,0,1))
    measured=2*counts/np.maximum(samples,1)-1
    u,_,v=np.linalg.svd(measured[0])
    u[:,-1]*=np.linalg.det(u@v)
    initial=Rotation.from_matrix(u@v).as_rotvec()/2
    def residual(x):
        return ((block_model(x,iters,attenuation)-measured)*np.sqrt(samples)).ravel()
    estimate=least_squares(residual,initial,max_nfev=100).x
    return estimate


def controlled(u,v,phase):
    out=np.zeros((4,4),complex)
    out[:2,:2]=np.exp(-1j*phase)*u
    out[2:,2:]=np.exp(1j*phase)*v
    return out


def run(rng, trial_count, shot_counts, iterations, depolarizing):
    iters=np.array(iterations)
    attenuation=(1-depolarizing)**iters
    pairs=[(haar_vector(rng),haar_vector(rng),rng.uniform(-np.pi/2,np.pi/2))
           for _ in range(trial_count)]
    grid=np.linspace(-np.pi,np.pi,1025)
    all_errors={}
    for shots in shot_counts:
        errors=[]
        phase_errors=[]
        for a,b,phi in pairs:
            branch0=rng.binomial(shots,.5,size=(len(iters),3,3))
            v0=fit_block(rng,a,branch0,iters,attenuation)
            v1=fit_block(rng,b,shots-branch0,iters,attenuation)
            a0,b0=su2(a),su2(b)
            u0,u1=su2(v0),su2(v1)
            e,vec=np.linalg.eig(u1.conj().T@u0)
            state=vec[:,0]
            undo=u0.conj().T
            coherence=np.array([np.vdot(np.linalg.matrix_power(undo@a0,int(n))@state,
                           np.linalg.matrix_power(undo@b0,int(n))@state)*np.exp(2j*n*phi) for n in iters])
            expected=attenuation[:,None]*np.stack((coherence.real,coherence.imag),axis=1)
            measured=2*rng.binomial(shots,np.clip((expected+1)/2,0,1))/shots-1
            def score(angle):
                z=np.exp(1j*np.asarray(angle)[...,None]*iters)*attenuation
                return np.sum((np.stack((z.real,z.imag),axis=-1)-measured)**2,axis=(-2,-1))
            best=int(np.argmin(score(grid)))
            spacing=grid[1]-grid[0]
            sol=minimize_scalar(score,bounds=(grid[best]-spacing,grid[best]+spacing),method="bounded")
            phase=(sol.x+np.angle(e[0]))/2
            actual=controlled(a0,b0,phi)
            estimate=controlled(u0,u1,phase)
            errors.append(float(1-abs(np.vdot(actual,estimate))**2/16))
            phase_errors.append(float(abs(np.angle(np.exp(2j*(phase-phi))))/2))
        all_errors[str(shots)]=dict(process_infidelities=errors,phase_errors=phase_errors)
    return all_errors
