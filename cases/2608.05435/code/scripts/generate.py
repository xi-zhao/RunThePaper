"""Generate and validate the LNN constructions and the large-register targets."""
import json
from pathlib import Path
import random
import numpy as np
from circuit import (apply,bit_reverse,convolution,cz_native,fourier,linear,mps_probability,
                     phase,phase_error,stats,target_probability,textbook)

cfg=json.loads(Path("config/protocol.json").read_text())
targets=json.loads(Path("config/targets.json").read_text())
rng=random.Random(cfg["seed"])
d0=cfg["retained_angles"]
matrices=[]
small_target=[]
for n in range(2,9):
    size=1<<n
    basis=np.eye(size,dtype=complex)
    fft=fourier(n)
    for d in range(1,n):
        ref=apply(n,textbook(n,d),basis)
        errors=dict(low=phase_error(apply(n,linear(n,d),basis),ref),
                    park=phase_error(apply(n,linear(n,d,False),basis),ref))
        if d==n-1:
            errors["fourier"]=phase_error(ref,fft)
        if d>=2:
            c=convolution(n,d)
            block=np.vstack((basis,0*basis))
            r=apply(n+1,c,block)
            errors["convolution"]=phase_error(r[::2],ref)
            errors["ancilla"]=float(np.max(abs(r[1::2])))
            if n<=5:
                errors["cz_native"]=phase_error(apply(n+1,cz_native(c),block),r)
            if d in (min(n-1,d0),n-1):
                # Columns of F^dagger are periodic inputs with ordered targets.
                positions=bit_reverse(n)
                v=fft.conj().T[:,positions]
                s=apply(n+1,c,np.vstack((v,0*v)))
                observed=abs(s[2*positions,np.arange(size)])**2
                expected=np.array([target_probability(n,d,k) for k in range(size)])
                small_target.append(dict(n=n,d=d,max_error=float(np.max(abs(observed-expected)))))
        matrices.append(dict(n=n,d=d,errors=errors))

# With d=1, check how far the last output can depend on the first input.
n=9
small=apply(n,textbook(n,1),np.eye(1<<n,dtype=complex))
index=np.arange(1<<n)
z_last=1-2*(index&1)
z_first=1-2*(index>>(n-1))
back=small.conj().T@(z_last[:,None]*small)
commutator=back*(z_first[None,:]-z_first[:,None])
d1=dict(n=n,predicted_table_depth=6,min_depth_for_shift=n-2,
        normalized_commutator=float(np.linalg.norm(commutator,"fro")/np.sqrt(1<<n)))

resources={}
for n,d in [(n,d0) for n in range(5,101)]+[(n,n-1) for n in (3,4,5,6,8,10,50,80,100)]:
    c=convolution(n,d)
    p=stats(n,linear(n,d,False))
    low=stats(n,linear(n,d))
    conv=stats(n+1,c)
    resources[f"{n},{d}"]=dict(n=n,d=d,park=p,low=low,conv=conv,
        table=dict(park_count=d*(2*n-d-1)+2*n-4,low_count=d*(2*n-d-1),
          conv_count=d*(2*n-d-1)+2,park_depth=2*(d+1)*n-d*(d+1)-4,
          low_depth=(2*d-1)*n-d*(d+1)+3,conv_depth_approx=2*(d-1)*n-d*(d+1)+8,
          conv_depth_full=n*n-3*n-8 if d==n-1 else None))

curves=[]
for n in range(5,101):
    k=[rng.getrandbits(n) for _ in range(cfg["per_width_samples"])]
    exact=[target_probability(n,d0,t) for t in k]
    plain=[target_probability(n,d0,t,False) for t in k]
    curves.append(dict(n=n,p10=float(np.quantile(exact,.1)),median=float(np.median(exact)),
        p90=float(np.quantile(exact,.9)),plain_median=float(np.median(plain)),
        worst=target_probability(n,d0,0),
        competitor_bound=float(np.sin(phase(d0+2))**2)))

big={}
for n in (50,80,100):
    c=convolution(n,d0)
    inputs=targets.get(str(n))
    if inputs is None:
        inputs=[hex(x) for x in (0,(1<<n)-1,((1<<n)-1)//3,*[rng.getrandbits(n) for _ in range(9)])]
    rows=[]
    for label in inputs:
        k=int(label,16)
        got=mps_probability(n,d0,k,c)
        ref=target_probability(n,d0,k)
        rows.append(dict(target=label,**got,independent_probability=ref,delta=abs(got["probability"]-ref)))
    big[str(n)]=rows
    if n==100:
        Path("results/convolution-100-d3.json").write_text(json.dumps(dict(data_qubits=n,
            qubits=n+1,ancilla_input=0,ancilla_output=n,output_endianness="reversed",
            gates=c),separators=(",",":"))+"\n")

# No measurement can distinguish ideal output from an added diagonal output unitary.
f=fourier(3)
d_out=np.where(np.arange(8)<4,1.,-1.)
bad=d_out[:,None]*f
overlap=np.trace(f.conj().T@bad)/8
phase_counterexample=dict(measured_difference=float(np.max(abs(abs(f@f.conj().T)**2-abs(bad@f.conj().T)**2))),
                          unitary_process_fidelity=float(abs(overlap)**2))
res=dict(matrices=matrices,small_targets=small_target,resources=resources,curves=curves,large=big,
         d1_causal_check=d1,phase_counterexample=phase_counterexample)
Path("results/qft-results.json").write_text(json.dumps(res,separators=(",",":"),allow_nan=False)+"\n")
