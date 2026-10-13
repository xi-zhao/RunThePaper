"""Exhaust every accepted independent-DEM set of weights zero through three.
This checks syndrome/logical ambiguity, not finite-p MLE performance or source identity.
"""
from pathlib import Path
import json,time,itertools
import numpy as np
from simulate_sd6_factory_v2 import factory,dem_arrays
from structured_schedule import structured_tri

def integer(x): return int.from_bytes(np.packbits(x,bitorder='little').tobytes(),'little')
def unpack(x): return [((int(x)>>(16*i))&65535)-1 for i in range(3) if ((int(x)>>(16*i))&65535)]
def audit(model):
    start=time.monotonic()
    _,dem,meta=factory(model,.001,.002,tri_override=structured_tri(model,(0,2,1,3)))
    h,o,p=dem_arrays(dem);full=[integer(x) for x in h.T];obs=np.array([integer(x) for x in o.T],np.uint8)
    lo=np.array([s&((1<<64)-1) for s in full],np.uint64);hi=np.array([s>>64 for s in full],np.uint64)
    mask=((1<<meta['npost'])-1)^((1<<meta['post_start'])-1)
    post=[s&mask for s in full];groups={}
    for i,s in enumerate(post):groups.setdefault(s,[]).append(i)
    groups={k:np.array(v,np.int64) for k,v in groups.items()}
    count3=0
    for i in range(len(full)):
        for j in range(i+1,len(full)):
            k=groups.get(post[i]^post[j])
            if k is not None:count3+=len(k)-np.searchsorted(k,j+1)
    count2=sum(len(g)*(len(g)-1)//2 for g in groups.values())
    count1=len(groups.get(0,[]))
    dtype=np.dtype([('hi','<u8'),('lo','<u8'),('logical','u1'),('weight','u1'),('ids','<u8')])
    arr=np.zeros(1+count1+count2+count3,dtype);at=1
    def put(indices,weight):
        nonlocal at
        size=len(indices[-1]) if isinstance(indices[-1],np.ndarray) else 1
        v=arr[at:at+size]
        for n,ix in enumerate(indices):
            v['lo']^=lo[ix];v['hi']^=hi[ix];v['logical']^=obs[ix];v['ids']|=(np.asarray(ix,np.uint64)+1)<<(16*n)
        v['weight']=weight;at+=size
    for i in groups.get(0,[]):put([i],1)
    for g in groups.values():
        for ii,i in enumerate(g[:-1]):put([i,g[ii+1:]],2)
    for i in range(len(full)):
        for j in range(i+1,len(full)):
            k=groups.get(post[i]^post[j])
            if k is None:continue
            kk=k[np.searchsorted(k,j+1):]
            if len(kk):put([i,j,kk],3)
    assert at==len(arr)
    arr.sort(order=['hi','lo','logical','weight'],kind='quicksort')
    same=(arr['hi'][1:]==arr['hi'][:-1])&(arr['lo'][1:]==arr['lo'][:-1])
    collisions=np.flatnonzero(same&(arr['logical'][1:]!=arr['logical'][:-1]))
    examples=[]
    for ii in collisions[:20]:
        a,b=arr[ii],arr[ii+1]
        examples.append({'syndrome':str((int(a['hi'])<<64)|int(a['lo'])),
                         'first':unpack(a['ids']),'second':unpack(b['ids']),
                         'weights':[int(a['weight']),int(b['weight'])],
                         'logical':[int(a['logical']),int(b['logical'])]})
    keys={(int(arr[i]['hi']),int(arr[i]['lo'])) for i in collisions}
    return dict(n4=model['quad'][0],mechanisms=len(full),accepted_sets_by_weight=list(map(int,[1,count1,count2,count3])),
                distinct_syndromes=int(len(arr)-same.sum()),ambiguous_syndromes=len(keys),
                examples=examples,wall_seconds=time.monotonic()-start,array_bytes=arr.nbytes)
out=Path('outputs/noise-accepted-triples-v2');out.mkdir(parents=True,exist_ok=True)
models=json.loads(Path('config/models.json').read_text())['pairs'][:2]
rows=[]
for m in models:
    rows.append(audit(m));print(json.dumps(rows[-1]),flush=True)
    (out/'results.json').write_text(json.dumps(dict(rows=rows,limits=[
        'Accepted means all teleportation detectors zero, with preparation and ideal terminal syndromes retained for decoding.',
        'Signatures are exact binary calculations; probabilities are not used to choose a finite-p decoder.',
        'An ambiguous syndrome shows some member of its class must fail under any syndrome-only deterministic decoder.',
        'Nonambiguous weight <=3 sets do not by themselves certify any finite-p MLE choice or all physical source circuits.'
    ]),indent=2)+'\n')
