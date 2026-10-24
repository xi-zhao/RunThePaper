"""Independent generation from the fixed paper's Hamiltonians, not reference data.

Convention: H(k)=A exp(ik)+B exp(-ik)+D; real-space H[j+1,j]=A.
No source, reference figure, author code, or comparison data is read here.
"""
from pathlib import Path
import os
os.environ['MPLCONFIGDIR'] = str(Path.cwd() / 'cache' / 'matplotlib')
os.environ['XDG_CACHE_HOME'] = str(Path.cwd() / 'cache')
os.environ['TMPDIR'] = str(Path.cwd() / 'cache')
Path('cache').mkdir(exist_ok=True)
import json, time
import numpy as np
from scipy import linalg as la
from threadpoolctl import threadpool_limits

I = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], complex)
sy = np.array([[0,-1j],[1j,0]], complex)
sz = np.diag([1,-1]).astype(complex)
T = 1j*sy
cfg = json.loads(Path('parameters.json').read_text())
arrays, metrics = {}, {}

def chain(n, a, b, onsite=None, periodic=False):
    d = len(a)
    h = np.zeros((n*d,n*d), complex)
    if onsite is not None:
        h += np.kron(np.eye(n), onsite)
    for j in range(n-1):
        h[(j+1)*d:(j+2)*d,j*d:(j+1)*d] = a
        h[j*d:(j+1)*d,(j+1)*d:(j+2)*d] = b
    if periodic:
        h[:d,-d:] = a
        h[-d:,:d] = b
    return h

