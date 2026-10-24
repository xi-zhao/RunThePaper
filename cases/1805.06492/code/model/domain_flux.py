"""Further conditioning repair: distribute cyclic nonreciprocity over every bond.
Uses only original model parameters. Existing arrays are read solely after generation
for error diagnostics against the already computed high-precision roots.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
import sys,json
from pathlib import Path
import numpy as np
import scipy.linalg as la
from diagnose import ring,mat,gauge


def flux(u,l):
    if np.any(u==0) or np.any(l==0):return gauge(u,l)
    g=(np.log(u)-np.log(l)).mean()/2;s=np.exp((np.log(u)+np.log(l))/2)
    return s*np.exp(g),s*np.exp(-g)


def main():
    td=np.linspace(-3,3,241);arrays={'t':td}
    for odd in [False,True]:
        for ratio in [6.,3.3,1.]:
            vals=[]
            for t in td:
                u,l=ring(25,25,t,ratio*.5,.5,odd);uf,lf=flux(u,l)
                vals.append(np.sort(abs(la.eigvals(mat(uf,lf)))))
            arrays[f'dw_{int(odd)}_{ratio}']=np.array(vals)
    np.savez_compressed('results/domain-flux.npz',**arrays)
    checks=[]
    for r in json.loads(Path('checks/ring-high-precision.json').read_text()):
        ix=int(np.argmin(abs(td-r['t1'])));key=f'dw_{int(r["odd"])}_{r["ratio"]}'
        reference=np.sort([abs(complex(float(z[0]),float(z[1]))) for z in r['roots_decimal']])
        checks.append({'odd':r['odd'],'ratio':r['ratio'],'t1':r['t1'],
                       'max_abs_error_vs_80_digit_polynomial_roots':float(max(abs(arrays[key][ix]-reference)))})
    # Source-ratio independent checks of pair and loop preservation, including Hermitian control.
    controls=[]
    for u,l in [(np.array([2,1,3,1],complex),np.array([2,1,3,1],complex)),ring(3,4,1.2,3.,.5,False)]:
        uf,lf=flux(u,l)
        controls.append({'pair_error':float(max(abs(uf*lf-u*l))),
                         'forward_loop_error':float(abs(np.prod(uf)-np.prod(u))),
                         'reverse_loop_error':float(abs(np.prod(lf)-np.prod(l)))})
    Path('checks/domain-flux-checks.json').write_text(json.dumps({'high_precision_comparisons':checks,'controls':controls},indent=2)+'\n')
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
