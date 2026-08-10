"""Independent scalable implementation of the paper's variational CV circuit.

The original feature run used a dense two-mode matrix representation.  This
module preserves the printed circuit while exploiting photon-number sectors for
the beam splitter and tensor structure for local gates.  It contains no access
to paper images, author code, author arrays, or digitized values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class VariationalCondition:
    """One independently restartable cutoff/seed training condition."""

    cutoff: int
    seed: int

    @property
    def condition_id(self) -> str:
        return f"cutoff-{self.cutoff:02d}_seed-{self.seed:05d}"

    def record(self) -> dict[str, int | str]:
        return {
            "condition_id": self.condition_id,
            "cutoff": self.cutoff,
            "seed": self.seed,
        }


def _torch() -> Any:
    import torch

    return torch


def resolve_device(requested: str) -> str:
    """Resolve a declared device without silently requiring an accelerator."""

    torch = _torch()
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    if requested not in {"cpu", "cuda"}:
        raise ValueError(f"unsupported device: {requested}")
    return requested


def benchmark_dataset(parameters: dict[str, Any], seed: int) -> dict[str, np.ndarray]:
    """Reconstruct the omitted moons benchmark from declared parameters."""

    inputs, labels = make_moons(
        n_samples=int(parameters["total_samples"]),
        noise=float(parameters["noise"]),
        random_state=seed,
    )
    train, test = train_test_split(
        np.arange(len(labels)),
        train_size=int(parameters["train_samples"]),
        stratify=labels,
        random_state=seed,
    )
    return {
        "inputs": np.asarray(inputs, dtype=float),
        "labels": np.asarray(labels, dtype=int),
        "train_indices": np.asarray(train, dtype=int),
        "test_indices": np.asarray(test, dtype=int),
    }


def squeezed_product_states(
    inputs: np.ndarray,
    squeezing: float,
    cutoff: int,
    *,
    device: str,
) -> tuple[Any, Any]:
    """Return normalized two-mode inputs and pre-normalization retained mass."""

    if cutoff < 3:
        raise ValueError("cutoff must include the |2> measurement state")
    torch = _torch()
    real = torch.float64
    complex_type = torch.complex128
    phases = torch.as_tensor(inputs, dtype=real, device=device)
    vectors = []
    retained = []
    for mode in range(2):
        state = torch.zeros((len(inputs), cutoff), dtype=complex_type, device=device)
        for photon in range(0, cutoff, 2):
            n = photon // 2
            amplitude = (
                1.0
                / math.sqrt(math.cosh(squeezing))
                * math.sqrt(math.factorial(2 * n))
                / (2**n * math.factorial(n))
                * (-math.tanh(squeezing)) ** n
            )
            state[:, photon] = amplitude * torch.exp(1.0j * n * phases[:, mode])
        mass = torch.sum(torch.abs(state) ** 2, dim=1)
        state = (
            state / torch.sqrt(torch.clamp(mass, min=torch.finfo(real).tiny))[:, None]
        )
        vectors.append(state)
        retained.append(mass)
    joint = torch.einsum("bi,bj->bij", vectors[0], vectors[1])
    return joint, retained[0] * retained[1]


class FactorizedCVCircuit:
    """Four-block CV circuit with sector-local beam-splitter evolution."""

    def __init__(self, cutoff: int, blocks: int, *, device: str) -> None:
        if cutoff < 3:
            raise ValueError("cutoff must be at least three")
        if blocks <= 0:
            raise ValueError("blocks must be positive")
        self.cutoff = cutoff
        self.blocks = blocks
        self.device = device
        self.torch = _torch()
        torch = self.torch
        complex_type = torch.complex128
        annihilation = torch.zeros((cutoff, cutoff), dtype=complex_type, device=device)
        for photon in range(1, cutoff):
            annihilation[photon - 1, photon] = math.sqrt(photon)
        self.annihilation = annihilation
        self.creation = annihilation.T.conj()
        self.quadrature_x = (annihilation + self.creation) / math.sqrt(2.0)
        self.quadrature_x2 = self.quadrature_x @ self.quadrature_x
        self.quadrature_x3 = self.quadrature_x2 @ self.quadrature_x
        self.sectors: list[tuple[Any, Any, dict[tuple[int, int], int]]] = []
        for total in range(2 * cutoff - 1):
            pairs = [
                (first, total - first)
                for first in range(cutoff)
                if 0 <= total - first < cutoff
            ]
            first = torch.as_tensor(
                [pair[0] for pair in pairs], dtype=torch.long, device=device
            )
            second = torch.as_tensor(
                [pair[1] for pair in pairs], dtype=torch.long, device=device
            )
            self.sectors.append(
                (first, second, {pair: index for index, pair in enumerate(pairs)})
            )

    @property
    def parameter_count(self) -> int:
        return 8 * self.blocks

    def _beam_splitter(self, state: Any, amplitude: Any, phase: Any) -> Any:
        torch = self.torch
        output = torch.empty_like(state)
        positive_phase = torch.exp(1.0j * phase)
        negative_phase = torch.exp(-1.0j * phase)
        for first, second, positions in self.sectors:
            size = len(positions)
            generator = torch.zeros(
                (size, size),
                dtype=torch.complex128,
                device=self.device,
            )
            pairs = list(positions)
            for source, (n_first, n_second) in enumerate(pairs):
                raised = (n_first + 1, n_second - 1)
                if raised in positions:
                    generator[positions[raised], source] += positive_phase * math.sqrt(
                        (n_first + 1) * n_second
                    )
                lowered = (n_first - 1, n_second + 1)
                if lowered in positions:
                    generator[positions[lowered], source] -= negative_phase * math.sqrt(
                        n_first * (n_second + 1)
                    )
            unitary = torch.matrix_exp(amplitude * generator)
            sector_state = state[:, first, second]
            output[:, first, second] = sector_state @ unitary.T
        return output

    def _local_gate(self, displacement: Any, quadratic: Any, cubic: Any) -> Any:
        torch = self.torch
        displacement_gate = torch.matrix_exp(
            displacement.to(torch.complex128) * (self.creation - self.annihilation)
        )
        quadratic_gate = torch.matrix_exp(0.5j * quadratic * self.quadrature_x2)
        cubic_gate = torch.matrix_exp((1.0j / 3.0) * cubic * self.quadrature_x3)
        return cubic_gate @ quadratic_gate @ displacement_gate

    def evolve(self, batch: Any, parameters: Any) -> Any:
        if parameters.numel() != self.parameter_count:
            raise ValueError("parameter vector does not match the circuit block count")
        state = batch
        for block in range(self.blocks):
            theta = parameters[8 * block : 8 * block + 8]
            state = self._beam_splitter(state, theta[0], theta[1])
            first_gate = self._local_gate(theta[2], theta[4], theta[6])
            second_gate = self._local_gate(theta[3], theta[5], theta[7])
            state = self.torch.einsum(
                "ij,bjk,lk->bil",
                first_gate,
                state,
                second_gate,
            )
        return state

    def probabilities(self, batch: Any, parameters: Any) -> Any:
        evolved = self.evolve(batch, parameters)
        output_zero = self.torch.abs(evolved[:, 2, 0]) ** 2
        output_one = self.torch.abs(evolved[:, 0, 2]) ** 2
        denominator = output_zero + output_one + 1.0e-14
        return self.torch.stack(
            [output_zero / denominator, output_one / denominator],
            dim=1,
        )


def _optimizer_state_to_cpu(value: Any) -> Any:
    torch = _torch()
    if torch.is_tensor(value):
        return value.detach().cpu()
    if isinstance(value, dict):
        return {key: _optimizer_state_to_cpu(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_optimizer_state_to_cpu(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_optimizer_state_to_cpu(item) for item in value)
    return value


def _move_optimizer_state(optimizer: Any, device: str) -> None:
    torch = _torch()
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def train_condition(
    parameters: dict[str, Any],
    condition: VariationalCondition,
    *,
    device: str,
    resume_payload: dict[str, Any] | None = None,
    checkpoint_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Train one cutoff/seed condition with deterministic resumable batches."""

    torch = _torch()
    torch.manual_seed(condition.seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(condition.seed)
    torch.use_deterministic_algorithms(True)
    dataset = benchmark_dataset(parameters, condition.seed)
    states, retained = squeezed_product_states(
        dataset["inputs"],
        float(parameters["variational_c"]),
        condition.cutoff,
        device=device,
    )
    circuit = FactorizedCVCircuit(
        condition.cutoff,
        int(parameters["variational_blocks"]),
        device=device,
    )
    if circuit.parameter_count != int(parameters["variational_parameter_count"]):
        raise ValueError(
            "printed parameter count does not match the circuit definition"
        )
    learned = torch.nn.Parameter(
        torch.randn(circuit.parameter_count, dtype=torch.float64, device=device)
        * float(parameters["initial_parameter_std"])
    )
    optimizer = torch.optim.Adam([learned], lr=float(parameters["learning_rate"]))
    rng = np.random.default_rng(condition.seed)
    steps = int(parameters["variational_steps"])
    loss_history = np.full(steps, np.nan, dtype=float)
    start = 0
    if resume_payload is not None:
        start = int(resume_payload["step"])
        learned.data.copy_(
            resume_payload["parameters"].to(device=device, dtype=torch.float64)
        )
        optimizer.load_state_dict(resume_payload["optimizer_state"])
        _move_optimizer_state(optimizer, device)
        previous_loss = np.asarray(resume_payload["loss"], dtype=float)
        loss_history[: len(previous_loss)] = previous_loss
        rng.bit_generator.state = resume_payload["numpy_rng_state"]
        torch.set_rng_state(resume_payload["torch_cpu_rng_state"])
        if device == "cuda" and resume_payload.get("torch_cuda_rng_state") is not None:
            torch.cuda.set_rng_state(
                resume_payload["torch_cuda_rng_state"].to(device="cpu")
            )
    train = dataset["train_indices"]
    batch_size = int(parameters["variational_batch_size"])
    regularization = float(parameters["l2_regularization"])
    interval = int(parameters["checkpoint_every_steps"])
    for step in range(start, steps):
        indices = rng.choice(train, size=batch_size, replace=False)
        targets = torch.nn.functional.one_hot(
            torch.as_tensor(dataset["labels"][indices], device=device),
            2,
        ).to(torch.float64)
        optimizer.zero_grad()
        predicted = circuit.probabilities(states[indices], learned)
        loss = torch.mean(torch.sum((predicted - targets) ** 2, dim=1))
        loss = loss + regularization * torch.mean(learned**2)
        loss.backward()
        torch.nn.utils.clip_grad_norm_([learned], max_norm=5.0)
        optimizer.step()
        loss_history[step] = float(loss.detach().cpu())
        completed = step + 1
        if checkpoint_callback is not None and (
            completed % interval == 0 or completed == steps
        ):
            checkpoint_callback(
                {
                    "step": completed,
                    "parameters": learned.detach().cpu(),
                    "optimizer_state": _optimizer_state_to_cpu(optimizer.state_dict()),
                    "loss": loss_history[:completed].copy(),
                    "numpy_rng_state": rng.bit_generator.state,
                    "torch_cpu_rng_state": torch.get_rng_state().cpu(),
                    "torch_cuda_rng_state": (
                        torch.cuda.get_rng_state().cpu() if device == "cuda" else None
                    ),
                }
            )

    def predict(inputs: np.ndarray) -> np.ndarray:
        values = []
        chunk = int(parameters["prediction_chunk_size"])
        with torch.no_grad():
            for begin in range(0, len(inputs), chunk):
                batch, _ = squeezed_product_states(
                    inputs[begin : begin + chunk],
                    float(parameters["variational_c"]),
                    condition.cutoff,
                    device=device,
                )
                values.append(circuit.probabilities(batch, learned).cpu().numpy())
        return np.concatenate(values)

    probabilities = predict(dataset["inputs"])
    train_accuracy = float(
        np.mean(
            np.argmax(probabilities[dataset["train_indices"]], axis=1)
            == dataset["labels"][dataset["train_indices"]]
        )
    )
    test_accuracy = float(
        np.mean(
            np.argmax(probabilities[dataset["test_indices"]], axis=1)
            == dataset["labels"][dataset["test_indices"]]
        )
    )
    padding = float(parameters["grid_padding"])
    lower = dataset["inputs"].min(axis=0) - padding
    upper = dataset["inputs"].max(axis=0) + padding
    points = int(parameters["variational_grid_points"])
    grid_x = np.linspace(lower[0], upper[0], points)
    grid_y = np.linspace(lower[1], upper[1], points)
    xx, yy = np.meshgrid(grid_x, grid_y)
    grid = np.column_stack([xx.ravel(), yy.ravel()])
    grid_probability = predict(grid)[:, 1].reshape(points, points)
    initial_window = float(np.median(loss_history[: min(20, steps)]))
    final_window = float(np.median(loss_history[-min(200, steps) :]))
    return {
        **dataset,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "class_one_probability": grid_probability,
        "loss": loss_history,
        "final_parameters": learned.detach().cpu().numpy(),
        "train_accuracy": np.asarray([train_accuracy]),
        "test_accuracy": np.asarray([test_accuracy]),
        "initial_loss_median": np.asarray([initial_window]),
        "final_loss_median": np.asarray([final_window]),
        "loss_reduction_ratio": np.asarray(
            [final_window / max(initial_window, np.finfo(float).tiny)]
        ),
        "input_retained_probability_min": np.asarray(
            [float(torch.min(retained).detach().cpu())]
        ),
        "cutoff": np.asarray([condition.cutoff]),
        "seed": np.asarray([condition.seed]),
        "actual_device": np.asarray([device]),
    }


def factorized_dense_crosscheck(cutoff: int = 4) -> dict[str, float | bool]:
    """Compare one factorized block with an independent dense Kronecker path."""

    torch = _torch()
    device = "cpu"
    circuit = FactorizedCVCircuit(cutoff, 1, device=device)
    parameters = torch.tensor(
        [0.17, -0.23, 0.11, -0.07, 0.13, -0.19, 0.05, 0.09],
        dtype=torch.float64,
    )
    inputs = np.asarray([[-0.31, 0.27], [0.44, -0.52]])
    state, _ = squeezed_product_states(inputs, 1.5, cutoff, device=device)
    factorized = circuit.evolve(state, parameters)

    annihilation = circuit.annihilation
    identity = torch.eye(cutoff, dtype=torch.complex128)
    first = torch.kron(annihilation, identity)
    second = torch.kron(identity, annihilation)
    first_adjoint = first.T.conj()
    second_adjoint = second.T.conj()
    generator = (
        torch.exp(1.0j * parameters[1]) * first_adjoint @ second
        - torch.exp(-1.0j * parameters[1]) * first @ second_adjoint
    )
    beam_splitter = torch.matrix_exp(parameters[0] * generator)
    first_gate = circuit._local_gate(parameters[2], parameters[4], parameters[6])
    second_gate = circuit._local_gate(parameters[3], parameters[5], parameters[7])
    dense = torch.kron(first_gate, second_gate) @ beam_splitter
    dense_result = (dense @ state.reshape(len(state), -1).T).T.reshape_as(state)
    difference = float(torch.max(torch.abs(factorized - dense_result)))
    identity_dense = torch.eye(cutoff * cutoff, dtype=torch.complex128)
    unitarity = float(torch.max(torch.abs(dense.T.conj() @ dense - identity_dense)))
    return {
        "factorized_dense_max_absolute_error": difference,
        "dense_unitarity_max_absolute_error": unitarity,
        "passed": difference <= 1.0e-10 and unitarity <= 1.0e-10,
    }
