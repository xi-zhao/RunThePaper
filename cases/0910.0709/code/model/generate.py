"""Independent Ermakov protocol and Hamilton-equation propagation, SI seconds.

No original curves or author numerical implementation are read here.
"""
import json
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root
from threadpoolctl import threadpool_limits

threadpool_limits(1)
C = json.loads(Path('calculation/config.json').read_text())
w0 = 2*np.pi*C['initial_hz']; wf = 2*np.pi*C['final_hz']
gamma = np.sqrt(w0/wf)
s = np.linspace(0,1,C['samples'])

def protocol(s,tf,exponential=False):
    q=10*s**3-15*s**4+6*s**5
    qp=30*s**2*(1-s)**2
    qpp=60*s*(1-s)*(1-2*s)
    if exponential:
        b=np.exp(np.log(gamma)*q)
        db=b*np.log(gamma)*qp/tf
        ddb=b*(np.log(gamma)*qpp+np.log(gamma)**2*qp**2)/tf**2
    else:
        b=1+(gamma-1)*q; db=(gamma-1)*qp/tf; ddb=(gamma-1)*qpp/tf**2
    w2=w0**2/b**4-ddb/b
    e=(db**2+w2*b**2+w0**2/b**2)/(2*w0**2)
    return b,db,w2,e

arrays={'s':s}; checks=[]
arrays['fig1_poly']=protocol(s,.002)[0]
arrays['fig1_exp']=protocol(s,.002,True)[0]
for ms in C['duration_ms']:
    tf=ms/1000
    for exp in ([False,True] if ms==2 else [False]):
        b,db,w2,e=protocol(s,tf,exp); tag=f'{ms}ms_'+('exp' if exp else 'poly')
        arrays[tag+'_energy']=e; arrays[tag+'_w2']=w2/w0**2
        # Independent evolution of q,p/w0 fundamental matrix in scaled time.
        def rhs(u,y):
            a=np.array([[0,w0*tf],[-float(protocol(u,tf,exp)[2])*tf/w0,0]])
            return (a@y.reshape(2,2)).ravel()
        observed=[]
        for tol in [1e-9,1e-12]:
            sol=solve_ivp(rhs,(0,1),np.eye(2).ravel(),t_eval=s,rtol=tol,atol=tol/30,method='DOP853')
            if not sol.success: raise RuntimeError(sol.message)
            m=sol.y.T.reshape(-1,2,2); cov=m@np.transpose(m,(0,2,1))
            energy=(cov[:,1,1]+w2/w0**2*cov[:,0,0])/2
            observed.append(energy)
        error=float(np.max(abs(observed[-1]-e)))
        convergence=float(np.max(abs(observed[-1]-observed[0])))
        # Normalized energy can transiently be negative in an expulsive trap.
        # Criterion resolves the final 0.01 cooling ratio and O(1) energy curves.
        assert error<2e-7 and convergence<2e-5, (tag,error,convergence)
        checks.append({'id':tag,'max_energy_error_E00':error,'tolerance_comparison':2e-7,
                       'tolerance_refinement_change_E00':convergence,
                       'final_energy_E00':float(observed[-1][-1]),
                       'final_expected':wf/w0})

# Piecewise-constant expulsive/real trap: solve continuity, do not fit its plotted switch.
wi=.9*w0
def left(t):
    b=np.sqrt(1+(w0*w0+wi*wi)/wi**2*np.sinh(wi*t)**2)
    db=(w0*w0+wi*wi)/wi*np.sinh(wi*t)*np.cosh(wi*t)/b
    return b,db
def right(t,tf):
    a=w0*w0/(w0*w0*gamma**2)-gamma**2
    b=np.sqrt(gamma**2+a*np.sin(w0*(t-tf))**2)
    db=a*w0*np.sin(w0*(t-tf))*np.cos(w0*(t-tf))/b
    return b,db
def matching(x):
    t1,dt=x/w0; l=left(t1); r=right(t1,t1+dt)
    return [l[0]-r[0],(l[1]-r[1])/w0]
solution=root(matching,[2.7,.8],tol=1e-11)
assert solution.success and np.linalg.norm(matching(solution.x))<1e-9
t1,dt=solution.x/w0; tf=t1+dt
b,db=np.where(s*tf<t1,np.array(left(s*tf)),np.array(right(s*tf,tf)))
w2=np.where(s*tf<t1,-wi**2,w0**2)
arrays['bang_w2']=w2/w0**2
arrays['bang_energy']=(db**2+w2*b**2+w0**2/b**2)/(2*w0**2)
arrays['bang_energy'][0]=1; arrays['bang_energy'][-1]=wf/w0
arrays['bang_w2'][0]=1;arrays['bang_w2'][-1]=(wf/w0)**2
Path('calculation/results').mkdir(parents=True,exist_ok=True)
np.savez_compressed('calculation/results/generation.npz',**arrays)
Path('calculation/results/checks.json').write_text(json.dumps({
    'checks':checks,'bang_total_ms':tf*1000,'bang_switch_ms':t1*1000,
    'matching_residual':list(matching(solution.x)),
    'real_frequency_bangbang_infimum_ms':1000*np.sqrt(1-wf/w0)/np.sqrt(wf*w0),
    'excitation_convention':'E_n/E_ground_initial=(2n+1)*energy, n=0,1,...; both labeling possibilities retained for source comparison',
    'scope_limit':'Exact quadratic Hamiltonian propagation and analytical invariant; not an experimental cooling demonstration.'},indent=2))
