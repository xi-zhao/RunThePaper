"""Recompute the original numerical comparisons and declared experiment models."""

from pathlib import Path
import json

import numpy as np
from scipy.fft import next_fast_len, rfft, rfftfreq
from scipy.integrate import cumulative_trapezoid
from scipy.linalg import solve
from scipy.signal.windows import dpss

from control import cpmg, fd, gaussian_projection_check, projections, pulsed_dpss, responses, variance_from_projections


def targets():
    j=json.loads(Path("config/published-input-spectra.json").read_text())
    return {k:np.asarray(v["frequency_psd"]) for k,v in j.items()}


def spectrum(table, f):
    return np.interp(f,table[:,0],table[:,1],right=0.)


def accumulate(freq, filters, breaks):
    breaks=np.asarray(breaks)
    z=np.clip(np.searchsorted(freq,breaks,side="right")-1,0,len(freq)-2)
    h=breaks-freq[z]
    vals=cumulative_trapezoid(filters,freq,axis=-1,initial=0)
    slope=(filters[...,z+1]-filters[...,z])/(freq[z+1]-freq[z])
    return vals[...,z]+h*(filters[...,z]+h*slope/2)


def area(freq, filt, lo, hi):
    return accumulate(freq,filt,hi)-accumulate(freq,filt,lo)


def signal(freq, filters, target):
    return 2*np.trapezoid(filters*target,freq,axis=-1)


def held_theta_fft(control, dt, subdivision, support):
    angles=np.r_[0.,np.cumsum(control)*dt]
    phase=angles[:-1,None]+np.diff(angles)[:,None]*((np.arange(subdivision)+.5)/subdivision)
    samples=np.sin(phase.ravel())
    step=dt/subdivision
    size=next_fast_len(max(16384,8*len(samples)))
    f=rfftfreq(size,step)
    count=np.searchsorted(f,support)+1
    f=f[:count]
    kernel=abs(rfft(samples,size)[:count])**2*(step*np.sinc(f*step))**2
    return f,kernel


def fd_normalized_estimate(table, n, total, centers, nw, subdivision, support):
    answer=[]
    for fc in centers:
        a=fd(n,total/n,nw,fc)
        f,filt=held_theta_fft(a,total/n,subdivision,support)
        scale=area(f,filt,max(0,fc-nw/total),fc+nw/total)
        answer.append(np.trapezoid(filt*spectrum(table,f),f)/scale)
    return np.asarray(answer)


def finite_comparison(table, tag):
    ion=tag=="ion"
    T, width, nmax, base, M, harmonics, N = (
        (.003,35e-6,83,.00075,4,10,600)
        if ion else (10e-6,11e-9,550,1e-6,10,27,2000))
    frequencies=np.arange(1,nmax+1)/(2*T)
    support=80_000 if ion else 100e6
    f=np.linspace(0,support,24001)
    S=spectrum(table,f)
    pulse=[]
    for n,fc in enumerate(frequencies,1):
        h=abs(cpmg(f,T,n,width))**2
        den=area(f,h,max(0.,fc-1/T),fc+1/T)
        pulse.append(np.trapezoid(h*S,f)/den)
    ids=np.arange(1,harmonics+1)
    centers=ids/base
    lengths=base/ids
    design=np.array([2*M*j/d*abs(cpmg(centers,d,2,width))**2 for j,d in zip(ids,lengths,strict=True)])
    design[(ids[None,:]%ids[:,None])!=0]=0
    observed=[]
    for j,d in zip(ids,lengths,strict=True):
        x=f*d
        x-=np.rint(x)
        repeat=M*j
        comb=(repeat*np.sinc(repeat*x)/np.sinc(x))**2
        observed.append(signal(f,abs(cpmg(f,d,2,width))**2*comb,S))
    comb=solve(design,observed)
    # Source vector markers resolve rounding of the printed grid.
    fc=np.linspace(100.,21000. if ion else 61e6,100)
    fd_value=fd_normalized_estimate(table,N,T,fc,2,4,support)
    fd_step_check=fd_normalized_estimate(table,N,T,fc[::10],2,8,support)
    literal=None
    if not ion:
        printed=100.+615.*np.arange(100)
        literal=dict(min_hz=printed[0],max_hz=printed[-1],inferred_max_hz=fc[-1],
                     independent_model=fd_normalized_estimate(table,N,T,printed,2,4,support))
    return dict(n_pulse_frequency=frequencies,n_pulse_estimate=np.asarray(pulse),comb_frequency=centers,
                comb_estimate=comb,dp_frequency=fc,dp_estimate=fd_value,
                dp_sampling_max_abs=float(max(abs(fd_value[::10]-fd_step_check))),
                model_nyquist=1/(2*T/N),comb_condition=float(np.linalg.cond(design)),printed_superconducting=literal,
                frequency=f[::20],truth=S[::20])


