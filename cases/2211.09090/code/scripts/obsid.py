"""Small-array closed-loop Hamiltonian learning for QC18."""
import numpy as np


TRUTH1=np.array([4.,6.])
PRIOR1=np.array([4.1,6.2])
SD1=np.array([.5,.5])
TRUTH2=np.array([4.1,5.5,4.,6.,.5])
SD2=np.array([.3,.3,.3,.3,.03])


def rabi(g,t):
    d,o=np.moveaxis(g,-1,0)
    f=np.hypot(d,o)
    return 1-(o*t/2*np.sinc(f*t/(2*np.pi)))**2


def ramsey(g,t,nominal):
    d,o=np.moveaxis(g,-1,0)
    return 1-(np.sin(np.pi*o/(2*nominal))*np.sin(d*t/2))**2


def piecewise(g,dt,c):
    d,o=np.moveaxis(g,-1,0)
    v=np.ones(len(g),complex)
    w=np.zeros_like(v)
    for a,step in zip(c,dt):
        f=np.hypot(d,o*abs(a))
        sin=step/2*np.sinc(f*step/(2*np.pi))
        co=np.cos(f*step/2)
        v,w=(co+1j*d*sin)*v-1j*o*a*sin*w,-1j*o*np.conj(a)*sin*v+(co-1j*d*sin)*w
    return abs(v)**2


def coupled(g,dt,c):
    d,o,e,p,j=np.moveaxis(g,-1,0)
    v=np.zeros((len(g),4),complex)
    v[:,0]=1
    h=np.zeros((len(g),4,4))
    h[:,0,0]=-(d+e)/2
    h[:,1,1]=(-d+e)/2
    h[:,2,2]=(d-e)/2
    h[:,3,3]=(d+e)/2
    h[:,1,2]=h[:,2,1]=j
    for (a,b),step in zip(c,dt):
        h[:,0,2]=h[:,2,0]=h[:,1,3]=h[:,3,1]=o*a/2
        h[:,0,1]=h[:,1,0]=h[:,2,3]=h[:,3,2]=p*b/2
        eigen,basis=np.linalg.eigh(h)
        z=np.einsum("nik,ni->nk",basis,v)*np.exp(-1j*eigen*step)
        v=np.einsum("nik,nk->ni",basis,z)
    return abs(v[:,0])**2


def respond(g,pulse):
    kind,t,control=pulse
    if kind=="rabi":
        return rabi(g,t)
    if kind=="ramsey":
        return ramsey(g,t,control)
    if kind in ("pwc","phase"):
        return piecewise(g,np.full(len(control),t/len(control)),control)
    if kind=="two":
        return coupled(g,np.full(len(control),t/len(control)),control)
    raise ValueError(kind)


def apc_gain(g,p,sigma,measurement_grid=None):
    # Law of total covariance: tr(prior)-E tr(posterior) = tr Cov(posterior mean).
    m=np.linspace(-5*sigma,1+5*sigma,57) if measurement_grid is None else measurement_grid
    likelihood=np.exp(-.5*((m[:,None]-p)/sigma)**2)
    q=likelihood.sum(axis=1)
    center=g-g.mean(axis=0)
    numerator=np.einsum("ij,jk->ik",likelihood,center)
    return float(np.sum(np.sum(numerator*numerator,axis=1)/q)/np.sum(q))


def direct_apc(g,p,sigma):
    m=np.linspace(-5*sigma,1+5*sigma,401)
    norm=[]
    costs=[]
    for x in m:
        w=np.exp(-.5*((p-x)/sigma)**2)
        norm.append(w.sum())
        u=np.average(g,axis=0,weights=w)
        costs.append(np.average(np.sum((g-u)**2,axis=1),weights=w))
    return np.average(costs,weights=norm)


def summarize(g,truth):
    cov=np.cov(g,rowvar=False)
    scale=np.sqrt(np.maximum(np.linalg.eigvalsh(cov),0))
    return dict(mean=g.mean(axis=0).tolist(),error=np.abs(g.mean(axis=0)-truth).tolist(),
                deviations=scale.tolist())


