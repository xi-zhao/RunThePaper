"""Discrete-time phase forecasts. Estimation stops at the last training sample."""
from numba import njit
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.fft import irfft
from scipy.linalg import solve


DT = 0.001
NT = 2000
Q = 100
M = 50


def phase_records(rng, trajectories, fundamental, modes, samples, cycle=2*np.pi):
    angles = rng.uniform(0, cycle, (trajectories, modes))
    if modes <= 200:
        phase = 2*np.pi*DT*fundamental*np.arange(samples)[:, None]*np.arange(1, modes+1)
        return np.sqrt(2/modes)*(np.cos(angles)@np.cos(phase).T - np.sin(angles)@np.sin(phase).T)
    period = round(1/(fundamental*DT))
    assert np.isclose(period*DT*fundamental, 1, rtol=0, atol=1e-14)
    result = np.empty((trajectories, samples))
    spectrum = np.zeros(period//2+1, dtype=np.complex128)
    for k in range(trajectories):
        spectrum[1:modes+1] = period/np.sqrt(2*modes)*np.exp(1j*angles[k])
        result[k] = irfft(spectrum, n=period)[:samples]
    return result


def measurements(rng, truth, noise_level):
    # The truth is used to set the simulation's readout noise, never to fit test predictors.
    readout_std = 3*noise_level*np.std(truth[:, :NT], axis=1, ddof=1)
    return truth[:, :NT] + readout_std[:, None]*rng.normal(size=(len(truth), NT))


def ar_fit(measured):
    lag = sliding_window_view(measured, Q+1, axis=1).reshape(-1, Q+1)
    past = np.ascontiguousarray(lag[:, -2::-1])
    target = lag[:, -1]
    a = past.T@past
    w = solve(a, past.T@target, assume_a="pos")
    assert np.max(np.abs(np.roots(np.r_[1., -w]))) < 1
    return w


@njit(nogil=True)
def extrapolate(a, state, steps):
    state = state.copy()
    output = np.empty(steps)
    for t in range(steps):
        prediction = np.dot(a, state)
        output[t] = prediction
        for j in range(len(state)-1, 0, -1):
            state[j] = state[j-1]
        state[0] = prediction
    return output


@njit(nogil=True)
def ar_filter(a, observed, steps, process, noise, initial, binary=False):
    """Companion recursion with scalar observation and source-specific Q."""
    q = len(a)
    n_trajectories, count = observed.shape
    state = np.full((n_trajectories, q), initial)
    n_cov = n_trajectories if binary else 1
    cov = np.zeros((n_cov, q, q))
    for m in range(n_cov):
        for j in range(q):
            cov[m, j, j] = 1.0
    training = np.empty_like(observed)
    for t in range(count):
        if not binary:
            col, scale = ar_predict_cov(a, cov[0], process, noise, 1., False)
        for m in range(n_trajectories):
            phase = np.dot(a, state[m])
            h = 0.5*np.cos(phase) if binary else phase
            if binary:
                col, scale = ar_predict_cov(a, cov[m], process, noise, -0.5*np.sin(phase), True)
            residual = scale*(observed[m, t]-h)
            for j in range(q-1, 0, -1):
                state[m, j] = state[m, j-1] + col[j]*residual
            state[m, 0] = phase + col[0]*residual
            training[m, t] = 0.5*np.cos(state[m, 0]) if binary else state[m, 0]
    pred = np.empty((n_trajectories, steps))
    for m in range(n_trajectories):
        pred[m] = extrapolate(a, state[m], steps)
    if binary:
        pred = 0.5*np.cos(pred)
    return training, pred


@njit(nogil=True)
def ar_predict_cov(a, cov, process, noise, h, full_q):
    v = cov@a
    p00 = np.dot(a, v)+process
    col = np.empty(len(a))
    col[0], col[1:] = p00, v[:-1]
    s = h/(noise+h*h*p00)
    reduce = h*s
    for i in range(len(a)-1, 0, -1):
        for j in range(len(a)-1, 0, -1):
            cov[i, j] = cov[i-1, j-1]-reduce*col[i]*col[j]
        cov[i, i] += process if full_q else 0.
        cov[i, 0] = col[i]*(1-reduce*p00)
        cov[0, i] = cov[i, 0]
    cov[0, 0] = p00*(1-reduce*p00)
    return col, s


def oscillator_basis(n, oscillators=100, step=0.5):
    theta = 2*np.pi*DT*step*np.arange(n)[:, None]*np.arange(1, oscillators+1)
    return np.ascontiguousarray(np.column_stack((np.cos(theta), -np.sin(theta))))


@njit(nogil=True)
def lkffb_row(observed, basis, process, noise):
    """Rotate into the initial oscillator frame, where the transition is identity."""
    count, q = len(observed), basis.shape[1]
    x = np.zeros(q)
    cov = np.eye(q)/q
    filtered = np.empty(count)
    for t in range(count):
        h = basis[t]
        norm = np.dot(x, x)
        amount = process/norm if norm > 1e-30 else 0.
        v = cov@h + (amount*np.dot(x, h))*x
        s = np.dot(h, v)+noise
        residual = (observed[t]-np.dot(x, h))/s
        for i in range(q):
            for j in range(q):
                cov[i, j] += (amount*x[i])*x[j] - (v[i]/s)*v[j]
        x += v*residual
        filtered[t] = np.dot(h, x)
    return filtered, basis[count:]@x, x


def ensemble_risk(true, prediction, mean=0.):
    return np.sum((true-prediction)**2, axis=0)/np.sum((true-mean)**2, axis=0)
