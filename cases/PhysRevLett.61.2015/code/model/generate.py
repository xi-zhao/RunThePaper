"""Original spinless Haldane honeycomb model: link Chern number and Dirac controls."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigh
from threadpoolctl import threadpool_limits
threadpool_limits(1)
t1=1.;t2=.1

def bloch(u,v,M,phi):
    g=t1*(1+np.exp(1j*u)+np.exp(1j*v))
    z=M-2*t2*np.sin(phi)*(np.sin(v)-np.sin(u)+np.sin(u-v))
    d0=2*t2*np.cos(phi)*(np.cos(v)+np.cos(u)+np.cos(u-v))
    h=np.empty(np.broadcast(u,v).shape+(2,2),complex)
    h[...,0,0]=d0+z;h[...,1,1]=d0-z;h[...,0,1]=g.conj();h[...,1,0]=g
    return h

def chern(M,phi,n):
    mesh=2*np.pi*np.arange(n)/n;u,v=np.meshgrid(mesh,mesh,indexing='ij')
    vals,vec=np.linalg.eigh(bloch(u,v,M,phi));psi=vec[...,0]
    U=np.sum(psi.conj()*np.roll(psi,-1,axis=0),axis=-1)
    V=np.sum(psi.conj()*np.roll(psi,-1,axis=1),axis=-1)
    U/=abs(U);V/=abs(V)
    flux=np.angle(U*np.roll(V,-1,axis=0)*np.roll(U,-1,axis=1).conj()*V.conj())
    # Forward <u(k)|u(k+dk)> links carry the opposite sign to A=i<u|du>.
    return float(-flux.sum()/(2*np.pi))

phi=np.linspace(-np.pi,np.pi,121);mratio=np.linspace(-7,7,141);numeric=np.empty((len(mratio),len(phi)));analytic=np.empty_like(numeric)
ambiguous=np.zeros_like(numeric,dtype=bool);refinement=[]
for i,m in enumerate(mratio):
 for j,p in enumerate(phi):
    masses=np.array([m*t2-3*np.sqrt(3)*t2*np.sin(p),m*t2+3*np.sqrt(3)*t2*np.sin(p)])
    if min(abs(masses))<1e-10:
        numeric[i,j]=np.nan;analytic[i,j]=np.nan;ambiguous[i,j]=True;continue
    expected=(np.sign(masses[1])-np.sign(masses[0]))/2;analytic[i,j]=expected
    c=chern(m*t2,p,31)
    if abs(c-expected)>1e-6 or min(abs(masses))<.01:
        c=chern(m*t2,p,61)
        if abs(c-expected)>1e-6:c=chern(m*t2,p,121)
    numeric[i,j]=c
    if abs(c-expected)>1e-6:ambiguous[i,j]=True
data={'phi':phi,'M_over_t2':mratio,'numeric_Chern_A_i':numeric,'Dirac_mass_Chern_A_i':analytic,'sigma_xy_jx_Ey_in_e2_over_h':-numeric,'finite_mesh_unresolved_mask':ambiguous}
checks={'phase_map_points':int(numeric.size),'gapless_or_finite_mesh_unresolved_points':int(ambiguous.sum()),
        'agreement_away_from_marked_points':int(np.sum(abs(numeric[~ambiguous]-analytic[~ambiguous])<1e-6))}

# Distinct velocity/Kubo integral; fixes the Hall sign without fitting a figure color.
kubo=[]
for M,p in [(0,1.),(0,-1.),(.2,1.),(.7,1.)]:
    n=301;mesh=2*np.pi*(np.arange(n)+.5)/n;u,v=np.meshgrid(mesh,mesh,indexing='ij')
    vals,V=np.linalg.eigh(bloch(u,v,M,p));ground=V[...,0];excited=V[...,1]
    def velocity(axis):
        dg=1j*np.exp(1j*(u if axis==0 else v))
        dz=-2*t2*np.sin(p)*((-np.cos(u)+np.cos(u-v)) if axis==0 else (np.cos(v)-np.cos(u-v)))
        h=np.zeros(u.shape+(2,2),complex);h[...,0,0]=dz;h[...,1,1]=-dz;h[...,0,1]=dg.conj();h[...,1,0]=dg;return h
    du,dv=velocity(0),velocity(1)
    a=np.einsum('...i,...ij,...j->...',ground.conj(),du,excited)
    b=np.einsum('...i,...ij,...j->...',excited.conj(),dv,ground)
    berry=-2*np.imag(a*b)/(vals[...,1]-vals[...,0])**2
    curvature_chern=2*np.pi*berry.mean();link=chern(M,p,101)
    kubo.append({'M':M,'phi':p,'curvature_Chern_A_i':float(curvature_chern),'sigma_xy_jx_Ey':float(-curvature_chern),'link_Chern_A_i':link,'error':float(abs(curvature_chern-link))})
checks['Kubo_independent_comparison']=kubo;assert max(x['error'] for x in kubo)<1e-6

# Band extrema and the single massless valley at a generic original phase boundary.
pb=.7;Mb=3*np.sqrt(3)*t2*np.sin(pb)
valleys=[(2*np.pi/3,-2*np.pi/3),(-2*np.pi/3,2*np.pi/3)]
data['boundary_valley_eigenvalues']=np.array([np.linalg.eigvalsh(bloch(np.array(u),np.array(v),Mb,pb)) for u,v in valleys])
checks['boundary_valley_gaps']=np.diff(data['boundary_valley_eigenvalues'],axis=1).ravel().tolist()
assert min(checks['boundary_valley_gaps'])<1e-12 and max(checks['boundary_valley_gaps'])>.1

# Dirac Landau levels and the anomalous unpaired zero mode; discard cutoff top states.
landau=[];cut=40;a=np.diag(np.sqrt(np.arange(1,cut)),1);B=.13;c=1.2
for valley in [-1,1]:
 for field in [-1,1]:
    mass=.37;s=valley*field;px=np.sqrt(B/2)*(a+a.T);py=-1j*s*np.sqrt(B/2)*(a-a.T)
    H=np.block([[mass*np.eye(cut),c*(-1j*px-py)],[c*(1j*px-py),-mass*np.eye(cut)]])
    ev,V=eigh(H);top=(abs(V[cut-1])**2+abs(V[-1])**2);physical=ev[top<.5]
    expected=np.r_[s*mass,*[sgn*np.sqrt(mass**2+2*n*B*c*c) for n in range(1,6) for sgn in [-1,1]]]
    error=float(max(min(abs(physical-ee)) for ee in expected));landau.append({'valley':valley,'field_sign':field,'zero_mode_expected':s*mass,'max_low_level_error':error})
assert max(x['max_low_level_error'] for x in landau)<1e-12
checks['Dirac_Landau_levels']=landau
checks['conditions']='spinless, T=0, Fermi level in the gap, t2/t1=.1<1/3; boundary excluded from a gapped Chern-number assignment. Two spin copies double Hall response only while the common Fermi gap survives Zeeman shifts.'
checks['sign_dictionary']='Declared oriented lattice and A=i<u|du>: mass C_A=(sign(m_minus)-sign(m_plus))/2; forward overlap link=-C_A; usual j_x=sigma_xy E_y response=-C_A e^2/h. Original published orientation/tensor glyph correspondence remains to be visually authenticated. No source Hall sign agreement is inferred from two internally agreeing numerical methods.'
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
