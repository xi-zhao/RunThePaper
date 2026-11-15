"""Recompute the nine Table 2 loss comparisons on the released circuit groups."""

import argparse
import json
from math import cos, pi, sin
from pathlib import Path
import sys

import numpy as np
from numba import njit
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rank_device_factors import idle_cost, load_dataset, split

LOSSES = {
    "score_mse": (0, 0),
    "nll_k1": (1, 1),
    "nll_k2": (1, 2),
    "nll_k3": (1, 3),
    "pearson": (2, 0),
    "spearman": (3, 0),
    "rank_mse_d1": (4, 1),
    "rank_mse_d2": (4, 2),
    "rank_mse_d3": (4, 3),
}
TEMPERATURE = .02
MAX_LR = .08
STEPS = 180


@njit
def soft_ranks(values):
    order = np.argsort(-values)
    n = len(values)
    means = np.empty(n)
    starts = np.empty(n, np.int64)
    ends = np.empty(n, np.int64)
    blocks = 0
    for j in range(n):
        starts[blocks] = j
        ends[blocks] = j + 1
        means[blocks] = values[order[j]] - (n - j)
        blocks += 1
        while blocks > 1 and means[blocks - 2] < means[blocks - 1]:
            k = blocks - 2
            size0 = ends[k] - starts[k]
            size1 = ends[k + 1] - starts[k + 1]
            means[k] = (size0 * means[k] + size1 * means[k + 1]) / (size0 + size1)
            ends[k] = ends[k + 1]
            blocks -= 1
    rank = np.empty(n)
    for k in range(blocks):
        for j in range(starts[k], ends[k]):
            i = order[j]
            rank[i] = values[i] - means[k]
    return rank, order, starts, ends, blocks


@njit
def negative_correlation(x, y):
    a = x - x.mean()
    b = y - y.mean()
    norm2 = np.sum(a * a)
    norm = np.sqrt(norm2 * np.sum(b * b))
    if norm < 1e-13:
        # A tie-only circuit supplies no correlation direction.
        return 0., np.zeros(len(x))
    corr = np.sum(a * b) / norm
    return -corr, corr * a / norm2 - b / norm


@njit
def loss_gradient(cost, target, ranks, true_order, offsets, groups, loss_kind, power):
    gradient = np.zeros(len(cost))
    loss = 0.
    count = 0
    for circuit in groups:
        lo, hi = offsets[circuit], offsets[circuit + 1]
        c = cost[lo:hi]
        y = target[lo:hi]
        score = np.exp(-c)
        count += len(c) if loss_kind == 0 else 1
        if loss_kind == 0:
            delta = score - y
            loss += np.sum(delta**2)
            gradient[lo:hi] = -2 * delta * score
        elif loss_kind == 1:
            order = true_order[lo:hi]
            for k in range(min(power, len(c))):
                rest = order[k:]
                m = c[rest].min()
                p = np.exp(m - c[rest])
                normalizer = p.sum()
                loss += c[order[k]] - m + np.log(normalizer)
                gradient[lo + order[k]] += 1
                for i in range(len(rest)):
                    gradient[lo + rest[i]] -= p[i] / normalizer
        elif loss_kind == 2:
            part, ds = negative_correlation(score, y)
            loss += part
            gradient[lo:hi] = -score * ds
        else:
            values = -score / TEMPERATURE
            soft, order, starts, ends, n = soft_ranks(values)
            true_rank = ranks[lo:hi]
            if loss_kind == 3:
                part, dr = negative_correlation(soft, true_rank)
            else:
                error = soft - true_rank
                rank_weight = true_rank ** (-power)
                part = np.sum(rank_weight * error**2)
                dr = 2 * rank_weight * error
            loss += part
            for k in range(n):
                block = order[starts[k]:ends[k]]
                mean_derivative = np.mean(dr[block])
                for j in block:
                    gradient[lo + j] = -values[j] * (dr[j] - mean_derivative)
    return loss / count, gradient / count


def powers_and_jacobian(angles):
    u, v, eta = angles
    su, cu, sv, cv, se, ce = sin(u), cos(u), sin(v), cos(v), sin(eta), cos(eta)
    powers = np.array([cu * se, su * se, cv * ce, sv * ce])
    jacobian = np.array([
        [-su * se, 0., cu * ce],
        [cu * se, 0., su * ce],
        [0., -sv * ce, -cv * se],
        [0., cv * ce, -sv * se],
    ])
    return powers, jacobian


