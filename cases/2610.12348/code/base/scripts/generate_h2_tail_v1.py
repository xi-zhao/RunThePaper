"""Separate exactly dark and decaying sectors in the final no-jump interval.

Earlier trajectory segments use the declared DOP853 equations. This isolates
the final-tail propagation error; it is not a certified complete path error
bound. Dark projection is onto ker(O) in the zero-photon subspace. The bright
generator has no dark zero modes; periodic normalization preserves tiny tails.
"""
import argparse
import json
import math
import time
import zipfile
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import svd
from scipy.optimize import brentq
from scipy.sparse import bmat, csr_matrix, diags
from scipy.sparse.linalg import expm_multiply
from generate_dynamics import Hybrid


class TailHybrid(Hybrid):
    @lru_cache(None)
    def decomposition(self,Q):
        states,_,G,ph,_=self.block(Q)
        zero=np.flatnonzero(ph==0);bright=np.flatnonzero(ph>0)
        coupling=G[bright][:,zero].toarray()
        _,s,vh=svd(coupling,full_matrices=True)
        threshold=1e-11*max(1.,s[0] if len(s) else 1.)
        r=int(np.count_nonzero(s>threshold))
        U=vh[:r].conj().T;D=vh[r:].conj().T
        cross=G[zero][:,bright]
        B=bmat([[csr_matrix((r,r),dtype=complex),csr_matrix(U.conj().T@cross)],
                [csr_matrix(coupling@U),G[bright][:,bright]]],format='csr')
        weights=np.r_[np.zeros(r),ph[bright]]
        dark_res=float(np.linalg.norm(coupling@D)) if D.size else 0.
        gram=float(np.linalg.norm(vh@vh.conj().T-np.eye(len(zero))))
        return zero,bright,U,D,B,weights,dict(dimension=len(states),bright_dimension=B.shape[0],
             dark_dimension=D.shape[1],rank_threshold=threshold,
             smallest_retained_singular=float(s[r-1]) if r else None,
             largest_discarded_singular=float(s[r]) if r<len(s) else 0.,
             dark_residual=dark_res,orthogonality_residual=gram)

    def tail(self,Q,psi,duration,step):
        zero,bright,U,D,B,weights,meta=self.decomposition(Q)
        d=D.conj().T@psi[zero];dark=float(np.vdot(d,d).real)
        b=np.r_[U.conj().T@psi[zero],psi[bright]]
        bnorm=float(np.linalg.norm(b));initial_bnorm=bnorm
        if bnorm==0:
            return dict(meta,photon=0.,log_photon=None,tail_norm2=dark,initial_bright_norm=0.,step=step)
        b/=bnorm;lognorm=math.log(bnorm)
        count=max(1,int(math.ceil(duration/step)));dt=duration/count
        for _ in range(count):
            b=expm_multiply(B*dt,b,traceA=complex(B.diagonal().sum()*dt))
            bn=float(np.linalg.norm(b));assert bn>0
            lognorm+=math.log(bn);b/=bn
        conditional_ph=float(np.vdot(b,weights*b).real)
        light=math.exp(2*lognorm)
        total=dark+light
        logp=(2*lognorm+math.log(conditional_ph)-math.log(total)) if conditional_ph>0 else None
        photon=math.exp(logp) if logp is not None and logp>-745 else 0.
        return dict(meta,photon=photon,log_photon=logp,tail_norm2=total,
                    initial_bright_norm=initial_bnorm,initial_dark_norm2=dark,
                    final_bright_log_norm=lognorm,step=step)

    def trace_to_tail(self,initial,rng,T,rtol,atol):
        Q=sum((j+1)*v for j,v in enumerate(initial));_,ix,G,ph,_=self.block(Q)
        psi=np.zeros(G.shape[0],complex);psi[ix[0,tuple(initial)]]=1
        t=0.;jumps=0
        while t<T-1e-10:
            threshold=rng.random();start=psi.copy();tstart=t
            def event(t,y):return np.vdot(y,y).real-threshold
            event.terminal=True;event.direction=-1
            sol=solve_ivp(lambda t,y:G@y,(t,T),psi,method='DOP853',rtol=rtol,atol=atol,events=event)
            assert sol.success,sol.message
            psi=sol.y[:,-1];t=float(sol.t[-1])
            if len(sol.t_events[0]):
                psi=self.jump(Q)@psi;Q-=1;jumps+=1;psi/=np.linalg.norm(psi)
                _,_,G,ph,_=self.block(Q)
            else:break
        photon=float(abs(psi)**2@ph/np.vdot(psi,psi).real)
        return Q,start,T-tstart,dict(jumps=jumps,start=tstart,duration=T-tstart,
                                    photon=photon,bin=Q-int(np.ceil(photon)),
                                    final_norm2=float(np.vdot(psi,psi).real))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True)
    cfg=json.loads(Path(ap.parse_args().config).read_text())
    models=json.loads(Path('config/dynamics.json').read_text())['models']
    out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    rows=[];states={};started=time.monotonic()
    for mid,m in enumerate(models):
        h=TailHybrid(m['L'],m['N'],m['statistics'],cfg['cutoff'],cfg['delta'],cfg['gamma'])
        for iid,ic in enumerate(m['initial_states']):
            if 'occupations' not in ic:continue
            rng=np.random.default_rng(cfg['seed']+10000*mid+iid)
            for index in range(cfg['trajectories_per_initial']):
                Q,v,duration,base=h.trace_to_tail(ic['occupations'],rng,cfg['T'],cfg['rtol'],cfg['atol'])
                key=m['statistics']+'_'+ic['id']+'_'+str(index)
                a=h.tail(Q,v,duration,cfg['step']);b=h.tail(Q,v,duration,cfg['step']/2)
                row=dict(id=key,statistics=m['statistics'],L=m['L'],N=m['N'],Q=Q,
                         initial=ic['occupations'],baseline=base,coarse=a,fine=b,
                         rescaled_bin=Q-int(np.ceil(b['photon'])),
                         log_photon_difference=None if a['log_photon'] is None or b['log_photon'] is None else abs(a['log_photon']-b['log_photon']),
                         total_norm_difference=abs(a['tail_norm2']-b['tail_norm2']))
                rows.append(row);states[key]=v
                np.savez_compressed(out/'last-segment-states.npz',**states)
                (out/'results.json').write_text(json.dumps(dict(config=cfg,rows=rows,seconds=time.monotonic()-started,
                    limitations=['Independent final no-jump propagator on DOP853-generated earlier path; earlier jump-time/state errors remain.',
                        'SVD rank separation is numerically checked; finite-step agreement is not an interval-arithmetic error certificate.',
                        'Explicit finite cavity cutoff and vacuum initial cavity. No author convention is inferred.',
                        'These are new paired-propagator diagnostics, not additional independent samples of the old 5000-shot cohort.']),indent=2)+'\n')
                print(json.dumps(dict(id=key,Q=Q,dim=a['dimension'],baseline=base['photon'],spectral=b['photon'],log_difference=row['log_photon_difference'],seconds=time.monotonic()-started)),flush=True)


if __name__=='__main__':main()
