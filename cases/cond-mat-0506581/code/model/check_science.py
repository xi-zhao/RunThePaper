"""Distinct geometric, algebraic, folding, and full-vector-reference checks.

This native execution is NOT a PRAgent execute receipt. Original vector values
are used only in comparisons. Geometric construction below does not call km.hoppings.
"""
from pathlib import Path
from itertools import product,combinations
import json,hashlib,time
import numpy as np
from scipy.linalg import eigvalsh
from km import bulk,ribbon,supercell,pfaffian,occupied,overlap,frame_pf,sx,sy,sz,I2,G,J4

nn=1/np.sqrt(3);a1=np.array([.5,np.sqrt(3)/2]);a2=np.array([-.5,np.sqrt(3)/2]);d=np.array([0.,nn])
deltas=np.array([d,d-a1,d-a2])

def geometric_block(ri,rj,ai,aj,v,r,so):
    delta=rj-ri;dist=np.linalg.norm(delta)
    if dist<1e-9:return ((-1)**ai)*v*I2
    if ai!=aj and abs(dist-nn)<1e-9:
        direction=-delta/nn
        return I2+1j*r*(direction[1]*sx-direction[0]*sy)
    if ai==aj and abs(dist-1)<1e-9:
        candidates=ri+((-1)**ai)*deltas
        mid=[c for c in candidates if abs(np.linalg.norm(c-rj)-nn)<1e-9]
        assert len(mid)==1
        v1=(mid[0]-rj)/nn;v2=(ri-mid[0])/nn
        nu=2/np.sqrt(3)*(v1[0]*v2[1]-v1[1]*v2[0])
        assert abs(abs(nu)-1)<1e-9
        return 1j*so*nu*sz
    return None

def geometric_terms(positions,sublattices,translations,v=.1,r=.05,so=.06):
    terms=[]
    for shift,vec in translations:
        for i,ri in enumerate(positions):
            for j,rj0 in enumerate(positions):
                h=geometric_block(ri,rj0+vec,sublattices[i],sublattices[j],v,r,so)
                if h is not None:terms.append((i,j,shift,h))
    return terms

def from_terms(terms,n,phase):
    H=np.zeros((2*n,2*n),complex)
    for i,j,shift,h in terms:H[2*i:2*i+2,2*j:2*j+2]+=h*np.exp(1j*np.dot(phase,shift))
    return H

def folded_spectrum(alpha1,alpha2,v=.1):
    vals=[]
    for m1 in range(2):
        for m2 in range(4):
            s=(alpha1+2*np.pi*m1)/2;z=(alpha2+2*np.pi*m2)/2
            vals.extend(eigvalsh(bulk((s+z)/2,(s-z)/2,v=v)))
    return np.sort(vals)

start=time.monotonic();result={};rng=np.random.default_rng(581)
bulkerrors=[];trerrors=[];herm=[]
for v,r,so in [(.1,.05,.06),(.4,.05,.06),(.1,0,.06),(-.1,-.05,-.06)]:
    terms=geometric_terms([np.zeros(2),d],[0,1],[((m,n),m*a1+n*a2) for m,n in product(range(-1,2),repeat=2)],v,r,so)
    for q1,q2 in rng.uniform(-np.pi,np.pi,(24,2)):
        H=bulk(q1,q2,v=v,r=r,so=so);geo=from_terms(terms,2,[q1,q2])
        bulkerrors.append(np.max(abs(H-geo)));herm.append(np.max(abs(H-H.conj().T)))
        trerrors.append(np.max(abs(J4@H.conj()@J4.conj().T-bulk(-q1,-q2,v=v,r=r,so=so))))
result['geometric_bulk_max_error']=float(max(bulkerrors));result['TR_max_error']=float(max(trerrors));result['hermiticity_max_error']=float(max(herm))

