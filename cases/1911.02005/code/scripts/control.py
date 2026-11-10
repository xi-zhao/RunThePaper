"""Exact held-control transforms and finite-width pulsed dephasing."""

import numpy as np
from scipy.signal.windows import dpss


def fd(n, dt, nw, shift, order=0, peak=.15, embedded=False):
    window=dpss(n,nw,order+1,sym=True,norm=2)[order]
    angle=window*np.cos(2*np.pi*shift*dt*np.arange(n))
    angle=peak*angle/np.max(abs(angle))
    angle[-1]=0.
    if embedded:
        # Conjugate the middle half about π while preserving sin(Θ).
        angle[n//4:3*n//4]=np.pi-angle[n//4:3*n//4]
    return np.diff(np.r_[0,angle])/dt


def responses(control, dt, frequency):
    """Return |Fxx/2|², |Fzy|² and |Fzz|² for a rectangular drive."""
    f=np.atleast_1d(frequency)
    n=len(control)
    position=(np.arange(n)+.5)*dt
    midpoint=(np.cumsum(control)-control/2)*dt
    freq_offset=control/(2*np.pi)
    positive=np.exp(1j*midpoint)
    result=np.empty((3,len(f)))
    chunk=max(1,800_000//n)
    for i in range(0,len(f),chunk):
        x=f[i:i+chunk,None]
        osc=dt*np.exp(2j*np.pi*x*position)
        rf=np.sum(osc*control,axis=1)*np.sinc(x[:,0]*dt)
        yp=np.sum(osc*np.sinc((x+freq_offset)*dt)*positive,axis=1)
        ym=np.sum(osc*np.sinc((x-freq_offset)*dt)*positive.conj(),axis=1)
        result[:,i:i+len(x)]=np.abs(np.stack((rf/2,(yp-ym)/(2j),(yp+ym)/2)))**2
    assert np.all(np.isfinite(result))
    return result


def toggling_pulses(freq, total, centers, width):
    """Fourier transform of cos Θ including finite π rotations."""
    x=np.asarray(freq,float)
    signs=(-1.)**np.arange(len(centers))
    sums=np.sum(np.exp(2j*np.pi*x[:,None]*centers)*signs,axis=1)
    return from_pulse_sum(x,total,len(centers),width,sums)


def from_pulse_sum(f,total,n,width,sums):
    form=np.pi/2*(np.sinc(f*width+.5)+np.sinc(f*width-.5))
    numerator=(-1.)**n*np.exp(2j*np.pi*f*total)-1+form*sums
    out=np.zeros_like(numerator)
    nz=f!=0
    out[nz]=numerator[nz]/(2j*np.pi*f[nz])
    return out


def cpmg(f,total,n,width):
    assert n*width<=total
    t=f*total/n
    phase=t+.5
    phase-=np.rint(phase)
    z=n*np.exp(1j*np.pi*(t+(n-1)*phase))*np.sinc(n*phase)/np.sinc(phase)
    return from_pulse_sum(f,total,n,width,z)


def pulsed_dpss(f,n,cell,pi_time,carrier,nw=2,relative=.45):
    v=dpss(n,nw,1,sym=True,norm=2)[0]
    margin=cell-2*pi_time
    displacement=relative*margin*v/max(v)*np.cos(2*np.pi*carrier*cell*np.arange(n))
    middle=(np.arange(n)+.5)*cell+displacement/2
    between=np.arange(1,n)*cell
    centers=np.sort(np.r_[middle,between])
    assert np.min(np.diff(centers))>pi_time
    integral=toggling_pulses(f,n*cell,centers,pi_time)
    # Use the exact static signed area of all intervals; each π rotation has
    # zero mean in cos Θ, and center replacement preserves its static area.
    edges=np.r_[0.,centers,n*cell]
    integral[f==0]=np.sum(np.diff(edges)*(-1.)**np.arange(len(edges)-1))
    return abs(integral)**2,centers


def variance_from_projections(probs):
    p=np.asarray(probs)
    assert p.shape[0]==3
    return (1+2*p-p.sum(axis=0))/2


def projections(variances):
    return 1-np.sum(variances,axis=0)+variances


def gaussian_projection_check():
    """Exact rotations averaged over small independent Gaussian vector errors."""
    from scipy.special import roots_hermite
    x,w=roots_hermite(11)
    grid=np.asarray(np.meshgrid(x,x,x,indexing="ij")).reshape(3,-1)
    weights=np.prod(np.asarray(np.meshgrid(w,w,w,indexing="ij")),axis=0).ravel()/np.pi**1.5
    rows=[]
    for scale in (.02,.01,.005):
        sig=np.array([1.,.8,.4])*scale
        q=grid*sig[:,None]*np.sqrt(2)
        squared=q**2
        norm=np.sqrt(np.sum(squared,axis=0))
        loss=(norm**2-squared)*np.sinc(norm/np.pi)**2
        p=1-np.sum(loss*weights,axis=1)
        inferred=variance_from_projections(p)
        rows.append(dict(scale=scale,maximum_bias=float(max(abs(inferred-sig**2)))))
    return rows

