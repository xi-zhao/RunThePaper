"""Two-layer particle filter derived from QC28's published equations."""

import math

import numpy as np
from numba import njit


@njit
def phase_from_records(physical_n, physical_sum, message_n, message_sum, decay):
    """Eqs. (19), (21), and (23) on a site with at least one observation."""
    if physical_n == 0:
        p = message_sum / message_n
    elif message_n == 0:
        p = physical_sum / physical_n
    else:
        weight = decay**physical_n / 2
        p = (1 - weight) * physical_sum / physical_n + weight * message_sum / message_n
    return math.acos(min(1.0, max(-1.0, 2 * p - 1)))


@njit
def born(phase):
    return (1 + math.cos(phase)) / 2


@njit
def beta_log_weight(distance2, field, phases, sharing_weight, length, variance):
    """Eqs. (5)–(13) with k0=1 and zero model-error mean."""
    log_density_at_zero = -0.5 * math.log(2 * math.pi * variance)
    log_density_at_zero -= math.log(math.erf(math.pi / math.sqrt(2 * variance)))
    radius2 = length * length
    value = 0.0
    for q in range(len(phases)):
        separation2 = distance2[q]
        if 0 < separation2 <= radius2:
            smeared = field * math.exp(-separation2 / radius2)
            error = sharing_weight[q] * (phases[q] - smeared)
            value += log_density_at_zero - error**2 / (2 * variance)
    return value


@njit
def observed_shots(site, shots, bank, used, physical_n, truth):
    if bank.shape[1] == 0:
        return np.random.binomial(shots, born(truth[site]))
    total = 0
    for k in range(shots):
        count = physical_n[site] + k
        index = np.random.randint(bank.shape[1])
        while np.any(used[site, :count] == index):
            index = np.random.randint(bank.shape[1])
        used[site, count] = index
        total += bank[site, index]
    return total


@njit
def alpha_log_weight(phi, successes, failures):
    """The common rho_0 factor of Eq. (2) cancels in normalization."""
    p = born(phi)
    if (successes and p == 0) or (failures and p == 1):
        return -math.inf
    out = 0.0
    if successes:
        out += successes * math.log(p)
    if failures:
        out += failures * math.log1p(-p)
    return out


@njit
def simulate(distance2, truth, bank, iterations, shots, lambdas, seed, n_alpha=15, n_beta=10):
    """Generate new measurements (or draw recorded bits) and a posterior map."""
    np.random.seed(seed)
    size = len(truth)
    l1, l2 = lambdas
    no_sharing = l1 == 0 and l2 == 0
    flat_distance = distance2.ravel()
    r_min = math.sqrt(np.min(flat_distance[flat_distance > 0]))
    r_max = 4 * math.sqrt(np.max(distance2))
    f = np.random.uniform(0, math.pi, (n_alpha, size))
    r = np.random.uniform(r_min, r_max, (n_alpha, size))
    uncertainty = np.full(size, r_max)
    measured_n, measured_sum = np.zeros(size, np.int64), np.zeros(size, np.int64)
    message_n, message_sum = np.zeros(size, np.int64), np.zeros(size, np.int64)
    used = np.empty((size, iterations * shots if bank.shape[1] else 0), np.int64)
    route = np.empty(iterations, np.int64)
    alpha_log = np.empty(n_alpha)
    n_pairs = n_alpha * n_beta
    weights = np.empty(n_pairs)
    leaf_lengths = np.empty(n_pairs)
    leaf_counts = np.empty(n_alpha, np.int64)
    length_sum, length_square = np.empty(n_alpha), np.empty(n_alpha)
    parents = np.empty(n_alpha, np.int64)
    null_alpha = 0
    if bank.shape[1] and bank.shape[1] < iterations * shots:
        raise ValueError("a site's recorded readout pool must cover the maximum shot budget")

    for t in range(iterations):
        if no_sharing:
            site = np.random.randint(size)
        else:
            candidates = np.where(uncertainty == uncertainty.max())[0]
            site = candidates[np.random.randint(len(candidates))]
        route[t] = site
        successes = observed_shots(site, shots, bank, used, measured_n, truth)
        for a in range(n_alpha):
            alpha_log[a] = alpha_log_weight(f[a, site], successes, shots - successes)
        if np.all(np.isneginf(alpha_log)):
            # Eq. (2) can give zero total likelihood after an extreme empirical
            # probability. Preserve the physical update and a neutral alpha layer.
            alpha_log.fill(0)
            null_alpha += 1

        measured_n[site] += shots
        measured_sum[site] += successes
        local = phase_from_records(measured_n[site], measured_sum[site],
                                   message_n[site], message_sum[site], l1)
        f[:, site] = local
        sharing_weight = l2**measured_n

        for k in range(n_pairs):
            a = k // n_beta
            length = np.random.uniform(r_min, r_max)
            leaf_lengths[k] = length
            weights[k] = alpha_log[a]
            if not no_sharing:
                weights[k] += beta_log_weight(distance2[site], local, f[a], sharing_weight,
                                              length, 1e-6)
        cdf = np.cumsum(np.exp(weights - weights.max()))
        leaf_counts.fill(0)
        length_sum.fill(0)
        length_square.fill(0)
        for _ in range(n_alpha):
            k = np.searchsorted(cdf, np.random.random() * cdf[-1], side="right")
            a = k // n_beta
            length = leaf_lengths[k]
            leaf_counts[a] += 1
            length_sum[a] += length
            length_square[a] += length**2

        fano, surviving = 0.0, 0
        for a in range(n_alpha):
            if leaf_counts[a]:
                mean = length_sum[a] / leaf_counts[a]
                var = max(0, length_square[a] / leaf_counts[a] - mean**2)
                r[a, site] = mean
                fano += var / mean
                surviving += 1
        uncertainty[site] = fano / surviving
        ancestor_cdf = np.cumsum(leaf_counts)
        for a in range(n_alpha):
            parents[a] = np.searchsorted(ancestor_cdf, np.random.randint(n_alpha), side="right")
        f, r = f[parents], r[parents]

        if not no_sharing:
            radius2 = r[:, site].mean()**2
            for q in range(size):
                d2 = distance2[site, q]
                if 0 < d2 <= radius2:
                    fraction = sharing_weight[q]
                    smeared = local * math.exp(-d2 / radius2)
                    outgoing = (1 - fraction) * f[:, q].mean() + fraction * smeared
                    message_n[q] += 1
                    message_sum[q] += np.random.random() < born(outgoing)
                    f[:, q] = phase_from_records(measured_n[q], measured_sum[q],
                                                 message_n[q], message_sum[q], l1)

    return f.sum(axis=0) / n_alpha, route, null_alpha
