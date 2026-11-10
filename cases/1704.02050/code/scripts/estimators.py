"""Implement Supplementary Notes 8–9, keeping manuscript and archive conventions explicit."""
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.linalg import solve

from physics import areas, shift, tapers, transfer


def spectral_bank(omega):
    """Held samples for the documented 9 × 4 bank in the public repository."""
    n = 2240
    duration = n*1e-6
    band = 2*np.pi*7/duration
    shifts = 2*np.pi*2.5*np.arange(9)/duration
    base = tapers(n,7,8)[[1,3,5,7]]
    rates = np.column_stack([areas(shift(v,duration/n,s/(2*np.pi),"SSB"),trapezoid=True)
                             for s in shifts for v in base])
    held = np.abs(transfer(rates,omega/(2*np.pi),duration))**2
    return held.reshape(len(omega),9,4).transpose(1,2,0), shifts, band


def integral_table(grid, curves, points):
    """Exact antiderivative of the piecewise-linear tabulation."""
    p = np.asarray(points)
    idx = np.clip(np.searchsorted(grid,p,side="right")-1,0,len(grid)-2)
    dx = p-grid[idx]
    accum = cumulative_trapezoid(curves,grid,axis=-1,initial=0)
    slope = (curves[...,idx+1]-curves[...,idx])/(grid[idx+1]-grid[idx])
    return accum[...,idx]+dx*(curves[...,idx]+slope*dx/2)


def area_per_band(grid, values, shifts, band):
    return np.array([integral_table(grid,row,s+band)-integral_table(grid,row,s)
                     for s,row in zip(shifts,values)])


def interpolate_spectrum(grid, centers, estimate, cutoff):
    return np.interp(grid,np.r_[0,centers,cutoff],np.r_[estimate[0],estimate,0],right=0)


def adaptive(grid, kernel, shifts, width, infidelity, iterations=10, archive=False):
    """Bias-based weights and a declared reconstruction interpolation."""
    centers = shifts+width/2
    if archive:
        step = grid[1]-grid[0]
        first = np.rint(shifts/step).astype(int)
        count = int(np.rint(width/step))
        used_shifts = grid[first]
        used_width = count*step
        centers = shifts+width/4
        cutoff = grid[first[-1]+(count+1)//2]
        anchor = grid[first+int(np.floor(count/2+0.5))]
        stop = grid[-2]
        # A left/right grid truncation and quarter-band interpolation are archive settings.
    else:
        used_shifts,used_width = shifts,width
        cutoff = shifts[-1]+width
        anchor,stop = centers,grid[-1]
    normal = area_per_band(grid,kernel,used_shifts,used_width)
    single = infidelity/normal
    history = [single[:,0]]
    weights = []
    for _ in range(iterations):
        estimate = history[-1]
        values = interpolate_spectrum(grid,centers,estimate,cutoff)
        grad = np.diff(estimate)/np.diff(centers)
        deriv = interpolate_spectrum(grid,centers,np.r_[grad,grad[-1]],cutoff)
        weighted = kernel*values
        inside = area_per_band(grid,weighted,used_shifts,used_width)
        broadband = (integral_table(grid,weighted,stop)-inside)/normal
        if archive:
            broadband[0] = (integral_table(grid,weighted[0],stop)-
                            integral_table(grid,weighted[0],used_width))/normal[0]
        local = area_per_band(grid,kernel*deriv*(grid-centers[:,None])[:,None,:],
                              used_shifts,used_width)/normal
        center = np.interp(anchor,grid,values)
        numerator = (integral_table(grid,weighted,grid[-1])/normal if archive else center[:,None])
        weight = numerator/(center[:,None]+broadband+local)
        weight = weight/weight.sum(axis=1,keepdims=True)
        weights.append(weight)
        history.append(np.sum(weight*single,axis=1))
    return np.asarray(history),np.asarray(weights),single


def bayes(grid, kernel, shifts, width, infidelity, variance, prior_centers, prior,
          sigma=1.5e-5, segments=4, archive_precision=False, archive_overlap=False):
    """Regularized weighted least squares, followed by local Fisher fusion."""
    edges = shifts[:,None]+np.linspace(0,width,segments+1)
    mid = (edges[:,1:]+edges[:,:-1])/2
    delta = width/segments
    prior_mean = np.interp(mid,prior_centers,prior)
    intervals = [(lo,hi) for row in edges for lo,hi in zip(row[:-1],row[1:])]
    local, condition = [], []
    precision = (delta if archive_precision else 1)/sigma**2
    for j,bounds in enumerate(edges):
        design = np.diff(integral_table(grid,kernel[j],bounds),axis=-1)
        lhs = (design/variance[j,:,None]).T @ design + precision*np.eye(segments)
        rhs = design.T @ (infidelity[j]/variance[j])+precision*prior_mean[j]
        local.append(solve(lhs,rhs,assume_a="pos"))
        condition.append(np.linalg.cond(lhs))
    local = np.asarray(local)
    fused = np.empty_like(local.ravel())
    for m,(lo,hi) in enumerate(intervals):
        group,weight = [],[]
        for p,(left,right) in enumerate(intervals):
            a,b = max(left,lo),min(right,hi)
            if b-a <= 1e-8:
                continue
            band_id = p//segments
            row = kernel[band_id]
            contribution = integral_table(grid,row,b)-integral_table(grid,row,a)
            var = variance[band_id]
            if archive_overlap and m != p:
                var = var[0]
            weight.append(np.sum(contribution**2/var))
            group.append(local.ravel()[p])
        fused[m] = np.average(group,weights=weight)
    order = np.argsort(mid.ravel())
    return mid.ravel()[order],fused[order],local,np.asarray(condition)
