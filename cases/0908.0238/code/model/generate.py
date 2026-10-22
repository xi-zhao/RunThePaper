"""Amplitude damping from a Lorentzian bath; closed form + pseudomode ODE.

Time in 1/lambda; gamma0/lambda=.01, exactly the original weak-coupling regime.
"""
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from threadpoolctl import threadpool_limits
threadpool_limits(1)
C=json.loads(Path('calculation/config.json').read_text()); g=C['gamma0_over_lambda']

def amp(t,delta):
    z=1-1j*delta; d=np.sqrt(z*z-2*g+0j)
    # Exponentials remain stable at long time (unlike exp(-zt/2)*cosh(dt/2)).
    a=(1+z/d)/2; b=(1-z/d)/2
    G=a*np.exp((-z+d)*t/2)+b*np.exp((-z-d)*t/2)
    Gp=a*(-z+d)/2*np.exp((-z+d)*t/2)+b*(-z-d)/2*np.exp((-z-d)*t/2)
    return G,2*np.real(np.conj(G)*Gp)

deltas=np.arange(0,20.0001,.5); time=np.linspace(0,4,401)
surface=np.array([amp(time,d)[1]/g for d in np.linspace(0,20,201)])
rng=np.random.default_rng(C['seed'])
# Independent uniform Bloch-ball mixed states, plus uniform pure states.
vec=rng.normal(size=(2,1000,3)); vec/=np.linalg.norm(vec,axis=-1,keepdims=True)
vec[:,:500]*=rng.random((2,500,1))**(1/3)
dr=(vec[0]-vec[1])/2; dz=dr[:,2]**2; xy=(dr[:,:2]**2).sum(axis=1)
N=[]; random=[]; optimization=[]; convergence=[]; checks=[]

def intervals(delta,T,dt):
    t=np.linspace(0,T,int(T/dt)+1); rate=amp(t,delta)[1]
    changes=np.flatnonzero(rate[:-1]*rate[1:]<0)
    roots=[0]+[brentq(lambda x:amp(x,delta)[1],t[i],t[i+1],xtol=2e-13) for i in changes]+[T]
    return [(a,b) for a,b in zip(roots[:-1],roots[1:]) if amp((a+b)/2,delta)[1]>0]

for delta in deltas:
    pairs=intervals(delta,30,.002)
    endpoints=np.array([[abs(amp(t,delta)[0]) for t in ab] for ab in pairs]).reshape(-1,2)
    value=float(np.sum(endpoints[:,1]**2-endpoints[:,0]**2));N.append(value)
    vals=np.zeros(1000); angles=np.linspace(0,1,1001); opt=np.zeros_like(angles)
    for a,b in endpoints:
        vals+=np.sqrt(b**4*dz+b**2*xy)-np.sqrt(a**4*dz+a**2*xy)
        opt+=np.sqrt(b**4*angles+b**2*(1-angles))-np.sqrt(a**4*angles+a**2*(1-angles))
    random.append(vals); optimization.append(float(opt.max()))
    fine=intervals(delta,60,.001)
    nf=sum(abs(amp(b,delta)[0])**2-abs(amp(a,delta)[0])**2 for a,b in fine)
    convergence.append(abs(value-nf))
    # ODE c'=-ig_eff b, b'=-(lambda-iDelta)b-ig_eff c.
    def rhs(t,y):return [-1j*np.sqrt(g/2)*y[1],-(1-1j*delta)*y[1]-1j*np.sqrt(g/2)*y[0]]
    sol=solve_ivp(rhs,(0,30),[1+0j,0j],method='DOP853',rtol=1e-11,atol=1e-13,t_eval=np.linspace(0,30,1001))
    err=float(np.max(abs(sol.y[0]-amp(sol.t,delta)[0]))); checks.append(err)
assert max(checks)<2e-10
assert max(convergence)<2e-10
assert np.max(np.array(optimization)-N)<2e-10
assert np.max(np.array(random)-np.array(N)[:,None])<2e-10

# A direct finite bath trace checks the exact central-spin coherence, not a time-local master approximation.
spinchecks=[]; st=np.linspace(0,3*np.pi,1001)
for nb in [1,2,5,8]:
    eigenvalues=np.array([sum(1 if (k>>j)&1 else -1 for j in range(nb)) for k in range(2**nb)])
    direct=np.mean(np.exp(-2j*st[:,None]*eigenvalues),axis=1)
    spinchecks.append(float(np.max(abs(direct-np.cos(2*st)**nb))))
assert max(spinchecks)<1e-13
np.savez_compressed('calculation/results/generation.npz',deltas=deltas,time=time,
                    surface_deltas=np.linspace(0,20,201),sigma_over_gamma0=surface,
                    N=np.array(N),random_pairs=np.array(random),optimized=np.array(optimization),
                    spin_time=st,spin_distance=np.abs(np.cos(2*st))**5)
Path('calculation/results/checks.json').write_text(json.dumps({
 'max_amplitude_ODE_error':max(checks),'max_time_window_and_grid_change':max(convergence),
 'central_spin_max_error':max(spinchecks),'global_qubit_optimization':'1001 polar values for antipodal pure states; axial symmetry and homogeneity reduce full state-pair optimization to this one variable',
 'peak_N':float(np.max(N)),'peak_detuning':float(deltas[np.argmax(N)]),
 'spin_infinite_measure_reason':'Each half-period of |cos(2At)|^N has a revival of exactly one for antipodal equatorial states. Infinitely many identical contributions diverge; finite sampling is not the proof.',
 'random_seed':C['seed'],'original_random_seed':'not assumed or fitted'},indent=2))
