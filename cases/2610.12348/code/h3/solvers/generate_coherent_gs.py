"""Full coherent free-particle GS photon-counting trajectories.

Unlike the Q-sector mixture this keeps coherence between all initial X sectors.
It uses the same Hamiltonian with an explicit cavity cutoff, no adiabatic
elimination. A pilot measures cost before a larger ensemble is requested.
"""
import json, math, time
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import numpy as np
from scipy.sparse import diags, eye, kron
from scipy.integrate import solve_ivp
from generate_statics import basis, matrix, entropies


class CoherentHybrid:
    def __init__(self, L, N, statistics, nmax, delta, gamma):
        self.L,self.N,self.stats,self.nmax=L,N,statistics,nmax
        self.states=basis(L,N,statistics);self.M=len(self.states)
        self.occ=np.array(self.states);self.X=self.occ@np.arange(1,L+1)
        self.bonds=[matrix(self.states,self.states,[(1,[(j+1,-1),(j,1)])],statistics) for j in range(L-1)]
        self.O=sum(self.bonds)
        a=diags(np.sqrt(np.arange(1,nmax+1)),1,shape=(nmax+1,nmax+1))
        ph=np.arange(nmax+1)
        self.G=1j*(kron(a.T,self.O)+kron(a,self.O.T))+kron(diags((-1j*delta-gamma/2)*ph),eye(self.M))
        self.G=self.G.tocsr();self.ph=np.repeat(ph,self.M)
        dst=basis(L,N-2,statistics) if N>=2 else []
        self.pairs=[matrix(self.states,dst,[((-1)**j*(.5 if j==L-1-j else 1),[(j,-1),(L-1-j,-1)])],statistics) for j in range((L+1)//2)] if N>=2 else []
        modes=np.arange(L-N+1,L+1)
        phi=np.sqrt(2/(L+1))*np.sin(np.pi*np.arange(1,L+1)*L/(L+1))
        v=[]
        for n in self.states:
            if statistics=='fermion':
                pos=np.flatnonzero(n)+1
                z=np.linalg.det(np.sqrt(2/(L+1))*np.sin(np.pi*pos[:,None]*modes[None,:]/(L+1)))
            else:z=math.sqrt(math.factorial(N)/math.prod(math.factorial(x) for x in n))*math.prod(phi[j]**x for j,x in enumerate(n))
            v.append(z)
        self.gs=np.zeros((nmax+1,self.M),complex);self.gs[0]=v;self.gs/=np.linalg.norm(self.gs)

    def entropy(self, psi):
        # Exact zero support is cheap to omit. The recorded nonzero tail below
        # 1e-14 amplitude only affects this observable, never the evolution.
        inds=np.flatnonzero(abs(psi)>1e-14);discarded=float(np.sum(abs(psi)**2)-np.sum(abs(psi[inds])**2))
        rows=[(int(i//self.M),self.states[i%self.M]) for i in inds]
        maps=[]
        for cut in range(self.L):
            buckets=defaultdict(list)
            for idx,(p,n) in enumerate(rows):
                left=(p,)+n[:cut];right=n[cut:]
                buckets[sum(right)].append((idx,left,right))
            groups=[]
            for b in buckets.values():
                li={x:i for i,x in enumerate(sorted({r[1] for r in b}))};ri={x:i for i,x in enumerate(sorted({r[2] for r in b}))}
                groups.append((len(li),len(ri),np.array([r[0] for r in b]),np.array([li[r[1]] for r in b]),np.array([ri[r[2]] for r in b])))
            maps.append(groups)
        return entropies(psi[inds,None],maps)[0],max(0.,discarded)

    def trajectory(self, rng, cfg):
        times=np.array(cfg['times']);psi=self.gs.ravel().copy();t=0.;sample=0;trace=[];jumps=0;nfev=0;top=0.
        while t<times[-1]-1e-10:
            threshold=rng.random()
            def event(t,y):return np.vdot(y,y).real-threshold
            event.terminal=True;event.direction=-1
            def rhs(t,y):
                nonlocal top
                norm=np.vdot(y,y).real
                if norm:top=max(top,float(np.vdot(y[-self.M:],y[-self.M:]).real/norm))
                return self.G@y
            # t_eval prevents retaining every large internal state and dense
            # interpolant; event states are returned separately by SciPy.
            sol=solve_ivp(rhs,(t,times[-1]),psi,method='DOP853',rtol=cfg['rtol'],atol=cfg['atol'],events=event,t_eval=times[sample:],dense_output=False)
            if not sol.success:raise RuntimeError(sol.message)
            nfev+=sol.nfev;t=float(sol.t_events[0][0]) if len(sol.t_events[0]) else float(times[-1])
            for col,ts in enumerate(sol.t):
                v=sol.y[:,col].reshape(self.nmax+1,self.M);prob=abs(v)**2;norm=prob.sum()
                trace.append([float(ts),float(prob.sum(axis=0)@self.X/norm),float(prob.sum(axis=1)@np.arange(self.nmax+1)/norm),float(np.sum(abs(self.O@v.T)**2)/norm)])
                sample+=1
            psi=sol.y_events[0][0] if len(sol.t_events[0]) else sol.y[:,-1]
            if len(sol.t_events[0]):
                v=psi.reshape(self.nmax+1,self.M);w=np.zeros_like(v);w[:-1]=v[1:]*np.sqrt(np.arange(1,self.nmax+1))[:,None]
                psi=w.ravel();psi/=np.linalg.norm(psi);jumps+=1
            else:break
        psi/=np.linalg.norm(psi);v=psi.reshape(self.nmax+1,self.M);prob=abs(v)**2
        hv=np.stack([b@v.T for b in self.bonds]);kin=np.einsum('ipq,jpq->ij',hv.conj(),hv).real
        pv=np.stack([b@v.T for b in self.pairs]);pair=np.einsum('ipq,jpq->ij',pv.conj(),pv).real
        S,tail=self.entropy(psi)
        obs=dict(density=prob.sum(axis=0)@self.occ,kinetic=kin,pairing=pair,entropy=S,X=float(prob.sum(axis=0)@self.X),photon=float(prob.sum(axis=1)@np.arange(self.nmax+1)),OdagO=float(kin.sum()),pair_sum=float(pair.sum()))
        return obs,trace,dict(jumps=jumps,nfev=nfev,max_top_photon_probability=top,entropy_discarded_probability=tail,full_hilbert_dimension=len(psi))


def job(args):
    cfg,m,index=args;started=time.monotonic();rng=np.random.default_rng(cfg['seed']+index)
    h=CoherentHybrid(m['L'],m['N'],m['statistics'],cfg['photon_cutoff'],cfg['delta'],cfg['gamma']);samples=[];traces=[];diag=[]
    for i in range(cfg['trajectories_per_job']):
        o,t,d=h.trajectory(rng,cfg);samples.append(o);traces.append(t);diag.append(d)
        print(m['statistics'],index,i+1,round(time.monotonic()-started,2),flush=True)
    return m['statistics'],{k:np.array([s[k] for s in samples]) for k in samples[0]},np.array(traces),diag,time.monotonic()-started


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);cfg=json.loads(Path(p.parse_args().config).read_text());started=time.monotonic()
    jobs=[(cfg,m,i*10000+j) for i,m in enumerate(cfg['models']) for j in range(cfg.get('jobs_per_model',1))]
    if cfg.get('workers',1)>1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:res=list(pool.map(job,jobs))
    else:res=[job(x) for x in jobs]
    arrays={};rows=[]
    for stats in sorted({r[0] for r in res}):
        same=[r for r in res if r[0]==stats];name=stats+'_GS';row={'id':name,'diagnostics':sum([r[3] for r in same],[])}
        for key in same[0][1]:
            a=np.concatenate([r[1][key] for r in same]);arrays[name+'_'+key]=a;row[key+'_mean']=a.mean(axis=0).tolist();row[key+'_standard_error']=(a.std(axis=0,ddof=1)/math.sqrt(len(a))).tolist() if len(a)>1 else None
        arrays[name+'_traces']=np.concatenate([r[2] for r in same]);row['trajectories']=len(a);rows.append(row)
    out=Path(cfg['output_prefix']);out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(str(out)+'.npz',**arrays)
    Path(str(out)+'.json').write_text(json.dumps({'config':cfg,'results':rows,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')

if __name__=='__main__':main()
