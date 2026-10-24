"""Independent XY-chain covariance calculation in the figure coordinate lambda_c=1.

H/h = -sum_i [lambda/2 ((1+gamma) X_i X_{i+1}
                        +(1-gamma) Y_i Y_{i+1}) + Z_i].
The source interchanges X/Y; a uniform z rotation leaves concurrence invariant.
Even spin parity -> antiperiodic Jordan-Wigner momenta, periodic spin chain.
No source figures, reference ordinates, or author-specific code are read.
"""
import numpy as np
from scipy.integrate import quad_vec
from scipy.linalg import toeplitz


def jets(lam, gamma=1., N=None, rmax=2, eps=2e-11):
    """Return G_r and first two analytic lambda derivatives, r=-rmax..rmax."""
    r = np.arange(-rmax, rmax+1)
    def f(k):
        k = np.atleast_1d(k)
        c,s = np.cos(k),np.sin(k)
        # Sum of squares avoids catastrophic cancellation near lambda=1.
        a,b = lam*c-1., lam*gamma*s
        q = a*a+b*b
        e = np.sqrt(q)
        cr,sr = np.cos(r[:,None]*k),np.sin(r[:,None]*k)
        u = cr*a+sr*b
        v = cr*c+gamma*sr*s
        q1 = 2*(a*c+b*gamma*s)
        q2 = 2*(c*c+gamma*gamma*s*s)
        val = u/e
        d1 = v/e-u*q1/(2*e**3)
        d2 = -v*q1/e**3-u*q2/(2*e**3)+3*u*q1*q1/(4*e**5)
        return np.stack([val,d1,d2],axis=-1)
    if N is not None:
        k = (2*np.arange(N)+1)*np.pi/N
        return f(k).mean(axis=1)
    if lam == 1. and gamma == 1.:
        # Derivatives are singular; values are exact critical Fourier integrals.
        return np.column_stack([2/(np.pi*(2*r-1)),np.full(len(r),np.nan),np.full(len(r),np.nan)])
    delta = abs(lam-1.)/max(lam*gamma,1e-15)
    points = sorted(set([0.,np.pi]+[x for x in [delta*.1,delta,delta*10,.01,.1,1.] if 0<x<np.pi]))
    # Only integrate even combinations over 0..pi. Adaptive vector quadrature.
    total=np.zeros((len(r),3))
    for a,b in zip(points[:-1],points[1:]):
        v,err=quad_vec(lambda k:f(k)[:,0,:],a,b,epsabs=eps,epsrel=eps,limit=1000)
        total+=v/np.pi
    return total


def mul(a,b):
    return np.array([a[0]*b[0], a[1]*b[0]+a[0]*b[1],
                     a[2]*b[0]+2*a[1]*b[1]+a[0]*b[2]])


def concurrence_jets(lam,gamma=1.,N=None,r=1,eps=2e-11):
    if r not in (1,2):
        raise ValueError('Derivative jets implemented for r=1,2 only')
    gj=jets(lam,gamma,N,2,eps)
    g=lambda j:gj[j+2]
    if r==1:
        xx,yy=g(1),g(-1)
    else:
        xx=mul(g(1),g(1))-mul(g(0),g(2))
        yy=mul(g(-1),g(-1))-mul(g(0),g(-2))
    zz=mul(g(0),g(0))-mul(g(r),g(-r))
    branch=(np.sign(xx[0]-yy[0])*(xx-yy)+zz-np.array([1.,0,0]))/2
    # C_minus is relevant outside the critical/Ising branch; derivatives of this
    # branch are not needed in the plotted regime. Calculate its value explicitly.
    alt=(abs(xx[0]+yy[0])-np.sqrt(max(0.,(1+zz[0])**2-4*g(0)[0]**2)))/2
    if alt>max(branch[0],0)+1e-12:
        return np.array([alt,np.nan,np.nan])
    return branch if branch[0]>0 else np.zeros(3)


def all_correlations(lam,gamma=1.,N=None,rmax=30):
    if lam==1. and gamma==1. and N is None:
        gs=2/(np.pi*(2*np.arange(-rmax,rmax+1)-1))
    else:
        # Value-only quadrature avoids derivative singularity at criticality.
        rr=np.arange(-rmax,rmax+1)
        def val(k):
            a=lam*np.cos(k)-1;b=lam*gamma*np.sin(k)
            e=np.hypot(a,b)
            return (np.cos(rr*k)*a+np.sin(rr*k)*b)/e
        if N is None:
            gs=quad_vec(val,0,np.pi,epsabs=1e-12,epsrel=1e-12,limit=1000)[0]/np.pi
        else:
            k=(2*np.arange(N)+1)*np.pi/N
            a=lam*np.cos(k)-1;b=lam*gamma*np.sin(k)
            gs=((np.cos(rr[:,None]*k)*a+np.sin(rr[:,None]*k)*b)/np.hypot(a,b)).mean(1)
    g=lambda r:gs[r+rmax]
    rows=[]
    for r in range(1,rmax+1):
        xx=np.linalg.det(toeplitz([g(1+j) for j in range(r)],[g(1-j) for j in range(r)]))
        yy=np.linalg.det(toeplitz([g(-1+j) for j in range(r)],[g(-1-j) for j in range(r)]))
        zz=g(0)**2-g(r)*g(-r)
        p=(abs(xx-yy)+zz-1)/2
        q=(abs(xx+yy)-np.sqrt(max(0.,(1+zz)**2-4*g(0)**2)))/2
        rows.append([r,xx,yy,zz,max(0,p,q),p,q])
    return -g(0),np.array(rows)
