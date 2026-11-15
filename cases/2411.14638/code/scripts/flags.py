"""Exact entangle/disentangle branches, teleported CNOT and GHZ flag controls."""
import json
from pathlib import Path
import numpy as np


def branch(mask,gates):
    for c,t in gates:
        if (mask>>c)&1: mask^=1<<t
    return mask


def bell_chain(n):
    root=(n-1)//2
    a=[(j,j-1) for j in range(root,0,-1)]+[(j,j+1) for j in range(root,n-1)]
    b=[(j-1,j) for j in range(root,0,-1)]+[(j+1,j) for j in range(root+1,n-1)]
    assert branch(0,a)==0 and branch(1<<root,a)==(1<<n)-1
    ends=1|(1<<(n-1))
    assert branch((1<<n)-1,b)==ends and branch(0,b)==0
    flags=((1<<n)-1)^ends
    detected=sum(bool(branch(1<<q,b)&flags) for q in range(n))
    return dict(intermediate_sites=n,preparation_cnot=len(a),disentangling_cnot=len(b),
                local_cnot_including_teleport=len(a)+len(b)+2,flags=n-2,
                detected_x_at_end_of_preparation=detected)


def teleport():
    cx=np.eye(4)[[0,1,3,2]]
    branch_errors=[]
    for m in (0,1):
        for k in (0,1):
            u=np.zeros((4,4),complex)
            for c in (0,1):
                for t in (0,1):
                    for r in (0,1):
                        if r^c != m:continue
                        b=r^m
                        u[2*c+(t^b),2*c+t]+=(-1)**(k*(b+c))/2
            branch_errors.append(float(abs(u-cx/2).max()))
    assert max(branch_errors)==0
    return branch_errors


def phase_check():
    out=[]
    for n in (10,27,54,75):
        phi=2*np.pi*np.arange(2*n+2)/(2*n+2)
        s=(1+np.cos(n*phi))/2
        C=2*np.sqrt(np.fft.fft(s)[n].real/len(s))
        assert abs(C-1)<2e-13
        out.append(dict(n=n,C=float(C),printed_F=float((.5+C)/2),density_matrix_F=1.))
    return out


def noise(n,p,pairs):
    q=1-p
    # Each disjoint parity flag requires its two bits to have equal errors.
    a=(q*q+p*p)**pairs
    bit=(q**n+p**n)
    damp_accept=(1+a)/2
    pop=(1+p**n+q**n)/2
    coherence=q**(n/2)
    return dict(p=p,bitflip_accept=a,bitflip_F=bit/a,damping_accept=damp_accept,
                damping_F=(pop+coherence)/(2*damp_accept),
                phaseflip_accept=1.,phaseflip_F=(1+(1-2*p)**n)/2)


def validate_small():
    n,p=10,.035
    pairs=[(8,9),(5,6)]
    s=np.arange(2**n)
    ones=np.array([int(x).bit_count() for x in s])
    mask=np.ones(len(s),bool)
    for a,b in pairs: mask&=(((s>>a)^(s>>b))&1)==0
    bit=p**ones*(1-p)**(n-ones)
    a=noise(n,p,len(pairs))
    assert abs(bit[mask].sum()-a["bitflip_accept"])<2e-14
    assert abs((1+bit[mask].sum())/2-a["damping_accept"])<2e-14
    return dict(exact_pairs=pairs,**a)


if __name__=="__main__":
    result=dict(chain=[bell_chain(n) for n in range(2,41)],teleport_branch_errors=teleport(),
                MQC=phase_check(),small=validate_small(),GHZ75=[noise(75,float(p),9) for p in np.linspace(0,.04,81)])
    Path("results/flags.json").write_text(json.dumps(result,allow_nan=False)+"\n")
