"""Checks of all four original finite-dimensional examples, not a theorem prover."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import expm,eigh,svdvals
from scipy.integrate import solve_ivp
from threadpoolctl import threadpool_limits
threadpool_limits(1)
t=np.linspace(0,10,2001); omega=1.; data={'time':t};checks={}
def evol(h,t,psi):
    e,v=eigh(h);return (v@(np.exp(-1j*e[:,None]*t)*(v.conj().T@psi)[:,None])).T

errors=[]
for k in [0,1,3,10,30,100]:
    h=np.array([[0,omega,0],[omega,0,k],[0,k,0.]])
    psi=evol(h,t,np.eye(3)[0]); p=abs(psi[:,0])**2
    exact=(k*k+omega*omega*np.cos(np.sqrt(k*k+omega*omega)*t))**2/(k*k+omega*omega)**2
    errors.append(float(max(abs(p-exact))));data[f'ex1_K{k}']=p
assert max(errors)<1e-11
checks['three_level_formula_max_error']=max(errors)

errors=[]
for kp in [0,10,100,1000]:
    k=10;h=np.array([[0,1,0,0],[1,0,k,0],[0,k,0,kp],[0,0,kp,0.]])
    psi=evol(h,t,np.eye(4)[0]);data[f'ex2_Kprime{kp}']=abs(psi[:,0])**2
    errors.append(float(max(abs(abs(psi[:,0])**2-np.cos(t)**2))))
checks['four_level_restoration_max_errors_vs_Kprime']=errors
assert errors[-1]<.002

cavity=[]
for photons in [2,3,4]:
    b=np.diag(np.sqrt(np.arange(1,photons+1)),1);id3=np.eye(3);a21=np.zeros((3,3));a21[2,1]=1
    interaction=np.kron(b,np.kron(a21,id3)+np.kron(id3,a21))
    h=1j*(interaction-interaction.conj().T)-1j*np.kron(b.T@b,np.eye(9))
    D=np.zeros(((photons+1)*9,5));D[0,0]=D[1,1]=D[3,2]=D[4,3]=1;D[7,4]=1/np.sqrt(2);D[5,4]=-1/np.sqrt(2)
    residual=np.linalg.norm(h@D);nullity=int(np.sum(svdvals(h)<1e-11))
    cavity.append({'photon_cutoff':photons,'nullity':nullity,'dark_basis_residual':float(residual)})
    assert nullity==5 and residual<1e-12
checks['cavity_dark_subspace']=cavity

# Original spontaneous-emission effective Hamiltonian, scaled tau_Z=1.
gamma=.1;decay=2/gamma
for k in [0,2,10,100]:
    h=np.array([[0,1,0],[1,-1j*decay,k],[0,k,0]],complex)
    psi=np.array([expm(-1j*h*u)@np.eye(3)[0] for u in t])
    data[f'ex4_K{k}']=abs(psi[:,0])**2
    # The dissipative fast mode can become too small to control an explicit
    # solver's step size, then recur through its stability error. Resolve that
    # timescale explicitly; do not weaken the failed comparison tolerance.
    ode=solve_ivp(lambda u,p:-1j*h@p,(0,t[-1]),np.array([1+0j,0j,0j]),t_eval=t,method='DOP853',rtol=1e-11,atol=1e-13,max_step=.02)
    err=float(np.max(abs(ode.y.T-psi)));assert err<1e-9
    checks[f'emission_K{k}_exp_vs_ODE_error']=err
checks['vacuum_strict_frequency_threshold_per_second']=1/(1e-29*1e9)

# General finite-dimensional projection statement: repeated projections vs projected H,
# and strong coupling vs its K-dependent block diagonal approximation.
rng=np.random.default_rng(20261021);a=rng.normal(size=(5,5))+1j*rng.normal(size=(5,5));h=(a+a.conj().T)/5
hm=np.diag([0,0,1,1,3]);ps=[np.diag(np.array([0,0,1,1,3])==n).astype(float) for n in [0,1,3]]
hd=sum(p@h@p for p in ps)
strong=[];projection=[]
for k in [32,64,128,256,512]:
    er=max(np.linalg.norm(expm(-1j*(h+k*hm)*u)-expm(-1j*(hd+k*hm)*u),2) for u in np.linspace(0,2,81))
    strong.append({'K':k,'max_observed_operator_error':float(er)})
for n in [10,30,100,300,1000]:
    a=sum(p@expm(-1j*h/n)@p for p in ps)
    er=np.linalg.norm(np.linalg.matrix_power(a,n)-expm(-1j*hd),2);projection.append({'N':n,'operator_error':float(er)})
checks['strong_coupling']=strong;checks['repeated_projection']=projection
assert strong[-1]['max_observed_operator_error']<strong[0]['max_observed_operator_error']/8
assert projection[-1]['operator_error']<projection[0]['operator_error']/50
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
