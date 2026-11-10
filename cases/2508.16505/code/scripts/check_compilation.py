"""Matrix checks of Appendix C and discriminating loss controls."""
import json
from pathlib import Path
import numpy as np
from optics import sparse_creation,haar

def bs(m,i,j,t,pt,pr):
    u=np.eye(m,dtype=complex)
    u[np.ix_([i,j],[i,j])]=[[np.exp(1j*pt)*np.cos(t),-np.exp(-1j*pr)*np.sin(t)],
                           [np.exp(1j*pr)*np.sin(t),np.exp(-1j*pt)*np.cos(t)]]
    return u

def main():
    rng=np.random.default_rng(16506);errors=[]
    s=np.eye(3,dtype=complex)[[1,0,2]]
    p=np.diag([-1,1,1])
    errors.append(np.max(abs(bs(3,0,1,np.pi/2,0,0)-p@s)))
    for _ in range(12):
        t,pt,pr=rng.uniform(-np.pi,np.pi,3)
        u=bs(3,1,2,t,pt,pr)
        errors.extend([np.max(abs(u.conj().T@u-np.eye(3))),
                       np.max(abs(s@u-bs(3,0,2,t,pt,pr)@s))])
        phases=rng.uniform(-np.pi,np.pi,3);v=haar(3,rng);occ=(2,1,0)
        a=sparse_creation(v@np.diag(np.exp(1j*phases)),occ)
        b=sparse_creation(v,occ);global_phase=np.exp(1j*np.dot(phases,occ))
        errors.append(max(abs(a[k]-global_phase*b[k]) for k in a))
        a=sparse_creation(v@s,occ);b=sparse_creation(v,(1,2,0))
        errors.append(max(abs(a[k]-b[k]) for k in a))
    assert max(errors)<1e-12
    # Positive controls: norm-preserving projected state equality fixes probabilities;
    # normalized direction alone cannot. Literal unprojected loss at f1 is nonzero.
    vectors=[np.array([np.sqrt(p),np.sqrt(1-p)]) for p in (.75,.25)]
    direction_overlap=abs(np.vdot(vectors[0][:1],vectors[1][:1]))/np.prod([np.linalg.norm(v[:1]) for v in vectors])
    data={'tolerance':1e-12,'matrix_and_fock_max_error':float(max(errors)),
          'number_of_matrix_and_fock_checks':len(errors),
          'projected_normalized_overlap':float(direction_overlap),
          'sector_probabilities':[float(v[0]**2) for v in vectors],
          'literal_initial_bures_angle':float(np.arccos(vectors[0][0])),
          'unnormalized_projected_distance':float(abs(vectors[0][0]-vectors[1][0])),
          'unchanged_state_control_distance':0.0,
          'decreasing_reward_control':{'target_loss':-1.,'orthogonal_loss':float(-(1-np.pi/2)**3)}}
    Path('results/compilation_checks.json').write_text(json.dumps(data,indent=2));print(json.dumps(data))

if __name__=='__main__':main()
