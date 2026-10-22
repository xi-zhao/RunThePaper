"""Exact expected products expose normalization/averaging noncommutation.
These are explicitly alternative statistics, not automatically the paper estimator.
"""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigh
from scipy.special import gammaln
from scipy.integrate import cumulative_trapezoid
from threadpoolctl import threadpool_limits
threadpool_limits(1)
x=np.linspace(0,np.pi,16385);groups={200:[10,20,25,40,50],400:[8,10,16,20,25,40,50],800:[10,16,20,25,32]};rows=[]
for NT,ps in groups.items():
 for p in ps:
  N=NT//p;m=np.arange(N+1)-N/2;off=np.sqrt((N-np.arange(N))*(np.arange(N)+1))/2;ev,V=eigh(1j*(np.diag(off,1)-np.diag(off,-1)))
  psi=np.exp(.5*(gammaln(N+1)-gammaln(np.arange(N+1)+1)-gammaln(N-np.arange(N+1)+1)-N*np.log(2))-1j*m*m/np.sqrt(N))
  P=abs(V@(np.exp(-1j*ev[:,None]*x)*(V.conj().T@psi)[:,None]))**2;q=P[:,len(x)//2].copy();q/=q.sum();Z=np.trapezoid(P,x,axis=1)/np.pi
  kernels={'expected_likelihood':q@P,'expected_product_single_measurement_posteriors':(q/Z)@P,'expected_log_likelihood':np.exp(q@np.log(np.maximum(P,1e-300)))}
  results={}
  for key,K in kernels.items():
   log=p*np.log(np.maximum(K,1e-300));log-=log.max();C=cumulative_trapezoid(np.exp(log),x,initial=0);C/=C[-1];k=int(np.argmax(log));center=x[k];d=np.arange(max(k,len(x)-1-k)+1)*(x[1]-x[0]);mass=np.interp(np.minimum(np.pi,center+d),x,C)-np.interp(np.maximum(0,center-d),x,C)
   results[key]=dict(coefficient=float(NT*np.interp(.68,mass,d)),MAP=float(center))
  rows.append(dict(NT=NT,p=p,N=N,results=results))
Path('calculation/alignment-v3-20261022/averaging_order.json').write_text(json.dumps(dict(rows=rows,derivation='E_data[product_i P(mu_i|phi)] = (sum_mu q_mu P(mu|phi))^p. Normalizing each p-record posterior before averaging is a different operation. Product of individually normalized one-measurement posteriors gives another kernel with Z_mu. Expected log likelihood is a further, distinct Asimov statistic. None is silently equated with mean68% width.'),indent=2))
