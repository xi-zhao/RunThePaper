"""Elliptic-integral corroboration and source-claim limit checks."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json,time
from pathlib import Path
import numpy as np
import mpmath as mp
from scipy.integrate import quad_vec
from scipy.optimize import minimize_scalar
from model import concurrence_jets,all_correlations
from generate import minimum,clean

def elliptic_C(l,r):
    m=4*l/(1+l)**2
    ebar=2*(1+l)*mp.ellipe(m)/mp.pi
    F=[2*mp.ellipk(m)/(mp.pi*(1+l))]
    F.append(((1+l*l)*F[0]-ebar)/(2*l))
    for k in [1,2]:
        F.append((k*(1+l*l)*F[k]-l*(k-mp.mpf('.5'))*F[k-1])/(l*(k+mp.mpf('.5'))))
    g=lambda j:l*F[abs(j-1)]-F[abs(j)]
    if r==1: xx,yy=g(1),g(-1)
    else:xx=g(1)**2-g(0)*g(2); yy=g(-1)**2-g(0)*g(-2)
    zz=g(0)**2-g(r)*g(-r)
    return (xx-yy+zz-1)/2

def main():
    start=time.time();out={};rows=[]
    for precision in [45,70]:
        with mp.workdps(precision):
            for r in [1,2]:
                for side in [-1,1]:
                    last=None
                    for exponent in [4,6,8,10]:
                        delta=mp.mpf(10)**(-exponent);l=1+side*delta
                        deriv=mp.diff(lambda z:elliptic_C(z,r),l,r)
                        entry={'precision':precision,'r':r,'side':side,'delta':str(delta),'value':mp.nstr(deriv,40)}
                        if last:
                            slope=(deriv-last[1])/(mp.log(delta)-mp.log(last[0]))
                            target=8/(3*mp.pi**2) if r==1 else 16/(15*mp.pi**2)
                            entry['slope']=mp.nstr(slope,40);entry['slope_error']=mp.nstr(slope-target,30)
                        if exponent<=6:
                            ordinary=concurrence_jets(float(l),r=r)[r]
                            entry['quadrature_minus_elliptic']=float(mp.mpf(ordinary)-deriv)
                        last=(delta,deriv);rows.append(entry)
    out['elliptic']=rows
    ns=np.array([41,61,101,151,251,401,701,1001,1501,2001,2701,4001,8001,16001,32001])
    mi=np.array([[n,*minimum(int(n))[0:1]] for n in ns])
    delta=mi[:,1]-1
    out['shift_window_fits']={}
    for lo,hi in [(41,2701),(401,2701),(401,8001),(2701,32001)]:
        s=(ns>=lo)&(ns<=hi)
        out['shift_window_fits'][f'{lo}-{hi}']={'pure_power':np.polyfit(np.log(ns[s]),np.log(delta[s]),1),
            'N2_shift_vs_logN':np.polyfit(np.log(ns[s]),ns[s]**2*delta[s],1)}
    out['shift_values']=np.c_[ns,delta,ns**2*delta].tolist()
    # gamma=0.5: independent low-k coefficient and numerical log-depth fits.
    gamma=.5;rs=np.array([-1,0,1])
    def fv(k):
        a=np.cos(k)-1;b=gamma*np.sin(k)
        return (np.cos(rs*k)*a+np.sin(rs*k)*b)/np.hypot(a,b)
    gv=quad_vec(fv,0,np.pi,epsabs=1e-13,epsrel=1e-13)[0]/np.pi
    A=(gv[0]+gv[2]-2*gv[1])/(2*np.pi*gamma)
    depth=[]
    for n in [401,701,1001,2001,4001,8001]:
        l,j=minimum(n,gamma);depth.append([n,l,j[1]])
    fit=np.polyfit(np.log(np.array(depth)[:,0]),np.array(depth)[:,2],1)
    out['gamma_half_exponent']={'analytic_log_amplitude':A,'depth_fit':fit,'nu_ratio':abs(fit[0])/A,'values':depth}
    # Quantify how much collapse distinguishes nu=1 from perturbed exponents.
    out['collapse_nu_control']={}
    for name,g,r,nlist in [('fig2',1,1,[41,101,401,1001,2701]),('fig3',1,2,[41,101,251,401]),('fig4',.5,1,[41,101,251,401])]:
        vals={};x=np.linspace(-.2,.2,41)
        for nu in [.9,1.,1.1]:
            ys=[]
            for n in nlist:
                lm,jm=minimum(n,g,r)
                v=np.array([concurrence_jets(lm+z/n**(1/nu),g,n,r)[r] for z in x])
                ys.append(v-jm[r])
            ys=np.array(ys)
            vals[str(nu)]={'rms_size_spread':np.sqrt(np.mean(np.ptp(ys,axis=0)**2)),'relative_rms':np.sqrt(np.mean(np.ptp(ys,axis=0)**2))/max(abs(ys[-1]))}
        out['collapse_nu_control'][name]=vals
    out['small_gamma']=[]
    for g in [.0125,.00625]:
        mz,rs=all_correlations(1.,g,rmax=int(2/g))
        ids=rs[rs[:,4]>1e-12,0]
        out['small_gamma'].append({'gamma':g,'xi_E':max(ids),'sum_C':sum(rs[:,4]),
                                   'rmax':int(2/g),'last_positive':rs[int(max(ids))-1,4],'first_zero_margin':rs[int(max(ids)),5]})
    m,rs=all_correlations(.8,rmax=40)
    out['sum_bound_counterexample']={'lambda':.8,'gamma':1,'C1':rs[0,4],'C2':rs[1,4],'sum_C':sum(rs[:,4]),'rmax':40}
    opt=minimize_scalar(lambda l:-concurrence_jets(l)[0],bounds=(.5,.95),method='bounded',options={'xatol':1e-12})
    out['C1_maximum']={'lambda':opt.x,'C':-opt.fun}
    out['runtime_seconds']=time.time()-start
    Path('checks/limits.json').write_text(json.dumps(clean(out),indent=2))
    print(json.dumps(clean({k:v for k,v in out.items() if k!='elliptic'}),indent=2))

if __name__=='__main__':main()
