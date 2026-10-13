"""Enumerated all-zero-detector minimum-order failures: a subset probability bound.
The empty error set is the MLE for zero syndrome when every DEM p_i<1/2.
Each selected set is distinct, so its exact finite-p probability can be summed.
This bounds only the declared phase probe, not source magic-state infidelity.
"""
from pathlib import Path
import json,itertools,hashlib,time
import numpy as np
from simulate_sd6_factory_v2 import factory,dem_arrays
from structured_schedule import structured_tri
def integer(x):return int.from_bytes(np.packbits(x,bitorder='little').tobytes(),'little')
def enumerate_sets(h,o,order):
    singles={}
    for i,s in enumerate(h):singles.setdefault(s,[]).append(i)
    found=set()
    if order==3:
        for i,j in itertools.combinations(range(len(h)),2):
            for k in singles.get(h[i]^h[j],[]):
                if k>j and o[i]^o[j]^o[k]:found.add((i,j,k))
    else:
        pairs={}
        for i,j in itertools.combinations(range(len(h)),2):
            key=h[i]^h[j];v=o[i]^o[j]
            for a,b,w in pairs.get(key,[]):
                if w!=v and len({a,b,i,j})==4:found.add(tuple(sorted((a,b,i,j))))
            pairs.setdefault(key,[]).append((i,j,v))
    return sorted(found)
def acceptance(h,p,meta):
    mask=(1<<(meta['npost']-meta['post_start']))-1
    keys=np.array([(s>>meta['post_start'])&mask for s in h],np.uint64)
    chars=np.arange(mask+1,dtype=np.uint64)
    parity=np.bitwise_count(chars[:,None]&keys[None,:])%2
    return float(np.exp(parity@np.log1p(-2*p)).mean())
out=Path('outputs/noise-minimum-failure-bounds-v2');out.mkdir(parents=True,exist_ok=True)
models=json.loads(Path('config/models.json').read_text())['pairs'][:2];result=[]
for m,order in zip(models,[3,4]):
    t0=time.monotonic();c,d,meta=factory(m,.001,.002,tri_override=structured_tri(m,(0,2,1,3)))
    hh,oo,_=dem_arrays(d);h=[integer(x) for x in hh.T];o=[integer(x) for x in oo.T]
    sets=enumerate_sets(h,o,order);inds=np.array(sets,dtype=int)
    logical=np.array([np.bitwise_xor.reduce([o[i] for i in v]) for v in sets],np.uint8)
    assert len(sets)>0 and all(np.bitwise_xor.reduce([h[i] for i in v])==0 for v in sets)
    rows=[]
    for p in [.0001,.0003,.0005,.001,.002,.003]:
        _,dd,_=factory(m,p,2*p,tri_override=structured_tri(m,(0,2,1,3)))
        h2,o2,prob=dem_arrays(dd);assert np.array_equal(hh,h2) and np.array_equal(oo,o2) and max(prob)<.5
        pzero=np.exp(np.log1p(-prob).sum());odds=prob/(1-prob)
        masses=pzero*np.prod(odds[inds],axis=1);alpha=acceptance(h,prob,meta)
        rows.append(dict(p=p,pccz=2*p,exact_model_acceptance=alpha,
          block_phase_ler_lower_bound=float(masses.sum()/alpha),
          per_qubit_phase_ler_lower_bound=float(masses@np.bitwise_count(logical)/(3*alpha))))
    result.append(dict(n4=m['quad'][0],fault_order=order,sets=sets,logical=logical.tolist(),rows=rows,
        count=len(sets),baseline_dem_sha256=hashlib.sha256(str(d).encode()).hexdigest(),wall_seconds=time.monotonic()-t0))
    print(json.dumps({k:v for k,v in result[-1].items() if k not in ('sets','logical')}),flush=True)
    (out/'results.json').write_text(json.dumps(dict(results=result,limits=[
      'Only minimum-order, exactly-zero-full-syndrome sets are included; nonzero syndromes and higher fault orders are excluded.',
      'The probability sum is a lower bound in the stated independent-DEM model, evaluated in float64; it is not an upper bound or an arbitrary-precision certified interval.',
      'The code-pair phase observable, schedule, ideal terminal readout and source identity limitations still apply.',
      'Acceptance is computed by the Fourier projector on the teleportation detectors, without Monte Carlo.'
    ]),indent=2)+'\n')
