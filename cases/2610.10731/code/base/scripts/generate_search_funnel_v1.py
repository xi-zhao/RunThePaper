"""Declared C4 x C19 random code ensemble, exact K and explicit distance witnesses.

No author sample/curve values are read. Distances are candidate upper bounds.
The fast CRT formula is used only in this principal local-ring case and checked
against full GF(2) matrices. Local witnesses are tested against the full
stabilizer image, not the ill-defined literal quotient printed in the source.
"""
import argparse
import collections
import itertools
import json
import math
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from generate_algebra import construct, nullspace, rank, bits, echelon
from complete_gadget_distances_v1 import kernel_search


def crt_dimension(polynomials):
    # y^19+1=(y+1)(1+y+...+y^18); ord_19(2)=18.
    # x=1+t, t^4=0. Coefficients are binary polynomial bit strings.
    vals=[]
    for terms in polynomials:
        cs=[]
        for j in range(4):
            c=0
            for x,y in terms:
                if (x & j)==j:c ^= 1<<y
            cs.append(c)
        one=next((j for j,c in enumerate(cs) if c.bit_count()%2),4)
        ext=next((j for j,c in enumerate(cs) if (c ^ (((1<<19)-1) if c&(1<<18) else 0))),4)
        vals.append((one,ext))
    return 6*(min(v[0] for v in vals)+18*min(v[1] for v in vals)),vals


def reduce_bits(v,piv):
    for k in sorted(piv,reverse=True):
        if (v>>k)&1:v ^= piv[k]
    return v


def quotient_basis(check,stabilizers):
    piv=echelon(bits(v) for v in stabilizers);out=[]
    for row in nullspace(check):
        v=reduce_bits(bits(row),piv)
        if v:piv[v.bit_length()-1]=v;out.append(row)
    return np.asarray(out,dtype=np.uint8).reshape(-1,check.shape[1])


def block_witness(hx,hz,rng,trials):
    ng=hx.shape[1]//6;piv=echelon(bits(row) for row in hz)
    best=None
    for block in range(6):
        ns=nullspace(hx[:,block*ng:(block+1)*ng]);d=len(ns)
        candidates=[v for v in ns]
        candidates += [ns[i]^ns[j] for i in range(d) for j in range(i)]
        if d:
            combos=rng.integers(0,2,size=(trials,d),dtype=np.uint8)@ns%2
            candidates.extend(combos)
        for v in candidates:
            weight=int(v.sum())
            if not weight or (best and weight>=best['weight']):continue
            support=(np.flatnonzero(v)+block*ng).tolist()
            if not reduce_bits(sum(1<<int(i) for i in support),piv):continue
            full=np.zeros(hx.shape[1],np.uint8);full[support]=1
            assert not np.any(hx@full%2)
            best=dict(weight=weight,block=block,support=support,syndrome_residual=0,nontrivial_mod_full_stabilizers=True)
    return best


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text());rng=np.random.default_rng(cfg['seed'])
    out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    coords=list(itertools.product(range(4),range(19)));models=[];ks=[];t0=time.monotonic()
    for i in range(cfg['samples']):
        polys=[[coords[j] for j in rng.choice(76,w,replace=False)] for w in [2,2,4,4]]
        K,vals=crt_dimension(polys);models.append(dict(group=[4,19],polynomials=polys));ks.append(K)
    logical_seconds=time.monotonic()-t0
    np.savez_compressed(out/'ensemble.npz',factors=np.array([[j for p in m['polynomials'] for j in p] for m in models],dtype=np.int8),K=np.array(ks,dtype=np.int16))
    validations=[]
    chosen=list(range(cfg['rank_controls']))
    for k in sorted(set(ks)):
        chosen += [ks.index(k)]
    for i in sorted(set(chosen)):
        hx,hz,*_=construct(models[i]);actual=hx.shape[1]-rank(hx)-rank(hz)
        assert actual==ks[i] and not np.any(hx@hz.T%2)
        validations.append(dict(sample=i,K_CRT=ks[i],K_rank=actual))
    # Complete the declared staged search on a fixed prefix. The larger K-only
    # population is separately reported, never used as the downstream denominator.
    rows=[];kt=6*(math.ceil(456/40)//6);scan=cfg['pipeline_samples']
    tmpstart=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='qldpc-search-') as tmp:
        scratch=Path(tmp);executable=scratch/'kernel'
        subprocess.run(['/usr/bin/clang++','-O3','-std=c++17','scripts/isd_kernel_v1.cpp','-o',str(executable)],check=True)
        for i in range(scan):
            if ks[i]<kt:continue
            started=time.monotonic();model=models[i];hx,hz,*_=construct(model)
            witness=block_witness(hx,hz,rng,cfg['block_trials']);ceiling_seconds=time.monotonic()-started
            row=dict(sample=i,K=ks[i],model=model,block_witness=witness,ceiling_seconds=ceiling_seconds)
            if witness is None or witness['weight']>=cfg['d_min']:
                lx=quotient_basis(hz,hx)
                assert len(lx)==ks[i] and not np.any(hz@lx.T%2)
                row['isd']=kernel_search(hx,lx[:64],np.ones(456),cfg['isd_trials'],cfg['seed']+i,executable,scratch)
                distance=row['isd']['best_cost']
                if witness is not None:distance=min(distance,witness['weight']) if distance>=0 else witness['weight']
                row['distance_upper_bound']=distance
                row['passed_declared_rejection_tests']=distance>=cfg['d_min']
            else:
                row['distance_upper_bound']=witness['weight'];row['passed_declared_rejection_tests']=False
            rows.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ('model','isd','block_witness')}),flush=True)
            result=dict(config=cfg,N=456,K_min=kt,logical_histogram=dict(sorted(collections.Counter(ks).items())),
                K_survival={str(k):sum(v>=k for v in ks)/len(ks) for k in [6,12,18,24]},
                logical_count_seconds=logical_seconds,rank_controls=validations,
                pipeline=dict(samples=scan,K_pass=sum(v>=kt for v in ks[:scan]),
                    ceiling_pass=sum('isd' in r for r in rows),distance_pass=sum(r['passed_declared_rejection_tests'] for r in rows),
                    processed_K_survivors=len(rows),elapsed_seconds=time.monotonic()-tmpstart),rows=rows,
                limitations=['Uniform distinct terms per factor and explicit seeds; author sampling law and per-window distance threshold are unspecified.',
                    'Random systematic kernel-basis search is Prange-style, not author Stern timing or a distance lower bound.',
                    'Single-block random/exhaustive-basis witnesses are a bounded rejection test, not the exact minimum U.',
                    'A fixed group/weight window cannot establish the full five-panel author Pareto envelope.'])
            (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    assert len(rows)==sum(v>=kt for v in ks[:scan])

if __name__=='__main__':main()
