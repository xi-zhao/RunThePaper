"""Importance sampling of a declared phase-probe DEM, with exact likelihood ratio."""
from pathlib import Path
import argparse,json,time
import numpy as np
import stim
from simulate_sd6_factory_v2 import factory,Decoder,binomial_interval
from structured_schedule import structured_tri

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text());models=json.loads(Path('config/models.json').read_text())['pairs']
    out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True);rows=[]
    for job in cfg['jobs']:
        t0=time.monotonic();m=next(m for m in models if m['quad'][0]==job['n4'])
        c,dem,meta=factory(m,job['p'],job['pccz'],job.get('schedule_seed',1),False,'phase',tri_override=structured_tri(m,(0,2,1,3)))
        decoder=Decoder(dem,cfg.get('decoder_timeout',30));factor=job.get('importance_factor',1)
        proposal=stim.DetectorErrorModel();probs=[];qprobs=[]
        for ins in dem.flattened():
            if ins.type=='error':
                p=ins.args_copy()[0];q=min(.2,factor*p);probs.append(p);qprobs.append(q)
                proposal.append('error',q,ins.targets_copy())
            else:proposal.append(ins)
        pp=np.array(probs);qp=np.array(qprobs)
        assert len(pp)==len(decoder.prob) and np.all(pp==decoder.prob)
        base=float(np.log1p(-pp).sum()-np.log1p(-qp).sum())
        coeff=np.log(pp/qp)-np.log((1-pp)/(1-qp))
        sampler=proposal.compile_sampler(seed=job['seed'])
        direct_shots=job.get('acceptance_shots',200000)
        direct=c.compile_detector_sampler(seed=job['seed']+1).sample(direct_shots)
        sl=slice(0 if job.get('postselection','teleport_only')=='all_prefix' else meta['post_start'],meta['npost'])
        direct_accept=int((~np.any(direct[:,sl],axis=1)).sum());alpha=direct_accept/direct_shots
        accum=np.zeros(6);failure_samples=0;accepted_samples=0;weight_mean=0.;n=0
        tag=f"n{job['n4']}_p{job['p']:.8g}_c{job['pccz']:.8g}_s{job.get('schedule_seed',1)}_f{factor}"
        (out/(tag+'.stim')).write_text(str(c));(out/(tag+'.dem')).write_text(str(dem))
        (out/(tag+'-schedule.json')).write_text(json.dumps(meta,indent=2)+'\n')
        while n<job['shots']:
            batch=min(cfg.get('batch',2000),job['shots']-n)
            det,obs,err=sampler.sample(batch,return_errors=True)
            weight=np.exp(base+err@coeff);weight_mean+=weight.sum()
            accept=~np.any(det[:,sl],axis=1);accepted_samples+=int(accept.sum())
            ds=det[accept].astype(np.uint8);os=obs[accept].astype(np.uint8)
            if len(ds):
                patterns,inverse=np.unique(ds,axis=0,return_inverse=True)
                predictions=np.array([decoder.predict(x) for x in patterns])
                residual=os^predictions[inverse]
                fail=np.any(residual,axis=1);fraction=residual.mean(1)
                wf=weight[accept]*fail;wb=weight[accept]*fraction;wa=weight[accept]
                accum+=np.array([wf.sum(),(wf*wf).sum(),wb.sum(),(wb*wb).sum(),wa.sum(),(wa*wa).sum()])
                failure_samples+=int(fail.sum())
            n+=batch
            (out/'progress.json').write_text(json.dumps(dict(tag=tag, completed_batches_shots=n, requested_shots=job['shots'], failure_samples=failure_samples, sums=accum.tolist(), weight_sum=float(weight_mean), accepted_samples=accepted_samples, direct_acceptance=alpha, decoder_calls=decoder.calls, decoder_seconds=decoder.seconds, wall_seconds=time.monotonic()-t0),indent=2)+'\n')
            if n%10000==0:print(tag,'shots',n,'raw proposal failures',failure_samples,'MLE calls',decoder.calls,flush=True)
        means=accum[[0,2,4]]/n
        ses=np.sqrt(np.maximum(0,accum[[1,3,5]]/n-means**2)/(n-1))
        # Independent direct acceptance estimate; delta-method sampling uncertainty.
        var_alpha=alpha*(1-alpha)/direct_shots
        rates=means[:2]/alpha
        rate_se=np.sqrt((ses[:2]/alpha)**2+means[:2]**2*var_alpha/alpha**4)
        row={**job,'acceptance':alpha,'acceptance_shots':direct_shots,'accepted_direct':direct_accept,
             'acceptance_ci95':binomial_interval(direct_accept,direct_shots),
             'weighted_acceptance':float(means[2]),'weighted_acceptance_SE':float(ses[2]),
             'weight_mean':float(weight_mean/n),'proposal_accepted':accepted_samples,'proposal_failure_samples':failure_samples,
             'block_phase_ler':float(rates[0]),'per_qubit_phase_ler':float(rates[1]),
             'block_phase_ler_SE':float(rate_se[0]),'per_qubit_phase_ler_SE':float(rate_se[1]),
             'failure_weight_ESS':float(accum[0]**2/accum[1]) if accum[1] else 0,
             'zero_failure_is_not_zero_rate':failure_samples==0,
             'decoder_calls':decoder.calls,'decoder_seconds':decoder.seconds,'low_weight_certificates':decoder.certified_low_weight,
             'dem_mechanisms':len(pp),'wall_seconds':time.monotonic()-t0,'tag':tag}
        rows.append(row);print(json.dumps(row),flush=True)
        (out/'results.json').write_text(json.dumps({'format':'qldpc.sd6-phase-importance.v3','rows':rows,
            'limits':['Only the explicitly specified Clifford phase probe. No full magic-state LER is established.',
                      'Structured tricycle schedule (layer order 0,2,1,3); independent quadcycle edge coloring remains seed-selected.',
                      'No author schedule, logical observable, decoder tie rule or terminal readout convention is inferred.',
                      'MLE optimizes independent DEM errors, not a logical coset posterior.',
                      'Importance uncertainties are empirical standard errors; rare weighted tails may be missed.',
                      'No failure samples is not a zero-error certificate.',
                      'Direct circuit acceptance is a distinct check of importance normalization.',
                      'Terminal Q readout is perfect and excluded from postselection. All physical factory layers have SD6 noise.']},indent=2)+'\n')
if __name__=='__main__':main()
