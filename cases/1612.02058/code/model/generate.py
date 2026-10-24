"""Independent generation from fixed-paper equations; reads no reference figures/data."""
import os
os.environ.setdefault('MPLCONFIGDIR', os.path.abspath('mpl-cache'))
import json, time, itertools, sys
from pathlib import Path
import numpy as np
import scipy.linalg as la
from scipy.sparse.linalg import expm_multiply
from threadpoolctl import threadpool_limits

P = [np.eye(2,dtype=complex), np.array([[0,1],[1,0]],complex),
     np.array([[0,-1j],[1j,0]],complex), np.diag([1.,-1.]).astype(complex)]
def kron_all(xs):
    a=np.array([[1.]],complex)
    for x in xs: a=np.kron(a,x)
    return a
def op1(a,q,n): return kron_all([a if j==q else P[0] for j in range(n)])
def haar(rng):
    z=rng.normal(size=(2,2))+1j*rng.normal(size=(2,2))
    q,r=la.qr(z); q=q @ np.diag(np.diag(r)/np.abs(np.diag(r)))
    return q/np.sqrt(la.det(q))
def rich_weights(c):
    return np.linalg.solve(np.array([np.asarray(c)**k for k in range(len(c))]), np.eye(len(c))[0])
def comm_super(h):
    d=len(h); return -1j*(np.kron(np.eye(d),h)-np.kron(h.T,np.eye(d)))
def lindblad(l):
    a=l.conj().T@l; d=len(l)
    return np.kron(l.conj(),l)-0.5*(np.kron(np.eye(d),a)+np.kron(a.T,np.eye(d)))
def reset_local(rho,qs,n):
    # Partial trace over specified ket/bra axes, then I/d inserted at same sites.
    qs=list(qs); rest=[q for q in range(n) if q not in qs]
    order=qs+rest+[n+q for q in qs]+[n+q for q in rest]
    inv=np.argsort(order); k=2**len(qs); r=2**(n-len(qs))
    t=rho.reshape([2]*(2*n)).transpose(order).reshape(k,r,k,r)
    tr=np.einsum('ar as->rs',t) if False else np.einsum('aras->rs',t)
    out=np.einsum('ab,rs->arbs',np.eye(k)/k,tr).reshape([2]*(2*n))
    return out.transpose(inv).reshape(2**n,2**n)
def apply_one(rho,u,q,n):
    t=rho.reshape([2]*(2*n))
    t=np.tensordot(u,t,axes=(1,q)); t=np.moveaxis(t,0,q)
    t=np.tensordot(u.conj(),t,axes=(1,n+q)); t=np.moveaxis(t,0,n+q)
    return t.reshape(2**n,2**n)
def apply_vec(v,u,q,n):
    t=np.tensordot(u,v.reshape([2]*n),axes=(1,q)); return np.moveaxis(t,0,q).reshape(-1)
def cnot_perm(c,t,n):
    x=np.arange(2**n); return x ^ (((x>>(n-1-c))&1)<<(n-1-t))

