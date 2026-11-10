"""Independent array implementation of the QC25 numerical protocols.

The paper and archive interpretations and their derivation are documented in
checks/numerical-reconstruction.md. Only the frozen protocol JSON is read.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.special import erf, ndtr, ndtri


def born(phase):
    return (1.0 + np.cos(phase)) / 2.0


def field(map_name, dimension):
    if map_name == "line":
        sites = np.column_stack((np.zeros(dimension), np.arange(dimension)))
        return sites, np.where(sites[:, 1] < 10, 0.25, 0.75) * np.pi
    side = int(np.sqrt(dimension))
    sites = np.indices((side, side)).reshape(2, -1).T.astype(float)
    if map_name == "gaussian":
        distance_squared = np.sum((sites - 2.0) ** 2, axis=1)
        height = 2.5 * np.pi / np.sqrt(2.0 * np.pi * 0.8)
        return sites, np.minimum(np.pi, height * np.exp(-0.4 * distance_squared))
    midpoint = side // 2
    same_quadrant = (sites[:, 0] < midpoint) == (sites[:, 1] < midpoint)
    on_odd_cross = (side % 2 == 1) & np.any(sites == midpoint, axis=1)
    return sites, np.where(same_quadrant | on_odd_cross, 0.75, 0.25) * np.pi


def history_probability(physical, physical_ones, messages, message_ones, lambda1, fallback):
    """Eqs. (50)-(51) with sums divided by their actual sample counts."""
    physical_mean = physical_ones / np.maximum(physical, 1)
    message_mean = message_ones / np.maximum(messages, 1)
    share = 0.5 * lambda1 ** physical
    blended = (1.0 - share) * physical_mean + share * message_mean
    observed = np.where(
        physical > 0,
        np.where(messages > 0, blended, physical_mean),
        message_mean,
    )
    return np.where((physical + messages) > 0, observed, fallback)


def radii_from_uniform(uniform, mean, variance, lower, upper):
    """Inverse CDF of a truncated Gaussian, with the zero-width point limit."""
    width = np.sqrt(variance)
    safe_width = np.where(width > 0.0, width, 1.0)
    cdf_low = ndtr((lower - mean) / safe_width)
    cdf_high = ndtr((upper - mean) / safe_width)
    quantile = cdf_low + uniform * (cdf_high - cdf_low)
    epsilon = np.finfo(float).eps
    sample = mean + safe_width * ndtri(np.clip(quantile, epsilon, 1.0 - epsilon))
    return np.where(width > 0.0, np.clip(sample, lower, upper), mean)


def categorical_rows(weights, uniform):
    """Select independent categorical outcomes for every row."""
    cumulative = np.cumsum(weights, axis=1)
    if np.any(cumulative[:, -1] <= 0.0):
        raise ArithmeticError("categorical distribution has zero total mass")
    total = cumulative[:, -1, None]
    target = np.minimum(uniform * total, np.nextafter(total, 0.0))
    return np.sum(cumulative[:, :, None] <= target[:, None, :], axis=1)


def collapse_children(parent, radii, count_alpha, archive):
    """Return survivor counts, conditional radii means and average Fano factor."""
    rows = np.arange(len(parent))[:, None]
    groups = count_alpha * rows + parent
    length = len(parent) * count_alpha
    group_ids = groups.ravel()
    counts = np.bincount(group_ids, minlength=length).reshape(-1, count_alpha)
    total = np.bincount(group_ids, weights=radii.ravel(), minlength=length)
    mean = total.reshape(counts.shape) / np.maximum(counts, 1)
    deviation = radii - mean[rows, parent]
    dispersion = np.bincount(group_ids, weights=deviation.ravel() ** 2, minlength=length)
    variance = dispersion.reshape(counts.shape) / np.maximum(counts, 1)
    # Exact repeated values have zero spread, including when a rounded mean
    # differs in its last bit from each identical value.
    smallest = np.full(counts.shape, np.inf)
    largest = np.full(counts.shape, -np.inf)
    np.minimum.at(smallest, (rows, parent), radii)
    np.maximum.at(largest, (rows, parent), radii)
    variance = np.where(smallest == largest, 0.0, variance)
    fano_by_parent = variance / np.where(counts > 0, mean, 1.0)
    # The archived subtree enumeration includes an initial empty entry.
    denominator = np.count_nonzero(counts, axis=1) + int(archive)
    return counts, mean, fano_by_parent.sum(axis=1) / denominator


def last_slots(ancestor, included):
    rows = np.arange(len(ancestor))[:, None]
    slots = np.arange(ancestor.shape[1])
    latest = np.full_like(ancestor, -1)
    np.maximum.at(latest, (rows, ancestor), np.where(included, slots, -1))
    return latest


def leaf_weights(distance_squared, radii, phases, center, decay, variance_f,
                 archived, phase_index_repair, x_positions=None):
    """Joint proposal scores for the length layer before the first draw."""
    distances = distance_squared[:, :, None, :]
    radius_squared = radii[..., None] ** 2
    within = distances <= radius_squared if archived else distances < radius_squared
    neighbours = (distances > 0.0) & within
    neighbour_phase = phases[:, :, None, :]
    influence = decay[:, None, None, :]
    smoothed = center[:, :, None, None] * np.exp(-distances / (2.0 * radius_squared))
    predicted = (1.0 - influence) * neighbour_phase + influence * smoothed
    reference = neighbour_phase
    if archived and not phase_index_repair:
        # The stored vector begins with x coordinates. The archived scorer
        # uses the ordinal within the candidate neighbourhood.
        ranks = np.maximum(np.cumsum(neighbours, axis=-1) - 1, 0)
        reference = np.take_along_axis(x_positions[:, :, None, :], ranks, axis=-1)
    exponent = -0.5 * (predicted - reference) ** 2 / variance_f
    truncation_mass = erf(np.pi / np.sqrt(2.0 * variance_f))
    if not archived:
        log_weights = np.where(neighbours, exponent - np.log(truncation_mass), 0.0)
        log_weights = np.sum(log_weights, axis=-1)
        peak = log_weights.max(axis=(1, 2), keepdims=True)
        return np.exp(log_weights - peak), 0, 0

    factor = 1.0 / (truncation_mass * np.sqrt(2.0 * np.pi * variance_f))
    raw = np.prod(np.where(neighbours, factor * np.exp(exponent), 1.0), axis=-1)
    capped = int(np.count_nonzero(raw > 100_000))
    clipped = np.minimum(raw, 100_000)
    mass = clipped.sum(axis=2, keepdims=True)
    normalised = clipped / np.where(mass > 0.0, mass, 1.0)
    return normalised, int(np.count_nonzero(mass == 0.0)), capped


def simulate(panel, expansion, count_alpha, count_beta, repeats, steps, random_key,
             protocol, fixed_schedule=False):
    """Simulate independent trajectories in parallel and retain repeat-level loss."""
    archived = protocol.startswith("archive")
    parameter_set = "archive" if archived else "paper"
    variance_v, variance_f, lambda1, lambda2 = panel[parameter_set][expansion]
    sharing_disabled = not archived and lambda1 == lambda2 == 0.0
    coordinates, truth = field(panel["map"], panel["dimension"])
    dimension = len(truth)
    geometry = coordinates[:, None] - coordinates[None, :]
    rmax = 4.0 * np.sqrt(np.sum(geometry ** 2, axis=-1).max())
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(random_key)))
    row = np.arange(repeats)
    rows = row[:, None]
    parents = np.arange(count_alpha)
    phase = rng.uniform(0, np.pi, (repeats, count_alpha, dimension))
    radius = rng.uniform(1, rmax, phase.shape)
    grid_prior = rng.uniform(0, np.pi, (repeats, dimension))
    initial_h = (rng.random(phase.shape) < born(phase)).astype(float)
    jitter = rng.normal(0.0, 1e-8, (*phase.shape, 2))
    grid_positions = coordinates + (jitter if archived else np.zeros_like(jitter))
    ancestor = np.broadcast_to(parents, (repeats, count_alpha)).copy()
    fano = np.full((repeats, dimension), rmax)
    eligible = np.ones((repeats, dimension), dtype=bool)
    physical = np.zeros((repeats, dimension), dtype=int)
    physical_ones = np.zeros_like(physical)
    messages = np.zeros_like(physical)
    message_ones = np.zeros_like(physical)
    mse = np.empty((repeats, steps))
    measured_sites = np.empty((repeats, steps), dtype=np.uint8)
    outcomes = np.empty_like(measured_sites)
    totals = dict(joint_uniform_reset=0, zero_beta_rows=0, clipped_leaves=0,
                  negative_alpha_score=0, zero_alpha_score=0, zero_fano=0,
                  message_events=0, restricted_scheduling_steps=0,
                  aliased_parent_slots=0)
    if archived:
        a = 1.0 / np.sqrt(2.0 * variance_v)
        rho = erf(a) + np.expm1(-a * a) / (a * np.sqrt(np.pi))

    for time in range(steps):
        available_scores = np.where(eligible, fano, -np.inf)
        tied = available_scores == available_scores.max(axis=1, keepdims=True)
        rank = (rng.random(repeats) * tied.sum(axis=1)).astype(int)
        chosen = np.argmax(np.cumsum(tied, axis=1) > rank[:, None], axis=1)
        if fixed_schedule:
            chosen = np.full(repeats, time % dimension)
        y = rng.random(repeats) < born(truth[chosen])
        measured_sites[:, time], outcomes[:, time] = chosen, y

        if archived:
            before = history_probability(physical, physical_ones, messages, message_ones,
                                         lambda1, born(grid_prior))
            g1 = rho / 2.0 + rho * (2.0 * before[row, chosen] - 1.0) * (2 * y - 1)
            totals["negative_alpha_score"] += int(np.count_nonzero(g1 < 0.0))
            totals["zero_alpha_score"] += int(np.count_nonzero(g1 == 0.0))
        physical[row, chosen] += 1
        physical_ones[row, chosen] += y
        if archived:
            probability = history_probability(physical, physical_ones, messages, message_ones,
                                              lambda1, born(grid_prior))
            global_phase = np.arccos(2.0 * probability - 1.0)
            local_phases = np.broadcast_to(global_phase[:, None, :], phase.shape)
            local_radius = radius[rows, ancestor].mean(axis=1)[row, chosen, None, None]
        else:
            probability = history_probability(physical[:, None], physical_ones[:, None],
                                              messages[:, None], message_ones[:, None],
                                              lambda1, initial_h)
            local_phases = np.arccos(2.0 * probability - 1.0)
            local_radius = radius[rows, parents, chosen[:, None]][..., None]
        center_phase = local_phases[rows, parents, chosen[:, None]]
        phase[rows, parents, chosen[:, None]] = center_phase
        uniform = rng.random((repeats, count_alpha, count_beta))
        if expansion == "uniform":
            proposals = 1.0 + (rmax - 1.0) * uniform
        else:
            proposal_variance = fano[row, chosen, None, None] * local_radius
            if archived:
                proposal_variance = np.where(proposal_variance == 0.0,
                                             variance_f * 1e-12, proposal_variance)
            proposals = radii_from_uniform(uniform, local_radius, proposal_variance, 1.0, rmax)

        positions = grid_positions[rows, ancestor]
        displacement = positions - positions[rows, parents, chosen[:, None]][..., None, :]
        distance_squared = np.sum(displacement ** 2, axis=-1)
        decay = lambda2 ** physical
        if sharing_disabled:
            weights = np.ones_like(proposals)
        else:
            weights, zero_rows, clipped = leaf_weights(
                distance_squared, proposals, local_phases, center_phase, decay, variance_f,
                archived, protocol == "archive-phase", positions[..., 0],
            )
            totals["zero_beta_rows"] += zero_rows
            totals["clipped_leaves"] += clipped

        if archived:
            # Before the binary observation the archive uses a single grid
            # probability. All nonzero scores normalize to equal parent weights.
            weights = np.where(g1[:, None, None] != 0.0, weights, 0.0)
            reset = weights.sum(axis=(1, 2)) == 0.0
            totals["joint_uniform_reset"] += int(reset.sum())
            weights[reset] = 1.0
        else:
            g1 = np.where(y[:, None], probability[rows, parents, chosen[:, None]],
                          1.0 - probability[rows, parents, chosen[:, None]])
            # At the measured site the included observation gives a positive,
            # common factor. Cancelling it avoids multiplying tiny weights.
            if np.any(g1 <= 0.0) or not np.all(g1 == g1[:, :1]):
                raise ArithmeticError("post-measurement parent scores differ or vanish")

        leaves = categorical_rows(weights.reshape(repeats, -1),
                                  rng.random((repeats, count_alpha)))
        parent, child = np.divmod(leaves, count_beta)
        selected_radius = proposals[rows, parent, child]
        if archived:
            latest = last_slots(ancestor, True)
            selected_id = ancestor[rows, parent]
            selected_radius = proposals[rows, latest[rows, selected_id], child]
            totals["aliased_parent_slots"] += int(np.count_nonzero(
                latest[rows, ancestor] != parents))
        counts, mean, new_fano = collapse_children(parent, selected_radius, count_alpha, archived)
        fano[row, chosen] = new_fano
        totals["zero_fano"] += int(np.count_nonzero(new_fano == 0.0))
        final_parent = categorical_rows(counts, rng.random((repeats, count_alpha)))
        if archived:
            latest = last_slots(ancestor, counts > 0)
            updated = latest >= 0
            updated_row, updated_id = np.nonzero(updated)
            radius[updated_row, updated_id, chosen[updated_row]] = mean[updated_row, latest[updated]]
            ancestor = ancestor[rows, final_parent]
        else:
            radius[rows, parents, chosen[:, None]] = np.where(
                counts > 0, mean, radius[rows, parents, chosen[:, None]])
            phase = phase[rows, final_parent]
            radius = radius[rows, final_parent]
            initial_h = initial_h[rows, final_parent]

        estimate = phase[rows, ancestor].mean(axis=1)
        mse[:, time] = np.mean((estimate - truth) ** 2, axis=1)
        rbar = radius[rows, ancestor].mean(axis=1)[row, chosen, None]
        averaged_positions = grid_positions[rows, ancestor].mean(axis=1)
        squared = np.sum((averaged_positions - averaged_positions[row, chosen, None, :]) ** 2, axis=2)
        within = squared <= rbar ** 2 if archived else squared < rbar ** 2
        neighbours = (squared > 0.0) & within
        message_base = global_phase if archived else estimate
        message_phase = (1.0 - decay) * message_base + decay * (
            estimate[row, chosen, None] * np.exp(-squared / (2.0 * rbar ** 2)))
        message_y = rng.random((repeats, dimension)) < born(message_phase)
        if not sharing_disabled:
            messages += neighbours
            message_ones += neighbours & message_y
            totals["message_events"] += int(neighbours.sum())
        if archived and time <= dimension:
            eligible = neighbours | (~neighbours.any(axis=1, keepdims=True))
            totals["restricted_scheduling_steps"] += int(np.count_nonzero(~eligible.all(axis=1)))
        else:
            eligible.fill(True)

    if not np.isfinite(mse).all() or np.any(mse < 0.0):
        raise ArithmeticError("invalid mean squared loss")
    return mse, measured_sites, outcomes, estimate, truth, totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True)
    parser.add_argument("--protocol", choices=("paper", "archive", "archive-phase"), required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--fixed-schedule", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path("config/qc25-conditions.json").read_text())
    panel = config["panels"][args.panel]
    repeats = config["repeats"] if args.repeats is None else args.repeats
    steps = config["steps"]
    if repeats < 1:
        raise ValueError("repeats must be positive")
    if args.fixed_schedule and (args.protocol != "paper" or args.panel[:2] != "F5"):
        raise ValueError("the paired fixed-schedule control is defined for strict zero sharing")
    mse, sites, observations, estimates, keys, details = [], [], [], [], [], []
    for expansion_index, expansion in enumerate(("uniform", "trunc")):
        for config_index, (count_alpha, count_beta) in enumerate(config["particles"]):
            key = [config["seed"], panel["index"], 0 if args.fixed_schedule else expansion_index,
                   config_index]
            loss, nodes, y, estimate, truth, diagnostic = simulate(
                panel, expansion, count_alpha, count_beta, repeats, steps, key,
                args.protocol, fixed_schedule=args.fixed_schedule,
            )
            mse.append(loss)
            sites.append(nodes)
            observations.append(y)
            estimates.append(estimate)
            keys.append(key)
            details.append(diagnostic)
    shape = (2, len(config["particles"]))
    metadata = {"panel": args.panel, "protocol": args.protocol, "steps": steps,
                "repeats": repeats, "fixed_schedule": args.fixed_schedule,
                "expansions": ["uniform", "trunc"], "particles": config["particles"],
                "random_keys": keys, "rng": "numpy.PCG64 via SeedSequence",
                "diagnostics_expansion_then_particle_config": details}
    np.savez_compressed(
        args.output, mse=np.asarray(mse).reshape(*shape, repeats, steps),
        sites=np.asarray(sites).reshape(*shape, repeats, steps),
        observations=np.asarray(observations).reshape(*shape, repeats, steps),
        estimates_last=np.asarray(estimates).reshape(*shape, repeats, len(truth)),
        truth=truth, metadata=json.dumps(metadata, sort_keys=True),
    )
    print(f"{args.panel} {args.protocol}: {2 * len(config['particles']) * repeats} "
          f"trajectories, {steps} observations each")


if __name__ == "__main__":
    main()
