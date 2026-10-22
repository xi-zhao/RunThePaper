"""Finite preparation-time control of quantum-regression curves from vacuum.
No original curve enters generation; source steady-state claim remains distinct.
"""
from pathlib import Path
import sys,json
import numpy as np
from scipy.sparse.linalg import expm_multiply
sys.path.insert(0,str(Path('calculation').resolve()))
from model import Model
from threadpoolctl import threadpool_limits
threadpool_limits(1)
m=Model(3,12,[0,.12,0],.1,.1);ss=m.steady('propagate');reference=m.rho.copy();time_ps=np.linspace(0,100,201);rows=[]
rho=np.zeros(len(m.ii),complex);rho[m.lookup[0,0]]=1.;last=0.
for lifetimes in [1,2,3,4,6,8,16,32,64]:
 t0=lifetimes/.1;rho=expm_multiply(m.L*(t0-last),rho);last=t0
 pop=rho[m.diag].real;n=float(pop@m.basis[:,0]);fac=float(pop@(m.basis[:,0]*(m.basis[:,0]-1)))
 cond=m.vector(m.a[0]@m.matrix(rho)@m.a[0].T)
 out=expm_multiply(m.L,np.c_[rho,cond],start=0,stop=float(time_ps[-1]/.6582119569),num=len(time_ps))
 nt=out[:,m.diag,0].real@m.basis[:,0];coinc=out[:,m.diag,1].real@m.basis[:,0]
 proper=coinc/(n*nt);stationary_normalizer=coinc/n**2
 rows.append(dict(t0_lifetimes=lifetimes,t0_ps=t0*.6582119569,n1=n,g2_zero=fac/n**2,
  mean_relative_error_to_steady=float(n/ss['n'][0]-1),g2_relative_error_to_steady=float(fac/n**2/ss['g2'][0]-1),
  density_max_error=float(np.max(abs(rho-reference))),stationarity_residual=float(np.max(abs(m.L@rho))),
  g11_correct_nonstationary=proper.tolist(),g11_using_steady_normalizer=stationary_normalizer.tolist()))
 print(lifetimes,n,fac/n**2,rows[-1]['stationarity_residual'],flush=True)
assert abs(rows[-1]['g2_zero']-ss['g2'][0])<1e-8
Path('calculation/alignment-v3-20261022/transient_regression.json').write_text(json.dumps(dict(rows=rows,time_ps=time_ps.tolist(),steady_g2=float(ss['g2'][0]),steady_n1=float(ss['n'][0]),limits='Finite t0 variants are not steady-state reproduction. Correct nonstationary normalization n(t0)n(t0+tau) is kept separate from the stationary assumption n(t0)^2.'),indent=2))
