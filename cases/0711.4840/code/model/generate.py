"""One-axis twisting, QFI and the original finite-shot Bayesian estimator."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigh,expm
from scipy.special import gammaln
from scipy.integrate import cumulative_trapezoid
from threadpoolctl import threadpool_limits
import mpmath as mp
threadpool_limits(1)
rng=np.random.default_rng(20261021)

def spin(N):
    m=np.arange(N+1)-N/2;j=N/2
    jp=np.diag(np.sqrt((j-m[:-1])*(j+m[:-1]+1)),-1)
    return (jp+jp.T)/2,(jp-jp.T)/(2j),np.diag(m),m
def state(N,tau):
    m=np.arange(N+1)-N/2
    return np.exp(.5*(gammaln(N+1)-gammaln(N/2-m+1)-gammaln(N/2+m+1)-N*np.log(2))-1j*tau*m*m)
def prob(N,tau,angles):
    _,jy,_,_=spin(N);ev,V=eigh(jy)
    a=V@(np.exp(-1j*ev[:,None]*angles)*(V.conj().T@state(N,tau))[:,None])
    return abs(a)**2
checks={};data={}
N=10000;scaled=np.linspace(0,3,3001);tau=scaled/np.sqrt(N)
A=-np.expm1((N-2)*np.log(np.cos(2*tau)));B=4*np.sin(tau)*np.exp((N-2)*np.log(np.cos(tau)))
sq=np.sqrt(A*A+B*B);difference=np.divide(-B*B,sq+A,out=np.zeros_like(A),where=sq+A>0)
xi=np.exp(-2*(N-1)*np.log(np.cos(tau)))
chi=2/(2+(N-1)*A)
opt=(4+(N-1)*difference)/4*xi
data.update(fig1a_scaled_time=scaled,fig1a_xi=xi,fig1a_chi=chi,fig1a_opt=opt)
high=[]
with mp.workdps(70):
 for i in [0,1,10,50,100,1000,2500]:
    t=mp.mpf(str(float(tau[i])));aa=1-mp.cos(2*t)**(N-2);bb=4*mp.sin(t)*mp.cos(t)**(N-2)
    exact=(4+(N-1)*(aa-mp.sqrt(aa*aa+bb*bb)))/(4*mp.cos(t)**(2*N-2))
    high.append(float(abs(mp.mpf(float(opt[i]))-exact)))
checks['N10000_squeezing_high_precision_max_error']=max(high)
assert max(high)<1e-7
finite=[]
for n in [5,15,30]:
 jx,jy,jz,m=spin(n)
 for t in [.0,.03,.1,.3,.7]:
    psi=state(n,t)
    variance=lambda op:float(np.vdot(psi,op@op@psi).real-abs(np.vdot(psi,op@psi))**2)
    direct=n/(4*variance(jy));exact=2/((n+1)-(n-1)*np.cos(2*t)**(n-2))
    finite.append(abs(direct-exact))
checks['Dicke_QFI_formula_error']=float(max(finite));assert max(finite)<1e-12

# Distinct tensor-product construction checks the spin convention and twisting.
n=5;sz=np.diag([-.5,.5]);sy=np.array([[0,1j],[-1j,0]])/2
JZ=np.zeros((2**n,2**n));JY=np.zeros_like(JZ,dtype=complex)
for i in range(n):
 for local,total in [(sz,JZ),(sy,JY)]:
    op=np.array([[1.]])
    for k in range(n):op=np.kron(op,local if k==i else np.eye(2))
    total+=op
psi=expm(-.13j*JZ@JZ)@np.ones(2**n)/np.sqrt(2**n)
theta=.37;out=expm(-1j*theta*JY)@psi
distribution=np.array([np.sum(abs(out[np.array([k.bit_count() for k in range(2**n)])==c])**2) for c in range(n+1)])
err=float(max(abs(distribution-prob(n,.13,np.array([theta]))[:,0])));checks['tensor_vs_Dicke_probability_error']=err;assert err<1e-12

angles=np.linspace(-np.pi,np.pi,1441);data['fig2_angles']=angles
for i,t in enumerate([0,np.pi/4,np.pi/2]):data[f'fig2_probability_{i}']=prob(15,t,angles)
checks['probability_normalization_error']=float(max(np.max(abs(data[f'fig2_probability_{i}'].sum(axis=0)-1)) for i in range(3)))

def posterior_widths(n,p,samples,grid=16385,counts=None):
    angles=np.linspace(0,np.pi,grid);P=prob(n,1/np.sqrt(n),angles)
    P0=prob(n,1/np.sqrt(n),np.array([np.pi/2]))[:,0];P0/=P0.sum()
    if counts is None:counts=rng.multinomial(p,P0,size=samples)
    logP=np.log(np.maximum(P,1e-300));widths=[]
    # Same source estimator: posterior maximum, symmetric 68% probability interval.
    for batch in np.array_split(counts,max(1,len(counts)//40)):
        lp=batch@logP;lp-=lp.max(axis=1,keepdims=True);post=np.exp(lp)
        cdf=cumulative_trapezoid(post,angles,axis=1,initial=0);cdf/=cdf[:,-1,None]
        modes=np.argmax(post,axis=1)
        for row,mode in zip(cdf,modes):
            k=np.arange(max(mode,grid-1-mode)+1)
            mass=row[np.minimum(mode+k,grid-1)]-row[np.maximum(mode-k,0)]
            ix=np.searchsorted(mass,.68);ix=max(1,min(ix,len(k)-1))
            frac=(.68-mass[ix-1])/(mass[ix]-mass[ix-1])
            widths.append((ix-1+frac)*(angles[1]-angles[0]))
    return np.array(widths),counts

posterior_records=[];stored_counts=None
for nt in [200,400,800,1000,1600]:
    w,c=posterior_widths(nt//20,20,2000)
    posterior_records.append({'NT':nt,'N':nt//20,'p':20,'mean_68_halfwidth':float(w.mean()),'SE':float(w.std(ddof=1)/np.sqrt(len(w))),'source_8p9_over_NT':8.9/nt,'trials':len(w)})
    if nt==800:stored_counts=c[:100]
    print('Bayes main NT',nt,flush=True)
inset=[]
for nt in [200,400,800]:
 for p in [5,10,20,25,40,50]:
    widths,_=posterior_widths(nt//p,p,1000)
    inset.append({'NT':nt,'N':nt//p,'p':p,'mean_68_halfwidth':float(widths.mean()),'SE':float(widths.std(ddof=1)/np.sqrt(len(widths))),'trials':len(widths)})
for grid in [8193,16385,32769]:
    widths,_=posterior_widths(40,20,100,grid=grid,counts=stored_counts)
    data[f'posterior_grid{grid}_widths']=widths
checks['posterior_grid_refinement_max_change']=float(max(abs(data['posterior_grid32769_widths']-data['posterior_grid16385_widths'])))
checks['posterior_main']=posterior_records;checks['posterior_inset']=inset
checks['posterior_estimator']='Uniform prior [0,pi], source twisting tau=1/sqrt(N), true theta=pi/2; maximum-posterior mode and symmetric 68% interval halfwidth. Numerical trials independently seeded. Compare this with original interval convention before attributing any constant-factor mismatch.'
checks['original_squeezing_scope']='Fixed-axis xi>=1 differs from optimized-axis xi. QFI gives local/asymptotic achievable sensitivity with a suitable measurement, not a guarantee for every finite-shot estimator.'
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
