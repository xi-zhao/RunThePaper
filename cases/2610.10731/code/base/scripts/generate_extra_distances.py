"""Exact additional distances and explicitly heuristic large-code upper bounds."""
import json,time
from pathlib import Path
import numpy as np
from generate_algebra import construct,logical_basis,nullspace
from generate_distance import certify

def upper_bound(check,stabilizer,trials,rng):
    dual=logical_basis(stabilizer,check)
    best=check.shape[1]+1;witness=None;history=[]
    for it in range(trials):
        perm=rng.permutation(check.shape[1]);v=nullspace(check[:,perm])
        logical=(v@dual[:,perm].T)%2
        candidates=np.flatnonzero(np.any(logical,axis=1))
        if len(candidates):
            i=candidates[np.argmin(v[candidates].sum(1))];w=int(v[i].sum())
            if w<best:
                best=w;witness=sorted(perm[np.flatnonzero(v[i])].tolist());history.append([it,best])
    return {'n':check.shape[1],'upper_bound':best,'logical_witness_support':witness,'trials':trials,'improvements':history,'method':'random information-set nullspace search; NOT a distance lower bound'}

def main():
    cfg=json.loads(Path('config/models.json').read_text());rng=np.random.default_rng(261010731)
    out=[];start=time.monotonic()
    for i,m in enumerate(cfg['pairs']):
        hx,hz,_,_,tx,tz=construct(m)
        if i<2:
            r=certify(tz,tx,[3,4][i]);r.update(code='tri_X',pair=i);out.append(r)
        else:
            r=certify(tx,tz,3);r.update(code='tri_Z',pair=i);out.append(r)
            for name,check,stab in [('quad',hx,hz),('tri_X',tz,tx),('tri_Z_upper',tx,tz)]:
                r=upper_bound(check,stab,300,rng);r.update(code=name,pair=i);out.append(r)
                print(name,i,r['upper_bound'],flush=True)
    p=Path('outputs/data/extra-distances.json');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({'results':out,'elapsed_seconds':time.monotonic()-start},indent=2)+'\n')

if __name__=='__main__':main()
