"""Fixed-seed Monte Carlo wave-function trajectory generation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.linalg

from .models import QuantumJumpModel, three_level_model, two_level_model


@dataclass(frozen=True)
class JumpTrajectory:
    duration: float
    jump_times: np.ndarray
    seed: int

    @property
    def activity(self) -> float:
        return float(self.jump_times.size / self.duration)


def simulate_quantum_jumps(
    model: QuantumJumpModel,
    *,
    duration: float,
    dt: float,
    seed: int,
    initial_state: np.ndarray | None = None,
) -> JumpTrajectory:
    if duration <= 0 or dt <= 0 or dt > duration:
        raise ValueError("duration and dt must define a positive time grid")
    dimension = model.hamiltonian.shape[0]
    if initial_state is None:
        state = np.zeros(dimension, dtype=np.complex128)
        state[0] = 1.0
    else:
        state = np.asarray(initial_state, dtype=np.complex128).copy()
        if state.shape != (dimension,):
            raise ValueError("initial_state has the wrong dimension")
        state /= np.linalg.norm(state)

    damping = sum(jump.conj().T @ jump for jump in model.jumps)
    effective_hamiltonian = model.hamiltonian - 0.5j * damping
    propagator = scipy.linalg.expm(-1j * effective_hamiltonian * dt)
    rng = np.random.default_rng(seed)
    jump_times: list[float] = []
    steps = int(np.ceil(duration / dt))
    for step in range(steps):
        current_dt = min(dt, duration - step * dt)
        if current_dt <= 0:
            break
        if current_dt == dt:
            no_jump_state = propagator @ state
        else:
            no_jump_state = (
                scipy.linalg.expm(-1j * effective_hamiltonian * current_dt) @ state
            )
        no_jump_probability = min(
            1.0, float(np.vdot(no_jump_state, no_jump_state).real)
        )
        if rng.random() >= no_jump_probability:
            weights = np.array(
                [
                    float(np.vdot(jump @ state, jump @ state).real)
                    for jump in model.jumps
                ]
            )
            if np.sum(weights) <= 0:
                state = no_jump_state / np.sqrt(no_jump_probability)
                continue
            jump_index = int(rng.choice(len(model.jumps), p=weights / np.sum(weights)))
            state = model.jumps[jump_index] @ state
            state /= np.linalg.norm(state)
            if jump_index == model.counted_jump:
                jump_times.append(min(duration, (step + 1) * dt))
        else:
            state = no_jump_state / np.sqrt(no_jump_probability)
    return JumpTrajectory(
        duration=float(duration),
        jump_times=np.asarray(jump_times, dtype=np.float64),
        seed=int(seed),
    )


def two_level_rescaled_trajectory(
    target_activity: float,
    *,
    omega: float,
    duration: float,
    dt: float,
    seed: int,
) -> JumpTrajectory:
    if target_activity <= 0:
        raise ValueError("target_activity must be positive")
    physical_activity = 2.0 * omega / 3.0
    scale = target_activity / physical_activity
    return simulate_quantum_jumps(
        two_level_model(omega=omega * scale, kappa=4.0 * omega * scale),
        duration=duration,
        dt=dt,
        seed=seed,
    )


def select_activity_window(
    jump_times: np.ndarray,
    *,
    total_duration: float,
    window_duration: float,
    target_activity: float,
    stride: float,
) -> JumpTrajectory:
    """Select the generated time window closest to a requested activity."""

    jump_times = np.asarray(jump_times, dtype=np.float64)
    starts = np.arange(0.0, total_duration - window_duration + 0.5 * stride, stride)
    best: tuple[float, float, np.ndarray] | None = None
    for start in starts:
        stop = start + window_duration
        mask = (jump_times >= start) & (jump_times < stop)
        local = jump_times[mask] - start
        activity = local.size / window_duration
        distance = abs(activity - target_activity)
        candidate = (distance, start, local)
        if best is None or (candidate[0], candidate[1]) < (best[0], best[1]):
            best = candidate
    if best is None:
        raise RuntimeError("no candidate trajectory window was generated")
    return JumpTrajectory(duration=window_duration, jump_times=best[2], seed=-1)


def three_level_blinking_windows(
    *,
    omega_1: float,
    omega_2: float,
    kappa_1: float,
    total_duration: float,
    window_duration: float,
    dt: float,
    seed: int,
    target_activities: tuple[float, ...],
) -> tuple[JumpTrajectory, tuple[JumpTrajectory, ...]]:
    long_trajectory = simulate_quantum_jumps(
        three_level_model(omega_1, omega_2, kappa_1),
        duration=total_duration,
        dt=dt,
        seed=seed,
    )
    windows = tuple(
        select_activity_window(
            long_trajectory.jump_times,
            total_duration=total_duration,
            window_duration=window_duration,
            target_activity=target,
            stride=max(dt, window_duration / 20.0),
        )
        for target in target_activities
    )
    return long_trajectory, windows
