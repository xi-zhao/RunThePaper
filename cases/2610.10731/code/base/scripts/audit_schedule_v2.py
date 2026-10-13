"""Finite fault-pattern and layer-order audit of the selected phase-probe schedule.
This exhausts accepted DEM error sets of sizes 0,1,2 and is not a whole LER
certificate. DEM signatures arise from physical Pauli locations, independently
audited by the separate diagnostic review.
"""
import json,itertools
from pathlib import Path
import numpy as np
from simulate_sd6_factory_v2 import factory,dem_arrays
from structured_schedule import structured_tri
def integer(x):return int.from_bytes(np.packbits(x,bitorder='little').tobytes(),'little')
def signatures(d):
    h,o,p=dem_arrays(d);return [integer(x) for x in h.T],[integer(x) for x in o.T],p
def zero_order(h,o):
    seen={};one=False;bad=0
    for i,(s,l) in enumerate(zip(h,o)):
        if s==0 and l:one=True
        if s in seen and seen[s][0]!=l:bad+=1
        seen[s]=(l,i)
    return (1 if one else 2 if bad else None),bad
def selected_audit(d,meta):
    h,o,p=signatures(d);mask=((1<<meta['npost'])-1)^((1<<meta['post_start'])-1)
    groups={};seen={0:(0,[])};conflicts=[];count=0
    for i,s in enumerate(h):groups.setdefault(s&mask,[]).append(i)
    def add(s,l,ids):
        nonlocal count
        count+=1
        if s in seen and seen[s][0]!=l:conflicts.append(dict(syndrome=str(s),first=seen[s][1],second=ids,logical=[seen[s][0],l]))
        else:seen[s]=(l,ids)
    for i in groups.get(0,[]):add(h[i],o[i],[i])
    for group in groups.values():
        for i,j in itertools.combinations(group,2):add(h[i]^h[j],o[i]^o[j],[i,j])
    # Meet-in-the-middle search for minimum all-zero-detector logical fault order.
    singles={s:[] for s in h}
    for i,s in enumerate(h):singles[s].append(i)
    minimum,_=zero_order(h,o);witness=None;pairs={}
    if minimum is None:
        for i,j in itertools.combinations(range(len(h)),2):
            key=h[i]^h[j];val=o[i]^o[j]
            for k in singles.get(key,[]):
                if k!=i and k!=j and o[k]!=val:
                    minimum=3;witness=[i,j,k];break
            if minimum==3:break
            if key in pairs:
                l,a,b=pairs[key]
                if l!=val and len({a,b,i,j})==4:
                    witness=[a,b,i,j]
            else:pairs[key]=(val,i,j)
        if minimum is None and witness is not None:minimum=4
    return dict(accepted_sets_le2=count,unique_syndromes=len(seen),logical_conflicts=len(conflicts),
      conflict_examples=conflicts[:3],minimum_zero_detector_dem_faults=minimum,zero_detector_witness=witness)
models=json.loads(Path('config/models.json').read_text())['pairs'][:2]
rows=[];out=Path('outputs/noise-schedule-v2');out.mkdir(parents=True,exist_ok=True)
for m in models:
    order_rows=[]
    for order in itertools.permutations(range(4)):
        c,d,meta=factory(m,.001,.002,tri_override=structured_tri(m,order))
        h,o,_=signatures(d);minimum,bad=zero_order(h,o)
        order_rows.append(dict(order=list(order),single_signature_logical_collisions=bad,zero_fault_order_at_most=minimum))
    order=(0,2,1,3);c,d,meta=factory(m,.001,.002,tri_override=structured_tri(m,order))
    row=dict(n4=m['quad'][0],orders=order_rows,selected_order=list(order),selected=selected_audit(d,meta))
    rows.append(row)
    (out/f'n{m["quad"][0]}.stim').write_text(str(c))
    (out/f'n{m["quad"][0]}.dem').write_text(str(d))
    (out/f'n{m["quad"][0]}-schedule.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({k:v for k,v in row.items() if k!='orders'}),flush=True)
(out/'audit.json').write_text(json.dumps(dict(results=rows,boundary='An all-zero-syndrome distance is not automatically a most-likely-error failure exponent. All accepted sets up to two DEM errors were checked, but accepted triples for n72 remain outside this audit; author schedule and full magic-state observable remain unestablished.'),indent=2)+'\n')
