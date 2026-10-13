"""Log-domain final-tail diagnostic with explicit dark-state boundary handling.

Reuses receipted final-interval inputs, not new trajectory samples. Exact dark
certificates refer only to the supplied binary64 state and generator. Numerical
tail classifications do not certify earlier jump times or the physical state.
"""
import io
import json
import math
import time
import zipfile
import hashlib
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import expm_multiply
from generate_h2_tail_v1 import TailHybrid as OriginalTailHybrid


def exact_zero_product(matrix, vector):
    """Exact rational arithmetic on stored binary64 complex coefficients."""
    matrix=matrix.tocsr()
    for row in range(matrix.shape[0]):
        real=Fraction(0);imag=Fraction(0)
        for pos in range(matrix.indptr[row],matrix.indptr[row+1]):
            a=matrix.data[pos];b=vector[matrix.indices[pos]]
            ar,ai=Fraction(float(a.real)),Fraction(float(a.imag))
            br,bi=Fraction(float(b.real)),Fraction(float(b.imag))
            real+=ar*br-ai*bi;imag+=ar*bi+ai*br
        if real or imag:return False
    return True


class TailHybrid(OriginalTailHybrid):
    def tail(self,Q,psi,duration,step):
        if duration<0 or step<=0:raise ValueError('Require duration >= 0 and step > 0')
        zero,bright,U,D,B,weights,meta=self.decomposition(Q)
        if not np.linalg.norm(psi)>0:raise ValueError('Zero input state')
        d=D.conj().T@psi[zero];dark=float(np.vdot(d,d).real)
        b=np.r_[U.conj().T@psi[zero],psi[bright]]
        bn=float(np.linalg.norm(b));initial_bnorm=bn
        # This guard detects projection-scale ambiguity; it is not a rigorous
        # physical error bound and never rounds a near-dark input to exact dark.
        guard=64*np.finfo(float).eps*math.sqrt(max(1,len(zero)))*float(np.linalg.norm(psi))
        base=dict(meta,initial_bright_norm=bn,initial_dark_norm2=dark,step=step,
                  projection_guard=guard,bin=None,certificate_scope='frozen binary64 generator and supplied state only')
        G=self.block(Q)[2]
        exact_dark=not np.any(psi[bright]) and exact_zero_product(G[bright][:,zero],psi[zero])
        if exact_dark:
            norm=float(np.vdot(psi,psi).real)
            return dict(base,photon=0.,log_photon=None,tail_norm2=norm,log_tail_norm2=math.log(norm),
                        bin=Q,classification='exact_dark_frozen_input',display_underflow=False)
        if bn<=guard:
            return dict(base,photon=None,log_photon=None,tail_norm2=None,log_tail_norm2=None,
                        classification='near_dark_unresolved',display_underflow=False)
        b/=bn;lognorm=math.log(bn)
        count=max(1,int(math.ceil(duration/step)));dt=duration/count
        for _ in range(count):
            b=expm_multiply(B*dt,b,traceA=complex(B.diagonal().sum()*dt))
            bn=float(np.linalg.norm(b))
            if not bn>0:raise ArithmeticError('Bright propagator underflow within one step')
            lognorm+=math.log(bn);b/=bn
        conditional=float(np.vdot(b,weights*b).real)
        logtotal=float(np.logaddexp(math.log(dark) if dark>0 else -np.inf,2*lognorm))
        logp=2*lognorm+math.log(conditional)-logtotal if conditional>0 else None
        photon=math.exp(logp) if logp is not None else 0.
        total=math.exp(logtotal)
        binvalue=None;classification='numerical_tail_integer_boundary_unresolved'
        if logp is not None and logp < -1e-10:
            # A strictly positive value below 1 has ceil 1, even when the
            # display float underflows. No subtraction Q - photon occurs.
            binvalue=Q-1;classification='numerical_positive_tail_below_one'
        elif logp is not None and abs(photon-round(photon))>1e-10*max(1.,photon):
            binvalue=Q-int(math.ceil(photon));classification='numerical_tail_away_from_integer'
        elif duration==0 and conditional==0:
            binvalue=Q;classification='initial_zero_photon'
        return dict(base,photon=photon,log_photon=logp,tail_norm2=total,log_tail_norm2=logtotal,
                    final_bright_log_norm=lognorm,classification=classification,bin=binvalue,
                    display_underflow=bool(logp is not None and photon==0))


def main():
    input_path=Path('inputs/h2-tail-v1-frozen.zip')
    with zipfile.ZipFile(input_path) as z:
        lineage=json.loads(z.read('lineage.json'))
        for path,sha in lineage['sha256'].items():assert hashlib.sha256(z.read(path)).hexdigest()==sha
        prior=json.loads(z.read('results.json'));states=np.load(io.BytesIO(z.read('last-segment-states.npz')))
    cfg=prior['config'];out=Path('outputs/h2-tail-v2');out.mkdir(parents=True,exist_ok=True)
    models={};rows=[];started=time.monotonic()
    for old in prior['rows']:
        key=(old['L'],old['N'],old['statistics'])
        if key not in models:models[key]=TailHybrid(*key,cfg['cutoff'],cfg['delta'],cfg['gamma'])
        h=models[key];v=states[old['id']];Q=old['Q'];duration=old['baseline']['duration']
        a=h.tail(Q,v,duration,cfg['step']);b=h.tail(Q,v,duration,cfg['step']/2)
        row=dict(old,coarse=a,fine=b,rescaled_bin=b['bin'],
            v1_rescaled_bin=old['rescaled_bin'],
            log_photon_difference=None if a['log_photon'] is None or b['log_photon'] is None else abs(a['log_photon']-b['log_photon']),
            total_norm_difference=None if a['tail_norm2'] is None or b['tail_norm2'] is None else abs(a['tail_norm2']-b['tail_norm2']))
        rows.append(row)
        (out/'results.json').write_text(json.dumps(dict(config=cfg,input_lineage=lineage,rows=rows,seconds=time.monotonic()-started,
            limitations=prior['limitations']+[
                'V1 exact-dark and underflow counterexamples are retained in the independent audit.',
                'Exact darkness is certified only for the supplied frozen numerical matrix/state; earlier trajectory error remains.',
                'Near-dark projections and near-integer numerical photon values remain unclassified.',
                'Positive log-domain photon tails are never replaced by a zero-photon bin after display underflow.']),indent=2)+'\n')
        print(json.dumps(dict(id=old['id'],bin=b['bin'],classification=b['classification'],seconds=time.monotonic()-started)),flush=True)


if __name__=='__main__':main()
