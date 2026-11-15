"""Fit layout ranks using time-dependent calibrated gate factors and idle data."""

import argparse
import json
from pathlib import Path

import numpy as np
from numba import njit
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.stats import rankdata

BASE = "config/layout-labels.npz"
GATES = "config/gate-factors.npz"
IDLE = "config/idle-exposures.npz"
TEMPERATURE = .02
RIDGE = .03


@njit
def layout_objective(cost, actual_ranks, offsets, selection):
    """Differentiate the rank loss through its L2 isotonic projection."""
    d_cost = np.zeros(len(cost))
    loss = 0.
    for group in selection:
        a,b=offsets[group:group+2]
        n=b-a
        v=-np.exp(-cost[a:b])/TEMPERATURE
        order=np.argsort(-v)
        means=np.empty(n)
        ends=np.empty(n,np.int64)
        starts=np.empty(n,np.int64)
        blocks=0
        for j in range(n):
            means[blocks]=v[order[j]]-(n-j)
            starts[blocks]=j
            ends[blocks]=j+1
            blocks+=1
            while blocks>1 and means[blocks-2]<means[blocks-1]:
                p=blocks-2
                m0=ends[p]-starts[p]
                m1=ends[p+1]-starts[p+1]
                means[p]=(m0*means[p]+m1*means[p+1])/(m0+m1)
                ends[p]=ends[p+1]
                blocks-=1
        for block in range(blocks):
            i,j=starts[block],ends[block]
            g=np.empty(j-i)
            for q in range(i,j):
                k=order[q]
                target=actual_ranks[a+k]
                delta=v[k]-means[block]-target
                loss+=delta*delta/target
                g[q-i]=2*delta/target
            g-=g.mean()
            for q in range(i,j):
                k=order[q]
                d_cost[a+k]=-g[q-i]*v[k]
    return loss/len(selection),d_cost/len(selection)


@njit
def idle_cost(t, z, t_offsets, z_offsets, t_mask, z_mask, prior, a, b, c):
    n=len(t_mask)
    penalties=prior.copy()
    derivative=np.zeros((n,3))
    for i in range(n):
        if t_mask[i]:
            penalties[i,0]=0.
            for j in range(t_offsets[i],t_offsets[i+1]):
                u=np.float64(t[j])
                v=u*(2-u)
                x=a*u+b*v
                penalties[i,0]-=np.log1p(-x)
                derivative[i,0]+=u/(1-x)
                derivative[i,1]+=v/(1-x)
        if z_mask[i]:
            penalties[i,1]=0.
            for j in range(z_offsets[i],z_offsets[i+1]):
                value=np.float64(z[j])
                penalties[i,1]-=np.log1p(-c*value)
                derivative[i,2]+=value/(1-c*value)
    return penalties, derivative


def load_dataset():
    with np.load(BASE,allow_pickle=False) as d:
        base={k:d[k] for k in d.files}
    with np.load(GATES,allow_pickle=False) as g:
        G=csr_matrix((g["data"],g["indices"],g["indptr"]),shape=tuple(g["shape"]))
        names=g["gate_names"]
    with np.load(IDLE,allow_pickle=False) as d:
        fields=("t","z","t_offsets","z_offsets","t_mask","z_mask")
        idle=[d[k] for k in fields]
    assert G.shape[0]==len(base["y"])
    return base,G,names,idle


def split(base, seed):
    n=len(base["offsets"])-1
    if seed==10:
        groups=base["group"][:,0]
        batches=sorted(set(groups))
        test_mask=np.isin(groups,batches[-max(1,len(batches)//5):])
        return np.flatnonzero(~test_mask),np.flatnonzero(test_mask)
    shuffle=np.random.default_rng(15100+seed).permutation(n)
    at=int(.8*n)
    return np.sort(shuffle[:at]),np.sort(shuffle[at:])


class Model:
    def __init__(self, base, G, idle, physical):
        self.G=G
        self.Gt=G.T.tocsr()
        self.idle=idle
        self.physical=physical
        self.n_gate=G.shape[1]
        self.x=base["x"][:,2:].astype(np.float64)
        self.y=base["y"].astype(np.float64)
        self.offset=base["offsets"]
        self.ranks=np.concatenate([rankdata(-self.y[a:b],method="average")
                                   for a,b in zip(self.offset,self.offset[1:])])

    def start(self):
        p=np.ones(self.n_gate+2)
        if self.physical:
            p=np.r_[p,[1/3,1/6,2/3]]
        return p

    def bounds(self):
        bound=[(0.,8.)]*(self.n_gate+2)
        if self.physical:
            bound.extend([(0.,.55),(0.,.40),(0.,.95)])
        return bound

    def get_cost(self, parameters):
        k=self.n_gate
        if self.physical:
            x, jac=idle_cost(*self.idle,self.x,*parameters[-3:])
        else:
            x,jac=self.x,None
        cost=self.G@parameters[:k]+x[:,0]*parameters[k]+x[:,1]*parameters[k+1]
        return cost,x,jac

    def objective(self, parameters, train):
        cost,x,jac=self.get_cost(parameters)
        result,change=layout_objective(cost,self.ranks,self.offset,train)
        k=self.n_gate
        prior=parameters[:k]-1.
        loss=result+RIDGE*np.dot(prior,prior)/k
        gradient=np.r_[self.Gt@change+2*RIDGE*prior/k,
                       np.sum(x*change[:,None],axis=0)]
        if self.physical:
            powers=parameters[[k,k,k+1]]
            gradient=np.r_[gradient,powers*np.sum(jac*change[:,None],axis=0)]
        assert np.isfinite(loss) and np.isfinite(gradient).all()
        return loss,gradient


def evaluate(offset,y,cost,groups, use_high_score=False):
    err,rk,chosen=[],[],[]
    for i in groups:
        a,b=offset[i:i+2]
        index=int(np.argmax(cost[a:b]) if use_high_score else np.argmin(cost[a:b]))
        hf=y[a+index]
        err.append(float(1-hf/max(y[a:b])))
        rk.append(int(1+np.sum(y[a:b]>hf)))
        chosen.append(index)
    return dict(mean_selection_error=float(np.mean(err)),median_rank=float(np.median(rk)),
                top1=float(np.mean(np.array(rk)==1)),selected=chosen,errors=err)


def run(seed):
    base,G,names,idle=load_dataset()
    train,test=split(base,seed)
    result=dict(seed=15100+seed,n_train=len(train),test_groups=test.tolist(),models={})
    result["mapomatic"]=evaluate(base["offsets"],base["y"],base["mm"],test,use_high_score=True)
    for name,shape in [("gate_expanded",False),("gate_and_idle",True)]:
        model=Model(base,G,idle,shape)
        initial=model.start()
        if shape:
            initial[:model.n_gate+2]=result["models"]["gate_expanded"]["parameters"]
        fit=minimize(model.objective,initial,args=(train,),method="L-BFGS-B",jac=True,
                     bounds=model.bounds(),options={"maxiter":70,"ftol":1e-9,"gtol":1e-6,"maxls":30})
        cost,_,_=model.get_cost(fit.x)
        out=evaluate(base["offsets"],base["y"],cost,test)
        result["models"][name]=dict(**out,parameters=fit.x.tolist(),train_loss=float(fit.fun),
            iterations=int(fit.nit),converged=bool(fit.success),message=str(fit.message))
        print(seed,name,out["mean_selection_error"],fit.nit,flush=True)
    result["gate_names"]=names.tolist()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,required=True,choices=range(11))
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(run(a.seed),indent=2,allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
