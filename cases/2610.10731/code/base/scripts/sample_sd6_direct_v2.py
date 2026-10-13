"""Direct-circuit sampling control for the structured single-pair phase probe."""
from pathlib import Path
import json,time
import numpy as np
from simulate_sd6_factory_v2 import factory,Decoder,binomial_interval
from structured_schedule import structured_tri
cfg=json.loads(Path('config/noise-direct-control-v2.json').read_text())
models=json.loads(Path('config/models.json').read_text())['pairs']
out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True);rows=[]
for j in cfg['jobs']:
    started=time.monotonic();m=next(m for m in models if m['quad'][0]==j['n4'])
    c,d,meta=factory(m,j['p'],j['pccz'],tri_override=structured_tri(m,(0,2,1,3)))
    sampler=c.compile_detector_sampler(seed=j['seed']);decoder=Decoder(d,30)
    n=accepted=failed=0;per=np.zeros(3,dtype=np.int64);sum_sq=0.
    while n<j['shots']:
        batch=min(1000,j['shots']-n);det,obs=sampler.sample(batch,separate_observables=True)
        mask=~np.any(det[:,meta['post_start']:meta['npost']],axis=1)
        ds=det[mask].astype(np.uint8);os=obs[mask].astype(np.uint8)
        if len(ds):
            patterns,inverse=np.unique(ds,axis=0,return_inverse=True)
            pred=np.array([decoder.predict(s) for s in patterns],np.uint8)
            residual=os^pred[inverse];fraction=residual.mean(1)
            accepted+=len(ds);failed+=int(np.any(residual,axis=1).sum());per+=residual.sum(0).astype(np.int64)
            sum_sq+=float(fraction@fraction)
        n+=batch
        (out/'progress.json').write_text(json.dumps(dict(n4=j['n4'],shots=n,accepted=accepted,failed=failed,
             decoder_calls=decoder.calls,decoder_seconds=decoder.seconds),indent=2)+'\n')
    mean=float(per.sum()/(3*accepted))
    row={**j,'accepted':accepted,'acceptance':accepted/n,'acceptance_ci95':binomial_interval(accepted,n),
         'failed':failed,'logical_bit_failures':per.tolist(),'block_phase_ler':failed/accepted,
         'block_phase_ler_ci95':binomial_interval(failed,accepted),'per_qubit_phase_ler':mean,
         'per_qubit_phase_ler_SE':float(np.sqrt(max(0.,sum_sq/accepted-mean**2)/(accepted-1))),
         'zero_failure_is_not_zero_rate':failed==0,'decoder_calls':decoder.calls,
         'wall_seconds':time.monotonic()-started}
    rows.append(row);print(json.dumps(row),flush=True)
    (out/'results.json').write_text(json.dumps(dict(rows=rows,limits=[
      'Direct Stim circuit samples; the same exact DEM-error MLE is used as in importance sampling.',
      'Three logical parity bits may be correlated; per-qubit SE is computed from the per-shot fraction, not a binomial with 3N trials.',
      'This is the same explicitly declared full-SD6 Clifford phase probe, not full non-Clifford magic-state fidelity or a source-curve acceptance.'
    ]),indent=2)+'\n')
