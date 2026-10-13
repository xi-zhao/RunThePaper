"""Coherent GS solver in a moving union of conserved Q sectors.

The union shifts by one after a photon loss, retaining coherence across sectors.
Only the initial GS tails below a declared total probability are omitted.
For linear bounded observables the unconditional trace-distance error is at
most 2 sqrt(discarded_probability); this is separate from MC and cavity errors.
"""
import math
from functools import lru_cache
import numpy as np
from scipy.integrate import solve_ivp
import generate_coherent_gs as base


class Packed(base.CoherentHybrid):
    @lru_cache(None)
    def block(self, lo, hi):
        q=self.ph+np.tile(self.X,self.nmax+1)
        ix=np.flatnonzero((q>=lo)&(q<=hi))
        return ix,self.G[ix][:,ix].tocsr(),self.ph[ix]

    def trajectory(self,rng,cfg):
        weights=np.bincount(self.X,weights=abs(self.gs[0])**2)
        lo=int(self.X.min());hi=int(self.X.max());discarded=0.
        while lo<hi:
            edge=lo if weights[lo]<=weights[hi] else hi
            if discarded+weights[edge]>cfg['initial_tail_probability']:break
            discarded+=weights[edge]
            if edge==lo:lo+=1
            else:hi-=1
        ix,G,ph=self.block(lo,hi);psi=self.gs.ravel()[ix].copy();psi/=np.linalg.norm(psi)
        initial_bounds=[lo,hi];t=0.;sample=0;trace=[];jumps=0;nfev=0;top=0.;maxdim=len(psi)
        times=np.array(cfg['times'])
        while t<times[-1]-1e-10:
            threshold=rng.random()
            def event(t,y):return np.vdot(y,y).real-threshold
            event.terminal=True;event.direction=-1
            def rhs(t,y):
                nonlocal top
                norm=np.vdot(y,y).real
                if norm:top=max(top,float(np.vdot(y[ph==self.nmax],y[ph==self.nmax]).real/norm))
                return G@y
            sol=solve_ivp(rhs,(t,times[-1]),psi,method='DOP853',rtol=cfg['rtol'],atol=cfg['atol'],events=event,t_eval=times[sample:],dense_output=False)
            if not sol.success:raise RuntimeError(sol.message)
            nfev+=sol.nfev;t=float(sol.t_events[0][0]) if len(sol.t_events[0]) else float(times[-1])
            for col,ts in enumerate(sol.t):
                full=np.zeros(self.gs.size,complex);full[ix]=sol.y[:,col];v=full.reshape(self.nmax+1,self.M);prob=abs(v)**2;norm=prob.sum()
                trace.append([float(ts),float(prob.sum(axis=0)@self.X/norm),float(prob.sum(axis=1)@np.arange(self.nmax+1)/norm),float(np.sum(abs(self.O@v.T)**2)/norm)]);sample+=1
            psi=sol.y_events[0][0] if len(sol.t_events[0]) else sol.y[:,-1]
            if len(sol.t_events[0]):
                lo-=1;hi-=1;newix,newG,newph=self.block(lo,hi);mask=ph>0
                w=np.zeros(len(newix),complex);w[np.searchsorted(newix,ix[mask]-self.M)]=psi[mask]*np.sqrt(ph[mask]);psi=w/np.linalg.norm(w)
                ix,G,ph=newix,newG,newph;jumps+=1;maxdim=max(maxdim,len(psi))
            else:break
        full=np.zeros(self.gs.size,complex);full[ix]=psi/np.linalg.norm(psi);v=full.reshape(self.nmax+1,self.M);prob=abs(v)**2
        hv=np.stack([b@v.T for b in self.bonds]);kin=np.einsum('ipq,jpq->ij',hv.conj(),hv).real
        pv=np.stack([b@v.T for b in self.pairs]);pair=np.einsum('ipq,jpq->ij',pv.conj(),pv).real
        S,tail=self.entropy(full)
        obs=dict(density=prob.sum(axis=0)@self.occ,kinetic=kin,pairing=pair,entropy=S,X=float(prob.sum(axis=0)@self.X),photon=float(prob.sum(axis=1)@np.arange(self.nmax+1)),OdagO=float(kin.sum()),pair_sum=float(pair.sum()))
        return obs,trace,dict(jumps=jumps,nfev=nfev,max_top_photon_probability=top,entropy_discarded_probability=tail,initial_discarded_probability=float(discarded),initial_Q_bounds=initial_bounds,max_hilbert_dimension=maxdim,final_hilbert_dimension=len(psi),linear_trace_distance_bound=2*math.sqrt(discarded))


if __name__=='__main__':
    base.CoherentHybrid=Packed
    base.main()
