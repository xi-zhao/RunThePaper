"""Discriminating p-scan control: keep each curve's preparation time fixed at its p=20 value.
This is a declared alternative to retuning tau=1/sqrt(N) at every p; no free fitted constant.
Predicts unchanged p20 main-panel points and systematic high-p changes before source comparison.
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
rows=[];arrays={};g=16385;trials=24000;x=np.linspace(0,np.pi,g);started=time.monotonic()
for NT,ps in groups.items():
 tau=np.sqrt(20/NT)
 for p in ps:
  N=NT//p;off=np.sqrt((N-np.arange(N))*(np.arange(N)+1))/2;m=np.arange(N+1)-N/2
  ev,V=eigh(1j*(np.diag(off,1)-np.diag(off,-1)))
  psi=np.exp(.5*(gammaln(N+1)-gammaln(np.arange(N+1)+1)-gammaln(N-np.arange(N+1)+1)-N*np.log(2))-1j*tau*m*m)
  P=abs(V@(np.exp(-1j*ev[:,None]*x)*(V.conj().T@psi)[:,None]))**2;q=P[:,g//2].copy();q/=q.sum();lp=np.log(np.maximum(P,1e-300));assert np.max(abs(P.sum(axis=0)-1))<2e-12
  counts=np.random.default_rng(2026102290+NT+p).multinomial(p,q,trials);radii=[]
  for batch in np.array_split(counts,600):
   z=batch@lp;z-=z.max(axis=1)[:,None];C=cumulative_trapezoid(np.exp(z),x,initial=0,axis=1);C/=C[:,-1,None]
   for logpost,cdf in zip(z,C):
    k=int(np.argmax(logpost));center=x[k];dd=np.arange(max(k,g-1-k)+1)*(x[1]-x[0]);mass=np.interp(np.minimum(np.pi,center+dd),x,cdf)-np.interp(np.maximum(0,center-dd),x,cdf)
    radii.append(np.interp(.68,mass,dd))
  a=NT*np.array(radii);arrays[f'NT{NT}_p{p}']=a;FQ=N/2*((N+1)-(N-1)*np.cos(2*tau)**(N-2))
  r=dict(NT=NT,N=N,p=p,tau=tau,twist_c=tau*np.sqrt(N),trials=trials,mean=float(a.mean()),SE=float(a.std(ddof=1)/np.sqrt(trials)),median=float(np.median(a)),RMS=float(np.sqrt(np.mean(a*a))),FQ=float(FQ));rows.append(r);print(json.dumps(r),flush=True)
np.savez_compressed('calculation/alignment-v3-20261022/fixed_twist_inset.npz',**arrays)
Path('calculation/alignment-v3-20261022/fixed_twist_inset.json').write_text(json.dumps(dict(rows=rows,grid=g,seconds=time.monotonic()-started,interpretation='Declared preparation-time variant: tau=sqrt(20/NT) is fixed for each inset curve, rather than retuned when p changesN=NT/p. No source figure values used in generation. At p20 the source preparation condition is recovered exactly.'),indent=2))
