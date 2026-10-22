"""Independent split-operator Schrodinger propagation, with a state-reset countermodel.
Uses no Ermakov b(t) during propagation and no original graphic arrays.
"""
import json
from pathlib import Path
import numpy as np
gamma=10.;q=.9;w0=2*np.pi*250;e2=(gamma**2+gamma**-2)/2
bs2=(2*e2-(1-q*q))/(1+q*q)
u1=np.arcsinh(np.sqrt((bs2-1)*q*q/(1+q*q)))/q
u2=np.arcsin(np.sqrt((gamma**2-bs2)/(gamma**2-gamma**-2)))
rows=[]
for N in [2048,4096]:
 dx=160/N;x=(np.arange(N)-N//2)*dx;k=2*np.pi*np.fft.fftfreq(N,d=dx)
 initial=np.exp(-x*x/2)/np.pi**.25;target=np.exp(-x*x/(2*gamma**2))/(np.pi*gamma**2)**.25
 def stats(psi,r2):
  density=abs(psi)**2;norm=float(density.sum()*dx);p=np.fft.ifft(k*np.fft.fft(psi));xx=float(density@(x*x)*dx);pp=float((abs(p)**2).sum()*dx)
  return dict(norm=norm,Cxx=2*xx,Cpp=2*pp,energy_over_initial_ground=pp+r2*xx,
   target_fidelity=float(abs(np.vdot(target,psi)*dx)**2),boundary_mass=float(density[abs(x)>70].sum()*dx))
 def propagate(psi,r2,duration,dtmax):
  steps=int(np.ceil(duration/dtmax));dt=duration/steps;half=np.exp(-.25j*r2*x*x*dt);kinetic=np.exp(-.5j*k*k*dt)
  for j in range(steps):psi=half*np.fft.ifft(kinetic*np.fft.fft(half*psi))
  return psi
 for dt in [.004,.002,.001]:
  left=propagate(initial.astype(complex),-q*q,u1,dt);final=propagate(left.copy(),1.,u2,dt)
  reset=propagate(initial.astype(complex),1.,u2,dt)
  r=dict(grid=N,dimensionless_dtmax=dt,first_before_switch=stats(left,-q*q),same_state_after_switch=stats(left,1.),final=stats(final,.0001),
   reset_second_platform=stats(initial,1.),reset_final=stats(reset,.0001))
  rows.append(r);print(json.dumps(r),flush=True)
assert max(abs(r['final']['norm']-1) for r in rows)<1e-9
fine=rows[-1];assert abs(fine['same_state_after_switch']['energy_over_initial_ground']-50.005)<2e-4
assert abs(fine['final']['energy_over_initial_ground']-.01)<1e-7
assert fine['final']['target_fidelity']>1-1e-5
Path('calculation/alignment-v3-20261022/wavefunction_switch.json').write_text(json.dumps(dict(rows=rows,
 u1=u1,u2=u2,t1_seconds=u1/w0,tf_seconds=(u1+u2)/w0,
 reset_analytic_final_energy=.5*(1+gamma**-4),reset_analytic_final_fidelity=2*gamma/(1+gamma**2),
 interpretation='The same propagated wavefunction has no state change at the Hamiltonian quench. A diagnostic reset to the initial ground state does give platform1, but produces final energy.50005 and target fidelity20/101, not .01 and1. This does not assert the authors performed a reset; it tests the physical meaning of that explanation.'),indent=2))