def figure1(cfg,rng):
    n=cfg['N']; d=2**n; X=[op1(P[1],q,n) for q in range(n)]; Z=[op1(P[3],q,n) for q in range(n)]
    j=rng.normal(0,cfg['coupling_std'],size=(n,n))*(rng.random((n,n))<cfg['graph_probability']); np.fill_diagonal(j,0)
    h0=sum(j[a,b]*X[a]@Z[b] for a in range(n) for b in range(n) if a!=b)
    hs=[]
    for _ in range(cfg['depth']):
        u=kron_all([haar(rng) for q in range(n)]); hs.append(u@h0@u.conj().T)
    paulis=rng.integers(1,4,size=n); a=kron_all([P[i] for i in paulis])
    c=np.r_[1.,np.sort(rng.uniform(1.,4.,3))]
    v=np.eye(d,dtype=complex)[:,0]; rho=np.outer(v,v.conj())
    ideal=rho.copy()
    for h in hs:
        u=la.expm(-1j*cfg['duration']*h); ideal=u@ideal@u.conj().T
    e0=np.trace(a@ideal).real
    dep=sum(lindblad(op1(P[p],q,n))/4 for q in range(n) for p in [1,2,3])
    # Source sigma^- = (X-iY)/2; its selected ground state is |1> in this convention.
    low=(P[1]-1j*P[2])/2
    damp=sum(1.5*lindblad(op1(low,q,n))+lindblad(Z[q]) for q in range(n))
    unitary=[comm_super(h) for h in hs]
    rates=-0.5*np.log1p(-np.asarray(cfg['eps']))
    out={'epsilon':cfg['eps'],'lambda':rates.tolist(),'c':c.tolist(),'Eideal':e0,'pauli_indices':paulis.tolist(),'J':j.tolist(),'models':{}}
    hsfull=[np.kron(h,np.eye(d)) for h in hs]
    bath_v=sum(0.5*np.kron(X[q],X[q])+0.5*np.kron(np.eye(d),Z[q]) for q in range(n))
    pb=np.exp(-cfg['beta']*np.diag(P[3]).real/2); pb/=pb.sum(); weights=np.diag(kron_all([np.diag(pb)]*n)).real
    psi0=np.zeros((d*d,d),complex); psi0[:d,:]=np.diag(np.sqrt(weights))
    afull=np.kron(a,np.eye(d))
    states={}
    for name in ['depolarizing','amp_dephase','bath']:
        values=[]; traces=[]; mineigs=[]
        for lam in rates:
            row=[]
            for scale in c:
                if name!='bath':
                    l=dep if name=='depolarizing' else damp
                    state=rho.reshape(-1,order='F')
                    for u in unitary: state=expm_multiply(cfg['duration']*(u+lam*scale*l),state,traceA=np.trace(cfg['duration']*(u+lam*scale*l)))
                    r=state.reshape(d,d,order='F'); e=np.trace(a@r).real
                    traces.append(abs(np.trace(r)-1)); mineigs.append(la.eigvalsh(r).min())
                else:
                    psi=psi0.copy()
                    for h in hsfull:
                        ev,w=la.eigh(h+lam*scale*bath_v); psi=w@(np.exp(-1j*cfg['duration']*ev)[:,None]*(w.conj().T@psi))
                    e=np.vdot(psi,afull@psi).real; traces.append(abs(np.vdot(psi,psi)-1))
                row.append(float(e))
            values.append(row)
        vals=np.array(values); errors=[]
        for order in range(4): errors.append(np.abs(vals[:,:order+1]@rich_weights(c[:order+1])-e0).tolist())
        out['models'][name]={'expectations':values,'errors':errors,'trace_error_max':float(max(traces)),'min_eigenvalue':float(min(mineigs)) if mineigs else None}
        print('Fig1',name,'low-noise errors',[x[0] for x in errors],flush=True)
    np.savez('results/fig1_inputs.npz',H=np.array(hs),A=a,rho0=rho,c=c,dep=dep,damp=damp,bath_V=bath_v,bath_psi0=psi0)
    return out

