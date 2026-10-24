"""Independent formulations: direct density ODE, dense expm, Dyson hierarchy,
explicit Pauli channel enumeration, Kraus/PTM algebra. No generator imports."""
import json,itertools,math,time,sys
from pathlib import Path
import numpy as np
from scipy.linalg import expm,block_diag
from scipy.integrate import solve_ivp
from scipy.sparse import bmat,csr_matrix
from scipy.sparse.linalg import expm_multiply
from threadpoolctl import threadpool_limits
I=np.eye(2,dtype=complex); X=np.array([[0,1],[1,0]],complex); Y=np.array([[0,-1j],[1j,0]],complex); Z=np.diag([1.,-1.]).astype(complex)
PA=[I,X,Y,Z]; H=(X+Z)/np.sqrt(2); S=np.diag([1,1j]); T=np.diag([1,np.exp(1j*np.pi/4)])
def kron(xs):
    r=np.ones((1,1),complex)
    for x in xs:r=np.kron(r,x)
    return r
def at(x,q,n):return kron([x if i==q else I for i in range(n)])
def chan(u):return np.kron(u.conj(),u)
def sup(fun,d):
    r=np.zeros((d*d,d*d),complex)
    for k in range(d*d):
        v=np.zeros(d*d,complex);v[k]=1
        r[:,k]=fun(v.reshape(d,d,order='F')).reshape(-1,order='F')
    return r
def prep(v):
    v=np.asarray(v,dtype=complex);rho=np.outer(v,v.conj());return sup(lambda r:np.trace(r)*rho,2)
def damping(e):
    a0=np.diag([1,np.sqrt(1-e)]);a1=np.array([[0,np.sqrt(e)],[0,0]])
    return chan(a0)+chan(a1)
def reset_loop(r,qs,n):
    # Explicit index trace; unlike generator tensor-axis contraction.
    d=2**n; mask=sum(1<<(n-1-q) for q in qs); ans=np.zeros_like(r)
    assignments=[i for i in range(d) if i&~mask==0]
    for a in range(d):
        for b in range(d):
            if (a&mask)==(b&mask):ans[a,b]=sum(r[(a&~mask)|s,(b&~mask)|s] for s in assignments)/len(assignments)
    return ans

