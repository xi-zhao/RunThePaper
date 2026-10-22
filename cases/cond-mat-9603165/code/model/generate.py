"""Original L=1000 Hatano-Nelson ring and L=500,100-sample localization check."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eig,eigvals
from scipy.optimize import linear_sum_assignment,brentq
from threadpoolctl import threadpool_limits
threadpool_limits(1)
C=json.loads(Path('calculation/config.json').read_text());rng=np.random.default_rng(C['seed'])
N=C['spectrum_L'];potential=rng.uniform(-1,1,N);data={'potential':potential};checks={}

def H(p,h):
    n=len(p);a=np.diag(p);ix=np.arange(n);a[(ix+1)%n,ix]=-.5*np.exp(h);a[ix,(ix+1)%n]=-.5*np.exp(-h)
    return a
def dH_times(r,h):return -.5*np.exp(h)*np.roll(r,1,axis=0)+.5*np.exp(-h)*np.roll(r,-1,axis=0)
for h in C['fields']:
    e,l,r=eig(H(potential,h),left=True,right=True,check_finite=False)
    Hr=potential[:,None]*r-.5*np.exp(h)*np.roll(r,1,axis=0)-.5*np.exp(-h)*np.roll(r,-1,axis=0)
    residual=float(np.max(np.linalg.norm(Hr-r*e,axis=0)))
    overlap=np.sum(l.conj()*r,axis=0)
    derivative=np.sum(l.conj()*dH_times(r,h),axis=0)/overlap
    current=-derivative.real
    order=np.lexsort((e.imag,e.real));data[f'energy_h{h}']=e[order];data[f'current_h{h}']=current[order]
    data[f'participation_h{h}']=1/np.sum(abs(r[:,order])**4,axis=0)
    checks[str(h)]={'right_eigen_residual':residual,'complex_fraction':float(np.mean(abs(e.imag)>1e-8)),
                    'maximum_abs_current':float(max(abs(current))),'minimum_left_right_overlap':float(min(abs(overlap)))}
    assert residual<1e-10
    print('completed L=1000, h=',h,flush=True)

# Independent Hellmann-Feynman derivative control at modest size; full figure above stays L=1000.
p=rng.uniform(-1,1,80);h=.7;dh=1e-5;e,l,r=eig(H(p,h),left=True,right=True)
derivative=np.sum(l.conj()*dH_times(r,h),axis=0)/np.sum(l.conj()*r,axis=0)
neighbors=[]
for hh in [h-dh,h+dh]:
    other=eigvals(H(p,hh));rows,cols=linear_sum_assignment(abs(e[:,None]-other[None,:]));neighbors.append(other[cols])
error=float(max(abs((neighbors[1]-neighbors[0])/(2*dh)-derivative)))
checks['finite_difference_current_error']=error;assert error<2e-5

# Fourier diagonalization, including the factor 1/2 in the original hopping.
h=.7;n=64;observed=eigvals(H(np.zeros(n),h));expected=-np.cos(2*np.pi*np.arange(n)/n+1j*h)
rows,cols=linear_sum_assignment(abs(observed[:,None]-expected[None,:]));checks['clean_band_error']=float(max(abs(observed-expected[cols])))
assert checks['clean_band_error']<1e-12

# Actual paper inset conditions: 100 independent chains of length 500, window .04t.
energies=np.arange(-1.8,1.80001,.04);samples=[]
for sample in range(C['localization_samples']):
    V=rng.uniform(-1,1,C['localization_L']);a=np.ones(len(energies));b=np.zeros(len(energies));growth=np.zeros(len(energies))
    for vv in V:
        aa=2*(vv-energies)*a-b;bb=a;norm=np.hypot(aa,bb);a=aa/norm;b=bb/norm;growth+=np.log(norm)
    samples.append(growth/len(V))
samples=np.array(samples);data['kappa_energy']=energies;data['kappa_samples']=samples
data['kappa_mean']=samples.mean(axis=0);data['kappa_SE']=samples.std(axis=0,ddof=1)/np.sqrt(len(samples))
checks['localization_parameters']={'L':C['localization_L'],'samples':len(samples),'energy_step':.04,'method':'normalized transfer products; finite-length endpoint bias O(1/L), not an exact author-specific estimator'}

# Original continuum single delta impurity: finite ring secular equation in the imaginary wave number.
imp=[];L=80.;kappa0=1.
for h in [0,.2,.8,1.2,1.8]:
    def secular(k):
        logcosh=lambda z:np.logaddexp(z,-z)-np.log(2)
        logsinh=k*L-np.log(2)+np.log1p(-np.exp(-2*k*L))
        return k*(1/np.tanh(k*L)-np.exp(logcosh(h*L)-logsinh))-kappa0
    k=brentq(secular,max(h,1e-9),max(h,kappa0)+1)
    imp.append({'h':h,'finite_ring_energy':-k*k/2,'thermodynamic_energy':-.5*max(kappa0,h)**2})
checks['single_impurity']=imp
checks['stretched_exponential']='Minimize f(r)=A r+tau/(g r^d): f_min=(d+1)d^(-d/(d+1))*A^(d/(d+1))*(tau/g)^(1/(d+1)); tau*=g*hbar^(d+1)/A^d. This is the original asymptotic estimate, not a finite-sample universal theorem.'
checks['disorder_comparison']='An independent seed under the original distribution. Compare spectral envelopes, real/complex mobility regions and averaged localization; individual disorder points are not paired.'
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
