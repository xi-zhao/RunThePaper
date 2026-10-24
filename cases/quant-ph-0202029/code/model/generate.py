"""Generate independently; all conditions are in the source-derived config/code.
Never reads the source directory, reference curves or comparison outputs.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json,time
from pathlib import Path
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from model import concurrence_jets,all_correlations,jets

def minimum(N,gamma=1.,r=1):
    if r==1:
        f=lambda l:concurrence_jets(l,gamma,N,r)[2]
        l=brentq(f,1-min(.3,2/N),1+min(.3,2/N),xtol=2e-15)
    else:
        f=lambda l:concurrence_jets(l,gamma,N,r)[2]
        opt=minimize_scalar(f,bounds=(1-min(.2,2/N),1+min(.2,2/N)),
                            method='bounded',options={'xatol':1e-14})
        l=opt.x
    return l,concurrence_jets(l,gamma,N,r)

def clean(v):
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,(np.floating,np.integer)):v=v.item()
    if isinstance(v,float) and not np.isfinite(v):return None
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v

def main():
    t=time.time();out={};arrays={}
    sizes=[11,21,41,61,101,151,251,401,701,1001,1501,2001,2701,4001,8001]
    minima=[]
    for n in sizes:
        l,j=minimum(n);minima.append([n,l,*j])
    out['minima_C1']=minima
    mi=np.array(minima)
    out['depth_fits']={str(lo):np.polyfit(np.log(mi[mi[:,0]>=lo,0]),mi[mi[:,0]>=lo,3],1).tolist() for lo in [11,41,101,401]}
    out['shift_fits']={str(lo):np.polyfit(np.log(mi[mi[:,0]>=lo,0]),np.log(mi[mi[:,0]>=lo,1]-1),1).tolist() for lo in [11,41,101,401]}
    arrays['fig1_lambda']=np.linspace(.7,1.3,301)
    for n in [11,41,101,251,401]:
        arrays[f'fig1_N{n}']=np.array([concurrence_jets(l,N=n) for l in arrays['fig1_lambda']])
    arrays['fig1_infinite_lambda']=np.r_[np.linspace(.7,.99,80),1-np.logspace(-2,-5,55),1+np.logspace(-5,-2,55),np.linspace(1.01,1.3,80)]
    arrays['fig1_infinite']=np.array([concurrence_jets(l) for l in arrays['fig1_infinite_lambda']])
    arrays['inset_lambda']=np.linspace(0,2,201)
    arrays['inset_C1']=np.array([concurrence_jets(l)[0] for l in arrays['inset_lambda']])
    arrays['inset_C2_lambda']=np.linspace(.5,1.5,201)
    for n in [11,41,101,251,401,None]:
        arrays[f'inset_C2_N{n}']=np.array([concurrence_jets(l,N=n,r=2)[0] for l in arrays['inset_C2_lambda']])
    x=np.linspace(-.2,.2,101);arrays['collapse_x']=x
    collapse={}
    for name,gamma,r,ns in [('fig2',1.,1,[41,101,251,401,701,1001,1501,2001,2701]),('fig3',1.,2,[41,101,251,401]),('fig4',.5,1,[41,101,251,401])]:
        rows=[]
        for n in ns:
            lm,jm=minimum(n,gamma,r)
            v=np.array([concurrence_jets(lm+z/n,gamma,n,r)[r] for z in x])
            y=(1-np.exp(v-jm[1]))*(1e4 if name=='fig2' else 1) if r==1 else (v-jm[2])*1e4
            arrays[f'{name}_N{n}']=y
            rows.append({'N':n,'lambda_m':lm,'minimum':jm[r]})
        ys=np.array([arrays[f'{name}_N{n}'] for n in ns])
        collapse[name]={'minima':rows,'max_spread':np.max(np.ptp(ys,axis=0)),
                        'rms_spread':np.sqrt(np.mean(np.ptp(ys,axis=0)**2)),
                        'reference_scale':np.max(abs(ys[-1])),
                        'relative_max_spread':np.max(np.ptp(ys,axis=0))/np.max(abs(ys[-1]))}
    out['collapse']=collapse
    arrays['fig4_infinite_lambda']=np.r_[np.linspace(.8,.99,70),1-np.logspace(-2,-6,70),1+np.logspace(-6,-2,70),np.linspace(1.01,1.1,60)]
    arrays['fig4_infinite']=np.array([concurrence_jets(l,.5) for l in arrays['fig4_infinite_lambda']])
    deltas=np.logspace(-2,-7,36)
    arrays['log_delta']=np.log(deltas)
    for r in [1,2]:
        for side in [-1,1]:
            arrays[f'singular_r{r}_side{side}']=np.array([concurrence_jets(1+side*d,r=r) for d in deltas])
    out['singular_fits']={}
    for r in [1,2]:
        for side in [-1,1]:
            arr=arrays[f'singular_r{r}_side{side}'][:,r]
            for hi in [1e-3,1e-4,1e-5]:
                sel=(deltas<=hi)&(deltas>=1e-7)
                out['singular_fits'][f'r{r}_side{side}_maxdelta{hi}']=np.polyfit(np.log(deltas[sel]),arr[sel],1)
    out['critical']={}
    for n in [7,9,11,41,401,None]:
        mz,rs=all_correlations(1.,N=n,rmax=(min(10,(n-1)//2) if n else 50))
        out['critical'][str(n)]={'mz':mz,'correlations':rs}
    out['range_scan']={}
    for n in [7,9,11,None]:
        vals=[]
        for l in np.r_[np.linspace(.1,.99,30),np.linspace(1,1.3,61),np.linspace(1.4,10,30)]:
            m,rs=all_correlations(l,N=n,rmax=3)
            vals.append([l,rs[2,4],rs[2,5],rs[2,6]])
        out['range_scan'][str(n)]=vals
    out['gamma_critical']=[]
    for g in [1.,.75,.5,.3,.2,.1,.075,.05,.025]:
        rmax=min(300,max(30,int(5/g)))
        mz,rs=all_correlations(1.,g,rmax=rmax)
        ids=rs[rs[:,4]>1e-12,0]
        out['gamma_critical'].append({'gamma':g,'rmax':rmax,'xi_E':max(ids) if len(ids) else 0,
                                     'sum_C':sum(rs[:,4]),'tail_margin':rs[-1,5],
                                     'last_entangled_C':rs[int(max(ids))-1,4] if len(ids) else 0})
        arrays[f'critical_gamma{g}']=rs
    out['runtime_seconds']=time.time()-t
    Path('results').mkdir(exist_ok=True)
    np.savez_compressed('results/independent.npz',**arrays)
    Path('results/independent.json').write_text(json.dumps(clean(out),indent=2,allow_nan=False))
    print(json.dumps(clean({'critical':out['critical']['None'],'collapse':collapse,'depth_fits':out['depth_fits'],'singular_fits':out['singular_fits'],'gamma_critical':out['gamma_critical'],'runtime_seconds':out['runtime_seconds']}),indent=2))

if __name__=='__main__':main()
