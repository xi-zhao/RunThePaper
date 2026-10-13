"""Finite full-SD6 alternative: repair noisy quad preparation frame before rejection.

BFS finds a minimum-Hamming-weight measurement-flip explanation of the accessible
quad preparation metacheck syndrome. Three fixed column orders expose ties.
This is not assumed to be the author's decoder or a circuit-level optimum.
"""
from pathlib import Path
import json,time,collections,hashlib
import numpy as np
from probe import ROOT,build,exact_distribution
from generate_algebra import construct,nullspace


def bfs_table(check,order):
    m,n=check.shape;states=1<<m
    cols=[sum(int(check[i,j])<<i for i in range(m)) for j in range(n)]
    distance=np.full(states,-1,np.int16);repair=np.zeros(states,np.uint64);distance[0]=0
    queue=collections.deque([0])
    while queue:
        s=queue.popleft()
        for j in order:
            t=s^cols[j]
            if distance[t]<0:
                distance[t]=distance[s]+1;repair[t]=int(repair[s])^(1<<int(j));queue.append(t)
    assert np.all(distance>=0)
    # Full table syndrome and Hamming-weight consistency checks, independent of traversal.
    syndrome=np.zeros(states,np.int64)
    weights=np.zeros(states,np.int16)
    for j,c in enumerate(cols):
        active=((repair>>j)&1).astype(bool);syndrome[active]^=c;weights+=active
    assert np.array_equal(syndrome,np.arange(states)) and np.array_equal(weights,distance)
    # Every graph edge changes shortest distance by at most one; together with
    # valid weight witnesses this certifies a shortest-path / minimum-weight table.
    for c in cols:assert np.all(np.abs(distance-distance[np.arange(states)^c])<=1)
    return repair,distance,cols


def main():
    cfg=json.loads((ROOT/'config/frame-repair.json').read_text());models=json.loads((ROOT/'config/models.json').read_text())['pairs'];rows=[];tables={};started=time.monotonic()
    for n4 in cfg['n4']:
        model=next(m for m in models if m['quad'][0]==n4);hx,hz,mx,mz,tx,tz=construct(model);mq=nullspace(hx.T);nt=len(nullspace(tz.T));q=len(tx)
        orders=[('ascending',list(range(len(hx)))),('descending',list(reversed(range(len(hx))))),('permuted',np.random.default_rng(cfg['tie_seed']).permutation(len(hx)).tolist())]
        decoders=[];tableinfo=[];refdist=None
        for name,order in orders:
            repair,dist,cols=bfs_table(mq,order)
            if refdist is None:refdist=dist
            else:assert np.array_equal(dist,refdist)
            mapped=((repair>>(3*q))&((1<<q)-1)).astype(np.uint16);decoders.append((name,mapped))
            tableinfo.append(dict(name=name,column_order=order,repair_sha256=hashlib.sha256(repair.tobytes()).hexdigest(),mapped_sha256=hashlib.sha256(mapped.tobytes()).hexdigest()))
            tables[f'n{n4}_{name}_repair']=repair;tables[f'n{n4}_{name}_distance']=dist;tables[f'n{n4}_{name}_mapped']=mapped
        for si,schedule in enumerate(cfg['schedules']):
          for vi,(p,pc) in enumerate(cfg['points']):
            c,d,meta,_=build(model,p,pc,schedule,dict(id='sd6'));prob,_=exact_distribution(d,meta)
            assert meta['post_start']==nt+len(mq) and meta['npost']-meta['post_start']==q
            seed=cfg['seed']+n4*10000+si*100+vi;sampler=c.compile_detector_sampler(seed=seed)
            totals={name:dict(accepted=0,salvaged=0,lost_raw=0,disagrees_ascending=0,delta_sum=0) for name,_ in decoders};rawtotal=0;syndrome_counts=np.zeros(1<<len(mq),np.int64);remaining=cfg['shots']
            while remaining:
                num=min(cfg['batch'],remaining);det=sampler.sample(num)
                syndrome=det[:,nt:meta['post_start']].astype(np.int64)@(1<<np.arange(len(mq),dtype=np.int64))
                post=det[:,meta['post_start']:meta['npost']].astype(np.int64)@(1<<np.arange(q,dtype=np.int64))
                raw=(post==0);rawtotal+=int(raw.sum());syndrome_counts+=np.bincount(syndrome,minlength=len(syndrome_counts));first=None
                for name,mapped in decoders:
                    accepted=(post==mapped[syndrome]);t=totals[name];t['accepted']+=int(accepted.sum());t['salvaged']+=int((accepted&~raw).sum());t['lost_raw']+=int((~accepted&raw).sum())
                    if first is None:first=accepted
                    t['disagrees_ascending']+=int((accepted!=first).sum());t['delta_sum']+=int(accepted.sum())-int(first.sum())
                remaining-=num
            for name,mapped in decoders:
                t=totals[name];a=t['accepted']/cfg['shots'];delta=t['delta_sum']/cfg['shots'];t['acceptance']=a;t['se']=float(np.sqrt(a*(1-a)/cfg['shots']));t['delta_vs_ascending']=delta;t['delta_se']=float(np.sqrt((t['disagrees_ascending']/cfg['shots']-delta*delta)/cfg['shots']))
            rows.append(dict(n4=n4,p=p,pccz=pc,schedule=schedule,shots=cfg['shots'],seed=seed,raw_exact_alpha=float(prob[0]),raw_accepted=rawtotal,raw_mc_alpha=rawtotal/cfg['shots'],repairs=totals,metacheck_rank=len(mq),states=len(syndrome_counts),quad_measurements=len(hx),table_max_weight=int(refdist.max()),quad_metacheck_zero=int(syndrome_counts[0]),tables=tableinfo,table_checks='all syndromes matched, weights matched, graph edge Lipschitz bound passed, three tie orders have identical minimum weights'))
        print(json.dumps(dict(n4=n4,rows=len(rows),elapsed=time.monotonic()-started)),flush=True)
    out=Path('frame-repair');out.mkdir(exist_ok=True);np.savez_compressed(out/'tables.npz',**tables)
    (out/'results.json').write_text(json.dumps(dict(format='qldpc.prep-frame-repair.v1',rows=rows,wall_seconds=time.monotonic()-started,definition='Minimum-Hamming-weight quad measurement errors e satisfy nullspace(HX.T)e=quad metacheck syndrome; teleport detector corrected by e[3q:4q]. All full SD6 noise retained. Unconditional denominator includes every attempted run.',limits=['Finite independent frame-repair candidate, not identified author implementation.','Only measurement error model in the repair cost; actual samples retain all circuit errors and correlations.','No logical error rate comparison; higher acceptance can trade off with conditional logical fidelity.','Three fixed tie-breaks are sensitivity controls, not optimized to source curves.']),indent=2)+'\n')

if __name__=='__main__':main()
