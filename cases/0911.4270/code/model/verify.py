"""Scientific checks, independently integrated dynamics and covariance eigenproblem."""
from pathlib import Path
import json,time
import numpy as np
from scipy.integrate import solve_ivp,quad
from scipy.linalg import expm
from threadpoolctl import threadpool_limits
from model import star_model,evolution,observe,negativity
cfg=json.loads(Path('code/config.json').read_text()); result={}; start=time.monotonic()
Omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]])); PT=np.diag([1,1,1,-1])
def direct_cov_E(u,noise,r=4.):
    cc=np.cosh(2*r); ss=np.sinh(2*r)
    # Cross block follows complex U00 directly, retaining its phase.
    X=np.array([[u.real,-u.imag],[u.imag,u.real]])
    V=np.zeros((4,4)); V[:2,:2]=(abs(u)**2*cc+noise)*np.eye(2); V[2:,2:]=cc*np.eye(2)
    V[:2,2:]=ss*X@np.diag([1.,-1.]); V[2:,:2]=V[:2,2:].T
    eig=np.linalg.eigvals(1j*Omega@(PT@V@PT)); nu=np.sort(abs(eig))[0]
    return max(0.,-np.log2(nu))
with threadpool_limits(limits=1):
 checks=[]
 for power,cutoff,alpha,Ts in [(1,15,.5,[0,1,2]),(1,15,1.,[0,1,2]),(1,15,1.5,[0,1,2]),(3,3,.05,[0,2,4]),(3,3,.1,[0,2,4]),(3,3,.15,[0,2,4])]:
  h,ws,g=star_model(alpha,power,cutoff); t=np.linspace(0,21,127); row,lam=evolution(h,t)
  def rhs(t,y): return -1j*np.r_[10*y[0]+g@y[1:],g*y[0]+ws*y[1:]]
  y0=np.zeros(351,dtype=complex); y0[0]=1
  sol=solve_ivp(rhs,[0,21],y0,t_eval=t,method='DOP853',rtol=2e-11,atol=2e-13)
  assert sol.success
  other=sol.y.T; o=observe(row,ws,Ts); o2=observe(other,ws,Ts)
  ce=[]
  for j,T in enumerate(Ts):
   direct=np.array([direct_cov_E(row[k,0],o[j][2][k]) for k in range(len(t))]); ce.append(float(max(abs(direct-o[j][1]))))
  checks.append({'power':power,'alpha':alpha,'row_abs_error':float(max(abs(row-other).flat)),'E_ode_abs_error':max(float(max(abs(x[1]-y[1]))) for x,y in zip(o,o2)),'E_covariance_abs_error':max(ce),'nfev':sol.nfev,'min_h_eigenvalue':float(lam[0])})
 result['independent_dynamics']=checks
 # Time resolution over full alpha range; exact tmax handled independently.
 convergence={}
 for f in cfg['figures']:
  allrows=[]
  for idx in range(f['alpha_count']):
   alpha=idx*f['alpha_step']; h,ws,g=star_model(alpha,f['power'],f['cutoff'])
   # Nested grids maintain the published dt; exact t=21 is appended in endpoint check.
   tt=np.arange(0,21+1e-12,f['dt']/4); row,lam=evolution(h,tt)
   i4=[x[0] for x in observe(row,ws,f['temperatures'])]
   i2=[x[0] for x in observe(row[::2],ws,f['temperatures'])]
   i1=[x[0] for x in observe(row[::4],ws,f['temperatures'])]
   # Fine and coarse grids stop at different last times; record endpoint effects.
   r21,_=evolution(h,np.array([21.])); coarse_end=np.concatenate([row[::4],r21]); fine_end=np.concatenate([row,r21])
   ie1=[x[0] for x in observe(coarse_end,ws,f['temperatures'])]; ie4=[x[0] for x in observe(fine_end,ws,f['temperatures'])]
   allrows.append({'alpha':alpha,'dt':i1,'dt_half':i2,'dt_quarter':i4,'dt_endpoint':ie1,'dt_quarter_endpoint':ie4})
  convergence[f['id']]=allrows
 result['time_convergence']=convergence
 # Different bath node scheme and M doubling are sensitivity checks, not tuning.
 bath=[]
 for f,alphas in [(cfg['figures'][0],[.5,.7,.85,1.,1.2,1.5]),(cfg['figures'][1],[.02,.05,.09,.1,.12,.15])]:
  t=np.r_[np.arange(0,21,f['dt']/4),21.]
  for alpha in alphas:
   rr={'figure':f['id'],'alpha':alpha}
   for M,grid in [(350,'right'),(350,'midpoint'),(700,'right'),(1400,'right')]:
    h,ws,g=star_model(alpha,f['power'],f['cutoff'],M=M,grid=grid); row,vals=evolution(h,t)
    rr[f'M{M}_{grid}']=[x[0] for x in observe(row,ws,f['temperatures'])]
   bath.append(rr)
 result['bath_sensitivity']=bath
 # Squeezing statement: source says curve shapes do not depend significantly on r.
 squeeze=[]
 for f in cfg['figures']:
  for idx in [50,100,150]:
   alpha=idx*f['alpha_step']; h,ws,g=star_model(alpha,f['power'],f['cutoff']); t=np.r_[np.arange(0,21,f['dt']/4),21.]; row,vals=evolution(h,t)
   squeeze.append({'figure':f['id'],'alpha':alpha,'r_values':{str(r):[x[0] for x in observe(row,ws,f['temperatures'],r=r)] for r in [1,2,3,4,5]}})
 result['squeezing_sensitivity']=squeeze
 # Pure dephasing: compute actual Choi matrices from explicit superoperator action.
 phi=np.array([1,0,0,1])/np.sqrt(2); P=np.outer(phi,phi); Z=np.diag([1.,-1.]); L=np.kron(Z,np.eye(2))@P@np.kron(Z,np.eye(2))-P
 dephase=[]
 for gamma in [-2.,-.7,0.,.3,2.]:
  for eps in [1e-3,1e-5,1e-7]:
   C=P+gamma*eps*L; gnum=(np.linalg.norm(C,ord='nuc')-1)/eps
   # Exact finite interval at constant gamma: offdiagonal multiplier exp(-2 gamma eps).
   Cexact=P.copy(); Cexact[0,3]*=np.exp(-2*gamma*eps); Cexact[3,0]*=np.exp(-2*gamma*eps)
   dephase.append({'gamma':gamma,'eps':eps,'g_linear_choi':float(gnum),'expected':max(0.,-2*gamma),'g_exact_finite':float((np.linalg.norm(Cexact,ord='nuc')-1)/eps)})
 result['dephasing']=dephase
 # Valid CP dephasing evolution gamma(t)=1-t on [0,2]. At t=1, g=0 but each
 # finite epsilon in (0,1] gives an intermediate non-CP map: f=e^(epsilon^2).
 result['pointwise_g_caveat']=[{'epsilon':e,'f_minus_1':float(np.expm1(e*e)),'g_finite':float(np.expm1(e*e)/e),'g_limit':0.} for e in [.1,.01,.001]]
 # For gamma=sin(t), cumulative rate=1-cos(t)>=0, so the family is CPTP;
 # on [0,2pi] I=4. Integrate the exact norm derivative independently.
 integral=quad(lambda t:max(0.,-2*np.sin(t)),0,2*np.pi,epsabs=1e-12,points=[np.pi])[0]
 result['dephasing_integral']={'gamma':'sin(t)','interval':[0.,2*np.pi],'numeric_I':integral,'exact_I':4.,'D_NM':integral/(1+integral)}
 result['tan_divergence']=[{'delta':d,'negative_area_times_2':float(-2*np.log(np.sin(d)))} for d in [.1,.01,.001,1e-6]]
 # Entanglement witness is not necessary: depolarizing p decreases to 1/5,
 # then rises but stays <1/3 (entanglement-breaking); max-entangled Choi E stays 0.
 result['witness_incompleteness']={'p_before':.2,'p_after':.25,'log_neg_before':max(0.,np.log2((1+3*.2)/2)),'log_neg_after':max(0.,np.log2((1+3*.25)/2)),'intermediate_choi_eigenvalues':[(1+3*1.25)/4]+[(1-1.25)/4]*3,'intermediate_trace_norm':1.375,'interpretation':'Checking example, not an added original-paper result.'}
 result['zero_coupling']={'E_expected':8/np.log(2),'E_scalar':float(negativity(1.,0.)),'covariance_E':direct_cov_E(1+0j,0.),'I_exact':0.}
result['elapsed_seconds']=time.monotonic()-start
Path('results/verification.json').write_text(json.dumps(result,indent=2,allow_nan=False))
print('independent checks',checks,flush=True)
for f,rows in result['time_convergence'].items():
 a=lambda name:np.array([r[name] for r in rows])
 print(f,'max(dt/4 - dt)=',np.max(abs(a('dt_quarter')-a('dt')),axis=0),'max(endpoint - truncated)=',np.max(abs(a('dt_endpoint')-a('dt')),axis=0),'max(half-quarter)',np.max(abs(a('dt_half')-a('dt_quarter')),axis=0),flush=True)
print('seconds',result['elapsed_seconds'])
