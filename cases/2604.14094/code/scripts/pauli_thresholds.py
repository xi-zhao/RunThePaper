"""Invert per-weight Pauli counts without constructing the full tensor operator."""

import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from generate import oscillator, pauli_local

TARGETS = "config/pauli-histogram-targets.csv"
RESULT = "results/pauli-thresholds.json"


def group(terms,k):
    return [np.sort([abs(c) for (x,z),c in terms.items() if (x|z).bit_count()==w])
            for w in range(k+1)]


def components(k,prescription,extract=pauli_local,matrix=oscillator):
    with np.errstate(divide="ignore",over="ignore",invalid="ignore"):
        x2,x4=matrix(2**k,prescription)
    assert np.isfinite(x2).all() and np.isfinite(x4).all()
    single=np.diag(np.arange(len(x2))+.5)+(x4+4*np.trace(x2)/len(x2)*x2)/64
    return group(extract(single,1e-13),k),group(extract(x2,1e-13),k)


def count(single,pair,w,t):
    k=len(pair)-1
    if w==0:
        return 1
    n=len(single[w])-np.searchsorted(single[w],t,side="right") if w<=k else 0
    for a in range(max(1,w-k),min(k,w-1)+1):
        x,y=pair[a],pair[w-a]
        n+=np.sum(len(y)-np.searchsorted(y,32*t/x,side="right"))
    return int(3*n)


def crossing(test, ceiling, steps=90):
    if test(0.):
        return 0.
    assert test(ceiling)
    low,high=0.,ceiling
    for _ in range(steps):
        mid=(low+high)/2
        if mid in (low,high):
            break
        if test(mid):
            high=mid
        else:
            low=mid
    return high


def infer(single,pair,target):
    k=len(pair)-1
    cap=max(max((p[-1] for p in single[1:] if len(p)),default=1.),
            max((p[-1] for p in pair[1:] if len(p)),default=1.)**2/32)
    cap=2*float(cap)
    count_all=lambda t:np.array([count(single,pair,w,t) for w in range(2*k+1)])
    intervals=[]
    for w,n in enumerate(target):
        if w==0 or n==0:
            low=crossing(lambda t:count(single,pair,w,t)<=n,cap)
            high=None
        else:
            low=crossing(lambda t:count(single,pair,w,t)<=n,cap)
            high=crossing(lambda t:count(single,pair,w,t)<n,cap)
        intervals.append([low,high])
    lo=max(p[0] for p in intervals)
    hi=min(p[1] for p in intervals if p[1] is not None)
    witness=None
    if lo>hi:
        midpoint=float(np.sqrt(lo*hi)) if hi else lo/2
        counts=count_all(midpoint)
        higher=int(np.argmax(counts-target))
        lower=int(np.argmin(counts-target))
        assert counts[higher]>target[higher] and counts[lower]<target[lower]
        witness=dict(threshold=midpoint,excess_weight=higher,excess_count=int(counts[higher]),
                     excess_target=int(target[higher]),deficit_weight=lower,
                     deficit_count=int(counts[lower]),deficit_target=int(target[lower]))
    intersect=hi>lo
    if intersect:
        trial=(lo+hi)/2
        assert np.array_equal(count_all(trial),target)
    def residual(t):
        delta=count_all(t)-target
        return delta.max(),(-delta).max()
    def more_deficits(t):
        excess,deficit=residual(t)
        return excess<=deficit
    boundary=crossing(more_deficits,cap)
    trial=[0.,boundary,np.nextafter(boundary,0.)]
    best=min(trial,key=lambda t:max(residual(t)))
    delta=count_all(best)-target
    return dict(weight_intervals=intervals,lower_max=lo,upper_min=hi,
        exact_threshold_exists=intersect,opposite_residual_witness=witness,
        best_sampled_max_error=int(np.max(abs(delta))),best_sampled_threshold=float(best),
        residual_counts=delta.tolist())


def main():
    raw=np.loadtxt(TARGETS,delimiter=",",skiprows=1,dtype=int)
    result={}
    for k in range(2,11):
        chosen=raw[raw[:,0]==k]
        assert np.array_equal(chosen[:,1],np.arange(2*k+1))
        target=chosen[:,2]
        out={}
        for p in ("projected_position","normal_ordered"):
            single,pair=components(k,p)
            out[p]=infer(single,pair,target)
        result[str(k)]=out
        print(k,[(p,v["lower_max"],v["upper_min"],v["best_sampled_max_error"]) for p,v in out.items()],flush=True)
    Path(RESULT).write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
