"""Middle-root non-Bloch bands, source phase diagrams and supplementary Lee model."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigvals
from scipy.spatial import cKDTree
from threadpoolctl import threadpool_limits
threadpool_limits(1)

def coefficients(p):
    t1,t2,t3,g1,g2=p;a=t2-g2/2;b=t1+g1/2;c=t3;d=t3;e=t1-g1/2;f=t2+g2/2
    return np.array([c*f,b*f+c*e,a*f+b*e+c*d,a*e+b*d,a*d],complex)
def R(beta,p):
    t1,t2,t3,g1,g2=p
    return (t2-g2/2)/beta+t1+g1/2+t3*beta,t3/beta+t1-g1/2+(t2+g2/2)*beta
def gbz(p,M=1024,all_pairs=False):
    co=coefficients(p);A,B,C,D,E=co
    points=[];mismatches=[];aux=[]
    for z in np.exp(2j*np.pi*(np.arange(M)+.5)/M):
        roots=np.roots([A*(1-z*z),B*(1-z),0,D*(1-1/z),E*(1-1/z**2)])
        for beta in roots:
            if abs(beta)<1e-10:continue
            rp,rm=R(beta,p);poly=co.copy();poly[2]-=rp*rm
            rr=np.roots(poly);radii=np.sort(abs(rr));mismatch=abs(np.log(radii[1]/radii[2]))
            aux.append(beta)
            if mismatch<1e-6 and abs(np.log(abs(beta)/radii[1]))<1e-5:
                points.extend([beta,beta*z]);mismatches.append(mismatch)
    points=np.array(points)
    if not len(points):raise ValueError(('empty GBZ',p))
    points=points[np.argsort(np.angle(points))]
    if all_pairs:return points,np.array(aux)
    return points,max(mismatches)

def finite(p,L,boundary=(0,0),radial_scale=1.):
    t1,t2,t3,g1,g2=p;h=np.zeros((2*L,2*L),complex)
    for n in range(L):
        a=2*n;b=a+1;h[a,b]=t1+g1/2;h[b,a]=t1-g1/2
        if n+1<L:
            h[a+2,b]=(t2-g2/2)/radial_scale;h[b,a+2]=(t2+g2/2)*radial_scale
            h[a,b+2]=t3*radial_scale;h[b+2,a]=t3/radial_scale
    h[0,0]+=boundary[0];h[-1,-1]+=boundary[1]
    return eigvals(h,check_finite=False)

def winding(points,p):
    rp,rm=R(np.r_[points,points[0]],p)
    return (np.unwrap(np.angle(rm))[-1]-np.unwrap(np.angle(rm))[0]-np.unwrap(np.angle(rp))[-1]+np.unwrap(np.angle(rp))[0])/(4*np.pi)

def phase_map(t1,t2,t3,g1,g2):
    t1,t2,g1,g2=np.broadcast_arrays(t1,t2,g1,g2)
    # Analytic zero-energy roots of R+ and R-, retaining degree-reduction limits.
    def quadratic(a,b,c):
        a,b,c=np.broadcast_arrays(a,b,c);dis=np.sqrt(b*b-4*a*c+0j)
        with np.errstate(divide='ignore',invalid='ignore'):
            r1=(-b+dis)/(2*a);r2=(-b-dis)/(2*a)
            r1=np.where(abs(a)<1e-13,-c/b,r1);r2=np.where(abs(a)<1e-13,np.inf,r2)
        return r1,r2
    pp=quadratic(t3,t1+g1/2,t2-g2/2);mm=quadratic(t2+g2/2,t1-g1/2,t3)
    rad=np.abs(np.array([*pp,*mm]));ix=np.argsort(rad,axis=0);ordered=np.take_along_axis(rad,ix,axis=0)
    nplus=np.sum(ix[:2]<2,axis=0);phase=1-nplus
    same=(ix[1]<2)==(ix[2]<2)
    tie=abs(ordered[1]-ordered[2])<1e-8*(1+ordered[1]+ordered[2])
    return np.where(same&tie,2,phase).astype(int)

data={};checks={}
params={
 'b1':[1.1,1,.2,4/3,0],'b2':[-1.1,1,.2,4/3,0],
 'c1':[.3,1.1,.2,0,4/3],'c2':[.3,1.1,.2,0,-4/3],
 'd1':[.3,.5,.2,5/3,1/3],'d2':[-.3,.5,.2,5/3,1/3]}
for label,p in params.items():
    beta,err=gbz(p,2048);data['fig2_'+label]=beta;checks[label]={'middle_root_log_modulus_residual':err,'points':len(beta),'abs_beta_min':float(min(abs(beta))),'abs_beta_max':float(max(abs(beta)))}
    assert err<1e-6

# Phase maps follow zero-energy roots, not image colors or curve fitting.
t1=np.linspace(-4,4,401);t2=np.linspace(-.5,3,351)
data['fig3_t1']=t1;data['fig3_t2']=t2;data['fig3_phase']=phase_map(t1[None,:],t2[:,None],.2,5/3,1/3)
g1=np.linspace(-5,5,501);g2=np.linspace(-5,5,501)
data['fig4_g1']=g1;data['fig4_g2']=g2;data['fig4_phase']=phase_map(0,1,.2,g1[None,:],g2[:,None])

for label,p in [('fig3c',[1,1.4,.2,5/3,1/3]),('fig4c',[0,1,.2,-1,1.4]),('fig4d',[0,1,.2,2.1,1.4])]:
    beta,err=gbz(p,4096);rp,rm=R(beta,p);data[label+'_beta']=beta;data[label+'_plus']=rp;data[label+'_minus']=rm
    phase=int(phase_map(*p))
    checks[label]={'middle_root_residual':err,'winding_sampled':float(winding(beta,p)) if phase!=2 else None,'winding_defined':phase!=2,'zero_energy_phase':phase}

line=np.linspace(-3,3,241);obc=[];continuum=[];wline=[]
for t in line:
    p=[t,1.4,.2,5/3,1/3];beta,_=gbz(p,128);r0=np.exp(np.mean(np.log(abs(beta))))
    obc.append(abs(finite(p,100,radial_scale=r0)));rr=R(beta,p);continuum.append(np.sqrt(rr[0]*rr[1]+0j))
    wline.append(int(phase_map(*p)))
data['fig3_line_t1']=line;data['fig3_obc_absE']=np.array(obc);data['fig3_winding']=np.array(wline)
# Unequal numbers of points per GBZ: preserve ragged arrays as flattened records without pickle.
data['fig3_continuum_t1']=np.concatenate([np.full(len(a),t) for a,t in zip(continuum,line)])
data['fig3_continuum_absE']=np.concatenate([abs(a) for a in continuum])
line4=np.linspace(-5,5,251);bands=[]
for gamma in line4:bands.append(abs(finite([0,1,.2,gamma,1.4],100)))
data['fig4_line_g1']=line4;data['fig4_obc_absE']=np.array(bands)

# Direct finite chain + boundary perturbation challenge to the asymptotic continuum.
p=[1,1.4,.2,5/3,1/3];beta,_=gbz(p,8192);rp,rm=R(beta,p);energy=np.sqrt(rp*rm+0j);energy=np.r_[energy,-energy]
tree=cKDTree(np.c_[energy.real,energy.imag]);rad=np.exp(np.mean(np.log(abs(beta))))
convergence=[]
for L in [30,60,120]:
 for edge in [(0,0),(.3+.2j,-.5j)]:
    ee=finite(p,L,boundary=edge,radial_scale=rad);dist=tree.query(np.c_[ee.real,ee.imag])[0]
    convergence.append({'L':L,'boundary':str(edge),'median_band_distance':float(np.median(dist)),'p90_band_distance':float(np.quantile(dist,.9)),'outliers_above_point05':int(np.sum(dist>.05))})
checks['finite_chain_convergence']=convergence
checks['finite_chain_lengths']='Main Figs3d/4b: L=100 chosen after explicit L=30,60,120 convergence control; source main captions do not state L. SI Fig5b: original L=50 exactly.'

beta,aux=gbz(params['d1'],2048,all_pairs=True);data['S4_middle_beta']=beta;data['S4_all_pair_beta']=aux

# Supplementary Lee model in its original site basis, L=50, r/gamma=1/3.
r=1/3;gamma=1.;L=50;vv=np.linspace(-1.5,1.5,601);lee=[]
for v in vv:
    h=np.zeros((2*L,2*L),complex)
    for n in range(L):
        a=2*n;b=a+1;h[a,a]=.5j;h[b,b]=-.5j;h[a,b]=h[b,a]=v
        if n+1<L:
            for i,j,val in [(a+2,a,1j*r/2),(a,a+2,-1j*r/2),(b+2,b,-1j*r/2),(b,b+2,1j*r/2),(a+2,b,r/2),(b,a+2,r/2),(b+2,a,r/2),(a,b+2,r/2)]:h[i,j]=val
    lee.append(eigvals(h))
data['S5_v']=vv;data['S5_energy']=np.array(lee);checks['Lee_gap_boundaries']=[float(np.sqrt(5)/6),float(np.sqrt(13)/6)]
np.savez_compressed('calculation/results/generation.npz',**data)
Path('calculation/results/checks.json').write_text(json.dumps(checks,indent=2))