positions=[row*a1+(d-a1 if sub else 0) for row in range(30) for sub in range(2)];subs=[sub for row in range(30) for sub in range(2)]
terms=geometric_terms(positions,subs,[((m,),np.array([m,0.])) for m in range(-1,2)])
result['geometric_ribbon_max_error']=max(float(np.max(abs(ribbon(k,n=30)-from_terms(terms,60,[k])))) for k in [.13,2.3,np.pi,4.7])
cells=[(p,q) for p,q in product(range(4),repeat=2) if (p-q)%2==0]
positions=[np.array([q/2,p*np.sqrt(3)/2])+s*d for p,q in cells for s in range(2)];subs=[s for p,q in cells for s in range(2)]
terms=geometric_terms(positions,subs,[((m,n),np.array([2*n,2*np.sqrt(3)*m])) for m,n in product(range(-1,2),repeat=2)])
result['geometric_supercell_max_error']=max(float(np.max(abs(supercell(a,b)-from_terms(terms,16,[a,b])))) for a,b in [(0,0),(.4,.7),(np.pi,0),(-1.7,2.1)])
result['folding_spectrum_max_error']=max(float(np.max(abs(eigvalsh(supercell(a,b,v=v))-folded_spectrum(a,b,v)))) for a,b in rng.uniform(-np.pi,np.pi,(16,2)) for v in [.1,.4,0])

