"""Independent linear-optical simulation. Columns are input modes.

Polynomial coefficients are unnormalised until converted to Fock amplitudes.
No occupancy cutoff: heralding norms include all signal occupations.
"""
import itertools as it
import math
import numpy as np

def fock(m, n):
    if m == 1:
        return [(n,)]
    return [(k,) + r for k in range(n+1) for r in fock(m-1, n-k)]

def factorial(v):
    return math.prod(math.factorial(k) for k in v)

def polynomial_fft(U, occupation):
    m = U.shape[0]
    n = sum(occupation)
    shape = (n+1,)*m
    product = np.ones(shape, dtype=complex)
    for i, count in enumerate(occupation):
        if not count:
            continue
        factor = np.zeros(shape, dtype=complex)
        for j in range(m):
            index = [0]*m
            index[j] = 1
            factor[tuple(index)] = U[j,i]
        product *= np.fft.fftn(factor)**count
    return np.fft.ifftn(product)

def full_fft(U, occupation):
    p = polynomial_fft(U, occupation)
    return {v:p[v]*math.sqrt(factorial(v)/factorial(occupation))
            for v in fock(U.shape[0],sum(occupation))}

def sparse_creation(U, occupation):
    """Separate recurrence directly on normalized bosonic occupation states."""
    state = {(0,)*U.shape[0]:1+0j}
    for col, count in enumerate(occupation):
        for repeat in range(count):
            out = {}
            for v, amp in state.items():
                for j in range(U.shape[0]):
                    dest = list(v)
                    dest[j] += 1
                    dest = tuple(dest)
                    out[dest] = out.get(dest,0j)+amp*U[j,col]*math.sqrt((v[j]+1)/(repeat+1))
            state = out
    return state

def bipartite(U, occupation, ms, ns):
    """Binomial sector expansion using raw polynomials, then Fock normalization."""
    sa, aa = fock(ms,ns), fock(U.shape[0]-ms,sum(occupation)-ns)
    B = np.zeros((len(sa),len(aa)),complex)
    for split in it.product(*(range(k+1) for k in occupation)):
        if sum(split) != ns:
            continue
        rest = tuple(n-s for n,s in zip(occupation,split))
        weight = math.prod(math.comb(n,s) for n,s in zip(occupation,split))
        ps = polynomial_fft(U[:ms],split)
        pa = polynomial_fft(U[ms:],rest)
        B += weight*np.outer([ps[v] for v in sa],[pa[v] for v in aa])
    B *= np.sqrt(np.outer([factorial(v) for v in sa],[factorial(v) for v in aa])/factorial(occupation))
    return sa,aa,B

def permanent(A):
    """Ryser inclusion-exclusion, separate amplitude checker."""
    n = len(A)
    return sum((-1)**(n-len(s))*np.prod(A[:,s].sum(axis=1))
               for k in range(1,n+1) for s in it.combinations(range(n),k)) if n else 1

def permanent_amplitude(U, occupation, output):
    cols = np.repeat(np.arange(len(occupation)),occupation)
    rows = np.repeat(np.arange(len(output)),output)
    return permanent(U[np.ix_(rows,cols)])/math.sqrt(factorial(occupation)*factorial(output))

def haar(m, rng):
    Q,R = np.linalg.qr(rng.normal(size=(m,m))+1j*rng.normal(size=(m,m)))
    return Q @ np.diag(np.diag(R)/np.abs(np.diag(R)))

def bell_reference():
    """Paper Eq. (23), verification fixture, never a discovery initialization."""
    w = np.exp(1j*np.pi/12)
    r = np.sqrt(2)
    return np.array([[r,r*w**6,r,0,0],
        [w**18,w**16,w**2,w**6,r],
        [r*w**18,r*w**8,r*w**10,0,0],
        [0,0,0,2,r*w**6],
        [w**6,w**4,w**14,w**6,r]],complex)/np.sqrt(6)
