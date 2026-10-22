"""100 independent ensembles at the original L500,100-disorder-sample conditions.
Preserves full curve fluctuation patterns; no original curve or prior output is read.
Raw and peak-unwrapped width definitions remain explicit competing observables.
"""
from pathlib import Path
import json,time
import numpy as np
from scipy.linalg import eigh
from threadpoolctl import threadpool_limits
threadpool_limits(1)
L=500;ix=np.arange(L);energy=np.arange(-1.8,1.80001,.04);rows=[];started=time.monotonic()
for block in range(100):
 rng=np.random.default_rng(2026102230+block);sums=np.zeros((91,2));counts=np.zeros(91,int)
 for sample in range(100):
  v=rng.uniform(-1,1,L);H=np.diag(v);H[ix,(ix+1)%L]=-.5;H[(ix+1)%L,ix]=-.5;e,U=eigh(H,check_finite=False,driver='evr');prob=U*U;peak=np.argmax(prob,axis=0)
  d=(ix[:,None]-peak[None,:]+L//2)%L-L//2;var=(prob*d*d).sum(axis=0)-(prob*d).sum(axis=0)**2;raw=(prob*ix[:,None]**2).sum(axis=0)-(prob*ix[:,None]).sum(axis=0)**2
  values=np.c_[1/np.sqrt(2*raw),1/np.sqrt(2*var)]
  for j,E in enumerate(energy):
   mask=abs(e-E)<.02;sums[j]+=values[mask].sum(axis=0);counts[j]+=mask.sum()
 means=np.divide(sums,counts[:,None],where=counts[:,None]>0,out=np.full_like(sums,np.nan));rows.append(dict(seed=2026102230+block,counts=counts.tolist(),raw_width=means[:,0].tolist(),unwrapped_width=means[:,1].tolist()))
 if block%10==0:print('finished100-sample ensembles',block+1,flush=True)
Path('calculation/alignment-v3-20261022/ensemble_predictive.json').write_text(json.dumps(dict(rows=rows,energy=energy.tolist(),samples_per_ensemble=100,L=L,seconds=time.monotonic()-started,limits='Whole-curve fluctuation distribution under declared estimators. Seeds are exhaustive fixed independent blocks, not selected by original agreement. Comparing ranks after observing the source is exploratory, not a preregistered hypothesis test or a calibrated reproduction score.'),indent=2))