pferr=[];svderr=[];antisym=[];even=[]
for dim in [4,8,16,32]:
    for rep in range(8):
        z=rng.normal(size=(dim,dim//2))+1j*rng.normal(size=(dim,dim//2));U=np.linalg.qr(z)[0]
        M=overlap(U);P=pfaffian(M);s=np.linalg.svd(M,compute_uv=False)
        pferr.append(abs(P*P-np.linalg.det(M)));svderr.append(abs(abs(P)-np.prod(s[::2])))
        antisym.append(np.max(abs(M+M.T)))
for rep in range(30):
    h=sum(float(c)*g for c,g in zip(rng.normal(size=5),G))
    even.append(abs(abs(pfaffian(overlap(occupied(h)[1])))-1))
result['pfaffian_checks']={'max_pf_squared_minus_det':float(max(pferr)),'max_abs_pf_minus_singular_product':float(max(svderr)),'max_antisymmetry':float(max(antisym)),'even_subspace_max_absP_minus_1':float(max(even))}

U=np.eye(4,dtype=complex)[:,:2];theta=np.pi/4
P=pfaffian(overlap(U));Pnew=pfaffian(overlap(U*np.exp(1j*theta)))
result['gauge_covariance']={'theta':theta,'base_P':[P.real,P.imag],'actual_P':[Pnew.real,Pnew.imag],'printed_law_error':float(abs(Pnew-P*np.exp(2j*theta))),'conjugated_law_error':float(abs(Pnew-P*np.exp(-2j*theta)))}
fock=[]
for dim,nel in [(4,2),(8,4)]:
    U=np.linalg.qr(rng.normal(size=(dim,nel))+1j*rng.normal(size=(dim,nel)))[0]
    J=np.kron(np.eye(dim//2),1j*sy);TU=J@U.conj()
    coef=np.array([np.linalg.det(U[list(c),:]) for c in combinations(range(dim),nel)])
    tcoef=np.array([np.linalg.det(TU[list(c),:]) for c in combinations(range(dim),nel)])
    fock.append({'orbitals':dim,'electrons':nel,'fock_overlap_minus_det':float(abs(np.vdot(coef,tcoef)-np.linalg.det(overlap(U)))),'normalization_error':float(abs(np.vdot(coef,coef)-1))})
result['manybody_fock_checks']=fock
back=[]
for dim in [4,32]:
    J=np.kron(np.eye(dim//2),1j*sy)
    for rep in range(30):
        u=rng.normal(size=dim)+1j*rng.normal(size=dim);u/=np.linalg.norm(u)
        V=rng.normal(size=(dim,dim))+1j*rng.normal(size=(dim,dim));V=(V+V.conj().T)/2;V=(V+J@V.conj()@J.conj().T)/2
        back.append(abs(np.vdot(J@u.conj(),V@u)))
result['Kramers_backscatter_max']=float(max(back));result['two_pair_allowed_matrix_element']=1.0

signchecks=[]
for k in np.linspace(.1,6.1,19):
    for v in [.1,.4]:
        es=eigvalsh(ribbon(k,n=30,v=v))
        flipso=eigvalsh(ribbon(k,n=30,v=v,so=-.06))
        flipr=eigvalsh(ribbon(k,n=30,v=v,r=-.05))
        zero=eigvalsh(ribbon(k,n=30,v=v,r=0))
        signchecks.append({'SO_flip_E_reflection':float(abs(flipso+es[::-1]).max()),'R_flip_invariant':float(abs(flipr-es).max()),'R_zero_particle_hole':float(abs(zero+zero[::-1]).max())})
result['energy_sign_controls']={key:max(row[key] for row in signchecks) for key in signchecks[0]}

ref=json.loads(Path('reference/vector_curves.json').read_text())['panels'];bands=np.load('data/bands.npz');curves=np.load('data/pf_curves.npz');comparison={};residuals={}
for key,tag in [('F1a','qsh'),('F1b','trivial')]:
    xy=np.concatenate([np.asarray(p['ke']) for p in ref[key]['paths']]);xy=np.unique(xy,axis=0)
    mask=(xy[:,0]>=0)&(xy[:,0]<=2*np.pi);xy=xy[mask]
    model=np.column_stack([np.interp(xy[:,0],bands['k'],e) for e in bands[tag].T])
    literal=np.min(abs(model-xy[:,1,None]),axis=1);reversed_=np.min(abs(model+xy[:,1,None]),axis=1)
    comparison[key]={'all_displayed_vertices':len(xy),'literal_E':{'rmse':float(np.sqrt(np.mean(literal**2))),'max_abs':float(max(literal))},'E_reflected':{'rmse':float(np.sqrt(np.mean(reversed_**2))),'max_abs':float(max(reversed_))},'observable':'distance to the nearest complete ribbon eigenvalue at every unique original displayed vector vertex'}
    residuals[key]=np.column_stack([xy,literal,reversed_])
for tag,key in [('qsh','QSH'),('trivial','I')]:
    xy=np.array(ref['F2c']['curves'][key]);calc=np.interp(xy[:,0]*np.pi,curves['alpha'],curves[tag]);err=calc-xy[:,1]
    comparison['F2c_'+key]={'vertices':len(xy),'max_abs':float(abs(err).max()),'rmse':float(np.sqrt(np.mean(err**2))),'reference_sample_min':xy[xy[:,1].argmin()].tolist()}
    residuals['F2c_'+key]=np.column_stack([xy,calc,err])
result['original_vector_comparison']=comparison

obs=json.loads(Path('data/observables.json').read_text());result['spin_conductance']={}
for key,states in obs['edge_fermi'].items():
    edge=[s for s in states if s['mean_row']<15]
    left=[s for s in edge if s['velocity']<0];right=[s for s in edge if s['velocity']>0]
    result['spin_conductance'][key]={'edge_states':len(edge),'G_over_e_over_2pi':left[0]['Sz_over_hbar']-right[0]['Sz_over_hbar'] if len(left)==len(right)==1 else None}

result['numerical_criteria']={'matrix_error_tolerance':1e-10,'source_display_comparison_target':3e-4,'timing':'Declared after exploratory calculations, not preregistered; all raw residuals retained.','scope':'Source display accuracy, not author-array identity; no pixel score used as physics evidence.'}
result['execution']={'route':'native exec_command, restricted task workspace; PRAgent execute rejected before launch','seconds':time.monotonic()-start,'not_a_pragent_receipt':True}
Path('checks').mkdir(exist_ok=True);Path('checks/results.json').write_text(json.dumps(result,indent=2)+'\n');np.savez_compressed('checks/reference_residuals.npz',**residuals)
print(json.dumps(result,indent=2))
