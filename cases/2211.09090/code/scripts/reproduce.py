"""One stage of the nine-figure QC18 reconstruction."""
from pathlib import Path
import json
import sys
import numpy as np
from obsid import TRUTH1, PRIOR1, SD1, TRUTH2, SD2, closed_loop, direct_apc, apc_gain, rabi


def analytic():
    times=np.linspace(.01,20,1101)
    eye=np.eye(2)*1e-5
    f=[]
    for t in times:
        p=rabi(TRUTH1,t)
        grad=np.array([(rabi(TRUTH1+e,t)-rabi(TRUTH1-e,t))/(2e-5) for e in eye])
        f.append(float(grad@grad/max(p*(1-p),1e-14)))
    rng=np.random.default_rng(2318)
    g=rng.normal(PRIOR1,SD1,size=(1500,2))
    c=[]
    for t in (1.,2.,8.):
        p=rabi(g,t)
        c.append(dict(t=t,truth_return=float(rabi(TRUTH1,t)),gain=apc_gain(g,p,.05),
            direct_prior_minus_apc=float(np.var(g,axis=0).sum()-direct_apc(g,p,.05))))
    m=.6;s=.05
    # One observation with residual one nominal sigma.
    bayes=dict(correct=float(np.exp(-.5)),printed=float(np.exp(-.25)),
        baseline_settings=300,adaptive_settings=5,baseline_omega_uncertainty=3.4,baseline_detuning_uncertainty=7.9,
        implied_uncertainty_for_reported_93=3.4*60/93)
    return dict(t=times.tolist(),fisher=f,apc=c,bayes=bayes)


def run(stage):
    if stage=="analytic":
        return analytic()
    if stage=="two":
        mean=np.random.default_rng(2211).normal(TRUTH2,SD2)
        return dict(prior_mean=mean.tolist(),truth=TRUTH2.tolist(),
                    rows=closed_loop("two",TRUTH2,mean,SD2,15,3718,1800))
    if stage=="phase":
        return dict(fixed=closed_loop("rabi",TRUTH1,PRIOR1,SD1,7,2718),
                    phase_only=closed_loop("phase",TRUTH1,PRIOR1,SD1,7,2718))
    rounds=7 if stage=="mixed" else 10
    return dict(rows=closed_loop(stage,TRUTH1,PRIOR1,SD1,rounds,2418 if stage=="mixed" else 2518),
                printed=closed_loop(stage,TRUTH1,PRIOR1,SD1,rounds,2418 if stage=="mixed" else 2518,printed_gaussian=True))


if __name__=="__main__":
    label=sys.argv[1]
    output=run(label)
    Path(f"results/{label}.json").write_text(json.dumps(output,allow_nan=False)+"\n")