def same_filter_panels():
    f=np.linspace(0,24000,1201)
    T=.003
    result={}
    t=(np.arange(600)+.5)*T/600
    for n in (3,8,12,83):
        center=n/(2*T)
        ctrl=fd(600,T/600,2,center)
        pulse=np.any(abs(t[:,None]-(np.arange(n)+.5)*T/n)<35e-6/2,axis=1)
        result[str(n)]=dict(n=n,center=center,frequency=f, time_s=t,fd_control=ctrl,
            cpmg_control=pulse.astype(int),Fzz=abs(cpmg(f,T,n,35e-6))**2,Fzy=responses(ctrl,T/600,f)[1])
    return result


def mixed_case(table):
    f=np.arange(0,24000+4,4.)
    p=spectrum(table,f)
    coarse=np.array([0,2100,4200,6200,8300,10400,12500,14600,16700])
    fine=np.array([8100,8400,8600,8900,9200,9400,9900,10200,10500,10900,11200,11500])
    a=np.array([responses(fd(500,5e-6,4,fc),5e-6,f)[1] for fc in coarse])
    b=np.array([responses(fd(1000,5e-6,2,fc),5e-6,f)[1] for fc in fine])
    points=np.r_[coarse[:4],fine,coarse[6:]]
    bins=np.r_[0,(points[1:]+points[:-1])/2,17800]
    A=2*np.diff(accumulate(f,a,bins),axis=-1)
    B=2*np.diff(accumulate(f,b,bins),axis=-1)
    a1=np.array([signal(f,k,p)/2/area(f,k,max(0,fc-1600),fc+1600)
                 for k,fc in zip(a,coarse,strict=True)])
    b1=np.array([signal(f,k,p)/2/area(f,k,max(0,fc-400),fc+400)
                 for k,fc in zip(b,fine,strict=True)])
    prior_floor=np.interp(points,coarse,a1)
    # PSD-space regularization and a declared equal projected-variance model.
    left=signal(f,a,p); right=signal(f,b,p)
    A=A/A.sum(axis=1,keepdims=True); B=B/B.sum(axis=1,keepdims=True)
    weak_var=.05**2
    a_precision=A.T@A/weak_var+np.eye(len(points))
    prior=solve(a_precision,A.T@a1/weak_var+prior_floor,assume_a="pos")
    post_precision=a_precision+B.T@B/weak_var
    posterior=solve(post_precision,a_precision@prior+B.T@b1/weak_var,assume_a="pos")
    uncertainty=np.diag(solve(post_precision,np.eye(len(points)),assume_a="pos"))
    return dict(frequency=f[::4],target=p[::4],coarse=coarse,fine=fine,coarse_filters=a[:,::4],fine_filters=b[:,::4],
        coarse_estimate=a1,fine_estimate=b1,bin_edges=bins,bin_centers=points,prior=prior,posterior=posterior,
        approximate_posterior_variance=uncertainty,coarse_rank=int(np.linalg.matrix_rank(A)),fine_rank=int(np.linalg.matrix_rank(B)),
        coarse_projected=left,fine_projected=right)


def overlap_case(tables):
    f=np.arange(0,24000+6,6.)
    centers=np.arange(2000.,15000.,1000.)
    controls=[fd(500,5e-6,4,c) for c in centers]
    filters=np.array([responses(a,5e-6,f) for a in controls])
    sa=spectrum(tables["overlap_amplitude"],f)
    sz=spectrum(tables["overlap_dephasing"],f)
    ax=signal(f,filters[:,0,:],sa)
    ay=signal(f,filters[:,1,:],sz)
    az=signal(f,filters[:,2,:],sz)
    # Calibration-free overlay. Each input amplitude is explicit, and keeps
    # the two expected peak variances comparable rather than fitting counts.
    sx=.023/max(ax); sy=.024/max(ay)
    variances=np.stack((sx*ax,sy*ay,sy*az))
    p=projections(variances)
    inferred=variance_from_projections(p)
    # Integrate only the target passband for the point estimator.
    normalization=np.array([[2*area(f,F,max(0,c-1600),c+1600) for F in ff[:2]]
                           for c,ff in zip(centers,filters,strict=True)]).T
    estimated=inferred[:2]/normalization/np.array([[sx],[sy]])
    error=np.max(abs(inferred-variances))
    return dict(centers=centers,frequency=f[::4],targets=np.array([sa,sz])[:,::4],
            filters=filters[:,:,::4],variances=variances,projections=p,spectral_estimate=estimated,
            inversion_error=float(error),calibration=[sx,sy])


