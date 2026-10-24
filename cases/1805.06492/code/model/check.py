"""Distinct physical-matrix, transfer-polynomial, and source-image checks.
Does not import the generating implementation or modify generated arrays.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['VECLIB_MAXIMUM_THREADS']='1'
import json,hashlib
from pathlib import Path
import numpy as np
import scipy.linalg as la
from scipy.optimize import linear_sum_assignment,brentq
from scipy.ndimage import distance_transform_edt
from PIL import Image
import mpmath as mp


def physical(N,a,b,gminus=1.,gplus=1.,d=0.,odd=True):
    # Different organization: A-block first, then B-block.
    nb=N-1 if odd else N
    T=np.zeros((N,nb),complex); S=np.zeros((nb,N),complex)
    for j in range(nb):
        T[j,j]=a;S[j,j]=b
        if j+1<N: T[j+1,j]=gminus;S[j,j+1]=gplus
    return np.block([[d*np.eye(N),T],[S,-d*np.eye(nb)]])


def match(x,y):
    cost=abs(np.asarray(x)[:,None]-np.asarray(y)[None,:])
    i,j=linear_sum_assignment(cost)
    return float(cost[i,j].max())


def normalized_residual(h,v,e):
    return float(la.norm(h@v-e*v)/max(la.norm(h)*la.norm(v),1e-300))


def exact_odd(N,a,b,c,d):
    m=np.arange(1,N)
    e=np.sqrt(d*d+a*b+c*c+2*c*np.sqrt(complex(a*b))*np.cos(np.pi*m/N)+0j)
    return np.r_[d,e,-e]


def boundary_checks():
    rows=[]
    # Include complex coefficients so real-only coincidences cannot mask conjugation.
    for a,b,gm,gp,d in [(2.5,-.5,1,1,.3),(1.2,.7,1,1,.2j),
                        (1+.2j,.4-.7j,.8+.3j,1.1-.2j,.2+.1j)]:
        N=9;h=physical(N,a,b,gm,gp,d)
        R=np.r_[(-b/gp)**np.arange(N),np.zeros(N-1)]
        L=np.r_[(-np.conj(a/gm))**np.arange(N),np.zeros(N-1)]
        rows.append({'coefficients':[str(x) for x in (a,b,gm,gp,d)],
                     'right':normalized_residual(h,R,d),'left':normalized_residual(h.conj().T,L,np.conj(d))})
    # B termination via physical Hamiltonian with B and A labels interchanged.
    br=[]
    for a,b in [(2.5,-.5),(1.2,1.2)]:
        N=6;d=.3
        hb=physical(N,1,1,b,a,-d) # first block B; rows yield B_(n+1)=-1/a B_n
        wrong=np.r_[(-1/b)**np.arange(N),np.zeros(N-1)]
        correct=np.r_[(-1/a)**np.arange(N),np.zeros(N-1)]
        br.append({'a':a,'b':b,'paper_literal_right_residual':normalized_residual(hb,wrong,-d),
                   'corrected_right_residual':normalized_residual(hb,correct,-d)})
    return {'A_termination':rows,'B_termination':br}


def spectral_checks(data):
    rows=[]
    for N in [3,7,13]:
        for t in [0.,.4,1.2,1.5,1.8,2.6]:
            a,b=t+1.5,t-1.5
            h=physical(N,a,b,1,1,.37,True)
            z=la.eigvals(h)
            rows.append({'N':N,'t':t,'max_assignment_error':match(z,exact_odd(N,a,b,1,.37))})
    # Finite source-scale comparison: a forward-error diagnostic, not an acceptance gate.
    direct=[]
    for t in [.0,.5,1.,1.2,1.4,1.6,1.8,2.,2.6]:
        ix=int(np.argmin(abs(data['t']-t))); actual=float(data['t'][ix])
        e=la.eigvals(physical(46,actual+1.5,actual-1.5,1,1,0,False))
        direct.append({'t1':actual,'naive_sorted_abs_error':float(np.max(abs(np.sort(abs(e))-data['F1'][ix])))})
    # Physical characteristic-polynomial check: tridiagonal recurrence in 80-digit math.
    residuals=[]
    with mp.workdps(80):
        for t in [0.,.5,1.2,1.8,2.6]:
            ix=int(np.argmin(abs(data['t']-t)));tt=mp.mpf(str(float(data['t'][ix])))
            # independently solve polynomial via complex reciprocal H, retain full complex E
            q=complex(float(tt*tt-mp.mpf('2.25')));s=np.sqrt(q)
            h=np.diag(np.tile([s,1],46)[:91],1)+np.diag(np.tile([s,1],46)[:91],-1)
            ee=la.eigvals(h)
            errs=[]
            for ev in ee:
                e=mp.mpc(float(ev.real),float(ev.imag)); p0=mp.mpf(1);p1=e
                scale0=mp.mpf(1);scale1=abs(e)
                for j in range(91):
                    v=tt*tt-mp.mpf('2.25') if j%2==0 else mp.mpf(1)
                    p0,p1=p1,e*p1-v*p0
                    scale0,scale1=scale1,abs(e)*scale1+abs(v)*scale0
                errs.append(float(abs(p1)/max(scale1,mp.mpf('1e-70'))))
            residuals.append({'t1':float(tt),'max_scaled_continuant_residual':max(errs)})
    return {'small_physical_vs_odd_analytic':rows,'source_scale_naive_eigensolver':direct,
            'physical_characteristic_polynomial':residuals}


def polarization_checks():
    rows=[]
    with mp.workdps(90):
        for val in ['0.5','2','-0.5','-2','0.4+0.2j']:
            q=mp.mpc(.4,.2) if 'j' in val else mp.mpf(val)
            for N in [23,46,92,368]:
                terms=[q**j for j in range(N)]
                direct=1-sum((j+1)*v for j,v in enumerate(terms))/(N*sum(terms))
                formula=1-(1+q/(1-q)-N*q**N/(1-q**N))/N
                rows.append({'q':val,'N':N,'P_real':float(mp.re(direct)),'P_imag':float(mp.im(direct)),
                             'sum_vs_derivative_error':mp.nstr(abs(direct-formula),6)})
    return rows


def phase_checks():
    rows=[]
    # Root solve the unfactored q=+/-1 polynomial, rather than calling Eq.(11).
    for t,g in [(0.1,3),(.5,3),(1,3),(2,3),(-1,3),(.3,.8),(1.4,3.2)]:
        roots=[]
        for sign in [1,-1]:
            poly=[1-sign,2*t*(1+sign),t*t*(1-sign)-g*g/4]
            rr=np.roots(np.trim_zeros(poly,'f'))
            for u in rr:
                if abs(u.imag)<1e-12 and abs(u.real)<1:
                    roots.extend([float(np.arccos(u.real)),float(2*np.pi-np.arccos(u.real))])
        rows.append({'t1':t,'gamma':g,'root_count':len(roots),'roots':sorted(roots)})
    # PT edge attachment from direct spectra and exact d-energy edge solution.
    pt=[]
    for t in [.5,1,1.5]:
        N=46;d=.6j;e=la.eigvals(physical(N,t,t,1,1,d,True))
        j=np.argmin(abs(e-d));bulk=np.delete(e,j)
        pt.append({'t1':t,'edge_energy_error':float(abs(e[j]-d)),'edge_bulk_separation':float(np.min(abs(bulk-d)))})
    return {'phase':rows,'PT':pt}


def crossover_checks(gen):
    rows=[]
    with mp.workdps(90):
        for r in gen['crossover']['rows']:
            L=r['physical_sites'];N=(L+1)//2;g=mp.mpf(r['gamma']);a=(3+mp.sqrt(13))/2
            linear=g*(a**(N-1)+a**(-(N-1)))/N
            rows.append({'L':L,'relative_first_order_threshold_error':float(abs(linear/mp.mpf('0.00001')-1))})
    fits=[]
    for lo in [11,21,31,41]:
        rr=[r for r in gen['crossover']['rows'] if r['physical_sites']>=lo]
        slope,intercept=np.polyfit([r['physical_sites'] for r in rr],[r['log_gamma'] for r in rr],1)
        fits.append({'L_range':[lo,71],'alpha':float(-slope),'log_prefactor':float(intercept)})
    # Finite matrices at moderate lengths (where threshold is not below FP noise).
    finite=[]
    for L in [11,21,31]:
        N=(L+1)//2;r=next(r for r in gen['crossover']['rows'] if r['physical_sites']==L)
        a=(3+np.sqrt(13))/2;b=1/a
        h=physical(N,a,b,1,1,0,True);gamma=float(r['gamma']);h[0,N-1]=h[N-1,0]=gamma
        ev=la.eigvals(h);finite.append({'L':L,'gamma':gamma,'min_abs_E':float(min(abs(ev)))})
    return {'first_order':rows,'fits':fits,'direct_finite_check':finite}


def domain_checks():
    rows=[]
    for M in [3,7,25]:
        for ratio in [6.,3.3,1.]:
            t4=.5;t3=t4*ratio
            h=physical(M,t3,t3,t4,t4,0,False)
            # A1 index 0; B_M index 2M-1 in grouped basis.
            rhs=np.zeros(2*M);rhs[-1]=1
            invend=la.solve(h,rhs,assume_a='her')[0]
            tau=abs(t4*t4*invend);pred=t4*ratio**(-M)
            rows.append({'M':M,'ratio':ratio,'tau_schur':float(tau),'tau_formula':pred,
                         'relative_error':float(abs(tau-pred)/pred),'beta_min_abs_E':float(min(abs(la.eigvalsh(h))))})
    return rows


def raster_envelope(image_path,xgrid,spectrum,calibration):
    im=np.asarray(Image.open(image_path).convert('RGB'))
    # Color selection makes labels/gray periodic bands irrelevant.
    mask=(im[:,:,2]>170)&(im[:,:,0]<90)&(im[:,:,1]<110)
    x0,x1,y0,yscale,xmin,xmax=calibration
    out=[]
    for px in range(int(np.ceil(x0))+2,int(np.floor(x1))-1):
        ys=np.flatnonzero(mask[:,px])
        if len(ys)<2:continue
        x=xmin+(px-x0)/(x1-x0)*(xmax-xmin)
        i=np.searchsorted(xgrid,x);i=min(max(i,1),len(xgrid)-1)
        # Envelope interpolation; no digitized ordinates enter the generated spectrum.
        w=(x-xgrid[i-1])/(xgrid[i]-xgrid[i-1])
        sim=(1-w)*spectrum[i-1]+w*spectrum[i]
        top=np.max(sim);bottom=np.min(sim)
        measured_top=(y0-ys.min())/yscale;measured_bottom=(y0-ys.max())/yscale
        out.append([x,measured_bottom,measured_top,bottom,top])
    a=np.array(out);err=a[:,1:3]-a[:,3:5]
    return {'calibration':calibration,'n_columns':len(a),'envelope_rmse_energy':np.sqrt(np.mean(err**2,axis=0)).tolist(),
            'envelope_max_abs_energy':np.max(abs(err),axis=0).tolist(),
            'pixel_energy':1/yscale,'rows':a.tolist()}


def main():
    data=np.load('results/spectra.npz');gen=json.loads(Path('results/generation.json').read_text())
    res={'boundary':boundary_checks(),'spectra':spectral_checks(data),'polarization':polarization_checks(),
         'phase_PT':phase_checks(),'crossover':crossover_checks(gen),'domain_schur':domain_checks()}
    # Main F1 blue excludes the two edge eigenvalues in its P=1 interval.
    f1=data['F1'].copy(); q=data['t']**2-2.25
    # Use NaN for discarded edges then nan envelope, converted to a sorted bulk matrix.
    # The fixed width array is padded with its maximum to avoid changing either envelope.
    for i in np.flatnonzero(abs(q)<1):f1[i,:2]=f1[i,-1]
    res['reference']={
       'F1':raster_envelope('reference/F1-embedded-2.png',data['t'],f1,[76,564,290,76,-3,3]),
       'F2b':raster_envelope('reference/F2-embedded-4.png',data['k'],abs(data['F2'][:,1:]),[74,558,303,112,0,2*np.pi])}
    res['provenance']={'generation_sha256':hashlib.sha256(Path('results/spectra.npz').read_bytes()).hexdigest(),
                       'scientific_context':'same_agent','execution':'native_sandboxed_python_not_PRAgent_receipt'}
    Path('checks/numerical-checks.json').write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps({'small_spectral_max':max(r['max_assignment_error'] for r in res['spectra']['small_physical_vs_odd_analytic']),
                      'B_termination':res['boundary']['B_termination'],'crossover_fits':res['crossover']['fits'],
                      'reference':{k:{a:v for a,v in vv.items() if a!='rows'} for k,vv in res['reference'].items()}},indent=2))


if __name__=='__main__':main()