def figure2(cfg,rng):
    n=cfg['N']; d=2**n; eps=cfg['epsilon']; M=cfg['M']
    gates=[P[0],(P[1]+P[3])/np.sqrt(2),np.diag([1,1j]),np.diag([1,np.exp(1j*np.pi/4)])]
    gammas={1:(1+eps/2)/(1-eps),2:(1+7*eps/8)/(1-eps)}
    gamma=gammas[1]**(n*cfg['depth']//2)*gammas[2]**(n*cfg['depth']//4)
    # Absolute QPR ensemble is another depolarizing channel: factor (1-eps)*(1-4^k*p_k).
    qeps={k:1-(1-eps)*(1-4**k*eps/(4**k+(4**k-2)*eps)) for k in [1,2]}
    rows=[]; circuits=[]; observables=[]
    for ci in range(cfg['circuits']):
        v=np.ones(d,complex)/np.sqrt(d); rho=np.outer(v,v.conj()); unsigned=rho.copy(); circ=[]
        for layer in range(cfg['depth']):
            if layer%2==0:
                for q in range(n):
                    gi=int(rng.integers(4)); u=gates[gi]; circ.append(['one',q,gi]); v=apply_vec(v,u,q,n)
                    rho=apply_one(rho,u,q,n); unsigned=apply_one(unsigned,u,q,n)
                    rho=(1-eps)*rho+eps*reset_local(rho,[q],n)
                    unsigned=(1-qeps[1])*unsigned+qeps[1]*reset_local(unsigned,[q],n)
            else:
                pairs=rng.permutation(n).reshape(-1,2)
                for c,t in pairs:
                    c,t=int(c),int(t); circ.append(['cnot',c,t]); perm=cnot_perm(c,t,n); v=v[perm]
                    rho=rho[np.ix_(perm,perm)]; unsigned=unsigned[np.ix_(perm,perm)]
                    rho=(1-eps)*rho+eps*reset_local(rho,[c,t],n)
                    unsigned=(1-qeps[2])*unsigned+qeps[2]*reset_local(unsigned,[c,t],n)
        probs=np.abs(v)**2; top=np.argsort(probs,kind='stable')[-d//2:]
        ideal=float(probs[top].sum()); noisy=float(np.diag(rho).real[top].sum()); q=float(np.diag(unsigned).real[top].sum())
        pj=np.array([(q+ideal/gamma)/2,(q-ideal/gamma)/2,1-q])
        assert np.min(pj)>-1e-12 and abs(pj.sum()-1)<1e-12
        counts=rng.multinomial(M,pj)
        mitigated=gamma*(counts[0]-counts[1])/M
        off=rng.binomial(M,noisy)/M
        rows.append([ideal,noisy,q,off,float(mitigated),abs(off-ideal),abs(mitigated-ideal),(gamma**2*q-ideal**2)/M])
        observables.append(top.tolist())
        circuits.append(circ)
        if ci%100==0: print('Fig2 circuits',ci,flush=True)
    ar=np.array(rows)
    return {'gamma':gamma,'gamma_over_sqrt_M':gamma/np.sqrt(M),'absolute_ensemble_depol':qeps,'columns':['ideal','noisy_exact','unsigned_QPR_A','off_sample','on_sample','off_error','on_error','on_variance'],'rows':rows,'circuits':circuits,'observable_basis_indices':observables,'median_off':float(np.median(ar[:,5])),'median_on':float(np.median(ar[:,6])),'mean_bias_on':float(np.mean(ar[:,4]-ar[:,0])),'mean_bias_on_SE':float(np.sqrt(ar[:,7].sum())/len(ar))}

def main():
    cfg=json.loads(Path('config.json').read_text()); Path('results').mkdir(exist_ok=True)
    with threadpool_limits(limits=1):
        if '--fig2-only' in sys.argv:
            f2=figure2(cfg['fig2'],np.random.default_rng(cfg['seed']+1)); Path('results/fig2.json').write_text(json.dumps(f2,separators=(',',':')));return
        start=time.monotonic(); f1=figure1(cfg['fig1'],np.random.default_rng(cfg['seed'])); Path('results/fig1.json').write_text(json.dumps(f1,indent=2))
        f2=figure2(cfg['fig2'],np.random.default_rng(cfg['seed']+1)); Path('results/fig2.json').write_text(json.dumps(f2,separators=(',',':')))
        Path('results/runtime.json').write_text(json.dumps({'seconds':time.monotonic()-start}))
        print({k:v for k,v in f2.items() if k not in ['rows','circuits']},flush=True)
if __name__=='__main__': main()