class RankingModel:
    def __init__(self, base, gates, gate_names, idle):
        self.gates = gates
        self.transpose = gates.T.tocsr()
        self.k = gates.shape[1]
        self.gate_class = np.array([int(x.startswith("('measure',")) for x in gate_names])
        assert 0 < self.gate_class.sum() < self.k
        self.base_idle = base["x"][:, 2:].astype(float)
        self.idle = idle
        self.target = base["y"].astype(float)
        self.offsets = base["offsets"]
        groups = [self.target[a:b] for a, b in zip(self.offsets, self.offsets[1:])]
        self.ranks = np.concatenate([rankdata(-y, method="average") for y in groups])
        self.order = np.concatenate([np.argsort(-y, kind="stable") for y in groups])

    def initial(self):
        return np.r_[np.ones(self.k), [pi / 4] * 3, [1/3, 1/6, 2/3]]

    def bounds(self):
        return np.zeros(self.k + 6), np.r_[np.full(self.k, 8.), [pi / 2] * 3, [.55, .40, .95]]

    def score_inputs(self, parameters):
        k = self.k
        p, dp = powers_and_jacobian(parameters[k:k+3])
        idle, deriv = idle_cost(*self.idle, self.base_idle, *parameters[-3:])
        cost = self.gates @ (parameters[:k] * p[self.gate_class])
        cost += idle[:, 0] * p[2] + idle[:, 1] * p[3]
        return cost, p, dp, idle, deriv

    def objective(self, parameters, groups, loss):
        cost, p, dp, idle, deriv = self.score_inputs(parameters)
        value, change = loss_gradient(cost, self.target, self.ranks, self.order,
                                      self.offsets, groups, *LOSSES[loss])
        gate_deriv = self.transpose @ change
        by_class = np.bincount(self.gate_class, weights=gate_deriv * parameters[:self.k], minlength=2)
        by_factor = np.r_[by_class, np.sum(idle * change[:, None], axis=0)]
        gradient = np.r_[p[self.gate_class] * gate_deriv, dp.T @ by_factor,
                         p[[2, 2, 3]] * np.sum(deriv * change[:, None], axis=0)]
        if not np.isfinite(value) or not np.isfinite(gradient).all():
            raise ValueError(f"non-finite objective or gradient in {loss}")
        return value, gradient


def cycle(step, steps):
    top = .3 * steps - 1
    if step <= top:
        phase = step / top
        w = (1 - cos(pi * phase)) / 2
        return (1-w) * MAX_LR / 25 + w * MAX_LR, .95 - .10 * w
    phase = (step - top) / (steps - 1 - top)
    w = (1 - cos(pi * phase)) / 2
    return (1-w) * MAX_LR + w * MAX_LR / 250000, .85 + .10 * w


def train(model, groups, loss, steps):
    parameters = model.initial()
    low, high = model.bounds()
    m = np.zeros_like(parameters)
    v = np.zeros_like(parameters)
    beta2 = .999
    cum_beta1 = 1.
    best = float("inf")
    best_parameters = parameters.copy()
    trace = []
    for i in range(steps):
        value, grad = model.objective(parameters, groups, loss)
        if value < best:
            best = value
            best_parameters = parameters.copy()
        if i == 0 or (i+1)%30 == 0 or i+1==steps:
            trace.append([i, float(value)])
        lr, beta1 = cycle(i, steps)
        cum_beta1 *= beta1
        m = beta1 * m + (1-beta1) * grad
        v = beta2 * v + (1-beta2) * grad**2
        parameters = np.clip(parameters-lr*(m/(1-cum_beta1)) /
                             (np.sqrt(v/(1-beta2**(i+1)))+1e-8), low, high)
    final, _ = model.objective(parameters, groups, loss)
    if final < best:
        best = final
        best_parameters = parameters
    return best_parameters, trace, float(best), float(final)


def selection_metrics(base, groups, selected, reference):
    stats = []
    for g, i, j in zip(groups, selected, reference, strict=True):
        a, b = base["offsets"][g:g+2]
        y = base["y"][a:b].astype(float)
        rank = 1 + int(np.count_nonzero(y > y[i]))
        stats.append((rank, (rank-1)/(b-a-1), 1-y[i]/max(y),
                      rank==1, (float(y[i]>y[j])+.5*float(y[i]==y[j]))))
    s = np.array(stats)
    return dict(median_rank=float(np.median(s[:, 0])), median_norm_rank=float(np.median(s[:, 1])),
                selection_error=float(s[:, 2].mean()), top1=float(s[:, 3].mean()),
                win_rate=float(s[:, 4].mean()), selected=[int(x) for x in selected])


def run(seed, steps, losses):
    base, gates, names, idle = load_dataset()
    model = RankingModel(base, gates, names, idle)
    tr, te = split(base, seed)
    limits = [base["offsets"][g:g+2] for g in te]
    mm = [np.argmax(base["mm"][a:b]) for a, b in limits]
    rng = np.random.default_rng(2026111100+seed)
    random = [rng.integers(b-a) for a,b in limits]
    result = {"seed": seed, "steps": steps, "train_groups": len(tr), "test_groups": te.tolist(),
              "metrics": {"mapomatic":selection_metrics(base,te,mm,mm),
                          "random":selection_metrics(base,te,random,mm)}}
    for loss in losses:
        p, trace, best, final = train(model, tr, loss, steps)
        cost, *_ = model.score_inputs(p)
        indices = [np.argmin(cost[a:b]) for a,b in limits]
        result["metrics"][loss] = {
            **selection_metrics(base, te, indices, mm), "parameters":p.tolist(),
            "training_trace":trace, "best_training_loss":best, "final_training_loss":final,
        }
        print(seed,loss,f"{best:.6g}",f"{result['metrics'][loss]['selection_error']:.6g}",flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True, choices=range(11))
    parser.add_argument("--steps", type=int, default=STEPS)
    parser.add_argument("--loss", choices=LOSSES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(run(args.seed,args.steps,[args.loss] if args.loss else LOSSES),
                                     indent=2,allow_nan=False)+"\n")
