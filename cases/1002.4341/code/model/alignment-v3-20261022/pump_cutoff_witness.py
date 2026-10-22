"""Independent tensor operators with explicit unequal occupation cutoffs.
Tests whether small absolute boundary occupation can still bias normalized g2 at F->0.
Deliberately small cutoffs are diagnostics, not substitute converged physics.
"""
from pathlib import Path
import numpy as np,json
from scipy.sparse import eye,diags,kron,csr_matrix
from scipy.sparse.linalg import splu,expm_multiply
from threadpoolctl import threadpool_limits
threadpool_limits(1)
def model(caps,F):
 sizes=[c+1 for c in caps];basis=np.array(list(np.ndindex(tuple(sizes))));d=len(basis);I=eye(d,format='csr');ops=[]
 for mode in range(3):
  a=csr_matrix([[1.]])
  for j,s in enumerate(sizes):a=kron(a,diags(np.sqrt(np.arange(1,s)),1,shape=(s,s)) if j==mode else eye(s),format='csr')
  ops.append(a)
 nums=[a.T@a for a in ops];H=csr_matrix((d,d),dtype=complex)
 for j in range(3):H+=[0,.12,0][j]*nums[j]+.012*(ops[j].T@ops[j].T@ops[j]@ops[j])
 for i in range(3):
  for j in range(i):H+=.048*(nums[i]@nums[j])
 pair=ops[0].T@ops[2].T@ops[1]@ops[1];H+=.024*(pair+pair.T)+F*(ops[1]+ops[1].T)
 L=-1j*(kron(I,H)-kron(H.T,I))
 for a,n in zip(ops,nums):L+=.1*(kron(a,a)-.5*kron(I,n)-.5*kron(n.T,I))
 q=basis[:,0]-basis[:,2];keep=np.flatnonzero((q[:,None]==q[None,:]).ravel(order='F'));L=L.tocsr()[keep][:,keep];trace=np.isin(keep,np.arange(d)*(d+1)).astype(float)
 return basis,ops,L,keep,trace
rows=[];times=np.linspace(0,100,201)
for caps in [(2,2,2),(2,3,2),(2,4,2),(3,4,3),(4,6,4)]:
 basis,ops,L0,keep,trace=model(caps,0.);_,_,LF,_,_=model(caps,1.);V=LF-L0;d=len(basis);diag=np.flatnonzero(trace);M=L0.tolil();M[0,:]=trace;lu=splu(M.tocsc());rho=np.zeros(len(keep),complex);rho[0]=1.;coeff=[]
 for k in range(1,9):
  rhs=-V@rho;rhs[0]=0.;rho=lu.solve(rhs);pop=rho[diag].real
  coeff.append([float(pop@basis[:,0]),float(pop@(basis[:,0]*(basis[:,0]-1)))])
 weak=coeff[7][1]/coeff[3][0]**2;finite=[];correlation=None
 for F in [.003,.01,.05,.1,.2,.4]:
  b,a,L,k,tr=model(caps,F);M=L.tolil();M[0,:]=tr;rhs=np.zeros(len(k),complex);rhs[0]=1.;r=splu(M.tocsc()).solve(rhs);pop=r[diag].real;n=pop@b[:,0];g=pop@(b[:,0]*(b[:,0]-1))/n**2
  boundary=np.any(b==np.array(caps),axis=1);res=float(np.max(abs(L@r)));assert res<1e-10
  finite.append(dict(F=F,n1=float(n),g2=float(g),any_boundary_probability=float(pop[boundary].sum()),pump_boundary_probability=float(pop[b[:,1]==caps[1]].sum()),residual=res))
  if F==.1:
   full=np.zeros(d*d,complex);full[k]=r;mat=full.reshape((d,d),order='F');condition=(a[0]@mat@a[0].T).ravel(order='F')[k]
   propagated=expm_multiply(L,condition,start=0,stop=100/.6582119569,num=len(times));correlation=(propagated[:,diag].real@b[:,0]/n**2).tolist()
 rows.append(dict(caps=list(caps),weak_drive_g2=float(weak),finite_drive=finite,g11_F0p1=correlation,pump3_state_present=caps[1]>=3,pump4_state_present=caps[1]>=4))
 print('caps',caps,'weak limit',weak,'g0F.1',finite[3]['g2'],flush=True)
Path('calculation/alignment-v3-20261022/pump_cutoff_witness.json').write_text(json.dumps(dict(rows=rows,time_ps=times.tolist(),derivation='Two signal photons require two pair-scattering events. In drive-order expansion factorial moment beginsF^8; intermediate pump states up to4 can contribute at that leading normalized order, even though their absolute probabilities vanish asF->0. A low occupation boundary probability alone is insufficient to bound g2 relative error.'),indent=2))
