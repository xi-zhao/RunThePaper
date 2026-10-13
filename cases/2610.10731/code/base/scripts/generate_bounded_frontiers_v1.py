"""Explicit bounded random search; Prange-style upper bounds, not author data.

All candidate factors and witness supports are retained. A fixed evaluation cap
per window is declared before execution. No author point/threshold is fitted.
"""
import collections
import itertools
import json
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from generate_algebra import construct, rank
from generate_search_funnel_v1 import quotient_basis
from complete_gadget_distances_v1 import kernel_search


def main():
    cfg=json.loads(Path('config/bounded-frontiers-v1.json').read_text())
    rng=np.random.default_rng(cfg['seed']);out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    rows=[];windows=[];started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='qldpc-frontiers-') as tmp:
        scratch=Path(tmp);exe=scratch/'kernel'
        subprocess.run(['/usr/bin/clang++','-O3','-std=c++17','scripts/isd_kernel_v1.cpp','-o',str(exe)],check=True)
        for group in cfg['groups']:
            coords=list(itertools.product(*[range(g) for g in group]));N=6*len(coords)
            threshold=max(1,6*(int(np.ceil(N/40))//6))
            for weights in cfg['weights']:
                check_weight=sum(weights)-min(weights);hist=collections.Counter();chosen=0;models=[]
                for sample in range(cfg['samples_per_window']):
                    polys=[[coords[i] for i in rng.choice(len(coords),w,replace=False)] for w in weights]
                    model=dict(group=group,polynomials=polys);hx,hz,*_=construct(model)
                    K=N-rank(hx)-rank(hz);hist[K]+=1
                    assert not np.any(hx@hz.T%2)
                    models.append(dict(model=model,K=K))
                    if K<threshold or chosen>=cfg['distance_candidates_per_window']:continue
                    chosen+=1;logs=quotient_basis(hz,hx);assert len(logs)==K
                    result=kernel_search(hx,logs[:64],np.ones(N),cfg['isd_trials'],
                        cfg['seed']+len(rows),exe,scratch)
                    assert result['best_cost']>0
                    rows.append(dict(group=group,weights=weights,check_weight=check_weight,N=N,K=K,rate=K/N,
                        sample=sample,model=model,distance_upper_bound=result['best_cost'],witness=result))
                windows.append(dict(group=group,weights=weights,check_weight=check_weight,
                    samples=cfg['samples_per_window'],K_min=threshold,K_histogram=dict(hist),
                    selected_for_distance=chosen,candidates=models))
                save(cfg,rows,windows,started,out)
                print(json.dumps({k:v for k,v in windows[-1].items() if k!='candidates'}),flush=True)
    render(json.loads((out/'results.json').read_text()),out/'frontiers.png')


def save(cfg,rows,windows,started,out):
    front={}
    for w in range(6,11):
        inds=[i for i,r in enumerate(rows) if r['check_weight']==w]
        front[str(w)]=[i for i in inds if not any(
            rows[j]['rate']>=rows[i]['rate'] and rows[j]['distance_upper_bound']>=rows[i]['distance_upper_bound']
            and (rows[j]['rate']>rows[i]['rate'] or rows[j]['distance_upper_bound']>rows[i]['distance_upper_bound'])
            for j in inds)]
    result=dict(config=cfg,windows=windows,rows=rows,empirical_frontier_indices=front,elapsed_seconds=time.monotonic()-started,
        limitations=['Bounded groups, one factor-weight pattern per maximum check weight, and fixed first-candidate cap; not the full author search.',
            'Distance witnesses are upper bounds from random systematic kernel bases, not Stern ISD or proven distances.',
            'An empirical frontier may move with additional candidates and decrease with additional distance trials.',
            'All nontrivial logical dimensions are tested by full GF(2) rank; no unrestricted local-ring valuation formula is used.'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')


def render(data,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,5,figsize=(16,3.5),layout='constrained')
    for ax,w in zip(axes,range(6,11)):
        subset=[r for r in data['rows'] if r['check_weight']==w]
        ax.scatter([r['distance_upper_bound'] for r in subset],[r['rate'] for r in subset],s=10,alpha=.35)
        frontier=sorted([data['rows'][i] for i in data['empirical_frontier_indices'][str(w)]],key=lambda r:r['distance_upper_bound'])
        ax.plot([r['distance_upper_bound'] for r in frontier],[r['rate'] for r in frontier],'o--',color='darkorange',ms=3)
        ax.set(title=f'max check weight {w}',xlabel='witness weight (upper bound)',ylabel='K/N');ax.grid(alpha=.2)
    fig.suptitle('Declared bounded search: empirical frontiers, not the source search dataset')
    fig.savefig(path,dpi=140);plt.close(fig)


if __name__=='__main__':main()