def eigdata(h, d):
    e, v = la.eig(h)
    p = np.sum(abs(v.reshape(len(h)//d,d,-1))**2, axis=1)
    p /= p.sum(axis=0)
    residual = la.norm(h@v-v*e, axis=0)/(la.norm(h,2)+abs(e))
    return e, p, float(residual.max())

def winding(z):
    return float(np.angle(np.roll(z,-1)/z).sum()/(2*np.pi))

with threadpool_limits(limits=1):
    started=time.monotonic()
    t,g,delta,n = cfg['t'], cfg['g'], cfg['Delta'], cfg['N']
    gamma=np.sqrt(g*g-delta*delta)
    a=t*I+g*sz-1j*delta*sx
    b=t*I-g*sz+1j*delta*sx
    h=chain(n,a,b)
    e,p,res=eigdata(h,2)
    m=np.arange(1,n+1)
    exact=2*np.sqrt(t*t-gamma*gamma)*np.cos(np.pi*m/(n+1))
    arrays.update(obc_direct=e,obc_exact=exact,obc_direct_density=p)
    k=2*np.pi*np.arange(n)/n
    bulk=np.array([la.eigvals(a*np.exp(1j*q)+b*np.exp(-1j*q)) for q in k]).ravel()
    arrays['pbc']=bulk
    q=np.sqrt((t-gamma)/(t+gamma))
    shape=q**np.arange(n)*np.sin(np.pi*m/(n+1))
    pleft=abs(shape)**2; pleft/=pleft.sum()
    arrays['doublet_density']=np.column_stack([pleft,pleft[::-1]])
    _,spin=la.eig(g*sz-1j*delta*sx)
    spin_left=spin[:,np.argmin(la.eigvals(g*sz-1j*delta*sx).real)]
    spin_left/=la.norm(spin_left)
    vleft=np.kron(shape/la.norm(shape),spin_left)
    pair_res=la.norm(h@vleft-exact[0]*vleft)
    metrics['F2']={'gamma':float(gamma),'q_left':float(q),'doublet_E':float(exact[0]),
      'doublet_peak':float(pleft.max()),'doublet_peak_site':int(pleft.argmax()+1),
      'doublet_residual':float(pair_res),'density_normalization':float(pleft.sum()),
      'left_10_mass':float(pleft[:10].sum()),'left_20_mass':float(pleft[:20].sum()),
      'direct_spectrum_to_exact_max':float(abs(e[:,None]-exact).min(axis=1).max()),
      'direct_max_ImE':float(abs(e.imag).max()),'direct_scaled_residual':res}
    dvec=np.array(cfg['stack_delta'])
    coupling=1j*(dvec[0]*sx+dvec[1]*sy+dvec[2]*sz)
    dstack=np.block([[np.zeros((2,2)),coupling],[-coupling,np.zeros((2,2))]])
    astack=la.block_diag(a,a); bstack=la.block_diag(b,b)
    hs=chain(n,astack,bstack,dstack)
    es,ps,rs=eigdata(hs,4)
    hb=h+np.kron(np.eye(n),cfg['dh']*sz)
    eb,pb,rb=eigdata(hb,2)
    arrays.update(stack=es,broken=eb,stack_density=ps,broken_density=pb)
    metrics['F2'].update(stack_scaled_residual=rs,broken_scaled_residual=rb,
        stack_max_ImE=float(abs(es.imag).max()),broken_max_ImE=float(abs(eb.imag).max()))
    metrics['finite_size']=[]
    for nn in cfg['size_checks']:
        row={'N':nn}
        for key,aa,bb,dd in [('stack',astack,bstack,dstack),('broken',a,b,cfg['dh']*sz)]:
            ee,pp,rr=eigdata(chain(nn,aa,bb,dd),len(aa))
            row[key]={'median_IPR':float(np.median((pp**2).sum(axis=0))),
                'median_edge10_mass':float(np.median(pp[:10].sum(axis=0)+pp[-10:].sum(axis=0))),
                'max_ImE':float(abs(ee.imag).max()),'scaled_residual':rr}
        row['unperturbed_m1_IPR']=float(( (q**np.arange(nn)*np.sin(np.pi*np.arange(1,nn+1)/(nn+1)))**4).sum()/((q**np.arange(nn)*np.sin(np.pi*np.arange(1,nn+1)/(nn+1)))**2).sum()**2)
        metrics['finite_size'].append(row)
    # Original Z2 invariant: continuous log along [0, pi], exact endpoint Pfaffians.
    metrics['Z2']=[]
    kk=np.linspace(0,np.pi,8193)
    for ee in [0,0.2j,2.5,0.6j,1+0.1j]:
        dets=np.array([la.det((a*np.exp(1j*x)+b*np.exp(-1j*x)-ee*I)@T) for x in kk])
        logdelta=np.log(abs(dets[-1])/abs(dets[0]))+1j*(np.unwrap(np.angle(dets))[-1]-np.unwrap(np.angle(dets))[0])
        pf0=((a+b-ee*I)@T)[0,1]; pfpi=((-a-b-ee*I)@T)[0,1]
        sign=pfpi/pf0*np.exp(-0.5*logdelta)
        kfull=np.linspace(0,2*np.pi,8192,endpoint=False)
        dfull=np.array([la.det(a*np.exp(1j*x)+b*np.exp(-1j*x)-ee*I) for x in kfull])
        metrics['Z2'].append({'E':[ee.real,ee.imag],'nu':int(sign.real<0),'sign':[float(sign.real),float(sign.imag)],'W':winding(dfull),'min_det':float(abs(dets).min())})
    metrics['reciprocity_error']=float(max(la.norm(T@(a*np.exp(1j*x)+b*np.exp(-1j*x)).T@T.conj().T-(a*np.exp(-1j*x)+b*np.exp(1j*x))) for x in np.linspace(0,6,17)))
    # SSH original two parameter sets. Balanced similarity avoids exponential
    # conditioning of direct OBC eigenvalues; both spectra are retained.
    metrics['SSH']=[]
    kk=np.linspace(0,2*np.pi,1000,endpoint=False)
    for idx,pars in enumerate(cfg['ssh']):
        v,w,gg=pars['v'],pars['w'],pars['g']
        intracell=np.array([[0,v+gg],[v-gg,0]],complex)
        aa=np.array([[0,0],[w,0]],complex); bb=aa.T
        raw=chain(n,aa,bb,intracell)
        # Diagonal similarity can symmetrize each individual bond.
        tr=np.sqrt(complex(v*v-gg*gg))
        bal=chain(n,aa,bb,np.array([[0,tr],[tr,0]],complex))
        ebalance=la.eigvals(bal); eraw=la.eigvals(raw)
        ep=np.array([la.eigvals(intracell+aa*np.exp(1j*x)+bb*np.exp(-1j*x)) for x in kk])
        r0=np.sqrt(abs((v-gg)/(v+gg)))
        nb=np.array([la.eigvals(intracell+aa*r0*np.exp(1j*x)+bb/r0*np.exp(-1j*x)) for x in kk])
        arrays[f'ssh{idx}_pbc']=ep; arrays[f'ssh{idx}_obc']=ebalance
        arrays[f'ssh{idx}_raw']=eraw; arrays[f'ssh{idx}_nonbloch']=nb
        zeros=np.sort(abs(ebalance))[:2]
        nongap=ebalance[np.argsort(abs(ebalance))[2:]]
        metrics['SSH'].append({'params':pars,'zero_magnitudes':zeros.tolist(),
           'bulk_min_abs_ReE':float(abs(nongap.real).min()),'r0':float(r0),
           'raw_to_balanced_directed_max':float(abs(eraw[:,None]-ebalance).min(axis=1).max()),
           'WP_at_zero':winding(-((v+gg+w*np.exp(-1j*kk))*(v-gg+w*np.exp(1j*kk))))})
    # Two-dimensional model: Fourier x / open y, and full open real-space matrix.
    L=cfg['L']; G=cfg['Gamma']
    ay=-.5j*sy+.5j*G*I; by=.5j*sy+.5j*G*I
    ax=-.5j*sx+.5j*G*I; bx=.5j*sx+.5j*G*I
    cylinder=[]; rows=[]; pbc2=[]
    for ix in range(L):
        kx=2*np.pi*ix/L
        ons=np.sin(kx)*sx+1j*G*np.cos(kx)*I
        ee,pp,rr=eigdata(chain(L,ay,by,ons),2)
        cylinder.extend(ee)
        rows.append({'ix':ix,'kx':float(kx),'max_ImE':float(ee.imag.max()),'min_ImE':float(ee.imag.min()),'median_IPR':float(np.median((pp**2).sum(axis=0))),'scaled_residual':rr})
        if ix in [0,L//2]: arrays[f'2d_skin_{ix}']=ee
        for ky in 2*np.pi*np.arange(L)/L:
            pbc2.extend(la.eigvals(np.sin(kx)*sx+np.sin(ky)*sy+1j*G*(np.cos(kx)+np.cos(ky))*I))
    full=np.kron(np.eye(L),chain(L,ay,by))
    for ix in range(L-1):
        sl=slice(2*L*ix,2*L*(ix+1)); sr=slice(2*L*(ix+1),2*L*(ix+2))
        full[sr,sl]=np.kron(np.eye(L),ax); full[sl,sr]=np.kron(np.eye(L),bx)
    efull=la.eigvals(full)
    arrays.update(cylinder=np.array(cylinder),pbc2=np.array(pbc2),full2=efull)
    exact2=np.sqrt(1-G*G)*np.cos(np.pi*np.arange(1,L+1)/(L+1))
    printed2=np.sqrt(1-G*G)*np.cos(2*np.pi*np.arange(1,L+1)/L)
    skin0=arrays['2d_skin_0']
    metrics['2D']={'L':L,'Gamma':G,'count_skin':4*L,'total':2*L*L,'kx_blocks':rows,
       'corrected_spectrum_error':float(abs(skin0[:,None]-(exact2+1j*G)).min(axis=1).max()),
       'printed_S75_directed_error':float(abs(skin0[:,None]-(printed2+1j)).min(axis=1).max()),
       'full_max_abs_ImE':float(abs(efull.imag).max()),'odd_L_count_rule':'2L for odd L; 4L for even L'}
    # Source S24 versus the actual quadratic: decimal-test parameters are explicit.
    ht,hg,he=1.,-.3,.2+.1j
    wrong=np.array([(he+s*np.sqrt(he*he-(ht*ht-hg*hg)))/(2*(ht-hg)) for s in [1,-1]])
    right=np.roots([ht-hg,-he,ht+hg])
    poly=lambda z:(ht-hg)*z*z-he*z+(ht+hg)
    metrics['S24']={'t':ht,'g':hg,'E':[he.real,he.imag],
       'printed_polynomial_residual':float(abs(poly(wrong)).max()),
       'corrected_polynomial_residual':float(abs(poly(right)).max()),
       'printed_product':[float(np.prod(wrong).real),float(np.prod(wrong).imag)],
       'required_product':(ht+hg)/(ht-hg),'corrected_product':[float(np.prod(right).real),float(np.prod(right).imag)]}
    # Semi-infinite truncation has a single residual at its discarded right end.
    metrics['SIBC']=[]
    for nn in [20,40,80,160]:
        jj=np.arange(1,nn+1); psi=right[0]**jj-right[1]**jj; psi/=la.norm(psi)
        hn=chain(nn,np.array([[ht+hg]]),np.array([[ht-hg]]))
        rr=la.norm(hn@psi-he*psi)
        metrics['SIBC'].append({'N':nn,'residual':float(rr)})
    metrics['elapsed_seconds']=time.monotonic()-started
Path('results').mkdir(exist_ok=True)
np.savez_compressed('results/generated.npz',**arrays)
Path('results/generation.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps(metrics,indent=2))
