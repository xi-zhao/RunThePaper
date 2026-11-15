"""Noiseless controls for the Fire Opal benchmark's scientific observables."""
import itertools
import json
from pathlib import Path

import numpy as np


def grover():
    n=32
    s=np.ones(n)/np.sqrt(n)
    target=5
    p=s.copy()
    out=[]
    for k in range(5):
        p0=float(p[target]**2)
        pt=np.sin((2*k+1)*np.arcsin(1/np.sqrt(n)))**2
        assert abs(pt-p0)<2e-14
        if k==2:
            assert np.argmax(abs(p)**2)==target
            probs=(abs(p)**2).tolist()
        out.append(float(pt))
        p[target]*=-1
        p=2*s*np.dot(s,p)-p
    others=(1-out[2])/31
    return dict(target="00101",probability_by_iteration=out,iteration2=probs,
                selectivity2=float(np.log2(out[2]/others)))


def fwht(v):
    v=v.copy()
    size=1
    while size<len(v):
        z=v.reshape(-1,2,size)
        a,b=z[:,0].copy(),z[:,1].copy()
        z[:,0]=(a+b)/np.sqrt(2)
        z[:,1]=(a-b)/np.sqrt(2)
        size*=2
    return v


def deterministic():
    rng=np.random.default_rng(1700)
    result=[]
    for width in range(2,17):
        N=2**width
        i=np.arange(N)
        parity=np.zeros(N,int)
        for k in range(width):
            parity^=(i>>k)&1
        bv=float(abs(fwht((1-2*parity)/np.sqrt(N))[-1])**2)
        assert bv>1-2e-13
        outputs=[]
        for k in rng.integers(0,N,10):
            state=np.exp(2j*np.pi*k*i/N)/np.sqrt(N)
            output=np.fft.fft(state)/np.sqrt(N)
            assert abs(output[k])>1-1e-12
            outputs.append(float(abs(output[k])**2))
        result.append(dict(width=width,bv=bv,qft_mean=float(np.mean(outputs))))
    return result


def syndrome():
    G=["XZZXI","IXZZX","XIXZZ","ZXIXZ"]
    p={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),
       "Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    def op(word):
        a=np.ones((1,1))
        for c in word:a=np.kron(a,p[c])
        return a
    st=[op(g) for g in G]
    for a,b in itertools.combinations(st,2): assert np.allclose(a@b,b@a)
    sig={}
    for j in range(5):
        for v in "XYZ":
            a=op("I"*j+v+"I"*(4-j))
            sig[f"{v}{j}"]="".join("1" if np.allclose(a@g,-g@a) else "0" for g in st)
    assert len(set(sig.values()))==15 and "0000" not in sig.values()
    repetition={str(x):"".join(str((x>>i&1)^(x>>(i+1)&1)) for i in range(4)) for x in range(32)}
    assert repetition["4"]=="0110"
    assert len({k for k in repetition.values()})==16
    assert len({repetition[str(x)] for x in range(32) if x.bit_count()<=2})==16
    return dict(five_qubit=sig,repetition=repetition)


def haar4(rng):
    z=rng.normal(size=(4,4))+1j*rng.normal(size=(4,4))
    q,r=np.linalg.qr(z)
    return q*(np.diag(r)/abs(np.diag(r)))


def quantum_volume():
    rng=np.random.default_rng(1709)
    result=[]
    for width in range(2,8):
        ideal,observed=[],[]
        for _ in range(300):
            s=np.zeros(2**width,complex)
            s[0]=1
            s=s.reshape((2,)*width)
            for _ in range(width):
                order=rng.permutation(width)
                for a,b in order[:2*(width//2)].reshape(-1,2):
                    x=np.moveaxis(s,(a,b),(0,1))
                    s=np.moveaxis((haar4(rng)@x.reshape(4,-1)).reshape(x.shape),(0,1),(a,b))
            p=abs(s.ravel())**2
            assert abs(p.sum()-1)<1e-12
            h=float(p[p>np.median(p)].sum())
            ideal.append(h)
            observed.append(rng.binomial(1000,np.clip(h,0.,1.))/1000)
        interval=np.quantile(np.mean(rng.choice(observed,(1000,300)),axis=1),[.025,.975])
        result.append(dict(width=width,ideal_mean=float(np.mean(ideal)),simulated_mean=float(np.mean(observed)),
                           bootstrap=interval.tolist(),sample_values=observed))
    return result


if __name__=="__main__":
    import warnings
    warnings.filterwarnings("ignore",message=".*encountered in matmul",category=RuntimeWarning)
    out=dict(grover=grover(),deterministic=deterministic(),syndrome=syndrome(),qv=quantum_volume())
    Path("results/ideal.json").write_text(json.dumps(out,allow_nan=False)+"\n")
