"""Paired continuum/discrete exponential-width calibrations and averaging conventions.
The exact exponential inversion is a declared envelope assumption, not an author formula.
Reuses prior random seeds deliberately for paired comparisons, but reads no old outputs.
"""
from pathlib import Path
import json,time
import numpy as np
from scipy.linalg import eigh
from threadpoolctl import threadpool_limits
threadpool_limits(1)
L=500;ix=np.arange(L);energy=np.arange(-1.8,1.80001,.04);rows=[];started=time.monotonic()
for block in range(10):
 rng=np.random.default_rng(2026102230+block);sums=np.zeros((91,4));counts=np.zeros(91,int);per_sample=[]
 for sample in range(100):
  v=rng.uniform(-1,1,L);H=np.diag(v);H[ix,(ix+1)%L]=-.5;H[(ix+1)%L,ix]=-.5;e,U=eigh(H,check_finite=False,driver='evr');prob=U*U;peak=np.argmax(prob,axis=0)
  d=(ix[:,None]-peak[None,:]+L//2)%L-L//2
  variance=(prob*d*d).sum(axis=0)-(prob*d).sum(axis=0)**2
  raw=(prob*ix[:,None]**2).sum(axis=0)-(prob*ix[:,None]).sum(axis=0)**2
  unwrapped=1/np.sqrt(2*variance);cut=1/np.sqrt(2*raw)
  quantities=np.c_[unwrapped,np.arcsinh(unwrapped),cut,np.arcsinh(cut)];samplemeans=np.full((91,4),np.nan)
  for j,E in enumerate(energy):
   keep=abs(e-E)<.02;n=int(keep.sum())
   if n:sums[j]+=quantities[keep].sum(axis=0);counts[j]+=n;samplemeans[j]=quantities[keep].mean(axis=0)
  per_sample.append(samplemeans)
 means=np.divide(sums,counts[:,None],where=counts[:,None]>0,out=np.full_like(sums,np.nan))
 rows.append(dict(block=block,seed=2026102230+block,counts=counts.tolist(),pooled_state_means=means.tolist(),equal_disorder_means=np.nanmean(per_sample,axis=0).tolist()))
 print('paired ensemble',block,flush=True)
Path('calculation/alignment-v3-20261022/lattice_width.json').write_text(json.dumps(dict(rows=rows,energy=energy.tolist(),columns=['unwrapped_continuum','unwrapped_discrete','raw_continuum','raw_discrete'],L=L,samples_per_block=100,seconds=time.monotonic()-started,derivation='p_j proportional exp(-2*kappa*abs(j)) gives variance1/(2*sinh(kappa)^2). Thus asinh(1/sqrt(2Var)) is exact for that envelope; real random eigenstates need not have that shape. Pooled-state versus equal-disorder aggregation are both explicit; no family is substituted for source by visual fit.'),indent=2))
