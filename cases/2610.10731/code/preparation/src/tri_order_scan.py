"""Broader source-blind tricycle edge-color scan with circuit-distance witnesses."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import itertools
import json
import time
import hashlib
import numpy as np
import audit_sd6_timing_v3 as timing
from prep_decoder import ROOT, select_preparation_noise, prep_circuit, factorization_check
from simulate_sd6_factory_v2 import factory, edge_color, dem_arrays
from structured_schedule import structured_tri
from generate_algebra import construct
from generate import posteriors
from probe import exact_distribution


def distance_leq4(dem):
    h,o,_=dem_arrays(dem)
    keys=[(sum(int(x)<<i for i,x in enumerate(a)),sum(int(x)<<i for i,x in enumerate(b))) for a,b in zip(h.T,o.T)]
    ones={}
    def result(d,ids):
        assert not np.bitwise_xor.reduce(h[:,ids],axis=1).any()
        assert np.bitwise_xor.reduce(o[:,ids],axis=1).any()
        return dict(lower=d,upper=d,witness=ids)
    for i,(s,l) in enumerate(keys):
        if s==0 and l:return result(1,[i])
    for i,(s,l) in enumerate(keys):
        if s in ones and ones[s][0]!=l:return result(2,[ones[s][1],i])
        ones[s]=(l,i)
    pairs={};four=None
    for i,(si,li) in enumerate(keys):
        for j in range(i):
            s=si^keys[j][0];l=li^keys[j][1]
            if s in ones and ones[s][0]!=l:
                ids=[ones[s][1],j,i]
                if len(set(ids))==3:return result(3,ids)
            if four is None and s in pairs and pairs[s][0]!=l:
                ids=pairs[s][1]+[j,i]
                if len(set(ids))==4:four=ids
            if s not in pairs:pairs[s]=(l,[j,i])
    return result(4,four) if four else dict(lower=5,upper=None,witness=None)


def main():
    config=json.loads((ROOT/'config/tri-scan.json').read_text())
    models=json.loads((ROOT/'config/models.json').read_text())['pairs'];rows=[]
    out=ROOT/'tri-scan';out.mkdir(exist_ok=True);start=time.monotonic()
    for n4 in config['n4']:
        model=next(m for m in models if m['quad'][0]==n4);hx,*_,tz=construct(model)
        quad=edge_color(hx,100001);posterior=None;unique=set()
        candidates=[(f'random_{seed}',edge_color(tz,seed)) for seed in config['random_seeds']]
        candidates += [(f'structured_{flips}_{perm}',structured_tri(model,perm,flips))
                       for flips in itertools.product(range(2),repeat=3)
                       for perm in itertools.permutations(range(4))]
        for label,tri in candidates:
            identity=hashlib.sha256(json.dumps(tri).encode()).hexdigest()
            if identity in unique:continue
            unique.add(identity)
            old=timing.factory
            def chosen(*args,**kwargs):
                kwargs['tri_override']=tri;kwargs['quad_override']=quad
                return factory(*args,**kwargs)
            timing.factory=chosen
            try:c,dem,meta=timing.timing_circuit(model,config['p'],config['pccz'],'fresh_aligned')
            finally:timing.factory=old
            _,pdem,_=prep_circuit(model,config['p'],meta)
            if posterior is None:posterior=posteriors(pdem)
            _,_,kmap,kmle,marginal,_=posterior
            rest=select_preparation_noise(c,model,meta,False).detector_error_model()
            factor=factorization_check(dem,pdem,rest,model,meta)
            prob,_=exact_distribution(rest,meta)
            distance=distance_leq4(dem)
            row=dict(n4=n4,label=label,tri_layers=tri,tri_hash=identity,
                phase_distance=distance,alpha_map=float(kmap@prob),alpha_mle=float(kmle@prob),
                alpha_raw=float(marginal@prob),oracle_upper_bound=float(prob[0]),factorization=factor)
            rows.append(row)
            if len(rows)%16==0:
                print(n4,len(rows),round(time.monotonic()-start,2),flush=True)
                (out/'results.json').write_text(json.dumps(dict(complete=False,rows=rows),indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(dict(complete=True,config=config,rows=rows,
        elapsed_seconds=time.monotonic()-start,
        limitations=['Finite 64 random colorings plus 192 structured orders per code, deduplicated by actual layer list.',
            'Distance is for the one-pair Clifford phase detector model with ideal final syndrome diagnostics; not an identified author full-Pauli fault distance.',
            'Source acceptance is never a selection input. Compare within maximum proven distance only after enumeration.',
            'Oracle bound only covers quad-only repair under the same remaining SD6 circuit.']),indent=2)+'\n')


if __name__=='__main__':main()
