"""Test the effect of the source's unreported K, with direct noisy QPR circuits.
Diagnostic uses three preselected full-size circuits and a fixed seed; not a replacement histogram.
"""
import json,itertools,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
I=np.eye(2,dtype=complex);X=np.array([[0,1],[1,0]],complex);Y=np.array([[0,-1j],[1j,0]],complex);Z=np.diag([1.,-1.]).astype(complex)
gates=[I,(X+Z)/np.sqrt(2),np.diag([1,1j]),np.diag([1,np.exp(1j*np.pi/4)])]
pa=[I,X,Y,Z];n=6;d=64;B=1024;eps=.01;M=4000;rng=np.random.default_rng(91023)
def one(r,u,q):
 t=r.reshape([B]+[2]*12);t=np.tensordot(u,t,axes=(1,q+1));t=np.moveaxis(t,0,q+1)
 t=np.tensordot(u.conj(),t,axes=(1,n+q+1));t=np.moveaxis(t,0,n+q+1)
 return t.reshape(B,d,d)
def reset(r,qs):
 rest=[q for q in range(n) if q not in qs];order=[0]+[q+1 for q in qs+rest]+[n+q+1 for q in qs+rest]
 k=2**len(qs);dd=d//k;t=r.reshape([B]+[2]*12).transpose(order).reshape(B,k,dd,k,dd)
 tr=np.einsum('baras->brs',t);out=np.einsum('ac,brs->barcs',np.eye(k)/k,tr).reshape([B]+[2]*12)
 return out.transpose(np.argsort(order)).reshape(B,d,d)
def random_paulis(r,qs,ids):
 for iq,q in enumerate(reversed(qs)):
  v=(ids//4**iq)%4;mask=1<<(n-1-q);indices=np.arange(d)[None,:]^(((v==1)|(v==2))[:,None]*mask)
  phase=np.ones((B,d),complex);bits=(np.arange(d)&mask)>0
  phase[(v==3)|(v==2)]=np.where(bits,-1,1)
  phase[v==2]*=-1j # P[out,in] phase at output bit for Y: -i*(-1)^out
  r=r[np.arange(B)[:,None,None],indices[:,:,None],indices[:,None,:]]*phase[:,:,None]*phase.conj()[:,None,:]
 return r
f=json.loads(Path('results/fig2.json').read_text());gamma=f['gamma'];results=[];start=time.monotonic()
with threadpool_limits(limits=1):
 for ci in [0,137,499]:
  rho=np.ones((B,d,d),complex)/d;sign=np.ones(B)
  for typ,p,q in f['circuits'][ci]:
   qs=[p] if typ=='one' else [p,q]
   if typ=='one':rho=one(rho,gates[q],p)
   else:
    perm=np.arange(d)^(((np.arange(d)>>(n-1-p))&1)<<(n-1-q));rho=rho[:,perm][:,:,perm]
   k=len(qs);prob=eps/(4**k+(4**k-2)*eps);weights=np.r_[1-(4**k-1)*prob,np.full(4**k-1,prob)]
   ids=rng.choice(4**k,size=B,p=weights);sign*=np.where(ids==0,1.,-1.)
   rho=random_paulis(rho,qs,ids);rho=(1-eps)*rho+eps*reset(rho,qs)
  top=np.array(f['observable_basis_indices'][ci]);probs=np.diagonal(rho,axis1=1,axis2=2).real[:,top].sum(axis=1);signed=sign*probs
  variance_circuit=float(np.var(signed,ddof=1));shotvar=float(np.mean(probs*(1-probs)));mean=float(np.mean(gamma*signed));standard=float(gamma*np.std(signed,ddof=1)/np.sqrt(B))
  exact_ideal=f['rows'][ci][0];pred=[]
  for K in [250,1000,2000,4000]:
   var=gamma**2*(variance_circuit/K+shotvar/M)
   pred.append({'K':K,'equal_shots_per_QPR_circuit':M/K,'estimated_estimator_SD':np.sqrt(var)})
  result={'circuit':ci,'sampled_QPR_circuits':B,'ideal':exact_ideal,'sampled_signed_mean':mean,'sampled_signed_mean_SE':standard,'mean_z':(mean-exact_ideal)/standard,'circuit_variance':variance_circuit,'mean_Bernoulli_variance':shotvar,'grouped_variance_predictions':pred,'mean_probability':float(probs.mean()),'unsigned_exact_probability':f['rows'][ci][2],'probability_bounds':[float(probs.min()),float(probs.max())]}
  results.append(result);print(ci,pred,flush=True)
out={'purpose':'Sensitivity of estimator variance to K, a parameter absent from the fixed source. Three full-size circuits, not a fitted reproduction of original Fig2 histogram. Physical depolarization integrated exactly for each sampled QPR circuit.','assumptions':'Equal deterministic allocations M/K; optimal allocation can only reduce the within-circuit Bernoulli contribution, not the variance of sampled signed conditional expectations.','results':results,'seconds':time.monotonic()-start}
Path('checks/grouping_diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
