"""Independent randomized upper bounds for the source's Table III minima.

Only source-defined code factors/maps are used. The C++ kernel is a random
information-set basis search; it is not claimed to reproduce the author's
unknown implementation or establish exact distances. Each candidate is checked
again with NumPy GF(2) operations before it is retained.
"""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from generate_algebra import construct, logical_basis, rank
from generate_gadgets_geometry import GADGETS, boundary, exterior, parse


def kernel_search(h, labels, costs, trials, seed, executable, scratch):
    m,n=h.shape
    matrix=scratch/'matrix.txt'; result=scratch/'search.json'
    with matrix.open('w') as f:
        f.write(f'{m} {n}\n')
        for j in range(n):
            words=[sum(int(h[i,j]) << (i-a) for i in range(a,min(a+64,m)))
                   for a in range(0,m,64)]
            label=sum(int(labels[i,j])<<i for i in range(len(labels)))
            f.write(' '.join(map(str,words+[label,int(costs[j])]))+'\n')
    subprocess.run([str(executable),str(matrix),str(result),str(trials),str(seed)],check=True)
    out=json.loads(result.read_text())
    v=np.zeros(n,dtype=np.uint8);v[out['support']]=1
    out['syndrome_residual']=int(np.count_nonzero(h@v%2))
    out['logical_bits']=(labels@v%2).tolist()
    out['recomputed_cost']=int(costs@v)
    if out['best_cost']>=0:
        assert out['syndrome_residual']==0 and any(out['logical_bits'])
        assert out['best_cost']==out['recomputed_cost']
    return out


def gadget_problem(index,model):
    n,replaced,entries,depth,_=GADGETS[index]
    g=model['group'];ng=math.prod(g)
    f=[set(map(tuple,p)) for p in model['polynomials']]
    fp=[parse(replaced[c],g) if c in replaced else a for c,a in zip('abcd',f)]
    a=[[{(0,)*len(g)} if i==j else set() for j in range(4)] for i in range(4)]
    for ij,s in entries.items():a['abcd'.index(ij[0])]['abcd'.index(ij[1])]=parse(s,g)
    F=exterior(a,2,g)
    hx,hz=boundary(f,3,g).T,boundary(f,2,g)
    ax,az=boundary(fp,3,g).T,boundary(fp,2,g)
    alz=logical_basis(ax,az); W=alz@F%2
    tx,tz=construct(model)[4:]; tl=logical_basis(tz,tx)
    embedded=np.zeros((3,n),np.uint8)
    for j,sector in enumerate([3,1,0]):embedded[:,sector*ng:(sector+1)*ng]=tl[:,j*ng:(j+1)*ng]
    # Select an explicit measured compute observable. For odd groups prefer a
    # source full-sector readout; for even groups the physical named basis is
    # not supplied, so choose a deterministic quotient representative.
    sector_candidates=[]
    for sector in range(6):
        z=np.zeros(n,np.uint8);z[sector*ng:(sector+1)*ng]=1
        if not np.any(ax@z%2) and np.any(z@F@embedded.T%2):sector_candidates.append(z)
    candidates=sector_candidates or [z for z in alz if np.any(z@F@embedded.T%2)]
    assert candidates
    zp=candidates[0]
    surviving_x=logical_basis(np.vstack([hz,W]),hx)
    Hx=az@np.hstack([F,np.eye(n,dtype=np.uint8)])%2
    Lx=(zp@np.hstack([F,np.eye(n,dtype=np.uint8)])%2)[None,:]
    Hz=np.block([[ax,ax,np.zeros_like(ax)],
                 [hx@F.T%2,np.zeros_like(hx),hx]])
    Lz=np.hstack([surviving_x@F.T%2,np.zeros_like(surviving_x),surviving_x])
    info=dict(row=index+1,n=n,depth=depth,ancilla_k=n-rank(ax)-rank(az),
              measured_readout_support=np.flatnonzero(zp).tolist(),
              compute_coefficients=(zp@F@embedded.T%2).tolist(),
              physical_basis='full_sector' if sector_candidates else 'canonical_GF2_quotient',
              unmeasured_logical_dimension=len(surviving_x))
    return info,(Hx,Lx,np.r_[np.full(n,2),np.ones(n)]),(Hz,Lz,np.ones(3*n))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True)
    args=parser.parse_args();cfg=json.loads(Path(args.config).read_text())
    models={m['quad'][0]:m for m in json.loads(Path('config/models.json').read_text())['pairs']}
    start=time.monotonic();outdir=Path(cfg['output_dir']);outdir.mkdir(parents=True,exist_ok=True)
    source=Path('scripts/isd_kernel_v1.cpp').resolve()
    rows=[]
    with tempfile.TemporaryDirectory(prefix='gadget-isd-') as temp:
        scratch=Path(temp);executable=scratch/'kernel'
        compiler=subprocess.check_output(['/usr/bin/clang++','--version'],text=True)
        subprocess.run(['/usr/bin/clang++','-std=c++17','-O3',str(source),'-o',str(executable)],check=True)
        for row in cfg['rows']:
            index=row-1;info,x,z=gadget_problem(index,models[GADGETS[index][0]])
            for tag,problem in [('dX',x),('dZ',z)]:
                info[tag]=kernel_search(*problem,cfg['trials'][tag],cfg['seed']+100*row+(tag=='dZ'),executable,scratch)
                print(json.dumps({'row':row,'kind':tag,**{k:info[tag][k] for k in ['best_cost','seconds','syndrome_residual']}}),flush=True)
            rows.append(info)
            payload=dict(config=cfg,rows=rows,elapsed_seconds=time.monotonic()-start,
                         compiler=compiler,cpp_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         interpretation='Certified candidate upper bounds for the displayed variational problems; not exact minima or a full intermediate-fault lower bound. Even-group physical logical basis is explicitly declared.')
            (outdir/'results.json').write_text(json.dumps(payload,indent=2)+'\n')
    assert len(rows)==len(cfg['rows'])

if __name__=='__main__':main()
