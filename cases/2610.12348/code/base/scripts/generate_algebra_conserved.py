"""Independent finite-matrix identities and direct adjoint stationary solve.

The conserved quantities are obtained by a constrained linear solve, not the
paper's inverse-superoperator recurrence. The exact photon cutoff is explicit.
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.sparse import kron,eye,diags,csc_matrix,hstack
from scipy.sparse.linalg import spsolve
from generate_statics import basis,matrix,qbinom

def matter(L,N,stats):
    states=basis(L,N,stats)
    O=matrix(states,states,[(1,[(j+1,-1),(j,1)]) for j in range(L-1)],stats)
    P=matrix(states,states,[((j+1)*(L-j-1),[(j,-1),(j+1,1)]) for j in range(L-1)],stats)
    Q=matrix(states,states,[(math.sqrt((j+1)*(L-j-1)),[(j+1,-1),(j,1)]) for j in range(L-1)],stats)
    X=np.array([sum((j+1)*v for j,v in enumerate(n)) for n in states])
    Z=diags(2*X-N*(L+1))
    dst=basis(L,N-2,stats)
    K=matrix(states,dst,[((-1)**j*(.5 if j==L-1-j else 1),[(j,-1),(L-1-j,-1)]) for j in range((L+1)//2)],stats)
    return states,O,P,Q,X,Z,K

def norm(a):return float(np.max(np.abs(a.toarray()))) if a.shape[0] else 0.

def main():
    arrays={};checks=[]
    for L,N,stats in [(6,3,'fermion'),(5,3,'boson')]:
        states,O,P,Q,X,Z,K=matter(L,N,stats);C=2*P@O+.5*Z@Z-Z
        logg=np.array([sum(v*.5*(math.lgamma(j+1)+math.lgamma(L)-math.lgamma(L-j)) for j,v in enumerate(n)) for n in states]);g=np.exp(logg-logg.min())
        KD=K.T@K
        row={'statistics':stats,'L':L,'N':N,'dimension':len(states),'sl2_ZO':norm(Z@O-O@Z+2*O),'sl2_ZP':norm(Z@P-P@Z-2*P),'sl2_PO':norm(P@O-O@P-Z),'casimir_O':norm(C@O-O@C),'casimir_P':norm(C@P-P@C),'casimir_Odagger_nonzero':norm(C@O.T-O.T@C),'eta_O':norm(KD@O-O@KD),'eta_Odagger':norm(KD@O.T-O.T@KD),'similarity':norm(diags(g)@Q@diags(1/g)-O)}
        checks.append(row)
    # Original Fig.16: fermion N=3,L=6; keep photon states 0..3, display 0..2.
    L,N,stats=6,3,'fermion';states,O,P,Q,X,Z,K=matter(L,N,stats);dm=len(states)
    npht=4;a=diags(np.sqrt(np.arange(1,npht)),1,shape=(npht,npht)).tocsc();phot=a.T@a
    aa=kron(eye(dm),a,format='csc');nn=aa.T@aa
    H=5*nn-kron(O,a.T,format='csc')-kron(O.T,a,format='csc');D=H.shape[0];I=eye(D,format='csc')
    LL=-1j*(kron(I,H)-kron(H.T,I))+10*(kron(aa.conj(),aa)-.5*kron(I,nn)-.5*kron(nn.T,I))
    vectors=[]
    terms=[[(1,'111000')],[(1,'110010'),(-1,'101100')],[(1,'110001'),(-1,'101010'),(1,'011100')]]
    for ts in terms:
        v=np.zeros(D)
        for val,s in ts:v[states.index(tuple(map(int,s)))*npht]=val
        v/=np.linalg.norm(v);vectors.append(v)
    R=csc_matrix(np.column_stack([np.outer(u,v).reshape(-1,order='F') for u in vectors for v in vectors]))
    # (Ldagger + R Rdagger) C = R enforces Rdagger C = identity.
    A=(LL.conj().T+R@R.T).tocsc();C=spsolve(A,R.toarray())
    residual=float(np.max(np.abs(LL.conj().T@C)));dual=float(np.max(np.abs(R.T@C-np.eye(9))))
    Ksuper=-LL.conj().T+10*kron(aa.T,aa.T) # J(C)=Gamma a† C a; a is real.
    kres=float(np.max(np.abs(Ksuper@R)))
    for k in range(9):arrays['C'+str(k//3+1)+str(k%3+1)]=C[:,k].reshape(D,D,order='F')
    arrays['matter_occupations']=np.array(states);arrays['dark_vectors']=np.array(vectors)
    arrays['H']=H.toarray();arrays['jump']=math.sqrt(10)*aa.toarray()
    # Strong-symmetry projector for Np=1 is K+K-/2 for N=3,L=6.
    strong=kron(K.T@K/2,eye(npht)).toarray()
    charges={'L':L,'N':N,'photon_cutoff':3,'hilbert_dimension':D,'steady_operator_dimension':9,'stationary_residual_max':residual,'duality_residual_max':dual,'right_dark_residual_max':float(np.max(np.abs(LL@R))),'K_has_nonzero_nullspace_residual':kres,'C22_strong_projector_max_difference':float(np.max(np.abs(arrays['C22']-strong))),'C11_jump_commutator_max':float(np.max(np.abs(arrays['C11']@aa-aa@arrays['C11']))),'C33_jump_commutator_max':float(np.max(np.abs(arrays['C33']@aa-aa@arrays['C33'])))}
    counts=[]
    for N in range(1,17):
        cf=qbinom(2*N,N);counts.append({'N':N,'fermion_L':2*N,'boson_L':N+1,'matter_dimension':math.comb(2*N,N),'null_dimension':cf[N*N//2]})
    out=Path('outputs/data');out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'algebra-conserved.npz',**arrays)
    (out/'algebra-conserved.json').write_text(json.dumps({'algebra':checks,'conserved_quantities':charges,'qbinomial_sizes':counts,'source_formula_diagnostics':{'neumann_series_printed_start':1,'required_formal_start':0,'reason':'For K=K0+V, inverse starts with K0^-1. At V=0 the printed j>=1 sum is zero although the inverse is nonzero. This is a local formula issue, not a failure of the GKSL model.','K_inverse_limit':'The full K annihilates all nine vacuum dark operators. Its inverse needs a stated restricted range/gauge; finite excitation alone does not ensure invertibility.'}},indent=2)+'\n')

if __name__=='__main__':main()
