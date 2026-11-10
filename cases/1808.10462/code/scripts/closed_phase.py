"""Optimize a constant-modulus phase quadratic under linear closure constraints."""
import numpy as np
from scipy.linalg import eigh, svd
from scipy.optimize import minimize


def real_map(segments, reflection):
    count = segments//2 if reflection else segments
    identity = np.eye(segments, count)
    if reflection:
        return np.column_stack((identity+identity[::-1], 1j*(identity-identity[::-1])))
    return np.column_stack((identity, 1j*identity))


def prepare(constraints, form, basis):
    matrix = np.einsum("rs,si->ri",constraints,basis)
    real = np.vstack((matrix.real, matrix.imag))
    _, singular, vectors = svd(real, full_matrices=True)
    rank = int(np.count_nonzero(singular > singular[0]*1e-12))
    applied = np.einsum("st,ti->si",form,basis)
    reduced = np.einsum("si,sj->ij",basis.conj(),applied).real
    reduced = (reduced+reduced.T)/2
    closed = vectors[rank:].T
    applied = np.einsum("ij,jk->ik",reduced,closed)
    values, directions = eigh(np.einsum("ij,ik->jk",closed,applied))
    return reduced, vectors[:rank], values, np.einsum("ij,jk->ik",closed,directions)


def phase_candidates(prepared, sign, cap, target, seed, attempts=2, initial=None):
    form, constraints, values, directions = prepared
    half = len(form)//2
    edge = -1 if sign > 0 else 0
    bound = float(sign*values[edge]*half*cap**2)
    magnitude = abs(target)
    if bound < magnitude*(1-1e-8):
        return None, dict(bound_rad=bound, classification="closed_spectral_bound", trials=[])

    direction = directions[:half,edge]+1j*directions[half:,edge]
    phases = np.angle(direction)
    scaled = sign*form/max(abs(values[edge]),1e-12)/half
    rng = np.random.default_rng(seed)

    def components(x):
        cos, sin = np.cos(x), np.sin(x)
        return cos,sin,np.r_[cos,sin]

    def value(x):
        cos,sin,v = components(x)
        p = np.einsum("ij,j->i",scaled,v)
        return -float(np.dot(v,p)), 2*(sin*p[:half]-cos*p[half:])

    def eq(x):
        return np.einsum("ij,j->i",constraints,components(x)[2])

    def eq_jac(x):
        cos,sin,_ = components(x)
        return -constraints[:,:half]*sin+constraints[:,half:]*cos

    shape = None
    rows = []
    for k in range(attempts):
        if k == 0 and initial is not None:
            x = np.angle(initial)
        elif k == 0:
            x = phases
        else:
            x = phases+rng.normal(0,0.4,half)
        result = minimize(value,x,jac=True,method="SLSQP",
            constraints=[dict(type="eq",fun=eq,jac=eq_jac)],
            options=dict(maxiter=160,ftol=1e-12))
        c,s,v = components(result.x)
        norm = float(np.linalg.norm(np.einsum("ij,j->i",constraints,v)))
        angle = float(np.einsum("i,ij,j",v,form,v))*cap**2
        rows.append(dict(phase_rad=angle,closure_normalized=norm,iterations=int(result.nit),
                         solver_exit=int(result.status)))
        if norm < 1e-9 and sign*angle >= magnitude:
            shape = (c+1j*s)*cap*np.sqrt(target/angle)
            break
    return shape,dict(bound_rad=bound,classification="witness" if shape is not None else "search_unresolved",trials=rows)
