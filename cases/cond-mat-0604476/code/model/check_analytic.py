"""Distinct finite-Hilbert-space checks of original algebra and conventions."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np,json
from itertools import combinations
from pathlib import Path
from hcb import free_modes,initial_box,occupations
r={}
for N in [2,3]:
 L=8;states=list(combinations(range(L),N));idx={s:i for i,s in enumerate(states)};D=len(states)
 def op(i,j,fermion):
  A=np.zeros((D,D))
  for a,s in enumerate(states):
   if j not in s:continue
   if i==j:A[a,a]=1;continue
   if i in s:continue
   target=tuple(sorted((set(s)-{j})|{i}));sgn=(-1)**sum(min(i,j)<k<max(i,j) for k in s) if fermion else 1
   A[idx[target],a]=sgn
  return A
 H=np.zeros((D,D));T2=np.zeros((D,D)); ns=[op(i,i,False) for i in range(L)]
 for i in range(L):
  v=op(i,(i+1)%L,False); H-=v+v.T
  v=op(i,(i+2)%L,False)@(np.eye(D)-2*ns[(i+1)%L]);T2+=v+v.T
 q=2*np.pi*(np.arange(L)+(0.5 if N%2==0 else 0))/L
 lhs=np.zeros((D,D),complex); wrong=np.zeros_like(lhs);conserve=0.
 for k in range(L):
  nq=sum(np.exp(1j*q[k]*(i-j))*op(i,j,True)/L for i in range(L) for j in range(L))
  lhs+=(1-np.cos(q[k]))**2*nq
  wrong+=(1-np.cos(2*np.pi*k/L))**2*nq
  conserve=max(conserve,float(np.max(abs(H@nq-nq@H))))
 rhs=1.5*N*np.eye(D)+H+.25*T2
 r['periodic_N'+str(N)]={'I4_matrix_max_error':float(np.max(abs(lhs-rhs))), 'unshifted_weight_max_error':float(np.max(abs(wrong-rhs))), 'mode_commutator_max':conserve}
# Canonical anticommutation: explicit matrices on full 2^3 Fock basis.
L=3;D=2**L;c=[]
for i in range(L):
 A=np.zeros((D,D))
 for s in range(D):
  if s>>i&1:A[s^(1<<i),s]=(-1)**((s&((1<<i)-1)).bit_count())
 c.append(A)
r['CAR_offsite_max']=float(np.max(abs(c[0]@c[1].T+c[1].T@c[0])))
r['printed_CAR_offsite_difference_from_identity']=float(np.max(abs(c[0]@c[1].T+c[1].T@c[0]-np.eye(D))))
r['CAR_onsite_error']=float(np.max(abs(c[0]@c[0].T+c[0].T@c[0]-np.eye(D))))
# Explicit product partition function for an arbitrary finite mode list.
lam=np.array([-2.1,-.4,.3,1.7]);w=[];bits=[]
for s in range(16):
 b=np.array([(s>>i)&1 for i in range(4)]); bits.append(b);w.append(np.exp(-lam@b))
w=np.array(w);bits=np.array(bits)
r['Z_factorization_error']=float(abs(w.sum()-np.prod(1+np.exp(-lam))))
r['gge_occupations_error']=float(np.max(abs((w@bits)/w.sum()-1/(1+np.exp(lam)))))
# Same original box state: extra conserved products are not fixed by occupation means.
e,U=free_modes(600);n,Q=occupations(U,initial_box(600,30,150));M=Q@Q.T;cov=-M*M;np.fill_diagonal(cov,0)
a,b=np.unravel_index(np.argmin(cov),cov.shape)
r['original_box_nonlocal_limit']={'modes_1based':[int(a+1),int(b+1)], 'actual_connected_mode_covariance':float(cov[a,b]),'gge_connected_mode_covariance':0., 'actual_total_number_variance':0.,'gge_total_number_variance':float(np.sum(n*(1-n))), 'meaning':'Finite-system GGE is not identical to the full diagonal ensemble for every nonlocal observable; this does not refute the plotted momentum-distribution approximation.'}
Path('checks/analytic_checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
