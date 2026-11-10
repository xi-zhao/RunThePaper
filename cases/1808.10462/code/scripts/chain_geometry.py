"""Linear Coulomb-chain geometry reused from the QC23 source model."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[key]="1"
import numpy as np
from scipy.constants import atomic_mass,hbar
from scipy.optimize import root
from scipy.linalg import eigh

def equilibrium(ions):
    def equations(z):
        differences=z[:,None]-z[None,:]
        np.fill_diagonal(differences,np.inf)
        force=np.zeros_like(differences)
        finite=np.isfinite(differences)
        force[finite]=np.sign(differences[finite])/abs(differences[finite])**2
        return z-force.sum(axis=1)
    answer=root(equations,np.linspace(-1,1,ions)*ions**0.55,tol=1e-12)
    z=np.sort(answer.x)
    assert max(abs(equations(z)))<1e-10 and min(np.diff(z))>0
    differences=abs(z[:,None]-z[None,:]);np.fill_diagonal(differences,np.inf)
    weight=differences**-3
    laplacian=np.diag(weight.sum(axis=1))-weight
    return z,laplacian,float(max(abs(equations(z))))


def modes(config):
    z,L,force_error=equilibrium(config["ions"])
    freq,part=[],[]
    for com in config["transverse_com_hz"]:
        vals,vec=eigh(com**2*np.eye(len(z))-config["axial_com_hz"]**2*L)
        assert vals.min()>0,"linear chain is unstable"
        freq.extend(np.sqrt(vals[::-1]));part.append(vec[:,::-1])
    freq=np.array(freq);vectors=np.column_stack(part)
    eta=vectors*np.sqrt(hbar/(4*np.pi*config["ion_mass_amu"]*atomic_mass*freq))[None,:]*(2*np.pi/config["wavelength_m"])
    return freq,eta,np.asarray(z),force_error


