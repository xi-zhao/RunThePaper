"""Independent Appendix F states and similarity check at original N=8.

Original figure captions and panel labels use bosonic X=38; the adjacent prose
has X=30. Both inputs are retained in the source audit, with figures taking
precedence for these numerical panels. No author curves are read here.
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.linalg import null_space, eigh
from generate_statics import sector, matrix, schmidt_maps, entropies


def haar(rng,n):
    z=rng.normal(size=(n,n))+1j*rng.normal(size=(n,n))
    q,r=np.linalg.qr(z);d=np.diag(r);return q*(d.conj()/abs(d))


def main():
    cfg=json.loads(Path('config/supplement.json').read_text())
    rng=np.random.default_rng(cfg['seed']);arrays={};records=[]
    for stats,L,X in [('fermion',16,58),('boson',9,38)]:
        N=8;states=sector(L,N,stats,X);lower=sector(L,N,stats,X-1)
        occ=np.array(states);hops=[matrix(states,lower,[(1,[(j+1,-1),(j,1)])],stats) for j in range(L-1)]
        O=sum(hops);Q=sum(math.sqrt(j*(L-j))*hops[j-1] for j in range(1,L))
        pairdst=sector(L,N-2,stats,X-L-1)
        K=sum(matrix(states,pairdst,[((-1)**j*(.5 if 2*j==L-1 else 1),[(j,-1),(L-j-1,-1)])],stats) for j in range((L+1)//2))
        U=null_space(O.toarray(),rcond=1e-12);ev,R=eigh((K@U).T@(K@U));U=U@R
        V=null_space(Q.toarray(),rcond=1e-12);qev,qr=eigh((K@V).T@(K@V));V=V@qr
        logw=np.array([.5*(math.lgamma(j)+math.lgamma(L)-math.lgamma(L-j+1)) for j in range(1,L+1)])
        logg=occ@logw;gm=np.exp(logg-logg.max());maps=schmidt_maps(states,L)
        for p in range(5):
            target=p*(p+1) if stats=='fermion' else p*(N+L/2-p-1)
            u=U[:,abs(ev-target)<1e-9];v=V[:,abs(qev-target)<1e-9];d=u.shape[1]
            if not d:continue
            assert v.shape[1]==d
            # A second formulation: transform a separately built Q kernel.
            t,_=np.linalg.qr(gm[:,None]*v)
            projector_error=float(np.linalg.norm(t@t.T-u@u.T))
            rb=u@haar(rng,d);rq=v@haar(rng,d)
            densities=(abs(rb)**2).T@occ;qdensities=(abs(rq)**2).T@occ;S=entropies(rb,maps)
            ensemble=[]
            for _ in range(cfg['haar_draws']):
                basis=u@haar(rng,d)
                ds=(abs(basis)**2).T@occ
                ss=entropies(basis,maps)
                ensemble.append([float(np.max(abs(ds-densities.mean(0)))),float(ss.mean(0).max())])
            prefix=f'{stats}_X{X}_Np{p}';arrays[prefix+'_density']=densities;arrays[prefix+'_Q_density']=qdensities;arrays[prefix+'_entropy']=S
            arrays[prefix+'_states']=occ;arrays[prefix+'_O_vectors']=rb;arrays[prefix+'_Q_vectors']=rq
            records.append(dict(id=prefix,statistics=stats,L=L,N=N,X=X,Np=p,Ns=d,similarity_projector_error=projector_error,O_residual=float(np.linalg.norm(O@rb)),Q_residual=float(np.linalg.norm(Q@rq)),pair_residual=float(np.linalg.norm(K.T@(K@rb)-target*rb)),Q_pair_residual=float(np.linalg.norm(K.T@(K@rq)-target*rq)),density_mean=densities.mean(0).tolist(),Q_density_mean=qdensities.mean(0).tolist(),entropy_mean=S.mean(0).tolist(),haar_draws=cfg['haar_draws'],haar_peak_entropy_range=[min(x[1] for x in ensemble),max(x[1] for x in ensemble)],haar_largest_single_state_density_deviation=max(x[0] for x in ensemble)))
    out=Path('outputs/data');out.mkdir(exist_ok=True,parents=True)
    np.savez_compressed(out/'supplement.npz',**arrays)
    (out/'supplement.json').write_text(json.dumps(dict(config=cfg,sectors=records,limitations='Finite independent Haar bases need distributional comparison, not author-seed identity. No thermodynamic entanglement law follows from one finite size.'),indent=2)+'\n')


if __name__=='__main__':main()
