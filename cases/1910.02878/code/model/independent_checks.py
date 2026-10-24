"""Different formulations: bond similarity, determinant recurrences, antiunitary
algebra, and scalar boundary roots. No import of generate.py.
"""
from pathlib import Path
import os
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'cache'/'matplotlib')
os.environ['XDG_CACHE_HOME']=str(Path.cwd()/'cache')
import numpy as np, json
from scipy import linalg as la
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits
import mpmath as mp
out={}; generated=np.load('results/generated.npz')
I=np.eye(2,dtype=complex); sx=np.array([[0,1],[1,0]],complex)
sy=np.array([[0,-1j],[1j,0]]); sz=np.diag([1,-1]).astype(complex)
T=1j*sy
with threadpool_limits(limits=1):
 # A spin-major 200x200 block assembly instead of generation's site blocks.
 n=100; r=np.diag(np.ones(n-1),-1); l=r.T
 h1=1.3*r+.7*l; off=-.2j*(r-l)
 H=np.block([[h1,off],[off,h1.T]])
 spinvals=la.eigvals(H)
 out['spin_major_unperturbed_to_exact']=float(abs(spinvals[:,None]-generated['obc_exact']).min(axis=1).max())
 # A model-derived Fourier matrix tests hopping order and boundary closure.
 nsmall=13; rr=np.roll(np.eye(nsmall),1,axis=0)
 hh=np.block([[1.3*rr+.7*rr.T,-.2j*(rr-rr.T)],[-.2j*(rr-rr.T),.7*rr+1.3*rr.T]])
 ev=la.eigvals(hh); k=2*np.pi*np.arange(nsmall)/nsmall
 exact=(2*np.cos(k)[:,None]+np.array([1,-1])[None,:]*2j*np.sqrt(.05)*np.sin(k)[:,None]).ravel()
 ii,jj=linear_sum_assignment(abs(ev[:,None]-exact));out['PBC_fourier_matrix_max_error']=float(abs(ev[ii]-exact[jj]).max())
 # Correct S24 with both signs of g and both inside/outside points. The claimed
 # identity fails even when printed roots are evaluated in 80 decimal digits.
 out['S24_high_precision']=[]
 with mp.workdps(80):
  for gs,Es in [('-0.3',('0.2','0.1')),('0.3',('0','0')),('-0.3',('2.5','0'))]:
   t=mp.mpf('1');g=mp.mpf(gs);E=mp.mpc(*Es)
   for factor,label in [(1,'printed'),(4,'quadratic_corrected')]:
    roots=[(E+s*mp.sqrt(E**2-factor*(t*t-g*g)))/(2*(t-g)) for s in [1,-1]]
    errs=[abs((t-g)*b*b-E*b+t+g) for b in roots]
    out['S24_high_precision'].append({'g':gs,'E':Es,'variant':label,'max_polynomial_residual':str(max(errs)),'root_moduli':[str(abs(b)) for b in roots]})
 # HN spectra, with the supplement's stated t>|g| and the unrestricted main-text
 # parameter range distinguished. Checks include a Hermitian positive control.
 out['HN_limits']=[]
 for g in [0,.3,-.3,2.]:
  n=12;r=np.diag(np.ones(n-1),-1);h=(1+g)*r+(1-g)*r.T
  ee=la.eigvals(h);target=2*np.sqrt(complex(1-g*g))*np.cos(np.pi*np.arange(1,n+1)/(n+1))
  ii,jj=linear_sum_assignment(abs(ee[:,None]-target))
  out['HN_limits'].append({'g':g,'spectrum_formula_error':float(abs(ee[ii]-target[jj]).max()),'max_abs_ImE':float(abs(ee.imag).max())})
 # SSH bond-by-bond diagonal similarity. Do not infer precision from raw eigvals.
 out['SSH']=[]
 for idx,(v,w,g) in enumerate([(1/3,1.,.5),(.75,1.,1.2)]):
  n=100;Q=(v+g)*np.eye(n)+w*np.diag(np.ones(n-1),1)
  P=(v-g)*np.eye(n)+w*np.diag(np.ones(n-1),-1)
  h=np.block([[np.zeros((n,n)),Q],[P,np.zeros((n,n))]])
  # Permute to connected chain B0,A0,B1,A1,... and solve pairwise D ratios.
  order=np.array([j for i in range(n) for j in [i+n,i]])
  hp=h[np.ix_(order,order)]
  D=np.ones(2*n,complex)
  for j in range(2*n-1): D[j+1]=D[j]*np.sqrt(complex(hp[j+1,j]/hp[j,j+1]))
  hb=hp*D[None,:]/D[:,None]
  eb=la.eigvals(hb)
  actual=generated[f'ssh{idx}_obc']
  ii,jj=linear_sum_assignment(abs(eb[:,None]-actual))
  record={'similarity_symmetry_error':float(abs(hb-hb.T).max()),'log10_condition_D':float(np.log10(abs(D).max()/abs(D).min())), 'spin_major_balanced_to_generation_max':float(abs(eb[ii]-actual[jj]).max())}
  # Independent determinant recurrence of QP uses only rational v,w,g.
  vals=[]
  for prec in [110,160]:
   with mp.workdps(prec):
    vv=mp.mpf(1)/3 if idx==0 else mp.mpf(3)/4
    gg=mp.mpf(1)/2 if idx==0 else mp.mpf(6)/5
    u=vv**2-gg**2
    def determinant(lam):
     p0=mp.mpf(1);p1=u-lam;dp0=mp.mpf(0);dp1=mp.mpf(-1)
     for j in range(2,n+1):
      p0,p1,dp0,dp1=p1,(u+1-lam)*p1-u*p0,dp1,-p1+(u+1-lam)*dp1-u*dp0
     return p1,dp1
    # Edge eigenvalue scale is exponentially small. Analytic leading estimate
    # fixes the search interval without using the generator's eigenvalues.
    guess=(1-u)**2*u**n
    lam=guess
    for iteration in range(20):
     value,derivative=determinant(lam)
     correction=value/derivative
     lam-=correction
     if abs(correction)<abs(lam)*mp.mpf('1e-40'):break
    ee=mp.sqrt(lam)
    vals.append({'dps':prec,'E_positive':str(ee),'lambda':str(lam),'recurrence_residual':str(abs(determinant(lam)[0]))})
  record['edge_high_precision']=vals
  out['SSH'].append(record)
 # Time reversal, doubled Hermitian symmetries, and singular values.
 rng=np.random.default_rng(20261023)
 H0=np.array([[.2+.3j,.4-.1j],[-.2+.7j,-.4+.2j]])
 # AII dagger model and class D model obey different transpose signs.
 algebra=[]
 for q in [.17,.79,1.3]:
  for kind,C,Hp,Hm,E in [
   ('AII_dagger',T,2*np.cos(q)*I+.4*np.sin(q)*sx+.6j*np.sin(q)*sz,2*np.cos(q)*I-.4*np.sin(q)*sx-.6j*np.sin(q)*sz,.17+.11j),
   ('D',sx,(.6+np.cos(q)) * sz+np.sin(q)*sy+.13j*np.sin(q)*I,(.6+np.cos(q))*sz-np.sin(q)*sy-.13j*np.sin(q)*I,0)]:
   A=Hp-E*I;Am=Hm-E*I
   ext=np.block([[np.zeros((2,2)),A],[A.conj().T,np.zeros((2,2))]])
   extm=np.block([[np.zeros((2,2)),Am],[Am.conj().T,np.zeros((2,2))]])
   ch=la.block_diag(I,-I)
   U=np.block([[np.zeros((2,2)),C],[C,np.zeros((2,2))]])
   if kind=='D': UT=1j*ch@U; uc=U
   else: UT=U;uc=ch@U
   s=la.svdvals(A)
   algebra.append({'kind':kind,'k':q,'Hermitian_error':float(la.norm(ext-ext.conj().T)),
    'chiral_error':float(la.norm(ch@ext@ch+ext)),
    'TR_error':float(la.norm(UT@ext.conj()@UT.conj().T-extm)),
    'TR_square_error':float(la.norm(UT@UT.conj()+np.eye(4))),
    'PH_error':float(la.norm(uc@ext.conj()@uc.conj().T+extm)),
    'singular_value_spectrum_error':float(abs(np.sort(la.eigvalsh(ext))-np.sort(np.r_[s,-s])).max())})
 out['doubling_algebra']=algebra
 # Original Eq.10 itself witnesses why total determinant winding is not a
 # full spectrum formula for matrix-valued symbols: +/- channels cancel.
 g=.3;d=.2;ga=np.sqrt(g*g-d*d);C=g*sz-1j*d*sx
 cv,cs=la.eig(C);spin=cs[:,np.argmin(cv.real)];spin/=la.norm(spin)
 E=.2j;roots=np.roots([1+ga,-E,1-ga])
 band_checks=[]
 for n in [20,40,80,160]:
  site=roots[0]**np.arange(1,n+1)-roots[1]**np.arange(1,n+1);site/=la.norm(site)
  r=np.diag(np.ones(n-1),-1);h=np.kron(r,I+C)+np.kron(r.T,I-C)
  v=np.kron(site,spin)
  band_checks.append({'N':n,'residual':float(la.norm(h@v-E*v))})
 out['multiband_winding_cancellation']={'E':[0,.2],'roots_moduli':abs(roots).tolist(),'SIBC_residuals':band_checks,'bulk_commutator_norm_at_pi_over_2':float(la.norm((.4*sx+.6j*sz)@(.4*sx-.6j*sz)-(.4*sx-.6j*sz)@(.4*sx+.6j*sz),2)), 'interpretation':'Refutes unrestricted multi-band equality using total W only; scalar Toeplitz theorem and nonzero-index sufficient guarantee remain intact.'}
 # 2D skin block: direct scalar recurrence versus k-space spin-block generation.
 out['2D_checks']=[]
 for L in [19,20,40]:
  r=np.diag(np.ones(L-1),-1);G=.5
  scalar=.75j*r-.25j*r.T+.5j*np.eye(L)
  ee=la.eigvals(scalar)
  exact=np.sqrt(1-G*G)*np.cos(np.pi*np.arange(1,L+1)/(L+1))+.5j
  ii,jj=linear_sum_assignment(abs(ee[:,None]-exact))
  out['2D_checks'].append({'L':L,'skin_modes':(2 if L%2 else 4)*L,'total':2*L*L,'scalar_exact_error':float(abs(ee[ii]-exact[jj]).max())})
 # Classification convention: a union of two images is not always a subgroup.
 # These are the actual Table S3 AIII/S_- maps in d=0, no new model.
 out['quotient_algebra']={'image_real_generator':[1,1],'image_imag_generator':[1,-1],
  'sum':[2,0],'sum_in_union':False,'generated_subgroup_index':2,
  'literal_union_quotient':'not a group quotient','sum_subgroup_quotient':'Z2; agrees with the corresponding classification-table entry'}
Path('checks/independent_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