def fig1_check():
    z=np.load('results/fig1_inputs.npz'); f=json.loads(Path('results/fig1.json').read_text());
    hs=z['H']; a=z['A']; rho=z['rho0']; cs=z['c']; n=4; d=16
    xs=[at(X,q,n) for q in range(n)];zs=[at(Z,q,n) for q in range(n)];ys=[at(Y,q,n) for q in range(n)]
    ls=[at((X-1j*Y)/2,q,n) for q in range(n)]; ldag=[l.conj().T@l for l in ls]
    basis=np.eye(d*d).reshape(d*d,d,d)
    # ODE uses matrix commutators and local channel operations; no Liouville matrix.
    def dissip(r,model):
        if model=='depolarizing':return sum((x@r@x+y@r@y+zz@r@zz-3*r)/4 for x,y,zz in zip(xs,ys,zs))
        return sum(1.5*(l@r@l.conj().T-(ld@r+r@ld)/2)+zz@r@zz-r for l,ld,zz in zip(ls,ldag,zs))
    numerical={}
    for model in ['depolarizing','amp_dephase']:
        diffs=[]; extdiff=[]; rows=[]
        for ei in [0,2,7]:
            lam=f['lambda'][ei]; vals=[]
            for c in cs:
                y=rho.reshape(-1)
                for h in hs:
                    def rhs(t,y):
                        r=y.reshape(d,d);return (-1j*(h@r-r@h)+lam*c*dissip(r,model)).reshape(-1)
                    sol=solve_ivp(rhs,(0,2),y,method='DOP853',rtol=2e-13,atol=2e-14)
                    assert sol.success;y=sol.y[:,-1]
                val=float(np.trace(a@y.reshape(d,d)).real);vals.append(val)
            ref=np.array(f['models'][model]['expectations'][ei]);diffs.extend(np.abs(np.array(vals)-ref).tolist())
            for order in range(4):
                nodes=cs[:order+1]; weights=np.array([np.prod([nodes[k]/(nodes[k]-nodes[j]) for k in range(order+1) if k!=j]) for j in range(order+1)])
                extdiff.append(float(abs(weights@(np.array(vals[:order+1])-ref[:order+1]))))
            rows.append({'epsilon':f['epsilon'][ei],'expectations':vals})
        numerical[model]={'max_observable_difference':max(diffs),'max_extrapolated_difference':max(extdiff),'rows':rows}
        print('ODE check',model,numerical[model]['max_observable_difference'],flush=True)
    # Matrix expm on total Hamiltonian, independent from Hermitian eigensolver.
    ps=z['bath_psi0']; v=z['bath_V']; af=np.kron(a,np.eye(d)); diffs=[]; rows=[]
    for ei in [0,2,7]:
        vals=[]
        for c in cs:
            pp=ps.copy()
            for h in hs:pp=expm(-2j*(np.kron(h,np.eye(d))+f['lambda'][ei]*c*v))@pp
            val=float(np.vdot(pp,af@pp).real);vals.append(val)
        diff=np.array(vals)-f['models']['bath']['expectations'][ei];diffs.extend(abs(diff).tolist());rows.append({'epsilon':f['epsilon'][ei],'expectations':vals})
    numerical['bath']={'max_observable_difference':max(diffs),'rows':rows}
    # Taylor coefficients from block-triangular Schrodinger hierarchy (not finite differences).
    degree=5; total=np.zeros(((degree+1)*d*d,d),complex);total[:d*d]=ps
    for h in hs:
        hf=csr_matrix(-1j*np.kron(h,np.eye(d))); vf=csr_matrix(-1j*v)
        blocks=[[hf if j==k else vf if j==k+1 else None for k in range(degree+1)] for j in range(degree+1)]
        mat=bmat(blocks,format='csr');total=expm_multiply(2*mat,total,traceA=2*(degree+1)*hf.diagonal().sum())
    ws=total.reshape(degree+1,d*d,d)
    coeff=[float(sum(np.vdot(ws[j],af@ws[k-j]) for j in range(k+1)).real) for k in range(degree+1)]
    residual=[]
    for ei,lam in enumerate(f['lambda']):
        series=sum(coeff[k]*lam**k for k in range(degree+1));residual.append(abs(series-f['models']['bath']['expectations'][ei][0]))
    numerical['bath']['dyson_coefficients_E0_through_E5']=coeff
    numerical['bath']['dyson_truncation_residual_by_epsilon']=residual
    numerical['bath']['first_order_cancellation_prediction']=float(cs[1])
    numerical['bath']['observed_n1_error_amplification_low_epsilon']=f['models']['bath']['errors'][1][0]/f['models']['bath']['errors'][0][0]
    # Time stretching checked at noncommuting controls with fixed physical Lindblad term.
    h=hs[0];lam=.003;c=2.7; rr=rho.reshape(-1,order='F')
    m=-1j*(np.kron(np.eye(d),h)-np.kron(h.T,np.eye(d)))
    left=expm(2*c*(m/c+lam*z['dep']))@rr;right=expm(2*(m+c*lam*z['dep']))@rr
    numerical['rescaling_max_state_difference']=float(np.max(abs(left-right)))
    return numerical

