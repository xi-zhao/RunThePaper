"""One-parameter convergence controls with an independent RNG per trajectory.

All matter initial states and Hamiltonian parameters are the original ones.
Vacuum cavity is an explicit reproduction condition. GS Q dephasing is valid
for the linear means only; these paths do not reproduce coherent-GS entropy.
"""
import json,math,time
from pathlib import Path
import numpy as np
from generate_dynamics import Hybrid


def run_job(args):
    cfg,m,ic,index=args;started=time.monotonic();arrays={};records=[]
    n=cfg['GS_trajectories'] if ic['id']=='GS' else cfg['Fock_trajectories']
    for lev in cfg['levels']:
        h=Hybrid(m['L'],m['N'],m['statistics'],lev['cutoff'],cfg['delta'],cfg['gamma'])
        samples=[];traces=[];diags=[]
        for i in range(n):
            rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],index,i]))
            obs,trace,diag=h.trajectory(ic.get('occupations','GS'),rng,np.array(cfg['times']),lev['rtol'],lev['atol'],entropy=ic['id']!='GS')
            samples.append(obs);traces.append(trace);diags.append(diag)
        prefix=m['statistics']+'_'+ic['id']+'_'+lev['id']
        arrays.update({prefix+'_'+k:np.array([s[k] for s in samples]) for k in samples[0]})
        arrays[prefix+'_traces']=np.array(traces)
        records.append(dict(id=prefix,trajectories=n,diagnostics=diags,level=lev))
        print(prefix,n,round(time.monotonic()-started,2),flush=True)
    return arrays,records


def main():
    from concurrent.futures import ProcessPoolExecutor
    cfg=json.loads(Path('config/paired-controls.json').read_text());jobs=[]
    for m in cfg['models']:
        for ic in m['initial_states']:jobs.append((cfg,m,ic,len(jobs)))
    started=time.monotonic();arrays={};records=[]
    with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
        for a,r in pool.map(run_job,jobs):arrays.update(a);records.extend(r)
    checks=[]
    for cfg,m,ic,index in jobs:
        prefix=m['statistics']+'_'+ic['id'];obs=['density','kinetic','pairing','X','photon','OdagO','pair_sum','traces']
        if ic['id']!='GS':obs+=['entropy']
        for la,lb in [('cut6_loose','cut6_tight'),('cut6_tight','cut8_tight'),('cut8_tight','cut10_tight')]:
            for key in obs:
                a=arrays[prefix+'_'+la+'_'+key];b=arrays[prefix+'_'+lb+'_'+key];difference=b-a
                mean=difference.mean(0);se=difference.std(0,ddof=1)/math.sqrt(len(a));z=np.divide(abs(mean),se,out=np.zeros_like(mean),where=se>1e-12)
                checks.append(dict(initial=prefix,observable=key,level_pair=[la,lb],trajectories=len(a),max_absolute_paired_mean=float(abs(mean).max()),max_paired_SE=float(se.max()),max_absolute_single_path_difference=float(abs(difference).max()),max_mean_over_SE=float(z.max())))
    out=Path('outputs/data');out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'paired-controls.npz',**arrays)
    (out/'paired-controls.json').write_text(json.dumps(dict(config=cfg,records=records,checks=checks,elapsed_seconds=time.monotonic()-started,limits=['Finite observed convergence, not a rigorous infinite-cavity error bound.','GS controls apply to linear Q-commuting ensemble means; coherent-GS trajectory entropy is excluded.','Pointwise empirical SEs do not by themselves define simultaneous figure acceptance.']),indent=2)+'\n')

if __name__=='__main__':main()
