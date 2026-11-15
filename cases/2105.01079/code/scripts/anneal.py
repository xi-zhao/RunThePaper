"""Cauchy proposals on the same eight-slot diagnostic transmon."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from policy import A, N, X, STEPS, score


def evolve(q,t,delta):
    amp,phase=q[:,:STEPS],q[:,STEPS:]
    c=amp*np.exp(1j*phase)*np.pi/(2*t)
    drift=np.diag([0.,0.,-2*np.pi*.32])[None,None,:,:]+2*np.pi*delta[:,None,None,None]*N
    h=drift+(c[:,:,None,None]*A.T+c.conj()[:,:,None,None]*A)/2
    e,v=np.linalg.eigh(h)
    u=(v*np.exp(-1j*e*t/STEPS)[:,:,None,:])@v.conj().swapaxes(-1,-2)
    output=np.broadcast_to(np.eye(3),(len(q),3,3)).astype(complex).copy()
    for j in range(STEPS):
        output=u[:,j]@output
    return output


def train(t,seed):
    rng=np.random.default_rng(seed)
    q=np.zeros((64,2*STEPS))
    q[:,:STEPS]=1.
    drift=np.array([-.003,0,.003])
    pool=[q[0]]
    for step in range(300):
        temp=1/(1+step/15)
        delta=rng.choice(drift,len(q))
        dirs=rng.normal(size=(len(q),2,STEPS))
        dirs/=np.linalg.norm(dirs,axis=2,keepdims=True)
        magnitudes=rng.standard_cauchy((len(q),2,1))*temp*np.array([.35,.8])[None,:,None]
        proposal=q+(magnitudes*dirs).reshape(q.shape)
        proposal[:,:STEPS]=np.clip(proposal[:,:STEPS],0,2)
        a=score(evolve(q,t,delta),rng)[0]
        b=score(evolve(proposal,t,delta),rng)[0]
        accept=rng.random(len(q))<np.exp(np.minimum((b-a)/(.008*temp),0))
        q=np.where(accept[:,None],proposal,q)
        if step%5==0: pool.extend(q[b.argsort()[-5:]])
    q=np.asarray(pool)
    val=np.mean([score(evolve(q,t,np.full(len(q),d)))[0] for d in drift],axis=0)
    q=q[val.argmax()]
    grid=np.linspace(-.008,.008,33)
    u=evolve(np.tile(q,(len(grid),1)),t,grid)
    reward,l=score(u)
    target=expm(-.25j*np.pi*X)
    loss=1-abs(np.einsum("ab,nab->n",target.conj(),u[:,:2,:2])/2)**2
    return dict(duration_ns=t,seed=seed,controls=q.tolist(),mean_leakage=float(l[:,0].mean()),
                center_trace_infidelity=float(loss[len(grid)//2]),trace_infidelity=loss.tolist(),
                mean_trace_infidelity=float(loss.mean()),reward=reward.tolist(),
                terminal_score_calls=2*300*64)


if __name__=="__main__":
    import warnings
    warnings.filterwarnings("ignore",message=".*encountered in matmul",category=RuntimeWarning)
    r=[train(t,s) for t,s in [(28.4,2051),(12.4,2052)]]
    Path("results/anneal.json").write_text(json.dumps(r,allow_nan=False)+"\n")
