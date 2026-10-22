"""Full driven quartic double well of Grossmann et al. (not a two-level replacement)."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigh,eigh_tridiagonal,eig
from scipy.integrate import solve_ivp,simpson
from scipy.signal import find_peaks
from threadpoolctl import threadpool_limits
threadpool_limits(1)
D=2.;x=np.linspace(-13,13,5201);dx=x[1]-x[0];wb=.5

def static(n):
    # Extra rows retain all virtual oscillator paths in projected x^4.
    xx=np.diag(np.sqrt(np.arange(1,n+8)/(2*wb)),1);xx+=xx.T
    x2=xx@xx;x4=x2@x2
    h=np.diag(wb*(np.arange(n+8)+.5))-(wb*wb/2+.25)*x2+x4/(64*D)
    e,v=eigh(h[:n,:n]);return e,v,xx[:n,:n]
e0,v0,xx0=static(120);e,v,xx=static(160)
checks={'oscillator_basis_low8_error':float(max(abs(e[:8]-e0[:8])))}
assert checks['oscillator_basis_low8_error']<1e-9
fd=[]
for step in [.02,.01,.005]:
    gx=np.arange(-13+step,13,step);potential=-gx*gx/4+gx**4/(64*D)
    fd.append(eigh_tridiagonal(1/step**2+potential,np.full(len(gx)-1,-.5/step**2),select='i',select_range=(0,7))[0])
rich=(4*fd[-1]-fd[-2])/3
checks['finite_difference_Richardson_low8_error']=float(max(abs(rich-e[:8])))
assert checks['finite_difference_Richardson_low8_error']<1e-7
checks['unperturbed_ground_energy']=float(e[0]);checks['tunnel_splitting']=float(e[1]-e[0]);wr=e[2]-e[1]
checks['fundamental_resonance_frequency']=float(wr)
phi=np.empty((len(x),160));phi[:,0]=(wb/np.pi)**.25*np.exp(-wb*x*x/2);phi[:,1]=np.sqrt(2*wb)*x*phi[:,0]
for n in range(1,159):phi[:,n+1]=np.sqrt(2*wb/(n+1))*x*phi[:,n]-np.sqrt(n/(n+1))*phi[:,n-1]
wave=phi@v[:,:40]
initial=np.pi**(-.25)*np.exp(-(x+np.sqrt(8*D))**2/2)
coeff=simpson(wave*initial[:,None],x=x,axis=0)
left=simpson(wave[x<=0,:,None]*wave[x<=0,None,:],x=x[x<=0],axis=0)

def period(S,w,levels,tol=2e-11):
    E=e[:levels];X=v[:,:levels].T@xx@v[:,:levels];T=2*np.pi/w
    # Subtract a scalar energy to avoid irrelevant rapid global phases.
    shift=E[0];HH=np.diag(E-shift)
    def rhs(t,y):
        U=y.reshape(levels,levels)
        return (-1j*(HH@U+S*np.sin(w*t)*(X@U))).ravel()
    sol=solve_ivp(rhs,(0,T),np.eye(levels,dtype=complex).ravel(),method='DOP853',rtol=tol,atol=tol/100)
    if not sol.success:raise RuntimeError(sol.message)
    U=sol.y[:,-1].reshape(levels,levels)
    unitarity=np.linalg.norm(U.conj().T@U-np.eye(levels),2)
    values,V=eig(U);phase=np.angle(values);c=np.linalg.solve(V,coeff[:levels])
    return phase,V,c,T,unitarity

def states(sol,ns):
    phase,V,c,T,_=sol
    return (V@(c[:,None]*np.exp(1j*phase[:,None]*np.asarray(ns)))).T

data={'x':x,'initial_density':initial**2,'unperturbed_energies':e[:40]}
N=np.arange(200001);probe=np.arange(0,200001,100)
curves=[]
for levels in [24,32]:
    sol=period(1e-4,wr,levels,tol=2e-12)
    psi=states(sol,probe);curves.append(abs(psi@coeff[:levels])**2)
    checks[f'resonance_U_unitarity_{levels}']=float(sol[-1])
    if levels==32:
        psi=states(sol,N);P=abs(psi@coeff[:levels])**2
        data['fig1_n']=N;data['fig1_survival']=P
        # Original ordinate is arbitrary, retain the measured frequency scale.
        spectrum=abs(np.fft.rfft(P-P.mean()))**2
        data['fig1_frequency']=2*np.pi*np.fft.rfftfreq(len(N),d=sol[3]);data['fig1_spectrum']=spectrum
        nfp=np.arange(3);weights=np.sum(abs(sol[1][:3,:])**2,axis=0);ii=np.argsort(weights)[-3:]
        quasi=-sol[0][ii]/sol[3]+e[0];quasi+=np.round((e[0]-quasi)/wr)*wr
        data['fig1_relevant_quasienergies']=quasi
checks['resonant_long_time_24_vs32_max_survival_difference']=float(max(abs(curves[0]-curves[1])))
assert checks['resonant_long_time_24_vs32_max_survival_difference']<.01
Svalues=np.linspace(0,.001,11);bands=[]
for S in Svalues:
    sol=period(S,wr,24);weights=np.sum(abs(sol[1][:3,:])**2,axis=0);ii=np.argsort(weights)[-3:]
    quasi=-sol[0][ii]/sol[3]+e[0];quasi+=np.round((e[0]-quasi)/wr)*wr;bands.append(np.sort(quasi))
data['fig1_S']=Svalues;data['fig1_bands']=np.array(bands)

N2=np.arange(1025);allP=[];allLeft=[]
for levels in [24,32,40]:
    sol=period(.003171,.01,levels,tol=2e-12)
    psi=states(sol,N2);survival=abs(psi@coeff[:levels])**2
    pleft=np.einsum('ni,ij,nj->n',psi.conj(),left[:levels,:levels],psi).real
    allP.append(survival);allLeft.append(pleft)
    checks[f'CDT_unitarity_{levels}']=float(sol[-1])
    checks[f'initial_weight_retained_{levels}']=float(sum(abs(coeff[:levels])**2))
    if levels==40:
        data['fig2_n']=N2;data['fig2_survival']=survival;data['fig2_left_probability']=pleft
        data['fig2_n458_density']=abs(wave[:,:levels]@psi[458])**2
    print('CDT completed oscillator eigenstates:',levels,flush=True)
checks['CDT_32_vs40_survival_max_difference']=float(max(abs(allP[-1]-allP[-2])))
checks['CDT_32_vs40_left_max_difference']=float(max(abs(allLeft[-1]-allLeft[-2])))
assert checks['CDT_32_vs40_survival_max_difference']<.005
assert checks['CDT_32_vs40_left_max_difference']<.005
checks['CDT_min_survival']=float(min(allP[-1]));checks['CDT_min_left_probability']=float(min(allLeft[-1]))
checks['input_condition']='D=2; Gaussian harmonic ground state in left well; Fig1 omega=E3-E2,S=1e-4; Fig2 omega=.01,S=.003171 from caption. Rounded source S=.00317 is not silently substituted.'
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
