"""Standalone public entry points; frozen results are never overwritten."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
sys.dont_write_bytecode = True
import numpy as np

CASE = Path(__file__).resolve().parents[2]
CODE = CASE/'code'

def read(path): return json.loads(path.read_text())

def verify():
    result=read(CASE/'outputs/data/preparation/results.json')
    assert result['complete'] and len(result['rows'])==44
    tables=np.load(CASE/'outputs/data/preparation/tables.npz', allow_pickle=False)
    programs=read(CASE/'outputs/data/preparation/programs.json')
    worst=0.
    for row in result['rows']:
        tag=row['tag'];rest=tables[tag+'__rest_distribution']
        assert np.min(rest)>-1e-12 and abs(rest.sum()-1)<1e-10
        assert hashlib.sha256(programs[tag]['full'].encode()).hexdigest()==row['circuit_sha256']
        for mode in ['map','mle']:
            kernel=tables[tag+'__'+mode+'_residual']
            assert np.min(kernel)>-1e-12 and abs(kernel.sum()-1)<1e-10
            error=abs(float(rest@kernel)-row['alpha_'+mode]);worst=max(worst,error)
            assert error<1e-11
    return dict(configurations=44,maximum_acceptance_reanalysis_error=worst,
                meaning='Checks frozen independent distributions, not author agreement.')

def quick():
    sys.path.insert(0,str(CODE/'preparation/src'))
    from generate_algebra import construct,rank
    from prep_decoder import full_factory,prep_circuit,select_preparation_noise
    from generate import posteriors
    from probe import exact_distribution
    models=read(CODE/'base/config/models.json')['pairs'];algebra=[]
    for m in models:
        hx,hz,mx,mz,tx,tz=construct(m)
        residuals=[int(np.count_nonzero(a@b%2)) for a,b in
                   [(hx,hz.T),(mx,hx),(mz,hz),(tx,tz.T)]]
        assert residuals==[0,0,0,0]
        k=hx.shape[1]-rank(hx)-rank(hz);kt=tx.shape[1]-rank(tx)-rank(tz)
        assert (k,kt)==(6,3)
        algebra.append(dict(n=hx.shape[1],k=k,tricycle_k=kt,residuals=residuals))
    cfg=read(CODE/'preparation/config/experiment.json');m=models[0]
    c,dem,meta=full_factory(m,.001,.002,'fresh_aligned',cfg['orders'][0])
    _,pdem,_=prep_circuit(m,.001,meta)
    _,_,kmap,kmle,_,_=posteriors(pdem)
    rest,_=exact_distribution(select_preparation_noise(c,m,meta,False).detector_error_model(),meta)
    alpha=float(rest@kmap)
    frozen=next(r for r in read(CASE/'outputs/data/preparation/results.json')['rows']
                if r['n4']==54 and r['schedule']=='fresh_aligned' and r['order']['id']=='s100001'
                and r['p']==.001 and r['pccz']==.002)
    error=abs(alpha-frozen['alpha_map']);assert error<1e-11
    return dict(algebra=algebra,acceptance_map=alpha,acceptance_mle=float(rest@kmle),
                absolute_replay_error=error,scope='Five algebra models and one original-size acceptance control; not the full paper.')

def render(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=read(CASE/'outputs/data/preparation/results.json')['rows']
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    for ax,n in zip(axes,[54,72]):
        chosen=sorted([r for r in rows if r['n4']==n and r['p']==.001
            and r['schedule']=='fresh_aligned' and r['order']['id']=='s100001'],key=lambda r:r['pccz'])
        for key,label,style in [('alpha_raw','Noisy frame','o-'),('alpha_map','Frame MAP','s-'),
               ('alpha_mle','Fault MLE','x--'),('oracle_quad_prep_upper_bound','Ideal-frame bound',':')]:
            ax.plot([r['pccz'] for r in chosen],[100*r[key] for r in chosen],style,label=label)
        ax.set(title=f'{n}-qubit quadcycle',xlabel=r'$p_{CCZ}$',ylabel='Acceptance per attempt (%)')
        ax.set_xticks([0,.001,.002,.003,.004])
        ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Independent full-SD6 calculation; p = 0.001',fontsize=12)
    target=out/'acceptance-generated.png';fig.savefig(target,dpi=170);plt.close(fig)
    return dict(figure=target.name,source='outputs/data/preparation/results.json')

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['quick','verify','render','algebra','preparation'],default='quick');a=p.parse_args()
    out=Path(tempfile.mkdtemp(prefix='qldpc-reproduction-'));start=time.monotonic()
    if a.mode in ['quick','verify']:result=quick() if a.mode=='quick' else verify()
    elif a.mode=='render':result=render(out)
    else:
        name='preparation' if a.mode=='preparation' else 'base'
        work=out/'calculation';shutil.copytree(CODE/name,work)
        entry='src/generate.py' if a.mode=='preparation' else 'scripts/generate_algebra.py'
        subprocess.run([sys.executable,entry],cwd=work,check=True)
        result=dict(mode=a.mode,results_directory='calculation/outputs',whole_paper_complete=False)
    result['elapsed_seconds']=time.monotonic()-start
    (out/'run-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(output_directory=str(out),result=result),indent=2))

if __name__=='__main__':main()
