"""Hydration QUBO controls from a declared synthetic density, and PDB source checks."""
from collections import Counter
from itertools import product
import gzip
import json
import os
from pathlib import Path
import re

os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")

import numpy as np
from scipy.integrate import simpson


def gauss_1d(x, centers, variance):
    return np.exp(-.5*(x[:,None]-centers[None,:])**2/variance)/np.sqrt(2*np.pi*variance)


def overlap(a,b,var_sum):
    distance_sq=np.sum((a[:,None,:]-b[None,:,:])**2,axis=2)
    return np.exp(-.5*distance_sq/var_sum)/(2*np.pi*var_sum)**1.5


def assemble(cfg):
    v,t=cfg["variance"],cfg["density_variance"]
    centers=np.array(cfg["control_centers"])
    weights=np.array(cfg["control_amplitudes"])
    points=np.array(list(product(range(-1,3),range(2),range(2))))*cfg["coarse_spacing"]
    native=np.rint(points/.5)*.5
    amplitude=overlap(native,centers,t)@weights
    good=amplitude>=cfg["threshold"]
    points=points[good]
    amplitude=amplitude[good]
    gram=overlap(points,points,2*v)*amplitude[:,None]*amplitude[None,:]
    exact_env=(overlap(points,centers,v+t)@weights)*amplitude
    matrix=gram-2*np.diag(exact_env)
    numeric={}
    for h in cfg["integration_spacing"]:
        x=np.arange(-8.,8.+h/2,h)
        integral=np.ones((len(points),len(centers)))
        for i in range(3):
            g=gauss_1d(x,points[:,i],v)
            p=gauss_1d(x,centers[:,i],t)
            integral*=simpson(g[:,:,None]*p[:,None,:],x=x,axis=0)
        q=gram-2*np.diag((integral@weights)*amplitude)
        numeric[str(h)]=dict(max_error=float(np.max(abs(q-matrix))),matrix=q.tolist())
    return points,amplitude,matrix,numeric


def exhaustive(q):
    x=((np.arange(2**len(q))[:,None]>>np.arange(len(q)))&1).astype(float)
    e=np.einsum("ni,ij,nj->n",x,q,x,optimize=True)
    order=np.argsort(e)
    s=1-2*x
    j=(q-np.diag(np.diag(q)))/4
    h=-q.sum(axis=1)/2
    ising=(q.sum()+q.trace())/4+np.sum(s*h,axis=1)+np.einsum("ni,ij,nj->n",s,j,s,optimize=True)
    return dict(n=len(q),minimum=float(e[order[0]]),next_cost=float(e[order[1]]),
                best=x[order[0]].astype(int).tolist(),minimizers=int(np.count_nonzero(abs(e-e.min())<1e-12)),
                ising_error=float(np.max(abs(e-ising))))


def anneal(q,rng,reads,sweeps,best):
    x=rng.integers(0,2,(reads,len(q)),dtype=np.int8)
    diag=np.diag(q)
    off=q-np.diag(diag)
    fields=x@(2*off)+diag
    scale=float(np.max(np.sum(abs(q),axis=1)))
    temp=np.geomspace(scale*2,scale*.002,sweeps)
    for t in temp:
        for i in rng.permutation(len(q)):
            shift=1-2*x[:,i]
            diff=shift*fields[:,i]
            accept=(diff<0)|(rng.random(reads)<np.exp(np.minimum(0,-diff/t)))
            change=shift*accept
            x[:,i]+=change
            fields+=change[:,None]*(2*off[i])
    energy=np.einsum("ni,ij,nj->n",x,q,x,optimize=True)
    return dict(reads=reads,sweeps=sweeps,temperature=temp[[0,-1]].tolist(),
                optimum_hits=int(np.count_nonzero(abs(energy-best)<1e-12)),
                minimum=float(energy.min()),mean=float(energy.mean()))


def geometry_metrics(ref,pred,radius):
    d=np.linalg.norm(ref[:,None,:]-pred[None,:,:],axis=2)
    near=d<=radius
    score=np.where(near,1/(1+d),0.)
    sizes=near.sum(axis=1)
    covered=sizes>0
    return dict(
       coverage=float(covered.mean()),
       literal_coverage_count_predicted=float(near.any(axis=0).sum()/len(ref)),
       literal_precision=float(score.sum()/len(ref)**2),
       mean_cluster_precision=float(np.mean(score.sum(axis=1)/np.maximum(sizes,1))),
       closest_precision=float(score.max(axis=1).mean()),
       mean_matched_cluster_size=float(sizes[covered].mean()) if covered.any() else 0.,
       mean_size_over_all_reference=float(sizes.mean()),
       cluster_sizes=sizes.tolist())


def pdb_inventory(cfg):
    structures=[]
    for pdb,expected in cfg["pdb_resolutions"].items():
        src=Path(f"source/{pdb}.pdb.gz")
        waters={}
        with gzip.open(src,"rt",encoding="ascii") as stream:
            for line in stream:
                if line.startswith("REMARK   2 RESOLUTION."):
                    match=re.search(r"(\d+\.\d+) ANGSTROMS",line)
                    if match:
                        resolution=float(match.group(1))
                if line.startswith("HETATM") and line[17:20]=="HOH" and line[12:16].strip()=="O":
                    occ=float(line[54:60])
                    key=line[21:27]
                    waters[key]=max(occ,waters.get(key,0))
        assert resolution==expected and waters
        structures.append(dict(id=pdb,resolution=resolution,water_residue_count=len(waters),
                               waters_by_chain=dict(Counter(k[0] for k in waters))))
    return structures


def main():
    cfg=json.loads(Path("config/protocol.json").read_text())
    points,amplitude,q,numeric=assemble(cfg)
    exact=exhaustive(q)
    narrow=dict(cfg,density_variance=cfg["narrow_density_variance"])
    npoints,na,nq,nnumeric=assemble(narrow)
    ref=np.array([[0.,0,0],[8.,0,0],[16.,0,0]])
    repeated=np.concatenate([ref,ref+np.array([0,.15,0])])
    out=dict(points=points.tolist(),amplitudes=amplitude.tolist(),matrix=q.tolist(),numeric=numeric,exact=exact,
             annealing=anneal(q,np.random.default_rng(cfg["seed"]),cfg["sa_reads"],cfg["sa_sweeps"],exact["minimum"]),
             narrow=dict(points=npoints.tolist(),amplitudes=na.tolist(),matrix=nq.tolist(),numeric=nnumeric,
                         exact=exhaustive(nq)),
             pdb=pdb_inventory(cfg),
             metrics={"perfect":geometry_metrics(ref,ref,cfg["distance_cutoff"]),
                      "extra_predictions":geometry_metrics(ref,repeated,cfg["distance_cutoff"])},
             physical_minimum_distance_counterexample=dict(
               distance_angstrom=1.05,matrix=[[-3.,.4],[.4,-3.]],result=exhaustive(np.array([[-3.,.4],[.4,-3.]]))))
    Path("results/model-controls.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
