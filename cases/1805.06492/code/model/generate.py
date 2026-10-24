"""Independent generation from arXiv 1805.06492v2 equations, no reference reads.
All paths are relative to the managed execution directory. No network or installs.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigvals, eigvalsh_tridiagonal
import mpmath as mp


def chain(ncells, a, b, c=1., d=0., odd=False, boundary=0.):
    """H[A_n,B_n]=a, H[B_n,A_n]=b; intercell=c, onsite=+/-d."""
    size = 2*ncells-int(odd)
    h = np.diag(np.array([d if j%2 == 0 else -d for j in range(size)], complex))
    for j in range(size-1):
        h[j,j+1] = a if j%2 == 0 else c
        h[j+1,j] = b if j%2 == 0 else c
    if boundary:
        h[0,-1] = h[-1,0] = boundary*c
    return h


def even_spectrum(n, a, b, c=1., d=0.):
    """Exact diagonal similarity to reciprocal complex-symmetric hopping.
    Eigenvalues are preserved. At a*b=0 take the continuous spectrum.
    """
    s = np.sqrt(complex(a*b))
    diag = np.array([d,-d]*n, complex)
    off = np.array([s if j%2 == 0 else c for j in range(2*n-1)], complex)
    if np.max(abs(off.imag)) == 0 and np.max(abs(diag.imag)) == 0:
        return eigvalsh_tridiagonal(diag.real, off.real).astype(complex)
    h = np.diag(diag)+np.diag(off,1)+np.diag(off,-1)
    return eigvals(h,check_finite=False)


def odd_spectrum(n, a, b, c=1., d=0.):
    m = np.arange(1,n)
    e = np.sqrt(d*d+a*b+c*c+2*c*np.sqrt(complex(a*b))*np.cos(m*np.pi/n)+0j)
    return np.r_[complex(d),e,-e]


def bloch_spectrum(t, gamma, c, d, nk=92):
    k = 2*np.pi*np.arange(nk)/nk
    e = np.sqrt(d*d+(t+gamma/2+c*np.exp(-1j*k))*(t-gamma/2+c*np.exp(1j*k)))
    return np.r_[e,-e]


def phase_count(t, g):
    # Interior regions only; equality curves have coincident roots.
    c1 = g*g/(16*t) if t else np.inf
    c2 = g*g/8-t*t
    return 2*int(abs(c1)<1)+4*int(0<c2<1)


def dw_chain(nalpha, nbeta, t1, t3, t4, odd):
    ha = chain(nalpha,t1+1.5,t1-1.5,odd=odd)
    hb = chain(nbeta,t3,t3,t4)
    na,nb=len(ha),len(hb)
    h=np.zeros((na+nb,na+nb),complex)
    h[:na,:na]=ha; h[na:,na:]=hb
    h[na-1,na]=h[na,na-1]=t4
    h[0,-1]=h[-1,0]=t4
    return h


def continuant(e, products):
    p0,p1=mp.mpf(1),e
    for v in products:
        p0,p1=p1,e*p1-v*p0
    return p1


def gamma_at_threshold(length, precision=70):
    """Exact cyclic-tridiagonal determinant at |E|=1e-5, odd physical length."""
    with mp.workdps(precision):
        m=(length-1)//2
        t=mp.sqrt(mp.mpf(13)/4);a=t+mp.mpf('1.5');b=t-mp.mpf('1.5')
        e=mp.mpf('0.00001')*((-1)**m)
        D=continuant(e,[mp.mpf(1)]*(length-1))
        A=continuant(e,[mp.mpf(1)]*(length-3))
        B=a**m+b**m
        gamma=2*D/(B+mp.sqrt(B*B+4*A*D))
        residual=abs(D-A*gamma**2-B*gamma)
        return {'physical_sites':length,'A_cells':m+1,'gamma':mp.nstr(gamma,55),
                'log_gamma':float(mp.log(gamma)),'det_residual':mp.nstr(residual,8),
                'first_order_gamma':mp.nstr(mp.mpf('0.00001')*(m+1)/B,55)}


def main():
    Path('results').mkdir(exist_ok=True)
    tgrid=np.linspace(-3,3,601)
    f1=np.array([np.sort(abs(even_spectrum(46,t+1.5,t-1.5))) for t in tgrid])
    p1=np.array([np.sort(abs(bloch_spectrum(t,3,1,0))) for t in tgrid])
    kgrid=np.linspace(0,2*np.pi,721)
    f2=[];p2=[]
    for k in kgrid:
        t=1+np.cos(k);c=1-np.cos(k);d=-np.sin(k)
        f2.append(odd_spectrum(46,t+1.5,t-1.5,c,d))
        p2.append(bloch_spectrum(t,3,c,d))
    f2=np.array(f2);p2=np.array(p2)
    pg=np.linspace(0,4,401);pt=np.linspace(-3,3,601)
    phase=np.array([[phase_count(t,g) for g in pg] for t in pt],np.uint8)
    # Domain-wall plots use inferred absolute t4=0.5; the source gives t3/t4 only.
    td=np.linspace(-3,3,241)
    dw={}
    for odd in [False,True]:
        for ratio in [6.,3.3,1.]:
            dw[f'dw_{int(odd)}_{ratio}']=np.array([np.sort(abs(eigvals(dw_chain(25,25,t,ratio*.5,.5,odd),check_finite=False))) for t in td])
    np.savez_compressed('results/spectra.npz',t=tgrid,F1=f1,P1=p1,k=kgrid,F2=f2,P2=p2,
                        phase_gamma=pg,phase_t=pt,phase=phase,dw_t=td,**dw)
    gamma_rows=[gamma_at_threshold(n) for n in range(11,72,2)]
    slope,intercept=np.polyfit([r['physical_sites'] for r in gamma_rows],[r['log_gamma'] for r in gamma_rows],1)
    qks=sorted([float(x) for c in [9/16,np.sqrt(1/8),-np.sqrt(1/8)] for x in [np.arccos(c),2*np.pi-np.arccos(c)]])
    checks={'source_version':'1805.06492v2','F1':{'N_cells':46,'physical_sites':92,'open_critical_t1':[-np.sqrt(3.25),-np.sqrt(1.25),np.sqrt(1.25),np.sqrt(3.25)],'periodic_critical_t1':[-2.5,-.5,.5,2.5]},
            'F2':{'N_A_cells':46,'physical_sites':91,'attachment_kx':qks,'periodic_EP_kx':sorted([float(k) for k in [np.arcsin(np.sqrt(7/12)),np.pi-np.arcsin(np.sqrt(7/12)),np.pi+np.arcsin(np.sqrt(7/12)),2*np.pi-np.arcsin(np.sqrt(7/12))]])},
            'phase_examples':[{'t1':t,'gamma':3,'solutions':phase_count(t,3)} for t in [.1,.5,1,2]],
            'crossover':{'threshold':'1e-5','critical_t1':'sqrt(13)/2','rows':gamma_rows,'fit_alpha_per_physical_site':-slope,'fit_log_prefactor':intercept,'asymptotic_alpha':float(np.log((3+np.sqrt(13))/2)/2)},
            'domain':{'Nalpha_cells':25,'Nbeta_cells':25,'t4':.5,'t4_status':'inferred from source Fig.S6 Hermitian band edges, not explicitly specified',
                      'zero_energy_effective_coupling':[{'ratio':r,'tau_abs':.5*r**(-25)} for r in [6.,3.3,1.]]}}
    Path('results/generation.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({'status':'generated','phase_examples':checks['phase_examples'],'gamma_fit':checks['crossover']['fit_alpha_per_physical_site']}))


if __name__=='__main__':main()
