"""Independent algebra and multistate propagation diagnostics, no source arrays."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, expm
from scipy.optimize import minimize_scalar
from scipy.integrate import quad

def propagate(peak,dt=1e-6,pad=4,method='eigh',literal=False,q=0.,intensity=1.,width='printed'):
    n=3;wr=2*np.pi*3771.;sigma=15e-6
    m=np.arange(-pad,n+pad+1);delta=4*n*wr
    D=wr*(2*m+q+delta/(4*wr))**2 if literal else 4*wr*m*(m+q)-m*delta
    # Scalar energy shifts leave all probabilities invariant.
    D=D-D[pad]
    end=90e-6;steps=round(2*end/dt);dt=2*end/steps
    psi=np.zeros(len(m),complex);psi[pad]=1
    max_edge=0.
    for j in range(steps):
        t=-end+(j+.5)*dt;omega=peak*intensity*np.exp(-t*t/((4 if width=='printed' else 2)*sigma*sigma))
        H=np.diag(D)+np.diag(np.full(len(m)-1,omega),1)+np.diag(np.full(len(m)-1,omega),-1)
        if method=='eigh':
            w,v=eigh(H);psi=np.einsum('ij,j->i',v,np.einsum('ji,j->i',v,psi)*np.exp(-1j*w*dt))
        else:psi=np.einsum('ij,j->i',expm(-1j*H*dt),psi)
        assert np.all(np.isfinite(psi))
        max_edge=max(max_edge,float(abs(psi[0])**2+abs(psi[-1])**2))
    return psi,dict(transfer=float(abs(psi[pad+n])**2),norm_error=float(abs(np.vdot(psi,psi).real-1)),max_edge_population=max_edge)

def main():
    I=np.eye(2,dtype=complex);X=np.array([[0,1],[1,0]],complex);T=I-1j*X;P=I+X;M=-1j*X
    def cost(U,T,P):
        A=P@T;B=P@U
        return float(1-abs(np.trace(A.conj().T@B)/np.trace(A.conj().T@A))**2)
    r={'scope':'Diagnostic model and printed-equation checks; not reproduction of optimized pulses',
       'literal_target_unitarity_defect':float(np.linalg.norm(T.conj().T@T-I)),
       'literal_projection_idempotence_defect':float(np.linalg.norm(P@P-P)),
       'literal_projection_rank':int(np.linalg.matrix_rank(P)),
       'literal_cost_identity':cost(I,T,P),'literal_cost_mirror':cost(M,T,P),
       'repaired_cost_identity':cost(I,M,I),'repaired_cost_mirror':cost(M,M,I),
       'literal_resonance_gap_over_omega_R':72.,'consistent_resonance_gap_over_omega_R':0.,
       'printed_gaussian_sd_over_sigma':np.sqrt(2.),
       'lateral_coefficient':np.sqrt(-np.log(.8)/8),
       'lateral_accel_m_s2':.005/.01**2*np.sqrt(-np.log(.8)/8)}
    # A fixed n=3 phase-dependent two-arm splitter tests the observable phase period.
    def split(theta,half=False):
        phase=3*theta/(2 if half else 1)
        A=np.array([[0,np.exp(1j*phase)],[np.exp(-1j*phase),0]])
        return (I-1j*A)/np.sqrt(2)
    phases=np.linspace(0,2*np.pi,601)
    fringes=[]
    for half in [False,True]:
        vals=np.array([abs((split(t,half)@M@split(0,half)@np.array([1,0]))[1])**2 for t in phases])
        predicted=(1-np.cos((1.5 if half else 3)*phases))/2
        # Output-port convention may complement; retain the best exact analytic identity.
        err=min(np.max(abs(vals-predicted)),np.max(abs(vals-(1-predicted))))
        fringes.append({'phase_multiplier':1.5 if half else 3,'analytic_max_error':float(err)})
    r['phase_checks']=fringes
    # First broad local maximum, calibrated from dynamics rather than source curve.
    peaks=2*np.pi*np.linspace(1000,40000,50)
    f=np.array([propagate(p,dt=2e-6)[1]['transfer'] for p in peaks]);j=int(np.argmax(f))
    lo=peaks[max(0,j-1)];hi=peaks[min(len(peaks)-1,j+1)]
    opt=minimize_scalar(lambda p:-propagate(p)[1]['transfer'],bounds=(lo,hi),method='bounded')
    peak=opt.x;r['diagnostic_peak_rad_s']=peak;r['propagation']=[]
    for dt,pad,method,literal in [(1e-6,4,'eigh',False),(.5e-6,4,'eigh',False),(.25e-6,4,'eigh',False),(.25e-6,6,'eigh',False),(1e-6,4,'expm',False),(1e-6,8,'eigh',True),(.5e-6,10,'eigh',True)]:
        psi,v=propagate(peak,dt,pad,method,literal);v.update(dt=dt,pad=pad,method=method,literal=literal);r['propagation'].append(v)
    a=propagate(peak,method='eigh')[0];b=propagate(peak,method='expm')[0]
    r['eigh_expm_state_l2']=float(np.linalg.norm(a-b))
    # Independent integral check of triangular acceleration sensitivity.
    r['sensitivity_area_over_T2']=quad(lambda t:t if t<.01 else .02-t,0,.02,points=[.01])[0]/.01**2
    out=Path('results');out.mkdir(exist_ok=True);(out/'model_checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
