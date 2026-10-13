"""Independent full hybrid quantum trajectories, conserved Q=X+n_ph sectors.

No elimination of cavity, no author result inputs. DOP853 solves the non-Hermitian
Schrodinger equation until norm crossing, then a photon jump lowers Q by one.
Photon cutoff, ODE tolerance, trajectory count and wall limit are explicit inputs.
This solver has no MPS approximation. A finite ensemble needs sampling errors.
"""
import json, math, time
from pathlib import Path
from functools import lru_cache
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.integrate import solve_ivp
from generate_statics import basis, sector, act, matrix, entropies


class Hybrid:
    def __init__(self,L,N,statistics,nmax,delta,gamma):
        self.L,self.N,self.stats,self.nmax=L,N,statistics,nmax
        self.delta,self.gamma=delta,gamma
        self.xmin=N*(N+1)//2 if statistics=='fermion' else N
        self.byX={}
        for n in basis(L,N,statistics):
            X=sum((j+1)*v for j,v in enumerate(n))
            self.byX.setdefault(X,[]).append(n)

    @lru_cache(None)
    def block(self,Q):
        states=[(p,n) for p in range(self.nmax+1) for n in self.byX.get(Q-p,[])]
        ix={s:i for i,s in enumerate(states)}
        rr=[];cc=[];vv=[]
        for k,(p,n) in enumerate(states):
            if p>=self.nmax:continue
            for j in range(self.L-1):
                m,a=act(n,[(j+1,-1),(j,1)],self.stats)
                if not a:continue
                i=ix.get((p+1,m))
                if i is None:continue
                v=-math.sqrt(p+1)*a
                rr.extend([i,k]);cc.extend([k,i]);vv.extend([v,v])
        H=coo_matrix((vv,(rr,cc)),shape=(len(states),len(states))).tocsr()
        ph=np.array([p for p,n in states],float)
        G=-1j*H+diags((-1j*self.delta-self.gamma/2)*ph)
        occupations=np.array([n for p,n in states])
        return states,ix,G,ph,occupations

    @lru_cache(None)
    def jump(self,Q):
        states,_,_,_,_=self.block(Q);dst,ix,_,_,_=self.block(Q-1)
        rows=[];cols=[];vals=[]
        for j,(p,n) in enumerate(states):
            if p:rows.append(ix[p-1,n]);cols.append(j);vals.append(math.sqrt(p))
        return coo_matrix((vals,(rows,cols)),shape=(len(dst),len(states))).tocsr()

    @lru_cache(None)
    def matter_left(self,Q):
        states,_,_,_,_=self.block(Q);dst,ix,_,_,_=self.block(Q-1)
        rr=[];cc=[];vv=[]
        for k,(p,n) in enumerate(states):
            for j in range(self.L-1):
                m,a=act(n,[(j+1,-1),(j,1)],self.stats)
                if a:rr.append(ix[p,m]);cc.append(k);vv.append(a)
        return coo_matrix((vv,(rr,cc)),shape=(len(dst),len(states))).tocsr()

    @lru_cache(None)
    def ground_sectors(self):
        """Exact free-particle ground state of +(O+Odagger), projected by X.

        Q dephasing leaves all recorded linear Q-commuting observables unchanged.
        It changes trajectory distributions and entropies: GS results for those
        observables are explicitly NOT comparisons with the original unraveling.
        """
        vals={}
        modes=np.arange(self.L-self.N+1,self.L+1)
        phi=np.sqrt(2/(self.L+1))*np.sin(np.pi*np.arange(1,self.L+1)*self.L/(self.L+1))
        for X,states in self.byX.items():
            amps=[]
            for n in states:
                if self.stats=='fermion':
                    pos=np.flatnonzero(n)+1
                    a=np.linalg.det(np.sqrt(2/(self.L+1))*np.sin(np.pi*pos[:,None]*modes[None,:]/(self.L+1)))
                else:
                    a=math.sqrt(math.factorial(self.N)/math.prod(math.factorial(v) for v in n))*math.prod(phi[j]**v for j,v in enumerate(n))
                amps.append(a)
            a=np.array(amps);weight=float(a@a)
            if weight>1e-20:vals[X]=(weight,a/math.sqrt(weight))
        return vals

    def entropy_with_cavity(self,Q,psi):
        from collections import defaultdict
        states=self.block(Q)[0];cuts=[]
        for cut in range(self.L):
            buckets=defaultdict(list)
            for idx,(p,n) in enumerate(states):
                left=(p,)+n[:cut];right=n[cut:]
                buckets[sum(right),sum((cut+j+1)*v for j,v in enumerate(right))].append((idx,left,right))
            groups=[]
            for rows in buckets.values():
                li={x:i for i,x in enumerate(sorted({r[1] for r in rows}))};ri={x:i for i,x in enumerate(sorted({r[2] for r in rows}))}
                groups.append((len(li),len(ri),np.array([r[0] for r in rows]),np.array([li[r[1]] for r in rows]),np.array([ri[r[2]] for r in rows])))
            cuts.append(groups)
        return entropies((psi/np.linalg.norm(psi))[:,None],cuts)[0]

    def observables(self,Q,psi):
        states,_,G,ph,occ=self.block(Q)
        norm=np.vdot(psi,psi).real;psi=psi/math.sqrt(norm)
        probability=np.abs(psi)**2;density=probability@occ
        kinetic=np.zeros((self.L-1,self.L-1),complex)
        npair=(self.L+1)//2;pairing=np.zeros((npair,npair),complex)
        for p in range(self.nmax+1):
            inds=[i for i,s in enumerate(states) if s[0]==p]
            if not inds:continue
            src=[states[i][1] for i in inds];v=psi[inds]
            dst=self.byX.get(Q-p-1,[])
            hv=np.stack([matrix(src,dst,[(1,[(j+1,-1),(j,1)])],self.stats)@v for j in range(self.L-1)])
            kinetic+=hv.conj()@hv.T
            pdst=sector(self.L,self.N-2,self.stats,Q-p-self.L-1)
            pv=np.stack([matrix(src,pdst,[((-1)**j*(.5 if j==self.L-1-j else 1),[(j,-1),(self.L-1-j,-1)])],self.stats)@v for j in range(npair)])
            pairing+=pv.conj()@pv.T
        return dict(density=density,kinetic=kinetic.real,pairing=pairing.real,
                    X=float(density@np.arange(1,self.L+1)),photon=float(probability@ph),
                    top_photon_probability=float(probability[ph==self.nmax].sum()),
                    OdagO=float(kinetic.real.sum()),pair_sum=float(pairing.real.sum()))

    def trajectory(self,initial,rng,times,rtol,atol,entropy=False):
        if initial=='GS':
            gs=self.ground_sectors();choices=list(gs);probs=np.array([gs[q][0] for q in choices]);probs/=probs.sum()
            Q=int(rng.choice(choices,p=probs));states,ix,G,ph,occ=self.block(Q)
            psi=np.zeros(len(states),complex);psi[:len(self.byX[Q])]=gs[Q][1]
        else:
            Q=sum((j+1)*v for j,v in enumerate(initial));states,ix,G,ph,occ=self.block(Q)
            psi=np.zeros(len(states),complex);psi[ix[0,tuple(initial)]]=1
        t=0.;records=[];next_sample=0;jumps=0;nfev=0;max_top=0.;maxdim=len(states)
        while t<times[-1]-1e-10:
            threshold=rng.random()
            def event(t,y):return np.vdot(y,y).real-threshold
            event.terminal=True;event.direction=-1
            sol=solve_ivp(lambda t,y:G@y,(t,times[-1]),psi,method='DOP853',rtol=rtol,atol=atol,events=event,dense_output=True)
            if not sol.success:raise RuntimeError(sol.message)
            nfev+=sol.nfev;last=float(sol.t[-1])
            top=(ph==self.nmax)
            max_top=max(max_top,float(np.max(np.sum(abs(sol.y[top])**2,axis=0)/np.sum(abs(sol.y)**2,axis=0))))
            while next_sample<len(times) and times[next_sample]<=last+1e-10:
                v=sol.sol(times[next_sample]);prob=abs(v)**2;prob/=prob.sum()
                Ov=self.matter_left(Q)@v
                records.append([float(times[next_sample]),float(prob@(Q-ph)),float(prob@ph),float(np.vdot(Ov,Ov).real/np.vdot(v,v).real)])
                next_sample+=1
            psi=sol.y[:,-1];t=last
            if len(sol.t_events[0]):
                psi=self.jump(Q)@psi;Q-=1;jumps+=1
                psi/=np.linalg.norm(psi)
                states,ix,G,ph,occ=self.block(Q);maxdim=max(maxdim,len(states))
            else:break
        obs=self.observables(Q,psi)
        if entropy:obs['entropy']=self.entropy_with_cavity(Q,psi)
        return obs,records,dict(jumps=jumps,nfev=nfev,max_top_photon_probability=max_top,max_dimension=maxdim)


