"""Different integration rule for actual selected Monte Carlo records.
Reconstructs the frozen generator's count vector from its exact seed and record index.
Only the selection config derives from our old output; no original reference enters.
"""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigh
from scipy.special import gammaln
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import brentq,minimize_scalar
from numpy.polynomial.legendre import leggauss
from threadpoolctl import threadpool_limits
threadpool_limits(1)
config=json.loads(Path('calculation/alignment-v3-20261022/selected_records.json').read_text());rows=[]
for selection in config['records']:
 N=selection['N'];p=selection['p'];m=np.arange(N+1)-N/2;off=np.sqrt((N-np.arange(N))*(np.arange(N)+1))/2
 ev,V=eigh(1j*(np.diag(off,1)-np.diag(off,-1)))
 psi=np.exp(.5*(gammaln(N+1)-gammaln(np.arange(N+1)+1)-gammaln(N-np.arange(N+1)+1)-N*np.log(2))-1j*m*m/np.sqrt(N));u=V.conj().T@psi
 def probabilities(x):return abs(V@(np.exp(-1j*ev[:,None]*np.atleast_1d(x))*u[:,None]))**2
 x=np.linspace(0,np.pi,16385);P=probabilities(x);q=P[:,len(x)//2].copy();q/=q.sum();counts=np.random.default_rng(selection['seed']).multinomial(p,q,selection['trials'])[selection['index']]
 logs=counts@np.log(np.maximum(P,1e-300));k=int(np.argmax(logs));Lmax=float(logs[k]);center=float(x[k]);grid_center=center
 def logpdf(xx):return counts@np.log(np.maximum(probabilities(xx),1e-300))-Lmax
 def pdf(xx):return np.exp(logpdf(xx))
 # No MAP estimate is rounded away from the exact parity point just to alter a radius.
 if k!=len(x)//2 and 0<k<len(x)-1:
  fit=minimize_scalar(lambda z:-float(logpdf([z])[0]),bounds=(x[k-1],x[k+1]),method='bounded',options={'xatol':1e-14});center=float(fit.x)
 results=[]
 for degree in [16,32]:
  node,weight=leggauss(degree);edge=np.linspace(0,np.pi,513);mid=(edge[1:]+edge[:-1])/2;half=(edge[1:]-edge[:-1])/2
  f=pdf((mid[:,None]+half[:,None]*node).ravel()).reshape(-1,degree);mass=half*(f@weight);cdf=np.r_[0,np.cumsum(mass)];Z=float(cdf[-1])
  def cdf_at(z):
   if z<=0:return 0.
   if z>=np.pi:return Z
   j=int(np.searchsorted(edge,z)-1);h=(z-edge[j])/2;mm=(z+edge[j])/2
   return float(cdf[j]+h*np.dot(weight,pdf(mm+h*node)))
  radius=brentq(lambda r:(cdf_at(min(np.pi,grid_center+r))-cdf_at(max(0,grid_center-r)))/Z-.68,0,np.pi,xtol=2e-13)
  refined=brentq(lambda r:(cdf_at(min(np.pi,center+r))-cdf_at(max(0,center-r)))/Z-.68,0,np.pi,xtol=2e-13)
  results.append(dict(degree=degree,normalization=Z,halfwidth=float(radius),refined_MAP_halfwidth=float(refined)))
 change=abs(results[0]['halfwidth']-results[1]['halfwidth']);diff=results[-1]['halfwidth']-selection['original_halfwidth'];refinements=[]
 for grid in [16385,65537]:
  xx=np.linspace(0,np.pi,grid);C=cumulative_trapezoid(pdf(xx),xx,initial=0);C/=C[-1]
  radius=brentq(lambda r:np.interp(min(np.pi,grid_center+r),xx,C)-np.interp(max(0,grid_center-r),xx,C)-.68,0,np.pi,xtol=2e-13)
  refinements.append(dict(grid=grid,fixed_MAP_halfwidth=float(radius),difference_from_Gauss=float(radius-results[-1]['halfwidth'])))
 rows.append(dict(selection=selection,counts=counts.tolist(),grid_MAP=grid_center,refined_MAP=center,quadrature=results,degree_refinement_change=change,difference_from_original_grid=diff,
  grid_refinement=refinements,original_grid_meets_declared_tolerance=abs(diff)<config['comparison_absolute_tolerance_rad']))
 assert change<1e-9 and abs(refinements[-1]['difference_from_Gauss'])<config['comparison_absolute_tolerance_rad'],rows[-1]
 print(selection['NT'],p,selection['selection'],'delta',diff,flush=True)
Path('calculation/alignment-v3-20261022/gauss_tail_check.json').write_text(json.dumps(dict(rows=rows,method='512 subintervals,16/32-point Gauss-Legendre integration with exact partial-interval quadrature and bracketed radius root. Challenges actual median/extreme generated records; not an exhaustive all-record bound.'),indent=2))
