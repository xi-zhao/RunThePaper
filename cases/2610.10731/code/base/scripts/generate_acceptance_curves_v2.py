"""Acceptance and live-qubit volume of explicitly specified full-SD6 circuits.
Generated directly from the noisy circuit, independently of rare-event weights
and the logical decoder. This does not establish source circuit identity.
"""
from pathlib import Path
import json,time
import numpy as np
from simulate_sd6_factory_v2 import factory,binomial_interval
from structured_schedule import structured_tri
cfg=json.loads(Path('config/acceptance-curves-v2.json').read_text())
models=json.loads(Path('config/models.json').read_text())['pairs']
out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True);rows=[];circuits=[]
for ji,j in enumerate(cfg['jobs']):
    t0=time.monotonic();m=next(x for x in models if x['quad'][0]==j['n4'])
    c,d,meta=factory(m,j['p'],j['pccz'],tri_override=structured_tri(m,(0,2,1,3)))
    sampler=c.compile_detector_sampler(seed=j['seed']);accepted=0;n=0
    while n<j['shots']:
        k=min(20000,j['shots']-n)
        det=sampler.sample(k);accepted+=int((~np.any(det[:,meta['post_start']:meta['npost']],axis=1)).sum());n+=k
    live=0;active=0;idle=0
    for layer in meta['layers']:
        acted=set(t for op in layer['operations'] for t in op['targets'])
        active+=len(acted);idle+=len(layer['idles']);live+=len(acted)+len(layer['idles'])
    alpha=accepted/n;ci=binomial_interval(accepted,n)
    rows.append(dict(**j,accepted=accepted,acceptance=alpha,acceptance_ci95=ci,
      single_pair_active_qubit_layers=active,single_pair_idle_qubit_layers=idle,
      three_pair_raw_live_volume=3*live,
      independence_yield=alpha**3,
      expected_live_volume_per_CCZ_assuming_independence=3*live/(2*alpha**3) if alpha else None,
      cost_ci95_from_acceptance_only=[3*live/(2*ci[1]**3),3*live/(2*ci[0]**3) if ci[0] else None],
      zero_acceptance_means_unbounded_cost_upper=not bool(ci[0]),
      wall_seconds=time.monotonic()-t0))
    circuits.append(dict(n4=j['n4'],p=j['p'],pccz=j['pccz'],stim=str(c),schedule=meta))
    (out/'results.json').write_text(json.dumps(dict(rows=rows,limits=[
       'All declared live idles have SD6 noise; fixed structured tricycle schedule and independent seed-1 quad schedule.',
       'Direct circuit sampling; binomial 95% intervals describe only this declared protocol.',
       'Costs use all live qubit layers and the source alpha^3 independence approximation; no downstream gadget overhead.',
       'No magic-state logical error rate, author schedule identity or source-curve agreement follows from this acceptance study.']),indent=2)+'\n')
    (out/'circuits.json').write_text(json.dumps(circuits,separators=(',',':'))+'\n')
    print(json.dumps(rows[-1]),flush=True)
