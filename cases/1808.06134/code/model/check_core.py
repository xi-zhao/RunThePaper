"""Dense-state oracle uses explicit Kronecker gates/Born probabilities, not tableau logic."""
import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'scratch/mpl')
os.environ['NUMBA_CACHE_DIR']=str(Path.cwd()/'scratch/numba')
import json,numpy as np
from scipy.integrate import quad
from clifford_core import clifford_group,trace_circuit

def local(psi,U,q,L):
    a=psi.reshape(2**q,4,2**(L-q-2))
    return np.einsum('ij,ajb->aib',U,a,optimize=False).reshape(-1)

def dense_measure(psi,q,L,kind,rng):
    ind=np.arange(2**L);b0=(ind>>(L-1-q))&1;b1=(ind>>(L-2-q))&1
    labels=2*b0+b1 if kind==1 else b0^b1
    probs=np.bincount(labels,weights=np.abs(psi)**2,minlength=4 if kind==1 else 2)
    result=rng.choice(len(probs),p=probs/probs.sum())
    return np.where(labels==result,psi,0)/np.sqrt(probs[result])

def dense_entropy(psi,a,L):
    mat=psi.reshape(2**a,-1);rho=mat@mat.conj().T
    return -np.log2(np.trace(rho@rho).real)

def run_checks():
    group,words=clifford_group();I=np.eye(2);X=np.array([[0,1],[1,0]],complex);Z=np.diag([1,-1]);H=(X+Z)/np.sqrt(2);S=np.diag([1,1j])
    CX=np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]],complex)
    ops=[np.kron(H,I),np.kron(I,H),np.kron(S,I),np.kron(I,S),CX]
    us=[]
    for word in words:
        u=np.eye(4,dtype=complex)
        for k in word:u=ops[k]@u
        us.append(u)
    paul=[np.kron(X,I),np.kron(Z,I),np.kron(I,X),np.kron(I,Z)]
    max_conj=0.0;max_unit=0.0
    for u,m in zip(us,group):
        max_unit=max(max_unit,float(np.max(abs(u@u.conj().T-np.eye(4)))))
        for j in range(4):
            p=np.eye(4,dtype=complex)
            for b in range(4):
                if (int(m[j])>>b)&1:p=p@paul[b]
            a=u@paul[j]@u.conj().T;phase=np.trace(p.conj().T@a)/4
            max_conj=max(max_conj,float(np.max(abs(a-phase*p))))
    rng=np.random.default_rng(730812);groups=[]
    for L in [4,6,8]:
        for typ in [0,1,2]:
            maxerr=0.0;maxnorm=0.0;count=0
            for trial in range(12):
                qs=rng.integers(0,L-1,50,dtype=np.int64);ids=rng.integers(0,720,50,dtype=np.int64)
                ms=np.where(rng.random(50)<.7,typ,0).astype(np.int64)
                got,state=trace_circuit(L,qs,ids,ms,group)
                psi=np.ones(2**L,dtype=complex)/np.sqrt(2**L)
                for t,(q,j,m) in enumerate(zip(qs,ids,ms)):
                    if m:psi=dense_measure(psi,int(q),L,int(m),rng)
                    psi=local(psi,us[j],int(q),L)
                    maxnorm=max(maxnorm,abs(float(np.vdot(psi,psi).real)-1))
                    for a in range(1,L):maxerr=max(maxerr,abs(dense_entropy(psi,a,L)-got[t,a-1]));count+=1
            groups.append({'L':L,'measurement':typ,'comparisons':count,'max_entropy_error_bits':maxerr,'max_norm_error':maxnorm})
    literal=.5*(np.eye(4)+np.kron(Z,I))+(np.eye(4)-np.kron(Z,I))@np.kron(I,X)
    corrected=.5*((np.eye(4)+np.kron(Z,I))+(np.eye(4)-np.kron(Z,I))@np.kron(I,X))
    haar_nats=np.pi/2-4/3;integral=quad(lambda x:3*x*x*(-np.log2((1+x*x)/2)),0,1,epsabs=1e-13)[0]
    r={'group_order_mod_pauli':len(group),'max_all_gate_unitarity_error':max_unit,'max_all_gate_conjugation_error':max_conj,'dense_oracle':groups,'literal_CNOT_UdagU_eigenvalues':np.linalg.eigvalsh(literal.conj().T@literal).tolist(),'corrected_CNOT_unitarity_error':float(np.max(abs(corrected.conj().T@corrected-np.eye(4)))),'haar_twoqubit_mean_S2_bits_closed':float(haar_nats/np.log(2)),'haar_twoqubit_mean_S2_bits_quadrature':float(integral),'tolerance':{'entropy_bits':1e-10,'norm':1e-11,'gate_matrix':1e-12},'method':'All 720 Clifford symplectic actions checked against explicit dense H,S,CNOT unitaries; 108 random circuits checked after every gate and each bipartition; Born outcomes sampled explicitly.'}
    r['passed']=bool(max(max(x['max_entropy_error_bits'] for x in groups),max_conj,max_unit)<1e-10)
    return r
if __name__=='__main__':
    r=run_checks();Path('checks/core-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
