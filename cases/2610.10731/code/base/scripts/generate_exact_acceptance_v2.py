"""Exact Fourier-projector acceptance of the finite independent DEM (float64)."""
from pathlib import Path
import json,time,hashlib
import numpy as np
from simulate_sd6_factory_v2 import factory,dem_arrays
from structured_schedule import structured_tri

cfg=json.loads(Path('config/acceptance-curves-v2.json').read_text())
models=json.loads(Path('config/models.json').read_text())['pairs']
rows=[];out=Path('outputs/acceptance-exact-v2/results.json');out.parent.mkdir(parents=True,exist_ok=True)
for job in cfg['jobs']:
    if job['n4'] not in (54,72):continue
    started=time.monotonic();m=next(m for m in models if m['quad'][0]==job['n4'])
    c,d,meta=factory(m,job['p'],job['pccz'],tri_override=structured_tri(m,(0,2,1,3)))
    h,_,p=dem_arrays(d);sel=h[meta['post_start']:meta['npost']];q=len(sel)
    signatures=np.array([int.from_bytes(np.packbits(col,bitorder='little').tobytes(),'little') for col in sel.T],np.uint64)
    assert np.all((p>0)&(p<.5)) and q<=12
    coeff=np.log1p(-2*p);chars=np.arange(1<<q,dtype=np.uint64)
    parity=np.bitwise_count(chars[:,None]&signatures[None,:])%2
    alpha=float(np.exp(parity@coeff).mean())
    rows.append(dict(n4=job['n4'],p=job['p'],pccz=job['pccz'],acceptance=alpha,
        detector_rows=q,fourier_characters=len(chars),dem_mechanisms=len(p),
        dem_sha256=hashlib.sha256(str(d).encode()).hexdigest(),wall_seconds=time.monotonic()-started))
    print(json.dumps(rows[-1]),flush=True)
    out.write_text(json.dumps(dict(rows=rows,limits=[
        'Exact finite-model expectation formula evaluated with float64, not a certified interval-arithmetic result.',
        'Only teleportation detectors are postselected; source circuit identity remains unestablished.',
        'No author numerical arrays, graph readings or Monte Carlo outcomes are used as inputs.']),indent=2)+'\n')
