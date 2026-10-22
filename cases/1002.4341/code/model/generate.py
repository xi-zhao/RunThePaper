"""Actual master-equation parameter scans and time correlations, independent Fock code."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import brentq
from scipy.sparse.linalg import expm_multiply
from model import Model,gaussian
from threadpoolctl import threadpool_limits
threadpool_limits(1)
data={};checks={};convergence=[]

def steady(m,E,F,Gamma,cut=8,dephasing=0,cross_factor=4):
    a=Model(m,cut,E,F,Gamma,dephasing=dephasing,cross_factor=cross_factor);r=a.steady();return a,r

grid2=np.linspace(-.2,.2,31);heat2=[];top2=[]
for E2 in grid2:
    vals=[];tops=[]
    for E1 in grid2:
        _,r=steady(2,[E1,E2],.1,.2,cut=8);vals.append(r['g2'][0]);tops.append(r['top_probability'])
    heat2.append(vals);top2.append(tops)
data['fig1_E']=grid2;data['fig1_heat_g2']=np.array(heat2);data['fig1_heat_top_probability']=np.array(top2)
print('two-mode grid complete',flush=True)

# Fig1b holds the detuning to the symmetric eigenmode fixed, not bare E1.
vary=np.linspace(-.2,.2,161);rows=[];bareE1=.07;reference_low=np.linalg.eigvalsh([[.07,-.5],[-.5,.05]])[0]
for E2 in vary:
    pump_shift=np.linalg.eigvalsh([[bareE1,-.5],[-.5,E2]])[0]-reference_low
    _,r=steady(2,[bareE1-pump_shift,E2-pump_shift],.1,.2)
    rows.append(np.r_[r['n'],r['g2']])
data['fig1b_E2']=vary;data['fig1b_observables']=np.array(rows)

for cut in [6,8,10]:
    a,r=steady(2,[.07,.05],.1,.2,cut);convergence.append({'model':'two','cut':cut,'g2':r['g2'][0],'n1':r['n'][0],'top':r['top_probability']})
    if cut==10:
        times=np.linspace(0,25,1001);data['fig1c_time_positive_ps']=times
        for i,j in [(0,0),(1,1),(0,1),(1,0)]:data[f'fig1c_g{i+1}{j+1}']=a.correlations(i,j,times)
        # A distinct time propagation from the vacuum checks the steady-state solve.
        vacuum=np.zeros(len(a.ii));vacuum[a.lookup[0,0]]=1
        propagated=expm_multiply(a.L*500,vacuum)
        checks['two_mode_stationary_vs_time_propagation']=float(np.max(abs(propagated-a.rho)))
        assert checks['two_mode_stationary_vs_time_propagation']<1e-9

grid3=np.linspace(-.3,.3,25);heat3=[];top3=[]
for E3 in grid3:
    vals=[];tops=[]
    for E2 in grid3:
        _,r=steady(3,[0,E2,E3],.1,.1,cut=8);vals.append(r['g2'][0]);tops.append(r['top_probability'])
    heat3.append(vals);top3.append(tops)
data['fig3_E']=grid3;data['fig3_heat_g2']=np.array(heat3);data['fig3_heat_top_probability']=np.array(top3)
print('three-mode grid complete',flush=True)

for cut in [4,6,8,10]:
    a,r=steady(3,[0,.12,0],.1,.1,cut);convergence.append({'model':'three','cut':cut,'g2':r['g2'][0],'n1':r['n'][0],'top':r['top_probability']})
    if cut==10:
        times=np.linspace(0,60,1201);data['fig3c_time_positive_ps']=times;data['fig3c_g11']=a.correlations(0,0,times)
        checks['three_mode_original_parameter_g2']=float(r['g2'][0])
        checks['three_mode_original_parameter_n1']=float(r['n'][0])

# Fixed-number manifolds of the actual three-mode Hamiltonian, no drive.
a,_=steady(3,[0,.12,0],0,.1,cut=4);H=a.H.toarray()
for total in [1,2,3]:
    mask=a.basis.sum(axis=1)==total;e,v=np.linalg.eigh(H[np.ix_(mask,mask)])
    data[f'fig2_N{total}_energy']=e;data[f'fig2_N{total}_eigenvectors']=v;data[f'fig2_N{total}_basis']=a.basis[mask]

n=np.geomspace(1e-4,1,121);gauss=np.array([gaussian(z) for z in n]);single=np.array([gaussian(z,J=0) for z in n])
data['fig1d_target_n1']=n;data['fig1d_gaussian_g2']=gauss[:,0];data['fig1d_single_gaussian_g2']=single[:,0]
checks['gaussian_stability_max_real_eigenvalue']=float(max(gauss[:,1]))
checks['Gaussian_comparison_status']='Literal supplied mean-field detunings E1=.07,E2=.05; negative weak-drive linearized g2 requires investigating source detuning/approximation before using Fig1d as agreement evidence. Exact master-equation correlations remain separate.'

# Drive scan covers occupation rather than using occupation as an independent Hamiltonian input.
scan=[]
for modes,E,G in [(1,[0],.1),(2,[.07,.05],.2),(3,[0,.12,0],.1)]:
    for dep in [0,.0003]:
        for F in np.geomspace(.006,.5,21):
            cut=10 if modes<3 else 8
            _,r=steady(modes,E,F,G,cut,dephasing=dep)
            scan.append({'modes':modes,'dephasing_meV':dep,'F_meV':float(F),'cut':cut,'n1':float(r['n'][0]),'g2':float(r['g2'][0]),'top_probability':r['top_probability']})
    print('occupation scan completed modes=',modes,flush=True)
checks['occupation_scan']=scan
checks['cutoff_convergence']=convergence
checks['unconverged_grid_requires_followup']={'two_max_top_probability':float(np.max(top2)),'three_max_top_probability':float(np.max(top3)),
 'criterion':'Retain top-population diagnostics and compare larger cutoffs; no unconverged region is silently counted complete.'}
checks['three_mode_convention_control']={}
for factor in [2.,4.]:
    _,r=steady(3,[0,.12,0],.1,.1,10,cross_factor=factor);checks['three_mode_convention_control'][str(factor)]=float(r['g2'][0])
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
