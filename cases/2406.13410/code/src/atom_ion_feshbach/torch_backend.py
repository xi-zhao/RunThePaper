"""Optional float64 CUDA backend for the paper-scale collision ensemble."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .md import simulate_collision_ensemble
from .trap import BA138_MASS_KG, BOLTZMANN_J_K, LI6_MASS_KG


@dataclass(frozen=True)
class BackendSamples:
    velocities_m_s: np.ndarray
    stationary_relative_drift: float
    backend: str


def cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def resolve_backend(requested: str) -> str:
    if requested not in {"auto", "numpy", "cuda"}:
        raise ValueError("backend must be auto, numpy, or cuda")
    if requested == "auto":
        return "cuda" if cuda_available() else "numpy"
    if requested == "cuda" and not cuda_available():
        raise RuntimeError("CUDA backend requested but torch.cuda is unavailable")
    return requested


def simulate_collision_shard(
    *,
    field_v_m: float,
    trajectories: int,
    collisions: int,
    seed: int,
    bath_temperature_k: float,
    background_temperature_k: float,
    drive_alpha_k_per_v_m2: float,
    backend: str,
) -> BackendSamples:
    resolved = resolve_backend(backend)
    if resolved == "numpy":
        result = simulate_collision_ensemble(
            field_v_m=field_v_m,
            trajectories=trajectories,
            collisions=collisions,
            seed=seed,
            bath_temperature_k=bath_temperature_k,
            background_temperature_k=background_temperature_k,
            drive_alpha_k_per_v_m2=drive_alpha_k_per_v_m2,
        )
        return BackendSamples(
            result.velocities_m_s, result.stationary_relative_drift, "numpy"
        )

    import torch

    device = torch.device("cuda")
    dtype = torch.float64
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    atom_sigma = np.sqrt(BOLTZMANN_J_K * bath_temperature_k / LI6_MASS_KG)
    ion_sigma = np.sqrt(BOLTZMANN_J_K * bath_temperature_k / BA138_MASS_KG)
    background_sigma = np.sqrt(BOLTZMANN_J_K * background_temperature_k / BA138_MASS_KG)
    drive_per_field = np.sqrt(
        6.0 * BOLTZMANN_J_K * drive_alpha_k_per_v_m2 / BA138_MASS_KG
    )
    secular = torch.randn(
        (trajectories, 3), device=device, dtype=dtype, generator=generator
    ) * float(ion_sigma)
    checkpoint_temperature = None
    checkpoint_step = max(1, int(0.8 * collisions))

    def median_temperature(velocity: "torch.Tensor") -> float:
        values = BA138_MASS_KG * torch.sum(velocity**2, dim=1) / (3.0 * BOLTZMANN_J_K)
        return float(torch.median(values).item())

    with torch.no_grad():
        for step in range(collisions):
            phase = torch.rand(
                trajectories, device=device, dtype=dtype, generator=generator
            ) * (2.0 * np.pi)
            micromotion = float(drive_per_field * field_v_m) * torch.sin(phase)
            instantaneous = secular.clone()
            instantaneous[:, 0] += micromotion
            atom = torch.randn(
                (trajectories, 3), device=device, dtype=dtype, generator=generator
            ) * float(atom_sigma)
            center = (BA138_MASS_KG * instantaneous + LI6_MASS_KG * atom) / (
                BA138_MASS_KG + LI6_MASS_KG
            )
            relative_speed = torch.linalg.vector_norm(instantaneous - atom, dim=1)
            direction = torch.randn(
                (trajectories, 3), device=device, dtype=dtype, generator=generator
            )
            direction /= torch.linalg.vector_norm(direction, dim=1)[:, None]
            secular = center + LI6_MASS_KG / (BA138_MASS_KG + LI6_MASS_KG) * (
                relative_speed[:, None] * direction
            )
            secular[:, 0] -= micromotion
            if step + 1 == checkpoint_step:
                checkpoint_temperature = median_temperature(secular)

        phase = torch.rand(
            trajectories, device=device, dtype=dtype, generator=generator
        ) * (2.0 * np.pi)
        observed = secular + torch.randn(
            (trajectories, 3), device=device, dtype=dtype, generator=generator
        ) * float(background_sigma)
        observed[:, 0] += float(drive_per_field * field_v_m) * torch.sin(phase)
        final_temperature = median_temperature(secular)
        drift = abs(final_temperature - float(checkpoint_temperature)) / max(
            final_temperature, 1e-30
        )
        velocities = observed.cpu().numpy()
    return BackendSamples(velocities, float(drift), "torch_cuda_float64")