def single_tone():
    T=.0025; dt=5e-6; n=500
    f=np.linspace(0,60000,2401)
    shifted=fd(n,dt,4,10000)
    embedded=fd(n,dt,4,10000,embedded=True)
    plain=dpss(n,4,1,sym=True,norm=2)[0]
    drive=plain*np.cos(2*np.pi*10000*np.arange(n)*dt)
    drive*=2*np.pi*30000/max(abs(drive))
    ff=responses(shifted,dt,f)
    regular=responses(drive,dt,f)
    compare=responses(embedded,dt,f)
    inband=abs(f-10000)<=1600
    bands=[float(np.trapezoid(h[inband],f[inband])/np.trapezoid(h,f))
           for h in (ff[0],ff[1],regular[1])]
    dc=np.array([ff[2,0],compare[2,0]])
    peak=int(np.argmax(ff[1]))
    ratio=ff[0,peak]/ff[1,peak]
    theory=(2*np.pi*f[peak])**2/4
    tone_scale=.003/np.max(ff[1]+ff[2])
    v=np.vstack((np.zeros(len(f)),tone_scale*ff[1],tone_scale*ff[2]))
    return dict(frequency=f,fd=ff,plain=regular,embedded=compare,band_fraction=bands,dc=dc,
        fd_angles=np.cumsum(shifted)*dt,embedded_angles=np.cumsum(embedded)*dt,
        time_s=(np.arange(n)+1)*dt,projections=projections(v),variances=v,
        theoretical_amplitude_to_dephasing_ratio=theory,computed_amplitude_to_dephasing_ratio=ratio)


def taper_and_intrinsic(table):
    f=np.arange(0,22000+6,6.)
    target=spectrum(table,f)
    # The supplementary example states six orders and shifts at 0.5 kHz.
    offsets=np.arange(4)*500.
    centers=np.arange(0,20000,2000.)
    windows=[]
    sums=[]
    variants=[]
    for offset in offsets:
        est0=[]; est6=[]
        for center in centers+offset:
            kernels=np.array([responses(fd(400,5e-6,4,center,order=j),5e-6,f)[1] for j in range(6)])
            areas=2*area(f,kernels,max(0,center-2000),center+2000)
            normalized=kernels/areas[:,None]
            vals=signal(f,normalized,target)
            est0.append(vals[0]);est6.append(np.mean(vals))
            if offset==0 and center==0:
                windows=normalized[:,::5]
                sums=np.mean(windows,axis=0)
        variants.append(dict(centers=centers+offset,k0=np.asarray(est0),multi=np.asarray(est6)))
    # Intrinsic spectra cannot be predicted from filter design alone.
    # Recompute Fig. 7(d,e) locally in each narrow 300 Hz interval.
    intrinsic=[]
    for fc in np.arange(15000,60001,5000):
        hz=np.linspace(fc-150,fc+150,151)
        ff=responses(fd(20000,1e-6,2,fc),1e-6,hz)
        intrinsic.append(dict(center=int(fc),frequency=hz,amplitude=ff[0],dephasing=ff[1],
              peak_ratio=ff[0].max()/ff[1].max()))
    return dict(tapers=dict(frequency=f[::5],filters=windows,average=sums,reconstruction=variants),intrinsic=intrinsic)


def pulsed():
    f=np.linspace(0,4700,2351)
    rows=[]
    for fc in np.arange(200,1801,200):
        ff,t=pulsed_dpss(f,50,240e-6,10e-6,fc)
        rows.append(dict(center=int(fc),value=ff,times=t))
    g=np.linspace(0,700,701)
    x,t=pulsed_dpss(g,25,1.87e-3,35e-6,0)
    y,_=pulsed_dpss(g,25,2e-3,35e-6,0)
    return dict(frequency=f,filters=rows,experimental_model_hz=g,at_1_87_ms=x,at_2_ms=y,
                nominal_harmonics=[1/1.87e-3,500.],trial_pulse_times=t)


def run():
    t=targets()
    return dict(F1=single_tone(), F2_F5=mixed_case(t["mixed"]),F3=overlap_case(t),
        F4_waveforms=same_filter_panels(),
        F4e=finite_comparison(t["ion"],"ion"),F4f=finite_comparison(t["superconducting"],"superconducting"),
        F6_F7=taper_and_intrinsic(t["mixed"]),F8=pulsed(),projection_check=gaussian_projection_check())


if __name__=="__main__":
    Path("results").mkdir(exist_ok=True)
    Path("results/model.json").write_text(json.dumps(run(),separators=(",",":"),allow_nan=False,
        default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+"\n")

