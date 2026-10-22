"""Original free-to-interacting Luttinger quench: mode sums vs log identities.

No original numerical figures exist. Chosen dimensionless controls test equations,
not a claim to have reconstructed an unpublished original numerical experiment.
"""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import expm
from scipy.integrate import quad
from scipy.special import loggamma
from threadpoolctl import threadpool_limits
threadpool_limits(1)
R=1.;L=400.;v=1.;x=31.;t=np.linspace(0,L/(2*v),801);y=2*v*t

def A(x):
    z=np.exp(-2*np.pi*R/L)
    return .5*np.log1p(2*z*(1-np.cos(2*np.pi*x/L))/(1-z)**2)
def closed(x,y,gamma):return -gamma**2*(A(x)+A(y)-.5*A(x+y)-.5*A(x-y))
arrays={'time':t,'x':np.array(x)};checks={}
for phi in [.2,.5,1.]:
    gamma=np.sinh(2*phi);values=[]
    for N in [2048,4096]:
        n=np.arange(1,N+1);q=2*np.pi*n/L
        summand=np.exp(-R*q)/n*(1-np.cos(q*x))
        values.append(-gamma**2*np.array([np.sum(summand*(1-np.cos(q*yy))) for yy in y]))
    error=float(max(abs(values[-1]-closed(x,y,gamma))))
    refine=float(max(abs(values[-1]-values[0])))
    assert error<2e-10 and refine<2e-10
    arrays[f'phi{phi}_ratio']=np.exp(values[-1]);checks[f'phi{phi}']={'log_ratio_sum_vs_closed':error,'cutoff_change':refine,'recurrence_error':float(abs(np.exp(values[-1][-1])-1))}

    # Heisenberg 2x2 dynamics independently diagonalized by the Bogoliubov map.
    errors=[];comm=[]
    for q in [.001,.1,1.,3.]:
        phiq=.5*np.arcsinh(gamma*np.exp(-R*q/2))
        B=np.array([[np.cosh(phiq),np.sinh(phiq)],[np.sinh(phiq),np.cosh(phiq)]])
        generator=np.linalg.inv(B)@np.diag([-1j*v*q,1j*v*q])@B
        for time in [.13,2.3,11.]:
            direct=expm(generator*time)
            f=np.cos(v*q*time)-1j*np.sin(v*q*time)*np.cosh(2*phiq)
            gc=-1j*np.sin(v*q*time)*np.sinh(2*phiq)
            analytic=np.array([[f,gc],[np.conj(gc),np.conj(f)]])
            errors.append(np.max(abs(direct-analytic)))
            comm.append(abs(abs(f)**2-abs(gc)**2-1))
    checks[f'phi{phi}']['bogoliubov_exponential_error']=float(max(errors))
    checks[f'phi{phi}']['canonical_commutator_error']=float(max(comm))
    assert max(errors)<1e-12

# Exact regulated thermodynamic identity and asymptotic form: do not test it at the light cone.
phi=.5;gamma=np.sinh(2*phi)
def Ai(a):return .5*np.log1p((a/R)**2)
def AiT(a,T):
    beta=1/T
    return .5*np.log1p((a/R)**2)+2*loggamma(1+R/beta).real-2*loggamma(1+R/beta+1j*a/beta).real
thermo=[];thermal=[]
for xx in [10.,30.,100.]:
 for yy in [xx*.2,xx*.8,xx*1.2,xx*5]:
    exact=-gamma**2*(Ai(xx)+Ai(yy)-.5*Ai(xx+yy)-.5*Ai(xx-yy))
    # Independent quadrature of the original mode integral.
    integrand=lambda q: np.exp(-R*q)*(1-np.cos(q*xx))*(1-np.cos(q*yy))/q if q else 0.
    integral=-gamma**2*quad(integrand,0,40,epsabs=1e-10,epsrel=1e-10,limit=5000)[0]
    thermo.append(abs(exact-integral))
    for T in [.01,.1]:
        # Force integration of the resolved oscillatory intervals. A single
        # adaptive call previously underestimated error for x=100,y=500,T=.1.
        direct=-gamma**2*quad(lambda q:integrand(q)/np.tanh(q/(2*T)) if q else 0.,0,40,
                              points=np.arange(.1,40,.1),epsabs=1e-11,epsrel=1e-11,limit=10000)[0]
        identity=-gamma**2*(AiT(xx,T)+AiT(yy,T)-.5*AiT(xx+yy,T)-.5*AiT(xx-yy,T))
        thermal.append(abs(direct-identity))
checks['thermodynamic_integral_error']=float(max(thermo));checks['thermal_integral_error']=float(max(thermal))
assert max(thermo)<1e-7 and max(thermal)<1e-6
xx=np.geomspace(20,2000,101);arrays['long_time_x']=xx
arrays['stationary_ratio']=(1+(xx/R)**2)**(-gamma**2/2)
slopes=-np.diff(np.log(arrays['stationary_ratio']))/np.diff(np.log(xx))
checks['stationary_anomalous_exponent']={'expected':gamma**2,'last_local_slope':float(slopes[-1]),'ground_state_exponent':float(2*np.sinh(phi)**2)}

# Regulated density-current correlation: direct q-weighted mode sum vs geometric identity.
n=np.arange(1,4097);q=2*np.pi*n/L;z=np.exp(-R*q)
def B(a):
    zz=np.exp(-2*np.pi*R/L+2j*np.pi*a/L)
    return (zz/(1-zz)**2).real/L**2
denssum=np.array([np.sum(n*z*(1+gamma**2*(1-np.cos(q*yy)))*np.cos(q*x))/L**2 for yy in y])
densclosed=(1+gamma**2)*B(x)-gamma**2/2*(B(x+y)+B(x-y))
checks['density_sum_vs_closed_error']=float(max(abs(denssum-densclosed)))
assert checks['density_sum_vs_closed_error']<1e-11
arrays['density_correlation']=denssum
checks['GGE_occupation']='n(q)=sinh(phi(q))^2; anomalous correlations dephase in the continuum. This preserves the quench exponent gamma^2, not the ground-state exponent.'
np.savez_compressed('calculation/results/generation.npz',**arrays)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