def qpr_checks():
    out={};epss=[.001,.01,.15,.7]; residuals=[];gammaerrors=[]
    rng=np.random.default_rng(20261023)
    for k in [1,2]:
        d=2**k; ps=[kron(v) for v in itertools.product(PA,repeat=k)]
        reset=sup(lambda r:np.eye(d)*np.trace(r)/d,d)
        for e in epss:
            dep=(1-e)*np.eye(d*d)+e*reset;eta=np.full(d*d,-e/(d*d*(1-e)));eta[0]=(1-e/(d*d))/(1-e)
            inv=sum(t*chan(p) for t,p in zip(eta,ps));residuals.append(float(np.max(abs(dep@inv-np.eye(d*d)))))
            ga=(1+(1-2/(d*d))*e)/(1-e);gammaerrors.append(abs(abs(eta).sum()-ga))
    out['depolarizing_inverse_max_residual']=max(residuals);out['gamma_max_residual']=max(gammaerrors)
    # Fully enumerate QPR branches in a non-Clifford two-qubit four-gate circuit.
    n=2;d=4;e=.03;per=np.array([0,1,3,2]);cx=np.eye(4)[per]
    gates=[(np.kron(H,I),[0]),(np.kron(I,T),[1]),(cx,[0,1]),(np.kron(I,H),[1])]
    start=np.full((d,d),1/d,complex); states=[(1.,1,start)];ideal=start.copy()
    for u,qs in gates:
        ideal=u@ideal@u.conj().T;k=len(qs);g=(1+(1-2/4**k)*e)/(1-e);ets=np.full(4**k,-e/(4**k*(1-e)));ets[0]=(1-e/4**k)/(1-e)
        ps=[]
        for ids in itertools.product(range(4),repeat=k):
            maps=dict(zip(qs,ids));ps.append(kron([PA[maps.get(q,0)] for q in range(n)]))
        new=[]
        for prob,sign,r in states:
            ru=u@r@u.conj().T
            for eta,p in zip(ets,ps):
                rp=p@ru@p.conj().T;noisy=(1-e)*rp+e*reset_loop(rp,qs,n)
                new.append((prob*abs(eta)/g,sign*(1 if eta>0 else -1),noisy))
        states=new
    gamma=((1+e/2)/(1-e))**3*((1+7*e/8)/(1-e))
    unsigned=sum(p*r for p,s,r in states);signed=sum(p*s*r for p,s,r in states)
    mask=np.argsort(np.diag(ideal).real)[-2:];q=np.diag(unsigned).real[mask].sum();eid=np.diag(ideal).real[mask].sum()
    probs=np.zeros(3)
    for p,s,r in states:
        a=np.diag(r).real[mask].sum();probs[0 if s==1 else 1]+=p*a;probs[2]+=p*(1-a)
    predicted=np.array([(q+eid/gamma)/2,(q-eid/gamma)/2,1-q])
    out['exhaustive_branch_count']=len(states);out['exhaustive_signed_density_residual']=float(np.max(abs(gamma*signed-ideal)))
    out['joint_estimator_probability_residual']=float(np.max(abs(probs-predicted)))
    out['joint_probabilities']=probs.tolist()
    # Direct four-outcome physical-noise mixture vs analytic absolute-mixture shrinkage.
    errs=[]
    for k in [1,2]:
        d=2**k;ps=[kron(v) for v in itertools.product(PA,repeat=k)];a=rng.normal(size=(d,d))+1j*rng.normal(size=(d,d));r=a@a.conj().T;r/=np.trace(r)
        p=e/(4**k+(4**k-2)*e);mix=(1-(4**k-1)*p)*r+sum(p*z@r@z.conj().T for z in ps[1:]);actual=(1-e)*mix+e*np.eye(d)/d
        shrink=(1-e)*(1-4**k*p);expected=shrink*r+(1-shrink)*np.eye(d)/d;errs.append(float(np.max(abs(actual-expected))))
    out['unsigned_channel_residual']=max(errs)
    return out

