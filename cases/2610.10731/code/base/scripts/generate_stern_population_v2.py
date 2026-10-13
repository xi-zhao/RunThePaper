"""Parallel bounded search with streamed compressed per-candidate witnesses.

Identical mathematical search to v1. A previous serial attempt was cancelled
because rewriting all rows would exceed capture/file limits; it is not counted
as extra candidate coverage. This run starts from the fixed input population.
"""
import argparse
import concurrent.futures
import gzip
import hashlib
import itertools
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from generate_stern_search_v1 import search, controls, logical_basis
from generate_algebra import construct, rank


def candidate_job(job):
    candidate,trials,ell,seed,dmin,executable=job
    hx,hz,*_=construct(candidate['model']);n=hx.shape[1];ng=n//6
    logs=logical_basis(hz,hx);K=n-rank(hx)-rank(hz);assert len(logs)==K
    with tempfile.TemporaryDirectory(prefix='stern-candidate-') as tmp:
        scratch=Path(tmp)
        result=search(hx,logs,trials,seed+candidate['sample'],ell,dmin,executable,scratch)
        block_results=[];best=result['best_cost']
        for width in (2,3):
            if 0<=best<dmin:break
            for subset in itertools.combinations(range(6),width):
                inds=np.array([b*ng+i for b in subset for i in range(ng)])
                r=search(hx[:,inds],logs[:,inds],30,seed+candidate['sample']*100+len(block_results),8,dmin,executable,scratch)
                r['blocks']=subset;r['global_support']=inds[r['support']].tolist();block_results.append(r)
                if r['best_cost']>=0:best=min(best,r['best_cost']) if best>=0 else r['best_cost']
                if 0<=best<dmin:break
    return dict(candidate,K=K,stern=result,multi_block=block_results,distance_upper_bound=best,rejected=0<=best<dmin)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True)
    config_path=Path(ap.parse_args().config);cfg=json.loads(config_path.read_text())
    out=Path('outputs/stern-population-v3');out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();summary=[]
    with tempfile.TemporaryDirectory(prefix='stern-population-') as tmp:
        scratch=Path(tmp);exe=scratch/'stern'
        subprocess.run(['/usr/bin/clang++','-O3','-std=c++17','scripts/stern_kernel_v1.cpp','-o',str(exe)],check=True)
        checks=controls(exe,scratch)
        jobs=[(c,cfg['trials'],cfg['ell'],cfg['seed'],cfg['d_min'],str(exe)) for c in cfg['candidates']]
        with gzip.open(out/'witnesses.jsonl.gz','wt',encoding='utf-8') as stream:
            with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
                for row in pool.map(candidate_job,jobs,chunksize=1):
                    stream.write(json.dumps(row,separators=(',',':'))+'\n')
                    summary.append({k:row[k] for k in ('sample','K','distance_upper_bound','rejected')})
                    if len(summary)%100==0:
                        stream.flush();print(json.dumps(dict(completed=len(summary),requested=len(jobs),rejected=sum(r['rejected'] for r in summary),seconds=time.monotonic()-started)),flush=True)
                        (out/'progress.json').write_text(json.dumps(dict(completed=len(summary),requested=len(jobs),seconds=time.monotonic()-started)))
    assert len(summary)==len(cfg['candidates']) and len({r['sample'] for r in summary})==len(summary)
    result=dict(format='qldpc.stern-population.v3',config_path=str(config_path),config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
        population_samples=cfg['population_samples'],K_min=cfg['K_min'],d_min=cfg['d_min'],
        requested=len(cfg['candidates']),completed=len(summary),rejected=sum(r['rejected'] for r in summary),
        not_rejected=sum(not r['rejected'] for r in summary),trials=cfg['trials'],ell=cfg['ell'],workers=4,
        controls=checks,summary=summary,seconds=time.monotonic()-started,
        witnesses_sha256=hashlib.sha256((out/'witnesses.jsonl.gz').read_bytes()).hexdigest(),
        limitations=['Every K-surviving candidate in the declared 100000 population is processed; no author sampling-law equivalence is established.',
            'Stern and restricted-block outputs are upper-bound witnesses. Not rejected never proves distance at least d_min.',
            'This bounded implementation uses p=1,2 and a basis fallback; no original author Stern timing or full general algorithm is claimed.',
            'No Kunneth-orbit ceiling and no new exhaustive-distance claim.',
            'Earlier overlapping serial/pilot attempts are not additional independent candidate samples.'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('completed','rejected','not_rejected','seconds')}),flush=True)


if __name__=='__main__':main()
