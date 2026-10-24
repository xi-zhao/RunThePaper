"""Arbitrary-precision original cyclic characteristic equation, no gauge assumption."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
from pathlib import Path
import json
import numpy as np
import mpmath as mp


def original_edges(t,ratio,odd):
    na=50-int(odd);nb=50
    u=[];l=[];h=mp.mpf('0.5');t3=h*ratio
    for j in range(na-1):u.append(t+mp.mpf('1.5') if j%2==0 else mp.mpf(1));l.append(t-mp.mpf('1.5') if j%2==0 else mp.mpf(1))
    u.append(h);l.append(h)
    for j in range(nb-1):u.append(t3 if j%2==0 else h);l.append(u[-1])
    u.append(h);l.append(h)
    return u,l


def determinant_and_derivative(z,products):
    p0,p1=mp.mpf(1),z;d0,d1=mp.mpf(0),mp.mpf(1)
    for q in products:
        p0,p1=p1,z*p1-q*p0
        d0,d1=d1,p0+z*d1-q*d0
    return p1,d1


def main():
    stable=np.load('results/domain-stable.npz'); raw=np.load('results/spectra.npz')
    # Calculate complex starting roots directly in a separately written cyclic gauge.
    import scipy.linalg as la
    records=[]
    with mp.workdps(80):
        for odd,ratio,target in [(False,6.,-1.425),(True,6.,-1.425),(False,1.,-1.575),(False,3.3,-1.225)]:
            ix=int(np.argmin(abs(stable['t']-target)));tv=float(stable['t'][ix]);t=mp.mpf(str(tv))
            u,l=original_edges(t,mp.mpf(str(ratio)),odd);q=[a*b for a,b in zip(u,l)];loops=mp.fprod(u)+mp.fprod(l)
            uv=np.array([complex(a) for a in u]);lv=np.array([complex(a) for a in l]);L=len(u)
            if sum(np.log(abs(uv)))>=sum(np.log(abs(lv))):
                c=np.exp(sum(np.log(uv))/L);u2=np.full(L,c);l2=uv*lv/c
            else:
                c=np.exp(sum(np.log(lv))/L);l2=np.full(L,c);u2=uv*lv/c
            mat=np.zeros((L,L),complex)
            for j in range(L):mat[j,(j+1)%L]=u2[j];mat[(j+1)%L,j]=l2[j]
            starts=la.eigvals(mat);roots=[];corrections=[];laststeps=[]
            for initial in starts:
                z=mp.mpc(float(initial.real),float(initial.imag));z0=z
                for iteration in range(80):
                    p,dp=determinant_and_derivative(z,q[:-1]);a,da=determinant_and_derivative(z,q[1:-2])
                    f=p-q[-1]*a-loops;df=dp-q[-1]*da;step=f/df;z-=step
                    if abs(step)<mp.mpf('1e-65'):break
                roots.append(z);corrections.append(abs(z-z0));laststeps.append(abs(step))
            sorted_abs=np.sort([float(abs(z)) for z in roots]);key=f'dw_{int(odd)}_{ratio}'
            minimum_separation=min(abs(roots[i]-roots[j]) for i in range(L) for j in range(i))
            records.append({'odd':odd,'ratio':ratio,'t1':tv,'roots':L,
                'minimum_root_separation':mp.nstr(minimum_separation,12),'max_final_newton_step':mp.nstr(max(laststeps),12),
                'max_complex_correction_to_gauge_double':mp.nstr(max(corrections),12),
                'max_abs_spectrum_difference_stable':float(max(abs(sorted_abs-stable[key][ix]))),
                'max_abs_spectrum_difference_naive':float(max(abs(sorted_abs-raw[key][ix]))),
                'characteristic_method':'80-digit original cyclic continuant; all roots polished; distinctness checked',
                'roots_decimal':[[mp.nstr(z.real,35),mp.nstr(z.imag,35)] for z in roots]})
            print(json.dumps({k:v for k,v in records[-1].items() if k!='roots_decimal'}),flush=True)
    Path('checks/ring-high-precision.json').write_text(json.dumps(records,indent=2)+'\n')

if __name__=='__main__':main()
