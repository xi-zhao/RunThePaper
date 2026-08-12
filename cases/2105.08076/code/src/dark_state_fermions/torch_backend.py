"""Batched Torch backend for A100 paper-scale trajectory campaigns.

The scientific update is identical to :mod:`gaussian`; Torch only changes the
array backend and batches independent trajectories.  It is optional for the
small feature run and selected automatically on a CUDA host.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from .gaussian import EnsembleResult, _sem, default_ell_values, hopping_dispersion
from .observables import density_correlations, entropy_profile


def torch_cuda_available() -> bool:
    try:
        import torch
    except ImportError:
        return False
    return bool(torch.cuda.is_available())


def simulate_ensemble_torch(
    *,
    length: int,
    exponent: float,
    gamma: float,
    dt: float,
    burn_time: float,
    sample_time: float,
    sample_interval: float,
    trajectories: int,
    seed_base: int,
    ell_values: Iterable[int] | None = None,
    entropy_origins: int = 1,
    device: str = "auto",
    batch_size: int = 4,
) -> EnsembleResult:
    """Run the same QSD integrator in independent Torch batches.

    A condition-level seed initializes a counter-based Torch stream for every
    batch.  Conditions receive nonoverlapping seed ranges from the paper-scale
    scheduler.  Complex128 is retained on the A100 to keep QR residuals auditable.
    """

    try:
        import torch
    except ImportError as exc:  # pragma: no cover - local environment has Torch.
        raise RuntimeError(
            "Torch backend requested but torch is not installed"
        ) from exc

    if trajectories < 1 or batch_size < 1:
        raise ValueError("trajectories and batch_size must be positive")
    selected_device = (
        "cuda" if device == "auto" and torch.cuda.is_available() else device
    )
    if selected_device == "auto":
        selected_device = "cpu"
    if selected_device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA backend requested but torch.cuda.is_available() is false"
        )

    ell = np.asarray(
        list(ell_values) if ell_values is not None else default_ell_values(length),
        dtype=np.int64,
    )
    if ell.size == 0 or np.any(ell < 1) or np.any(ell > length // 2):
        raise ValueError("ell_values must lie between 1 and L/2")
    burn_steps = int(np.ceil(burn_time / dt))
    interval_steps = max(1, int(np.ceil(sample_interval / dt)))
    sample_count = max(1, int(np.floor(sample_time / (interval_steps * dt))) + 1)

    torch_device = torch.device(selected_device)
    real_dtype = torch.float64
    complex_dtype = torch.complex128
    dispersion = torch.as_tensor(
        hopping_dispersion(length, exponent), dtype=real_dtype, device=torch_device
    )
    half_phase = torch.exp(-0.5j * dt * dispersion).to(complex_dtype)
    column_indices = torch.arange(length // 2, device=torch_device)

    trajectory_entropy: list[np.ndarray] = []
    trajectory_positive: list[np.ndarray] = []
    trajectory_connected: list[np.ndarray] = []
    drift_values: list[float] = []
    invariant_max = 0.0

    def unitary_half(q: "torch.Tensor") -> "torch.Tensor":
        momentum = torch.fft.fft(q, dim=1)
        return torch.fft.ifft(momentum * half_phase[None, :, None], dim=1)

    def advance(
        q: "torch.Tensor", steps: int, generator: "torch.Generator"
    ) -> "torch.Tensor":
        for _ in range(steps):
            q = unitary_half(q)
            if gamma:
                occupation = torch.sum(torch.abs(q) ** 2, dim=2).real
                innovation = torch.randn(
                    (q.shape[0], length),
                    dtype=real_dtype,
                    device=torch_device,
                    generator=generator,
                ) * np.sqrt(gamma * dt)
                log_weight = innovation - gamma * (1.0 - occupation) * dt
                log_weight -= torch.max(log_weight, dim=1, keepdim=True).values
                q, _ = torch.linalg.qr(
                    torch.exp(log_weight)[:, :, None] * q, mode="reduced"
                )
            q = unitary_half(q)
        return q

    for batch_start in range(0, trajectories, batch_size):
        current_batch = min(batch_size, trajectories - batch_start)
        q = torch.zeros(
            (current_batch, length, length // 2),
            dtype=complex_dtype,
            device=torch_device,
        )
        for local_index in range(current_batch):
            offset = (batch_start + local_index) % 2
            row_indices = torch.arange(offset, length, 2, device=torch_device)
            q[local_index, row_indices, column_indices] = 1.0
        generator = torch.Generator(device=torch_device)
        generator.manual_seed(seed_base + batch_start)
        q = advance(q, burn_steps, generator)

        entropy_samples = [[] for _ in range(current_batch)]
        positive_samples = [[] for _ in range(current_batch)]
        connected_samples = [[] for _ in range(current_batch)]
        for sample_index in range(sample_count):
            if sample_index:
                q = advance(q, interval_steps, generator)
            projectors = q @ q.conj().transpose(-2, -1)
            for local_index in range(current_batch):
                projector = projectors[local_index].detach().cpu().numpy()
                origins = np.linspace(
                    0,
                    length - 1,
                    num=min(entropy_origins, length),
                    endpoint=False,
                    dtype=int,
                )
                entropy_samples[local_index].append(
                    entropy_profile(projector, ell, origins=origins)
                )
                positive, connected = density_correlations(projector, ell)
                positive_samples[local_index].append(positive)
                connected_samples[local_index].append(connected)

        gram = q.conj().transpose(-2, -1) @ q
        identity = torch.eye(length // 2, dtype=complex_dtype, device=torch_device)
        residuals = torch.linalg.matrix_norm(gram - identity[None, :, :], dim=(-2, -1))
        invariant_max = max(invariant_max, float(torch.max(residuals).detach().cpu()))

        for local_index in range(current_batch):
            entropy_array = np.asarray(entropy_samples[local_index], dtype=float)
            positive_array = np.asarray(positive_samples[local_index], dtype=float)
            connected_array = np.asarray(connected_samples[local_index], dtype=float)
            trajectory_entropy.append(np.mean(entropy_array, axis=0))
            trajectory_positive.append(np.mean(positive_array, axis=0))
            trajectory_connected.append(np.mean(connected_array, axis=0))
            if entropy_array.shape[0] > 1:
                start = float(np.mean(entropy_array[0]))
                end = float(np.mean(entropy_array[-1]))
                drift_values.append(abs(end - start) / max(abs(start), 1e-12))

    entropy_stack = np.asarray(trajectory_entropy, dtype=float)
    positive_stack = np.asarray(trajectory_positive, dtype=float)
    connected_stack = np.asarray(trajectory_connected, dtype=float)
    return EnsembleResult(
        length=length,
        exponent=exponent,
        gamma=gamma,
        ell=ell.astype(float),
        entropy_mean=np.mean(entropy_stack, axis=0),
        entropy_sem=_sem(entropy_stack),
        correlation_positive_mean=np.mean(positive_stack, axis=0),
        correlation_positive_sem=_sem(positive_stack),
        correlation_connected_mean=np.mean(connected_stack, axis=0),
        trajectories=trajectories,
        samples_per_trajectory=sample_count,
        max_invariant_residual=float(invariant_max),
        stationary_relative_drift=float(max(drift_values, default=0.0)),
    )
