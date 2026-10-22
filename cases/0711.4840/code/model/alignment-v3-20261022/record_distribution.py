"""Posterior-width distributions at the exact original inset resource pairs.
Distinguishes a single posterior width from an average over repeated experiments.
No reference values or previously generated answers are consumed.
"""
from pathlib import Path
import json,time
import numpy as np
from scipy.linalg import eigh
from scipy.special import gammaln
from scipy.integrate import cumulative_trapezoid
from threadpoolctl import threadpool_limits
threadpool_limits(1)
groups={200:[10,20,25,40,50],400:[8,10,16,20,25,40,50],800:[10,16,20,25,32]}
trials=16000;grid=16385;x=np.linspace(0,np.pi,grid);rows=[];arrays={};started=time.monotonic()
for NT,ps in groups.items():
 for p in ps:
  assert NT%p==0;n=NT//p;m=np.arange(n+1)-n/2;off=np.sqrt((n-np.arange(n))*(np.arange(n)+1))/2
  ev,V=eigh(1j*(np.diag(off,1)-np.diag(off,-1)))
  psi=np.exp(.5*(gammaln(n+1)-gammaln(np.arange(n+1)+1)-gammaln(n-np.arange(n+1)+1)-n*np.log(2))-1j*m*m/np.sqrt(n))
  P=abs(V@(np.exp(-1j*ev[:,None]*x)*(V.conj().T@psi)[:,None]))**2
  assert np.max(abs(P.sum(axis=0)-1))<2e-12
  q=P[:,grid//2].copy();q/=q.sum();lp=np.log(np.maximum(P,1e-300))
  counts=np.random.default_rng(2026102270+NT+p).multinomial(p,q,trials);radii=[]
  for batch in np.array_split(counts,400):
   z=batch@lp;z-=z.max(axis=1)[:,None];pdf=np.exp(z);cdf=cumulative_trapezoid(pdf,x,axis=1,initial=0);cdf/=cdf[:,-1,None]
   for density,C in zip(pdf,cdf):
    k=int(np.argmax(density));center=x[k];dd=np.arange(max(k,grid-1-k)+1)*(x[1]-x[0])
    mass=np.interp(np.minimum(np.pi,center+dd),x,C)-np.interp(np.maximum(0,center-dd),x,C)
    radii.append(np.interp(.68,mass,dd))
  a=NT*np.array(radii);arrays[f'NT{NT}_p{p}']=a
  rows.append(dict(NT=NT,N=n,p=p,trials=trials,mean_coefficient=float(a.mean()),SE=float(a.std(ddof=1)/np.sqrt(trials)),median=float(np.median(a)),RMS=float(np.sqrt(np.mean(a*a))),quantiles=np.quantile(a,[.005,.025,.16,.5,.84,.975,.995]).tolist()))
  print(json.dumps(rows[-1]),flush=True)
np.savez_compressed('calculation/alignment-v3-20261022/record_distribution.npz',**arrays)
Path('calculation/alignment-v3-20261022/record_distribution.json').write_text(json.dumps(dict(rows=rows,grid=grid,seconds=time.monotonic()-started,conditions='Source tau=1/sqrt(N), theta=pi/2, flat prior[0,pi], MAP-centered68% halfwidth. Width of a posterior conditioned on one p-outcome record is not a repeated-record mean or RMS. Generation does not choose a summary to match the source.'),indent=2))
