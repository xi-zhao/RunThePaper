"""Constant-element TM boundary-element method for dielectric cavities.

The implementation follows the equations in Wiersig, J. Opt. A 5, 53 (2003).
It deliberately accepts geometry and physical parameters only; source images
and author-generated arrays are not inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import linalg, optimize, special


ComplexArray = NDArray[np.complex128]
FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class BoundaryMesh:
    """Oriented straight boundary elements with a fixed cavity-outward normal."""

    start: FloatArray
    end: FloatArray
    midpoint: FloatArray
    tangent: FloatArray
    normal: FloatArray
    length: FloatArray
    curvature: FloatArray
    cavity: NDArray[np.int64]

    @property
    def size(self) -> int:
        return int(self.length.size)


def _mesh_from_segments(
    starts: ArrayLike,
    ends: ArrayLike,
    cavity: ArrayLike,
    curvature: ArrayLike | None = None,
) -> BoundaryMesh:
    start = np.asarray(starts, dtype=float)
    end = np.asarray(ends, dtype=float)
    cavity_ids = np.asarray(cavity, dtype=np.int64)
    edge = end - start
    length = np.linalg.norm(edge, axis=1)
    if np.any(length <= 0):
        raise ValueError("boundary elements must have positive length")
    tangent = edge / length[:, None]
    # Right normal is outward for counter-clockwise cavity contours.
    normal = np.column_stack((tangent[:, 1], -tangent[:, 0]))
    curv = np.zeros_like(length) if curvature is None else np.asarray(curvature, dtype=float)
    return BoundaryMesh(
        start=start,
        end=end,
        midpoint=(start + end) / 2,
        tangent=tangent,
        normal=normal,
        length=length,
        curvature=curv,
        cavity=cavity_ids,
    )


def regular_polygon_mesh(
    centers: ArrayLike,
    *,
    sides: int = 6,
    side_length: float = 1.0,
    elements_per_side: int = 8,
    rotation: float = 0.0,
) -> BoundaryMesh:
    """Build counter-clockwise regular polygons split uniformly by side."""
    if sides < 3 or elements_per_side < 1:
        raise ValueError("sides >= 3 and elements_per_side >= 1 are required")
    centers_array = np.atleast_2d(np.asarray(centers, dtype=float))
    radius = side_length / (2 * np.sin(np.pi / sides))
    base_angles = rotation + 2 * np.pi * np.arange(sides) / sides
    base = radius * np.column_stack((np.cos(base_angles), np.sin(base_angles)))
    starts: list[FloatArray] = []
    ends: list[FloatArray] = []
    cavity_ids: list[int] = []
    for cavity_id, center in enumerate(centers_array):
        vertices = base + center
        for side in range(sides):
            a = vertices[side]
            b = vertices[(side + 1) % sides]
            for element in range(elements_per_side):
                t0 = element / elements_per_side
                t1 = (element + 1) / elements_per_side
                starts.append(a + t0 * (b - a))
                ends.append(a + t1 * (b - a))
                cavity_ids.append(cavity_id)
    return _mesh_from_segments(starts, ends, cavity_ids)


def coupled_hexagon_mesh(elements_per_side: int) -> BoundaryMesh:
    """Paper geometry, centered in the plotting frame.

    The two centers differ by (1.8, -0.5) R, matching the orientation shown in
    the geometry panel; reflection in y is physically equivalent before the
    incidence direction is fixed.
    """
    centers = np.array([[-0.9, 0.25], [0.9, -0.25]])
    return regular_polygon_mesh(
        centers,
        sides=6,
        side_length=1.0,
        elements_per_side=elements_per_side,
        rotation=0.0,
    )


def rounded_regular_polygon_mesh(
    centers: ArrayLike,
    *,
    sides: int = 6,
    side_length: float = 1.0,
    side_elements: int = 16,
    corner_elements: int = 6,
    corner_radius: float = 0.0205,
    rotation: float = 0.0,
) -> BoundaryMesh:
    """Circular-fillet realization of the paper's otherwise unspecified rounding.

    The publication says results are insensitive to the selected rounding but
    provides no curve.  This explicit circular choice is therefore a declared
    reconstruction, never an inferred hidden parameter.
    """
    if corner_radius <= 0:
        raise ValueError("corner_radius must be positive")
    centers_array = np.atleast_2d(np.asarray(centers, dtype=float))
    circumradius = side_length / (2 * np.sin(np.pi / sides))
    angles = rotation + 2 * np.pi * np.arange(sides) / sides
    base = circumradius * np.column_stack((np.cos(angles), np.sin(angles)))
    interior_angle = np.pi * (sides - 2) / sides
    tangent_offset = corner_radius / np.tan(interior_angle / 2)
    starts: list[FloatArray] = []
    ends: list[FloatArray] = []
    cavity_ids: list[int] = []
    curvatures: list[float] = []

    for cavity_id, center_shift in enumerate(centers_array):
        vertices = base + center_shift
        tangent_in = np.empty_like(vertices)
        tangent_out = np.empty_like(vertices)
        fillet_centers = np.empty_like(vertices)
        for index, vertex in enumerate(vertices):
            previous = vertices[(index - 1) % sides]
            following = vertices[(index + 1) % sides]
            incoming = (vertex - previous) / np.linalg.norm(vertex - previous)
            outgoing = (following - vertex) / np.linalg.norm(following - vertex)
            tangent_in[index] = vertex - tangent_offset * incoming
            tangent_out[index] = vertex + tangent_offset * outgoing
            left_normal = np.array([-incoming[1], incoming[0]])
            fillet_centers[index] = tangent_in[index] + corner_radius * left_normal

        for index in range(sides):
            # Rounded corner at vertex i, traversed counter-clockwise.
            center = fillet_centers[index]
            start_angle = np.arctan2(
                tangent_in[index, 1] - center[1], tangent_in[index, 0] - center[0]
            )
            end_angle = np.arctan2(
                tangent_out[index, 1] - center[1], tangent_out[index, 0] - center[0]
            )
            while end_angle <= start_angle:
                end_angle += 2 * np.pi
            arc_angles = np.linspace(start_angle, end_angle, corner_elements + 1)
            arc_points = center + corner_radius * np.column_stack(
                (np.cos(arc_angles), np.sin(arc_angles))
            )
            for element in range(corner_elements):
                starts.append(arc_points[element])
                ends.append(arc_points[element + 1])
                cavity_ids.append(cavity_id)
                curvatures.append(1 / corner_radius)

            # Straight side after vertex i.
            a = tangent_out[index]
            b = tangent_in[(index + 1) % sides]
            for element in range(side_elements):
                t0 = element / side_elements
                t1 = (element + 1) / side_elements
                starts.append(a + t0 * (b - a))
                ends.append(a + t1 * (b - a))
                cavity_ids.append(cavity_id)
                curvatures.append(0.0)
    return _mesh_from_segments(starts, ends, cavity_ids, curvatures)


def coupled_rounded_hexagon_mesh(
    side_elements: int,
    corner_elements: int,
    corner_radius: float = 0.0205,
) -> BoundaryMesh:
    centers = np.array([[-0.9, 0.25], [0.9, -0.25]])
    return rounded_regular_polygon_mesh(
        centers,
        sides=6,
        side_length=1.0,
        side_elements=side_elements,
        corner_elements=corner_elements,
        corner_radius=corner_radius,
    )


def circular_mesh(elements: int, radius: float = 1.0) -> BoundaryMesh:
    """Polygonal circle benchmark with analytic midpoint curvature."""
    angles = 2 * np.pi * np.arange(elements + 1) / elements
    points = radius * np.column_stack((np.cos(angles), np.sin(angles)))
    return _mesh_from_segments(
        points[:-1],
        points[1:],
        np.zeros(elements, dtype=np.int64),
        np.full(elements, 1 / radius),
    )


def resolution_metric(mesh: BoundaryMesh, k: complex, refractive_index: float) -> float:
    """Minimum elements per local wavelength, Eq. discussion after (38)."""
    return float(2 * np.pi / (refractive_index * np.real(k) * np.max(mesh.length)))


def green_kernel(distance: ArrayLike, k: complex, refractive_index: float) -> ComplexArray:
    distance_array = np.asarray(distance, dtype=float)
    return -0.25j * special.hankel1(0, refractive_index * k * distance_array)


def normal_green_kernel(
    displacement: ArrayLike,
    source_normal: ArrayLike,
    k: complex,
    refractive_index: float,
) -> ComplexArray:
    displacement_array = np.asarray(displacement, dtype=float)
    normal_array = np.asarray(source_normal, dtype=float)
    distance = np.linalg.norm(displacement_array, axis=-1)
    cosine = np.sum(normal_array * displacement_array, axis=-1) / distance
    return (
        0.25j
        * refractive_index
        * k
        * cosine
        * special.hankel1(1, refractive_index * k * distance)
    )


def quadrature_geometry(mesh: BoundaryMesh, order: int = 8) -> tuple[FloatArray, FloatArray]:
    """Return quadrature coordinates [source, q, xy] and arc weights."""
    nodes, weights = np.polynomial.legendre.leggauss(order)
    half_edge = (mesh.end - mesh.start)[:, None, :] / 2
    points = mesh.midpoint[:, None, :] + nodes[None, :, None] * half_edge
    arc_weights = mesh.length[:, None] * weights[None, :] / 2
    return points, arc_weights


def medium_blocks(
    mesh: BoundaryMesh,
    k: complex,
    refractive_index: float,
    *,
    quadrature_order: int = 8,
) -> tuple[ComplexArray, ComplexArray]:
    """Evaluate the B and C matrices for one homogeneous medium."""
    points, weights = quadrature_geometry(mesh, quadrature_order)
    # axes: target i, source l, quadrature q, coordinate
    displacement = points[None, :, :, :] - mesh.midpoint[:, None, None, :]
    distance = np.linalg.norm(displacement, axis=-1)
    safe_distance = np.where(distance == 0, 1.0, distance)
    cosine = np.sum(
        displacement * mesh.normal[None, :, None, :], axis=-1
    ) / safe_distance
    argument = refractive_index * k * safe_distance
    b_kernel = 0.5j * special.hankel1(0, argument)
    c_kernel = (
        0.5j
        * refractive_index
        * k
        * cosine
        * special.hankel1(1, argument)
    )
    b = np.sum(b_kernel * weights[None, :, :], axis=-1)
    c = np.sum(c_kernel * weights[None, :, :], axis=-1)

    diagonal = np.arange(mesh.size)
    euler_gamma = float(np.euler_gamma)
    b[diagonal, diagonal] = (
        mesh.length
        / np.pi
        * (
            1
            - np.log(refractive_index * k * mesh.length / 4)
            + 0.5j * np.pi
            - euler_gamma
        )
    )
    c[diagonal, diagonal] = -1 + mesh.curvature * mesh.length / (2 * np.pi)
    return np.asarray(b, dtype=np.complex128), np.asarray(c, dtype=np.complex128)


def assemble_matrix(
    mesh: BoundaryMesh,
    k: complex,
    *,
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
) -> tuple[ComplexArray, tuple[ComplexArray, ComplexArray]]:
    """Assemble the 2N by 2N interior/exterior TM system."""
    b_in_all, c_in_all = medium_blocks(
        mesh, k, n_inside, quadrature_order=quadrature_order
    )
    same_cavity = mesh.cavity[:, None] == mesh.cavity[None, :]
    b_in = np.where(same_cavity, b_in_all, 0)
    c_in = np.where(same_cavity, c_in_all, 0)
    b_out, c_out_interior_limit = medium_blocks(
        mesh, k, n_outside, quadrature_order=quadrature_order
    )
    # The exterior trace approaches the same fixed, cavity-outward normal from
    # the opposite side of the interface.  The double-layer jump therefore
    # changes from -I to +I (a +2I correction to the interior-limit block).
    c_out = c_out_interior_limit + 2 * np.eye(mesh.size, dtype=np.complex128)
    matrix = np.block([[b_in, c_in], [b_out, c_out]])
    return np.asarray(matrix, dtype=np.complex128), (b_out, c_out)


def incident_boundary_values(
    mesh: BoundaryMesh,
    k: float,
    incidence_angle: float,
) -> tuple[ComplexArray, ComplexArray]:
    direction = np.array([np.cos(incidence_angle), np.sin(incidence_angle)])
    phase = np.exp(1j * k * (mesh.midpoint @ direction))
    derivative = 1j * k * (mesh.normal @ direction) * phase
    return derivative.astype(np.complex128), phase.astype(np.complex128)


def solve_scattering(
    mesh: BoundaryMesh,
    k: float,
    *,
    incidence_angle: float = np.deg2rad(15),
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
) -> dict[str, ComplexArray | float]:
    matrix, (b_out, c_out) = assemble_matrix(
        mesh,
        complex(k),
        n_inside=n_inside,
        n_outside=n_outside,
        quadrature_order=quadrature_order,
    )
    phi_in, psi_in = incident_boundary_values(mesh, k, incidence_angle)
    rhs = np.concatenate(
        [np.zeros(mesh.size, dtype=np.complex128), b_out @ phi_in + c_out @ psi_in]
    )
    solution = linalg.solve(matrix, rhs, assume_a="gen")
    residual = float(np.linalg.norm(matrix @ solution - rhs) / np.linalg.norm(rhs))
    return {
        "phi": solution[: mesh.size],
        "psi": solution[mesh.size :],
        "phi_in": phi_in,
        "psi_in": psi_in,
        "relative_residual": residual,
    }


def far_field(
    mesh: BoundaryMesh,
    k: complex,
    phi: ArrayLike,
    psi: ArrayLike,
    angles: ArrayLike,
    *,
    phi_in: ArrayLike | None = None,
    psi_in: ArrayLike | None = None,
    quadrature_order: int = 8,
) -> ComplexArray:
    """Equation (21), with optional incident boundary values subtracted."""
    phi_array = np.asarray(phi, dtype=np.complex128)
    psi_array = np.asarray(psi, dtype=np.complex128)
    if phi_in is not None:
        phi_array = phi_array - np.asarray(phi_in, dtype=np.complex128)
    if psi_in is not None:
        psi_array = psi_array - np.asarray(psi_in, dtype=np.complex128)
    theta = np.asarray(angles, dtype=float)
    directions = np.column_stack((np.cos(theta), np.sin(theta)))
    points, weights = quadrature_geometry(mesh, quadrature_order)
    phase = np.exp(-1j * k * np.einsum("ad,lqd->alq", directions, points))
    projected_normal = directions @ mesh.normal.T
    integrand = (
        1j * k * projected_normal[:, :, None] * psi_array[None, :, None]
        + phi_array[None, :, None]
    )
    integral = np.sum(phase * integrand * weights[None, :, :], axis=(1, 2))
    # Equation (21) uses the exterior-domain normal.  Our single interface
    # normal points from cavity to exterior, i.e. in the opposite direction
    # on the exterior trace, hence the global minus sign.
    return -(1 + 1j) * integral / (4 * np.sqrt(np.pi * k))


def cross_section(
    mesh: BoundaryMesh,
    k: float,
    *,
    incidence_angle: float = np.deg2rad(15),
    angular_samples: int = 360,
    n_inside: float = 1.466,
    quadrature_order: int = 8,
) -> dict[str, float | ComplexArray]:
    solution = solve_scattering(
        mesh,
        k,
        incidence_angle=incidence_angle,
        n_inside=n_inside,
        quadrature_order=quadrature_order,
    )
    angles = np.linspace(0, 2 * np.pi, angular_samples, endpoint=False)
    amplitude = far_field(
        mesh,
        k,
        solution["phi"],
        solution["psi"],
        angles,
        phi_in=solution["phi_in"],
        psi_in=solution["psi_in"],
        quadrature_order=quadrature_order,
    )
    sigma_integrated = float(2 * np.pi * np.mean(np.abs(amplitude) ** 2))
    forward = far_field(
        mesh,
        k,
        solution["phi"],
        solution["psi"],
        np.array([incidence_angle]),
        phi_in=solution["phi_in"],
        psi_in=solution["psi_in"],
        quadrature_order=quadrature_order,
    )[0]
    sigma_optical = float(
        2 * np.sqrt(np.pi / k) * np.imag((1 - 1j) * forward)
    )
    denominator = max(abs(sigma_integrated), abs(sigma_optical), 1e-15)
    return {
        **solution,
        "angles": angles,
        "amplitude": amplitude,
        "sigma_integrated": sigma_integrated,
        "sigma_optical": sigma_optical,
        "optical_relative_error": abs(sigma_integrated - sigma_optical) / denominator,
    }


def scan_cross_section(
    mesh: BoundaryMesh,
    wave_numbers: Iterable[float],
    **kwargs: object,
) -> dict[str, FloatArray]:
    k_values = np.asarray(list(wave_numbers), dtype=float)
    integrated = np.empty_like(k_values)
    optical = np.empty_like(k_values)
    optical_error = np.empty_like(k_values)
    residual = np.empty_like(k_values)
    for index, k in enumerate(k_values):
        result = cross_section(mesh, float(k), **kwargs)
        integrated[index] = float(result["sigma_integrated"])
        optical[index] = float(result["sigma_optical"])
        optical_error[index] = float(result["optical_relative_error"])
        residual[index] = float(result["relative_residual"])
    return {
        "k": k_values,
        "sigma": integrated,
        "sigma_optical": optical,
        "optical_relative_error": optical_error,
        "linear_residual": residual,
    }


def trace_newton(
    mesh: BoundaryMesh,
    initial_k: complex,
    *,
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
    derivative_step: float = 2e-5,
    max_iterations: int = 12,
    tolerance: float = 1e-9,
    degeneracy: int = 1,
) -> tuple[complex, list[dict[str, float]]]:
    """Equation (37), using a centered complex matrix derivative."""
    current = complex(initial_k)
    history: list[dict[str, float]] = []
    for _ in range(max_iterations):
        matrix, _ = assemble_matrix(
            mesh,
            current,
            n_inside=n_inside,
            n_outside=n_outside,
            quadrature_order=quadrature_order,
        )
        plus, _ = assemble_matrix(
            mesh,
            current + derivative_step,
            n_inside=n_inside,
            n_outside=n_outside,
            quadrature_order=quadrature_order,
        )
        minus, _ = assemble_matrix(
            mesh,
            current - derivative_step,
            n_inside=n_inside,
            n_outside=n_outside,
            quadrature_order=quadrature_order,
        )
        derivative = (plus - minus) / (2 * derivative_step)
        trace_term = np.trace(linalg.solve(matrix, derivative, assume_a="gen"))
        step = degeneracy / trace_term
        singular_values = linalg.svdvals(matrix)
        history.append(
            {
                "k_real": float(current.real),
                "k_imag": float(current.imag),
                "step_abs": float(abs(step)),
                "smallest_singular": float(singular_values[-1]),
            }
        )
        if not np.isfinite(step):
            raise RuntimeError("trace-Newton produced a non-finite step")
        # A trust radius keeps a coarse mesh from jumping to a distant pole.
        if abs(step) > 0.35:
            step *= 0.35 / abs(step)
        current -= step
        if abs(step) < tolerance:
            break
    return current, history


def minimize_resonance(
    mesh: BoundaryMesh,
    initial_k: complex,
    *,
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
    max_iterations: int = 80,
) -> tuple[complex, optimize.OptimizeResult]:
    """Independent fallback: minimize log smallest singular value in C."""
    def objective(values: FloatArray) -> float:
        trial = complex(values[0], values[1])
        matrix, _ = assemble_matrix(
            mesh,
            trial,
            n_inside=n_inside,
            n_outside=n_outside,
            quadrature_order=quadrature_order,
        )
        smallest = linalg.svdvals(matrix)[-1]
        return float(np.log10(max(smallest, np.finfo(float).tiny)))

    result = optimize.minimize(
        objective,
        np.array([initial_k.real, initial_k.imag]),
        method="Nelder-Mead",
        options={"maxiter": max_iterations, "xatol": 2e-7, "fatol": 2e-6},
    )
    return complex(result.x[0], result.x[1]), result


def resonance_boundary_state(
    mesh: BoundaryMesh,
    k: complex,
    *,
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
) -> dict[str, ComplexArray | float]:
    matrix, _ = assemble_matrix(
        mesh,
        k,
        n_inside=n_inside,
        n_outside=n_outside,
        quadrature_order=quadrature_order,
    )
    _, singular_values, vh = linalg.svd(matrix, full_matrices=False)
    vector = vh[-1].conj()
    vector /= np.max(np.abs(vector[mesh.size :]))
    residual = float(np.linalg.norm(matrix @ vector) / np.linalg.norm(vector))
    return {
        "phi": vector[: mesh.size],
        "psi": vector[mesh.size :],
        "smallest_singular": float(singular_values[-1]),
        "relative_residual": residual,
    }


def _points_in_polygon(points: FloatArray, vertices: FloatArray) -> NDArray[np.bool_]:
    """Vectorized ray casting; boundary points are treated as outside."""
    x = points[:, 0]
    y = points[:, 1]
    inside = np.zeros(points.shape[0], dtype=bool)
    x0, y0 = vertices[-1]
    for x1, y1 in vertices:
        crosses = ((y1 > y) != (y0 > y)) & (
            x < (x0 - x1) * (y - y1) / (y0 - y1 + np.finfo(float).eps) + x1
        )
        inside ^= crosses
        x0, y0 = x1, y1
    return inside


def cavity_vertices(mesh: BoundaryMesh, cavity_id: int) -> FloatArray:
    selected = np.flatnonzero(mesh.cavity == cavity_id)
    if selected.size == 0:
        raise ValueError(f"unknown cavity {cavity_id}")
    # Starts are already contour ordered. Collapse repeated collinear samples
    # is unnecessary for ray casting.
    return mesh.start[selected]


def reconstruct_field(
    mesh: BoundaryMesh,
    k: complex,
    phi: ArrayLike,
    psi: ArrayLike,
    points: ArrayLike,
    *,
    n_inside: float = 1.466,
    n_outside: float = 1.0,
    quadrature_order: int = 8,
    chunk_size: int = 512,
) -> ComplexArray:
    """Reconstruct Eq. (38) inside each cavity and in the exterior."""
    query = np.atleast_2d(np.asarray(points, dtype=float))
    phi_array = np.asarray(phi, dtype=np.complex128)
    psi_array = np.asarray(psi, dtype=np.complex128)
    field = np.empty(query.shape[0], dtype=np.complex128)
    region = np.full(query.shape[0], -1, dtype=np.int64)
    for cavity_id in np.unique(mesh.cavity):
        mask = _points_in_polygon(query, cavity_vertices(mesh, int(cavity_id)))
        region[mask] = cavity_id
    quadrature_points, weights = quadrature_geometry(mesh, quadrature_order)

    for start in range(0, query.shape[0], chunk_size):
        stop = min(query.shape[0], start + chunk_size)
        for target_index in range(start, stop):
            cavity_id = region[target_index]
            if cavity_id >= 0:
                source_mask = mesh.cavity == cavity_id
                refractive_index = n_inside
            else:
                source_mask = np.ones(mesh.size, dtype=bool)
                refractive_index = n_outside
            source_points = quadrature_points[source_mask]
            displacement = source_points - query[target_index]
            distance = np.linalg.norm(displacement, axis=-1)
            distance = np.maximum(distance, 1e-12)
            cosine = np.sum(
                displacement * mesh.normal[source_mask, None, :], axis=-1
            ) / distance
            argument = refractive_index * k * distance
            green = -0.25j * special.hankel1(0, argument)
            derivative = (
                0.25j
                * refractive_index
                * k
                * cosine
                * special.hankel1(1, argument)
            )
            weighted = weights[source_mask]
            field[target_index] = np.sum(
                psi_array[source_mask, None] * derivative * weighted
                - phi_array[source_mask, None] * green * weighted
            )
    return field


def analytic_tm_circle_characteristic(
    k: complex,
    azimuthal_order: int,
    refractive_index: float,
) -> complex:
    """Separation-of-variables TM resonance equation for a unit circle."""
    m = azimuthal_order
    return (
        refractive_index
        * special.jvp(m, refractive_index * k)
        * special.hankel1(m, k)
        - special.jv(m, refractive_index * k) * special.h1vp(m, k)
    )


def analytic_tm_circle_root(
    initial_k: complex,
    azimuthal_order: int,
    refractive_index: float,
) -> complex:
    def residual(values: FloatArray) -> FloatArray:
        value = analytic_tm_circle_characteristic(
            complex(values[0], values[1]), azimuthal_order, refractive_index
        )
        return np.array([value.real, value.imag])

    result = optimize.root(residual, np.array([initial_k.real, initial_k.imag]))
    if not result.success:
        raise RuntimeError(f"analytic circle root failed: {result.message}")
    return complex(result.x[0], result.x[1])