def amplitude_checks():
    out={};res=[];preps=[];norms=[];p0=prep([1,0]);pp=prep(np.array([1,1])/np.sqrt(2));pm=prep(np.array([1,-1])/np.sqrt(2));p1=prep([0,1])
    for e in [.001,.01,.2,.7]:
        s=np.sqrt(1-e);am=damping(e);eta=np.array([1/s,(1-s)/(2*(1-e)),(1-s)/(2*(1-e)),-e/(1-e)])
        inv=eta[0]*np.eye(4)+eta[1]*chan(S)+eta[2]*chan(S.conj().T)+eta[3]*p0
        res.append(float(np.max(abs(am@inv-np.eye(4)))))
        ep=np.array([(1/s+(1-2*e)/(1-e))/2,(-1/s+(1-2*e)/(1-e))/2,e/(1-e)])
        preps.append(float(np.max(abs(ep[0]*am@pp+ep[1]*am@pm+ep[2]*am@p1-pp))))
        norms.append({'epsilon':e,'gamma':(1+e)/(1-e),'inverse_l1':float(abs(eta).sum()),'prep_l1':float(abs(ep).sum())})
    out['inverse_identity_residual']=max(res);out['prep_identity_residual']=max(preps);out['norms']=norms
    # Explicit two-qubit CNOT + (H on control, T on target), including every reset branch.
    e=.01;s=np.sqrt(1-e);eta=[1/s,(1-s)/(2*(1-e)),(1-s)/(2*(1-e)),-e/(1-e)];am=damping(e)
    unit=[I,S,S.conj().T,I];cx=np.eye(4)[[0,1,3,2]];follow=[H,T];sumchan=np.zeros((16,16),complex);tot=0.
    # Construct tensor product channels from action to respect column-major vectorization.
    def tensor_channels(a,b):
        def fun(r):
            z=r.reshape(2,2,2,2)
            # Apply via local operator-basis expansion, no Kronecker-order shortcut.
            o=np.zeros((4,4),complex)
            for i,j,k,l in itertools.product(range(2),repeat=4):
                e1=np.zeros((2,2));e1[i,k]=1;e2=np.zeros((2,2));e2[j,l]=1
                ra=(a@e1.reshape(-1,order='F')).reshape(2,2,order='F');rb=(b@e2.reshape(-1,order='F')).reshape(2,2,order='F')
                o+=z[i,j,k,l]*np.kron(ra,rb)
            return o
        return sup(fun,4)
    amp2=tensor_channels(am,am)
    for i,j in itertools.product(range(4),repeat=2):
        noisy_cnot=amp2@chan(np.kron(unit[i],unit[j])@cx)
        follow_qprs=[]
        for q,index in enumerate([i,j]):
            if index!=3:
                u=follow[q];follow_qprs.append([(eta[0],am@chan(u)),(eta[1],am@chan(S@u)),(eta[2],am@chan(S.conj().T@u)),(eta[3],p0)])
            elif q==0:
                ep=[(1/s+(1-2*e)/(1-e))/2,(-1/s+(1-2*e)/(1-e))/2,e/(1-e)]
                follow_qprs.append([(ep[0],am@pp),(ep[1],am@pm),(ep[2],am@p1)])
            else:follow_qprs.append([(1.,p0)])
        # Sum branches analytically only after their individual physical-channel forms are defined.
        qa=sum(w*c for w,c in follow_qprs[0]);qb=sum(w*c for w,c in follow_qprs[1])
        sumchan+=eta[i]*eta[j]*tensor_channels(qa,qb)@noisy_cnot
        tot+=abs(eta[i]*eta[j])*sum(abs(w) for w,c in follow_qprs[0])*sum(abs(w) for w,c in follow_qprs[1])
    target=chan(np.kron(H,T)@cx)
    out['full_cnot_following_layer_residual']=float(np.max(abs(sumchan-target)))
    out['full_cnot_following_layer_l1']=tot;out['gamma_power4_bound']=((1+e)/(1-e))**4
    return out

