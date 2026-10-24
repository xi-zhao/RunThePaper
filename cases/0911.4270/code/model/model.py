"""Independent fixed-v2 model; no author curve/reference reads."""
import numpy as np
from scipy.linalg import eigh

def star_model(alpha, power, cutoff, M=350, wmax=50., grid='right'):
    dw=wmax/M
    if grid=='right': ws=(np.arange(M)+1)*dw
    elif grid=='midpoint': ws=(np.arange(M)+.5)*dw
    elif grid=='endpoint': ws=np.linspace(wmax/M,wmax,M)
    else: raise ValueError(grid)
    g=np.sqrt(alpha*ws**power*np.exp(-ws/cutoff)*dw)
    h=np.diag(np.r_[10.,ws]); h[0,1:]=g; h[1:,0]=g
    return h,ws,g

def evolution(h,t):
    vals,vecs=eigh(h,driver='evd')
    row=(np.exp(-1j*np.outer(t,vals))*vecs[0])@vecs.T
    return row,vals

def negativity(eta,noise,r=4.):
    c=np.cosh(2*r); s=np.sinh(2*r)
    a=eta*c+noise; b=c
    radical=np.sqrt((a-b)**2+4*eta*s*s)
    nu=2*(eta+c*noise)/(a+b+radical)
    return np.maximum(0.,-np.log2(nu))

def observe(row,ws,temperatures,r=4.):
    probs=abs(row)**2; eta=probs[:,0]
    out=[]
    for T in temperatures:
        nb=np.zeros_like(ws) if T==0 else 1/np.expm1(ws/T)
        noise=1-eta+2*(probs[:,1:]@nb)
        E=negativity(eta,noise,r)
        I=2*np.maximum(np.diff(E),0).sum()
        out.append((float(I),E,noise))
    return out
