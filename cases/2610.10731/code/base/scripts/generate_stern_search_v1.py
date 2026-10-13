"""Stern meet-in-the-middle and bounded multi-block rejection witnesses.

Candidates are the owned prior fixed-prefix ensemble; no source answers enter.
The block tests use the full stabilizer quotient via logical X pairings.
"""
import argparse
import itertools
import json
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from generate_algebra import construct, logical_basis as rank_logical_basis, nullspace, rank, echelon, bits


def logical_basis(check,stabilizers):
    """Incremental exact GF(2) independence, same selected rows as rank tests."""
    piv=echelon(bits(row) for row in stabilizers);rows=[]
    for row in nullspace(check):
        value=bits(row)
        for p in sorted(piv,reverse=True):
            if (value>>p)&1:value^=piv[p]
        if value:
            piv[value.bit_length()-1]=value;rows.append(row)
    return np.asarray(rows,dtype=np.uint8).reshape(-1,check.shape[1])


def search(h, labels, trials, seed, ell, stop_below, exe, scratch):
    m,n=h.shape
    assert len(labels)<=64
    matrix=scratch/'matrix.txt'; result=scratch/'result.json'
    with matrix.open('w') as f:
        f.write(f'{m} {n}\n')
        for j in range(n):
            words=[sum(int(h[i,j])<<(i-a) for i in range(a,min(a+64,m))) for a in range(0,m,64)]
            label=sum(int(labels[i,j])<<i for i in range(len(labels)))
            f.write(' '.join(map(str,words+[label,1]))+'\n')
    subprocess.run([str(exe),str(matrix),str(result),str(trials),str(seed),str(ell),str(stop_below)],check=True)
    r=json.loads(result.read_text());v=np.zeros(n,np.uint8);v[r['support']]=1
    if r['best_cost']>=0:
        assert int(v.sum())==r['best_cost'] and not np.any(h@v%2) and np.any(labels@v%2)
    r['checked_support']=True
    return r


def controls(exe,scratch):
    rng=np.random.default_rng(26101391); rows=[]
    for n in (8,10,12,14):
        for repeat in range(3):
            hx=rng.integers(0,2,size=(n//2,n),dtype=np.uint8)
            cycles=nullspace(hx)
            hz=cycles[:max(0,len(cycles)-2)]
            logs=logical_basis(hz,hx)
            assert np.array_equal(logs,rank_logical_basis(hz,hx))
            candidates=np.array(list(itertools.product([0,1],repeat=n)),np.uint8)
            valid=(np.all(candidates@hx.T%2==0,axis=1)&np.any(candidates@logs.T%2,axis=1))
            exact=int(candidates[valid].sum(axis=1).min())
            r=search(hx,logs,300,261013+n*10+repeat,2,0,exe,scratch)
            assert r['best_cost']==exact
            rows.append(dict(n=n,repeat=repeat,exact_minimum=exact,stern=r))
    return rows


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True)
    cfg=json.loads(Path(ap.parse_args().config).read_text())
    out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();rows=[]
    with tempfile.TemporaryDirectory(prefix='stern-') as tmp:
        scratch=Path(tmp);exe=scratch/'stern'
        subprocess.run(['/usr/bin/clang++','-O3','-std=c++17','scripts/stern_kernel_v1.cpp','-o',str(exe)],check=True)
        checks=controls(exe,scratch)
        for candidate in cfg['candidates']:
            hx,hz,*_=construct(candidate['model']);n=hx.shape[1];ng=n//6
            logs=logical_basis(hz,hx);K=n-rank(hx)-rank(hz);assert len(logs)==K
            result=search(hx,logs,cfg['trials'],cfg['seed']+candidate['sample'],cfg['ell'],cfg['d_min'],exe,scratch)
            block_results=[];best=result['best_cost']
            # Bounded two/three-block tests are separate from the full Stern
            # trial count. Every local witness is checked after full embedding.
            for width in (2,3):
                if best<cfg['d_min']:break
                for subset in itertools.combinations(range(6),width):
                    inds=np.array([b*ng+i for b in subset for i in range(ng)])
                    r=search(hx[:,inds],logs[:,inds],30,cfg['seed']+candidate['sample']*100+len(block_results),8,cfg['d_min'],exe,scratch)
                    r['blocks']=subset;r['global_support']=inds[r['support']].tolist()
                    block_results.append(r)
                    if r['best_cost']>=0:best=min(best,r['best_cost']) if best>=0 else r['best_cost']
                    if best<cfg['d_min']:break
            row=dict(candidate,K=K,stern=result,multi_block=block_results,distance_upper_bound=best,
                     rejected=best>=0 and best<cfg['d_min'])
            rows.append(row)
            payload=dict(config=cfg,controls=checks,rows=rows,seconds=time.monotonic()-started,
                method='Random systematic kernel basis, random information split, p=1 and p=2 equal-part meet-in-the-middle collisions on ell parity coordinates, plus basis candidates.',
                limitations=['Witness upper bounds only; no absence-of-low-weight guarantee.',
                             'This completes the declared 20 candidates, not the 100000-candidate downstream search or author sampling law.',
                             'Bounded two/three-block searches stop on rejection; no Kunneth-orbit ceiling or exhaustive block minimum.',
                             'Timings describe this implementation/machine; no claim of reproducing original Stern runtime.'])
            (out/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
            print(json.dumps(dict(sample=candidate['sample'],K=K,weight=best,kind=result['best_kind'],trials=result['trials'],rejected=row['rejected'],seconds=payload['seconds'])),flush=True)


if __name__=='__main__':main()
