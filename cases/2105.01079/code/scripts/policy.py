"""Finite three-level learning control for the eight-slot Rx(pi/2) protocol."""
from pathlib import Path
import json

import numpy as np
from scipy.linalg import expm

A=np.diag([1.,np.sqrt(2)],1)
N=np.diag([0.,1.,2.])
X=np.array([[0,1],[1,0]])
I=np.eye(2)
Z=np.diag([1.,-1.])
STEPS=8
REPS=(1,3,5)
TARGET=[expm(-.25j*np.pi*r*X)[:,0] for r in REPS]


def gates(t,det):
    amp=np.arange(1,5)/2*np.pi/(2*t)
    drives=np.r_[0.,(amp[:,None]*np.exp(1j*np.arange(4)[None,:]*np.pi/2)).ravel()]
    return np.array([[expm(-1j*(c*A.conj().T+c.conjugate()*A)/2*t/STEPS
                           -1j*np.diag([0,0,-2*np.pi*.32])*t/STEPS
                           -1j*2*np.pi*d*N*t/STEPS) for c in drives] for d in det])


def propagate(bank,actions):
    u=np.broadcast_to(np.eye(3),(len(actions),3,3)).astype(complex).copy()
    for j in range(STEPS): u=bank[np.arange(len(actions)),actions[:,j]]@u
    return u


def score(u,rng=None):
    values=[]
    leak=[]
    for k,r in enumerate(REPS):
        z=np.linalg.matrix_power(u,r)[:,:,0]
        l=abs(z[:,2])**2
        f=abs(z[:,:2]@TARGET[k].conj())**2/np.maximum(1-l,1e-15)
        if rng is not None:
            l=rng.binomial(1024,l.clip(0,1))/1024
            f=rng.binomial(1024,f.clip(0,1))/1024
        values.append(f/(1+l*l))
        leak.append(l)
    return np.mean(values,axis=0),np.asarray(leak).T


def train(duration,seed):
    rng=np.random.default_rng(seed)
    drift=np.array([-.003,0,.003])
    bank=gates(duration,drift)
    n=64
    count=300
    weights=[rng.normal(0,.08,(4,10)),np.zeros((10,bank.shape[1]))]
    momentum=[np.zeros_like(w) for w in weights]
    variance=[np.zeros_like(w) for w in weights]
    visited=[]
    history=[]
    rows=np.arange(n)
    for step in range(1,count+1):
        z=np.zeros((n,3),complex)
        z[:,0]=1.
        bs=bank[rng.integers(len(drift),size=n)]
        u=np.broadcast_to(np.eye(3),(n,3,3)).astype(complex).copy()
        obs=[]
        for k in range(STEPS):
            p=abs(z)**2
            p_obs=rng.binomial(256,p.clip(0,1))/256
            f=np.column_stack([np.full(n,k/STEPS),p_obs])
            h=np.tanh(f@weights[0])
            logits=h@weights[1]
            pr=np.exp(logits-logits.max(axis=1,keepdims=True))
            pr/=pr.sum(axis=1,keepdims=True)
            ac=np.minimum((np.cumsum(pr,axis=1)<rng.random((n,1))).sum(axis=1),pr.shape[1]-1)
            z=(bs[rows,ac]@z[:,:,None])[:,:,0]
            u=bs[rows,ac]@u
            obs.append((f,h,pr,ac))
        values,_=score(u,rng)
        advantage=values-values.mean()
        grad=[np.zeros_like(w) for w in weights]
        for f,h,pr,ac in obs:
            dl=-pr
            dl[rows,ac]+=1
            dl*=advantage[:,None]/n
            grad[1]+=h.T@dl
            grad[0]+=f.T@((dl@weights[1].T)*(1-h*h))
        for j,g in enumerate(grad):
            momentum[j]=.9*momentum[j]+.1*g
            variance[j]=.999*variance[j]+.001*g*g
            weights[j]+=.012*(momentum[j]/(1-.9**step))/(np.sqrt(variance[j]/(1-.999**step))+1e-8)
        visited.extend(np.asarray([o[-1] for o in obs]).T[values.argsort()[-4:]].tolist())
        history.append(float(values.mean()))
    cand=np.unique(np.asarray(visited),axis=0)
    def selection(a,dt):
        return np.mean([score(propagate(np.broadcast_to(b,(len(a),*b.shape)),a))[0] for b in gates(duration,dt)],axis=0)
    best=cand[selection(cand,drift).argmax()]
    grid=np.linspace(-.008,.008,33)
    def evaluate(a):
        us=propagate(gates(duration,grid),np.tile(a,(len(grid),1)))
        f,l=score(us)
        u=us[:,:2,:2]
        loss=1-abs(np.einsum("ab,nab->n",expm(-.25j*np.pi*X).conj(),u)/2)**2
        return dict(actions=a.tolist(),reward=f.tolist(),leakage=l[:,0].tolist(),trace_infidelity=loss.tolist(),
                    center_trace_infidelity=float(loss[len(grid)//2]),mean_leakage=float(l[:,0].mean()))
    # The square action of unit amplitude exists in the discrete bank.
    baseline=np.full(STEPS,5)
    return dict(duration_ns=duration,seed=seed,grid_detuning_mhz=(grid*1000).tolist(),batch=n,updates=count,
                history=history,policy=evaluate(best),same_duration_square=evaluate(baseline))


def counterexamples():
    zx=expm(.25j*np.pi*np.kron(Z,X))
    z=expm(-.5j*np.pi*np.kron(Z,I))
    swap=np.eye(4)[[0,2,1,3]]
    pm=np.array([1.,-1.])/np.sqrt(2)
    d=np.kron(pm,pm)
    plus=np.array([1.,1.])/np.sqrt(2)
    example=[]
    for name,target,u,states in [
      ("ZX",zx,z@zx,np.eye(4)[[0,2]]),
      ("SWAP",swap,swap@(np.eye(4)-2*np.outer(d,d)),[np.kron(plus,v) for v in np.eye(2)])]:
        errors=[]
        for k in range(1,65):
            for v in states:
                a=np.linalg.matrix_power(target,k)@v
                b=np.linalg.matrix_power(u,k)@v
                errors.append(abs(1-abs(np.vdot(a,b))**2))
        example.append(dict(gate=name,max_repeat_test_infidelity=float(max(errors)),
            trace_fidelity=float(abs(np.trace(target.conj().T@u)/4)**2),repetitions_checked=64))
    assert max(x["max_repeat_test_infidelity"] for x in example)<1e-12
    assert example[0]["trace_fidelity"]<1e-20 and abs(example[1]["trace_fidelity"]-.25)<1e-14
    return example


if __name__=="__main__":
    import warnings
    warnings.filterwarnings("ignore",message=".*encountered in matmul",category=RuntimeWarning)
    r=dict(duration_ratios=[36/28.4,36/12.4],counterexamples=counterexamples(),
           conditions="Eight PWC slots, hidden layer 10, action and drift grids declared in code. Independent transmon eta=-320 MHz and simulated shots, no hardware training.",
           train=[train(t,s) for t,s in [(28.4,2001),(12.4,2002)]])
    Path("results/policy.json").write_text(json.dumps(r,allow_nan=False)+"\n")
    print([(x["duration_ns"],x["policy"]["center_trace_infidelity"],x["same_duration_square"]["center_trace_infidelity"]) for x in r["train"]])
