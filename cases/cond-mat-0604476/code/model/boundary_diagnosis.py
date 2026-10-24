import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np,json,time
from hcb import *
r={}; data={}; L=600;N=30;P=initial_box(L,N,150);x=np.arange(1,L+1)
for shift in [0.,.5]:
 q=2*np.pi*(np.arange(L)+shift)/L;W=np.exp(1j*np.outer(x,q))/np.sqrt(L)
 n=np.sum(abs(W.conj().T@P)**2,axis=1);C=((W*n)@W.conj().T).real
 R=gaussian_real_rho(C,160); f=momentum(R)
 # translational ring bosonic reconstruction: restore wrap correlations by shortest string.
 rr=R[0,:241]; k=np.arange(-300,300)
 fperiod=rr[0]+2*np.cos(2*np.pi*np.outer(k,np.arange(1,241))/L)@rr[1:]
 r[str(shift)]={'n_max':float(max(n)),'open_string_f0':float(f[300]),'ring_string_f0':float(fperiod[300]),'open_string_f50':float(f[350]),'ring_string_f50':float(fperiod[350]),'imaginary_C_max':float(np.max(abs(((W*n)@W.conj().T).imag)))}
 data['plane_shift'+str(shift)+'_openstring']=f;data['plane_shift'+str(shift)+'_ringstring']=fperiod
# Pair-average OBC occupations is a transparent counterfactual, not a source prescription.
e,U=free_modes(L);n,Q=occupations(U,P);nav=(n[::2]+n[1::2])/2;nav=np.repeat(nav,2);R=gaussian_real_rho((U*nav)@U.T,160);f=momentum(R)
r['paired_OBC']={'f0':float(f[300]),'f50':float(f[350])};data['paired_OBC']=f
np.savez_compressed('results/boundary_diagnosis.npz',**data);Path('checks/boundary_diagnosis.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
