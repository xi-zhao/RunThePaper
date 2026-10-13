"""Exhaustive meet-in-the-middle distance certification at bounded weight.

If d <= 2h, a minimum logical operator partitions into two subsets of size <= h
with equal check syndrome and unequal logical syndrome. Store a minimum-weight
representative per syndrome. If two logical classes occur, at least one differs
from that representative, with a total weight no larger than the pair's total.
Thus exhaustive enumeration certifies the minimum whenever a witness <= 2h exists.
"""
import itertools
import json
import math
import time
from pathlib import Path
import numpy as np
from generate_algebra import construct, logical_basis, bits


def certify(check, stabilizer, h):
    logical = logical_basis(stabilizer, check)
    cs = [bits(col) for col in check.T]
    ls = [bits(col) for col in logical.T]
    n = len(cs)
    seen = {0:(0,0,0)}
    best = n+1
    witness = None
    tested = 1
    start = time.monotonic()
    for w in range(1,h+1):
        for inds in itertools.combinations(range(n),w):
            s = l = mask = 0
            for j in inds:
                s ^= cs[j];l ^= ls[j];mask |= 1<<j
            old = seen.get(s)
            if old is None:
                seen[s] = (l,w,mask)
            elif old[0] != l:
                combined = mask ^ old[2]
                distance = combined.bit_count()
                if distance < best:
                    best = distance;witness = combined
            tested += 1
        print('n',n,'enumerated_weight',w,'count',tested,'best',best,flush=True)
    support = None if witness is None else [j for j in range(n) if (witness>>j)&1]
    return {'n':n,'max_subset_weight':h,'enumerated_subsets':tested,
            'expected_enumeration':sum(math.comb(n,k) for k in range(h+1)),
            'exact_distance':best if best<=2*h else None,
            'certified_lower_bound':best if best<=2*h else 2*h+1,
            'logical_witness_support':support,'elapsed_seconds':time.monotonic()-start}


def main():
    models = json.loads(Path('config/models.json').read_text())['pairs']
    out=[]
    for model,h in zip(models[:2],[3,4]):
        hx,hz,_,_,tx,tz = construct(model)
        for name,check,stab,depth in [('quad_Z',hx,hz,h),('tri_Z',tx,tz,2)]:
            row=certify(check,stab,depth);row['code']=name;out.append(row)
    p=Path('outputs/data/distance.json');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