def choice(rng,points,family,previous,nominal,sigma):
    # Same candidate set for any draw; small design population is drawn from the prior.
    points=points[rng.choice(len(points),min(len(points),384),replace=False)]
    spread=np.sqrt(np.max(np.linalg.eigvalsh(np.cov(points,rowvar=False))))
    top=min(10000.,8/spread)
    if family in ("pwc","two") and previous is not None:
        top=min(top,2*previous)
    times=np.geomspace(max(.06,top/24),top,30)
    if family in ("mixed","rabi"):
        kinds=("rabi","ramsey") if family=="mixed" else ("rabi",)
        candidates=[(k,float(t),nominal if k=="ramsey" else 1.) for t in times for k in kinds]
    else:
        # Random coarse controls and local perturbations of the best point.
        if family=="pwc":
            draw=lambda: rng.uniform(-1,1,10)
        elif family=="two":
            draw=lambda: rng.uniform(-1,1,(10,2))
        else:
            draw=lambda: np.exp(1j*rng.uniform(-np.pi,np.pi,10))
        candidates=[(family,float(times[i%len(times)]),draw()) for i in range(90 if family!="two" else 48)]
    def value(probe):
        return apc_gain(points,respond(points,probe),sigma)
    gains=[value(p) for p in candidates]
    best=candidates[int(np.argmax(gains))]
    score=max(gains)
    if family in ("pwc","phase","two"):
        for _ in range(20 if family!="two" else 10):
            k,t,c=best
            candidate_t=min(top,max(.06,t*np.exp(.16*rng.normal())))
            if family=="phase":
                new=c*np.exp(.3j*rng.normal(size=c.shape))
            else:
                new=np.clip(c+.2*rng.normal(size=c.shape),-1,1)
            trial=(k,float(candidate_t),new)
            v=value(trial)
            if v>score:
                score,best=v,trial
    return best,score


def closed_loop(family,truth,mean,sd,rounds,seed,population=2200,printed_gaussian=False):
    rng=np.random.default_rng(seed)
    g=rng.normal(mean,sd,size=(population,len(truth)))
    rows=[summarize(g,truth)]
    measurements=[]
    prev=None
    def likelihood(z,probes):
        logp=-.5*np.sum(((z-mean)/sd)**2,axis=1)
        for control,m,sig in probes:
            logp-=.5*((respond(z,control)-m)/sig)**2
        return logp
    for n in range(rounds):
        sigma=.05
        sigma_model=sigma*np.sqrt(2) if printed_gaussian else sigma
        pulse,score=choice(rng,g,family,prev,max(abs(g[:,1].mean()),.1),sigma_model)
        truth_p=float(respond(truth[None],pulse)[0])
        observed=truth_p+sigma*rng.normal()
        p=respond(g,pulse)
        weights=np.exp(-.5*((p-observed)/sigma_model)**2)
        weights/=weights.sum()
        idx=np.searchsorted(np.cumsum(weights),(rng.random()+np.arange(population))/population)
        g=g[idx]
        measurements.append((pulse,observed,sigma_model))
        cov=np.cov(g,rowvar=False)+np.eye(len(mean))*1e-12
        prop=np.linalg.cholesky(cov)
        posterior=likelihood(g,measurements)
        # Metropolis correction keeps all past likelihoods in the particle target.
        for _ in range(3):
            proposed=g+.6*(rng.normal(size=g.shape)@prop.T)
            l=likelihood(proposed,measurements)
            take=np.log(rng.random(population))<l-posterior
            g[take],posterior[take]=proposed[take],l[take]
        prev=pulse[1]
        kind,t,c=pulse
        if np.iscomplexobj(c):
            c=np.column_stack((c.real,c.imag))
        row=summarize(g,truth)
        row.update(pulse=kind,duration=t,control=np.asarray(c).tolist(),gain=score,m=observed,
                   model_probability=truth_p,likelihood_sigma=sigma_model,effective_particles=float(1/(weights@weights)))
        if len(rows)<=2 or n==rounds-1:
            row["posterior_sample"]=g[::11].tolist()
        rows.append(row)
    return rows
