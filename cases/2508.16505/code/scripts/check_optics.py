"""Small exact-sector checks; fixed tolerances chosen before execution."""
import json
from pathlib import Path
import numpy as np
from optics import *

def main():
    rng = np.random.default_rng(16505)
    records = []
    for m,occ,ms,ns in [(3,(1,1,0),2,1),(4,(2,1,0,0),2,2),(5,(1,1,1,1,0),4,2)]:
        U = haar(m,rng)
        a,b = full_fft(U,occ),sparse_creation(U,occ)
        ss,aa,B = bipartite(U,occ,ms,ns)
        errors = {'fft_vs_creation':max(abs(a[v]-b[v]) for v in a),
                  'fft_vs_permanent':max(abs(a[v]-permanent_amplitude(U,occ,v)) for v in a),
                  'sector_vs_full':max(abs(B[i,j]-a[s+t]) for i,s in enumerate(ss) for j,t in enumerate(aa)),
                  'normalization':abs(sum(abs(x)**2 for x in a.values())-1)}
        assert max(errors.values()) < 1e-11,errors
        records.append({'m':m,'occupation':occ,'errors':errors})
    U = bell_reference()
    a = full_fft(U,(1,1,1,1,0))
    herald = {v:amp for v,amp in a.items() if v[-1]==2}
    p = sum(abs(x)**2 for x in herald.values())
    overlap = (herald[(1,0,1,0,2)]-herald[(0,1,0,1,2)])/np.sqrt(2)
    bell = {'probability':p,'fidelity':abs(overlap)**2/p,
            'unitarity_error':float(np.max(abs(U.conj().T@U-np.eye(5)))),
            'probability_error':abs(p-1/9),
            'permanent_error':max(abs(a[v]-permanent_amplitude(U,(1,1,1,1,0),v)) for v in a)}
    assert bell['probability_error'] < 1e-12 and abs(bell['fidelity']-1)<1e-12
    # Exact optical counterexample: one photon, two modes; signal sector amplitude cos(theta).
    # Normalised sector angle is identically zero; sector probability is cos(theta)^2.
    counter = []
    for theta in [np.pi/6,np.pi/3]:
        p = np.cos(theta)**2
        counter.append({'theta':float(theta),'sector_probability':float(p),'projected_bures_angle':0.,
                        'unprojected_bures_angle':float(np.arccos(np.sqrt(p)))})
    data = {'precision':'complex128','tolerance':1e-11,'random_checks':records,'bell_reference_check':bell,
            'sparsification_counterexample':counter,
            'loss_sign_counterexample':{'target_angle':0.,'orthogonal_angle':float(np.pi/2),
             'printed_loss_target':0.,'printed_loss_orthogonal':float(-np.pi/2)}}
    Path('results').mkdir(exist_ok=True)
    Path('results/optics_checks.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(data))

if __name__=='__main__': main()