def direct_figure2_check():
    f=json.loads(Path('results/fig2.json').read_text());rows=np.array(f['rows']);errs=[];unsigned_err=[];ideals=[]
    n=6;d=64;eps=.01;one=[I,H,S,T]
    # Apply dense gates and depolarization as Pauli twirling, unlike tensor-axis reset.
    # Three circuits are enough to cross-check the physical implementation at full size/depth.
    for ci in [0,137,499]:
        rho=np.ones((d,d),complex)/d;ur=rho.copy();ideal=rho.copy()
        for typ,p,q in f['circuits'][ci]:
            qs=[p] if typ=='one' else [p,q]
            if typ=='one':u=at(one[q],p,n)
            else:
                u=np.eye(d);perm=np.arange(d)^(((np.arange(d)>>(n-1-p))&1)<<(n-1-q));u=u[perm]
            rho=u@rho@u.conj().T;ur=u@ur@u.conj().T;ideal=u@ideal@u.conj().T
            ps=[]
            for ids in itertools.product(range(4),repeat=len(qs)):
                dic=dict(zip(qs,ids));ps.append(kron([PA[dic.get(j,0)] for j in range(n)]))
            twirl=sum(z@rho@z for z in ps)/len(ps);utwirl=sum(z@ur@z for z in ps)/len(ps)
            rho=(1-eps)*rho+eps*twirl;ep=f['absolute_ensemble_depol'][str(len(qs))];ur=(1-ep)*ur+ep*utwirl
        top=np.argsort(np.diag(ideal).real,kind='stable')[-32:]
        # If ideal probabilities tie, selecting a different equally weighted basis subset may alter noisy A.
        # Reconstruct generator's ideal vector via independent dense gates to recover its same declared observable.
        vec=np.ones(d,complex)/8
        for typ,p,q in f['circuits'][ci]:
            if typ=='one':u=at(one[q],p,n)
            else:
                perm=np.arange(d)^(((np.arange(d)>>(n-1-p))&1)<<(n-1-q));u=np.eye(d)[perm]
            vec=u@vec
        alternate_top=np.argsort(abs(vec)**2,kind='stable')[-32:]
        top=np.array(f['observable_basis_indices'][ci])
        excluded=np.setdiff1d(np.arange(d),top)
        boundary_gap=float(np.max(abs(vec[excluded])**2)-np.min(abs(vec[top])**2))
        errors=[abs(np.diag(ideal).real[top].sum()-rows[ci,0]),abs(np.diag(rho).real[top].sum()-rows[ci,1]),abs(np.diag(ur).real[top].sum()-rows[ci,2])]
        errs.append({'circuit':ci,'differences':list(map(float,errors)),
                     'alternate_tied_projector_noisy_change':float(np.diag(rho).real[alternate_top].sum()-np.diag(rho).real[top].sum()),
                     'top_half_selection_boundary_gap':boundary_gap})
    # Prespecified cohort statistics; bootstrap quantifies our new cohort only.
    rng=np.random.default_rng(414);boots=np.median(rows[rng.integers(0,500,(5000,500))][:,:,[5,6]],axis=1)
    se=f['mean_bias_on_SE'];out={'full_size_crosschecks':errs,'median_errors':np.median(rows[:,5:7],axis=0).tolist(),'median_bootstrap_95CI':np.quantile(boots,[.025,.975],axis=0).tolist(),'mean_bias_z':f['mean_bias_on']/se,'rmse_off_on':np.sqrt(np.mean((rows[:,[3,4]]-rows[:,[0]])**2,axis=0)).tolist(),'ideal_range':[float(rows[:,0].min()),float(rows[:,0].max())],'improved_fraction':float(np.mean(rows[:,6]<rows[:,5])),'source_median_off':.15,'source_median_on':.05}
    return out

def literal_checks():
    out={};tests=[]
    for n in range(1,4):
        c=np.arange(1,n+2,dtype=float);wrong=np.array([np.prod([c[m]/(c[j]-c[m]) for m in range(n+1) if m!=j]) for j in range(n+1)]);right=(-1)**n*wrong
        tests.append({'order':n,'printed':wrong.tolist(),'printed_sum':float(wrong.sum()),'corrected':right.tolist(),'moment_residual':float(max(abs(right@c**k-(k==0)) for k in range(n+1)))})
    out['richardson']=tests;out['literal_depolarization_min_eigenvalue_t1_lambda001']=(1-math.exp(.01))/2
    out['physical_depolarization_min_eigenvalue_t1_lambda001']=(1-math.exp(-.01))/2
    # Consistent Schr vs printed interaction-picture definition for noise-free, noncommuting rho.
    r=np.array([[1.,0],[0,0]],complex);u=expm(-.3j*X);rs=u@r@u.conj().T
    out['printed_interaction_picture_noise_free_change']=float(np.max(abs(u@rs@u.conj().T-r)))
    out['correct_interaction_picture_noise_free_change']=float(np.max(abs(u.conj().T@rs@u-r)))
    return out

if __name__=='__main__':
    start=time.monotonic();out=json.loads(Path('checks/numerical_checks.json').read_text()) if ('--resume' in sys.argv or '--fig2-only' in sys.argv) else {}
    if '--fig2-only' in sys.argv: out.pop('fig2',None)
    with threadpool_limits(limits=1):
        for name,fn in [('literal',literal_checks),('qpr',qpr_checks),('amplitude',amplitude_checks),('fig1',fig1_check),('fig2',direct_figure2_check)]:
            if name in out: continue
            out[name]=fn();Path('checks/numerical_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(name,'done',flush=True)
    out['runtime_seconds']=time.monotonic()-start;Path('checks/numerical_checks.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
