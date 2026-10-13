"""Standalone calculations and frozen-array checks, without private tooling."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
sys.dont_write_bytecode=True
import numpy as np
CASE=Path(__file__).resolve().parents[2]
CODE=CASE/'code'

def read(path):return json.loads(path.read_text())

def verify():
    arrays=np.load(CASE/'outputs/data/h3/samples.npz',allow_pickle=False)
    result=read(CASE/'outputs/data/h3/results.json');total=0;worst=0.;mean_error=0.
    for row in result['summaries']:
        cohort=row['cohort'];prefix=cohort['id']+'__'
        norm=arrays[prefix+'entropy_normalized'];raw=arrays[prefix+'entropy_raw']
        w=arrays[prefix+'terminal_survival_norm']
        assert len(w)==cohort['samples'] and np.all(w>0) and np.all(w<=1+1e-7)
        assert np.isfinite(norm).all() and np.isfinite(raw).all()
        assert np.min(norm)>-1e-10
        delta=float(np.max(np.abs(raw-(w[:,None]*norm-w[:,None]*np.log(w[:,None])))))
        worst=max(worst,delta);total+=len(w);assert delta<1e-12
        for key in ['entropy_normalized','entropy_raw']:
            err=float(np.max(np.abs(arrays[prefix+key].mean(0)-row['mean'][key])))
            mean_error=max(mean_error,err);assert err<1e-12
    assert total==1280
    return dict(trajectory_evaluations=total,maximum_identity_error=worst,
                maximum_mean_reanalysis_error=mean_error,
                scope='Reanalysis of frozen v2 arrays; not large-ensemble or infinite-cutoff acceptance.')

def quick():
    sys.path.insert(0,str(CODE/'h3'))
    import generate as trajectories
    sys.path.insert(0,str(CODE/'h3/solvers'))
    from generate_statics import basis,matrix
    from scipy.linalg import null_space
    rows=[]
    for index,stats in enumerate(['fermion','boson']):
        states=basis(4,2,stats)
        O=matrix(states,states,[(1,[(j+1,-1),(j,1)]) for j in range(3)],stats).toarray()
        U=null_space(O);res=float(np.linalg.norm(O@U));assert res<1e-12 and U.shape[1]>0
        cohort=dict(id=stats+'_control',statistics=stats,L=4,N=2,photon_cutoff=3,
            delta=5.,gamma=10.,time=.25,seed_group=index,
            initial=dict(id='Fock',occupations=[0,0,1,1] if stats=='fermion' else [0,0,0,2]))
        values,_=trajectories.job((dict(seed=20261013,rtol=1e-9,atol=1e-11),cohort,[0,1]))
        w=values['terminal_survival_norm'][:,None]
        err=float(np.max(np.abs(values['entropy_raw']-(w*values['entropy_normalized']-w*np.log(w)))))
        assert err<1e-12
        rows.append(dict(statistics=stats,matter_dimension=len(states),null_dimension=U.shape[1],
             null_residual=res,actual_trajectories=2,identity_error=err))
    return dict(controls=rows,scope='Small-system mathematical and trajectory smoke test, not original-size convergence.')

def render(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    result=read(CASE/'outputs/data/h3/results.json')
    rows=[r for r in result['summaries'] if r['cohort']['group']=='paper']
    fig,axes=plt.subplots(3,4,figsize=(13,8.3),layout='constrained')
    for ax,row in zip(axes.flat,rows):
        c=row['cohort'];x=np.arange(len(row['mean']['entropy_normalized']))
        for key,label,color in [('entropy_normalized','Physical entropy','#265ea9'),('entropy_raw','Raw diagnostic','#c36b20')]:
            y=np.asarray(row['mean'][key]);se=np.asarray(row['SE'][key])
            ax.plot(x,y,color=color,label=label);ax.fill_between(x,y-2*se,y+2*se,color=color,alpha=.16)
        ax.set(title=f"{c['statistics']} {c['initial']['id']} (n={c['samples']})",
               xlabel='Cut index (0 = cavity)',ylabel='Entropy / diagnostic (nats)')
        ax.grid(alpha=.15);ax.tick_params(labelsize=8)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle('Independent H3 trajectories: physical entropy and raw diagnostic; bands = 2 empirical SE',fontsize=12)
    target=out/'h3-generated.png';fig.savefig(target,dpi=150);plt.close(fig)
    return dict(figure=target.name,source='outputs/data/h3/results.json')

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['quick','verify','render','statics','h3'],default='quick');a=p.parse_args()
    out=Path(tempfile.mkdtemp(prefix='liouvillian-reproduction-'));start=time.monotonic()
    if a.mode in ['quick','verify']:result=quick() if a.mode=='quick' else verify()
    elif a.mode=='render':result=render(out)
    else:
        work=out/'calculation';shutil.copytree(CODE/('h3' if a.mode=='h3' else 'base'),work)
        entry='generate.py' if a.mode=='h3' else 'scripts/generate_statics.py'
        subprocess.run([sys.executable,entry],cwd=work,check=True)
        result=dict(mode=a.mode,results_directory='calculation/outputs',whole_paper_complete=False)
    result['elapsed_seconds']=time.monotonic()-start
    (out/'run-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(output_directory=str(out),result=result),indent=2))

if __name__=='__main__':main()