def one_ensemble(job):
    cfg,m,ic,seed=job;started=time.monotonic();rng=np.random.default_rng(seed)
    h=Hybrid(m['L'],m['N'],m['statistics'],cfg['photon_cutoff'],cfg['delta'],cfg['gamma'])
    samples=[];traces=[];diagnostics=[];initial=ic.get('occupations','GS')
    for i in range(cfg['trajectories']):
        obs,trace,diag=h.trajectory(initial,rng,np.array(cfg['times']),cfg['rtol'],cfg['atol'],cfg.get('entropy',False))
        samples.append(obs);traces.append(trace);diagnostics.append(diag)
        if (i+1)%25==0:print(m['statistics'],ic['id'],i+1,'seconds',round(time.monotonic()-started,1),flush=True)
        if time.monotonic()-started>cfg['wall_limit_seconds']:break
    name=m['statistics']+'_'+ic['id'];row={'id':name,'trajectories':len(samples),'seed':seed,'diagnostics':diagnostics,'elapsed_seconds':time.monotonic()-started}
    arrays={}
    for key in samples[0]:
        a=np.array([s[key] for s in samples]);arrays[name+'_'+key]=a
        row[key+'_mean']=np.mean(a,axis=0).tolist()
        row[key+'_standard_error']=(np.std(a,axis=0,ddof=1)/math.sqrt(len(a))).tolist() if len(a)>1 else None
    arrays[name+'_traces']=np.array(traces)
    return row,arrays


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--config',default='config/dynamics-pilot.json');args=p.parse_args()
    cfg=json.loads(Path(args.config).read_text());started=time.monotonic();arrays={};summary=[]
    jobs=[(cfg,m,ic,cfg['seed']+i*10000+j) for i,m in enumerate(cfg['models']) for j,ic in enumerate(m['initial_states'])]
    if cfg.get('workers',1)>1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:results=list(pool.map(one_ensemble,jobs))
    else:results=[one_ensemble(job) for job in jobs]
    for row,a in results:summary.append(row);arrays.update(a)
    out=Path(cfg['output_prefix']);out.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(str(out)+'.npz',**arrays)
    Path(str(out)+'.json').write_text(json.dumps({'config':cfg,'results':summary,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')

if __name__=='__main__':main()
