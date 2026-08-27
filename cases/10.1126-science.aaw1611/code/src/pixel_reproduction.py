"""Pixel-domain comparison primitives for paper figure reproduction.

The core object is a scalar-field target: a simulated array, a crop from the
paper's theoretical panel, and the colorbar that maps scalar values to pixels.
The module deliberately separates visual fidelity from physics acceptance.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from PIL import Image
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
ByteArray = NDArray[np.uint8]


@dataclass(frozen=True)
class ScalarFieldTarget:
    """A paper panel whose interior encodes a scalar field with a colorbar."""

    target_id: str
    reference_image: Path
    data_box: tuple[int, int, int, int]
    values: FloatArray
    vmin: float
    vmax: float
    exclude_boxes: tuple[tuple[int, int, int, int], ...] = ()
    flip_vertical: bool = True
    smooth_vertical: bool = True


@dataclass(frozen=True)
class PixelMetrics:
    """Literal-pixel and decoded-pattern metrics on a normalized 0--1 scale."""

    valid_pixel_count: int
    literal_rgb_similarity: float
    decoded_mae: float
    decoded_rmse: float
    decoded_pearson_r: float
    decoded_global_ssim: float
    decoded_gradient_r: float
    pattern_similarity_percent: float
    mean_palette_distance_rgb: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True)
class DigitizedGridMetrics:
    """Physics-cell metrics after removing axes, labels and interpolation."""

    valid_cell_count: int
    mae: float
    rmse: float
    pearson_r: float
    global_ssim: float
    pattern_similarity_percent: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def load_long_matrix(
    path: Path,
    row_field: str,
    column_field: str,
    value_field: str,
    filters: Mapping[str, str] | None = None,
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Pivot a long CSV table into a dense, sorted numeric matrix."""

    selected: list[tuple[float, float, float]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if filters and any(row[key] != expected for key, expected in filters.items()):
                continue
            selected.append((float(row[row_field]), float(row[column_field]), float(row[value_field])))
    if not selected:
        raise ValueError(f"no rows selected from {path}")

    row_values = np.asarray(sorted({item[0] for item in selected}), dtype=np.float64)
    column_values = np.asarray(sorted({item[1] for item in selected}), dtype=np.float64)
    row_index = {value: index for index, value in enumerate(row_values)}
    column_index = {value: index for index, value in enumerate(column_values)}
    matrix = np.full((len(row_values), len(column_values)), np.nan, dtype=np.float64)
    for row_value, column_value, value in selected:
        matrix[row_index[row_value], column_index[column_value]] = value
    if np.isnan(matrix).any():
        raise ValueError(f"selected rows from {path} do not form a dense matrix")
    return row_values, column_values, matrix


def extract_vertical_palette(
    image_path: Path,
    sample_box: Sequence[int],
    color_count: int = 256,
    low_at_bottom: bool = True,
) -> ByteArray:
    """Sample a vertical colorbar, recording its actual in-panel direction."""

    page = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.float64)
    left, top, right, bottom = (int(value) for value in sample_box)
    strip = page[top:bottom, left:right]
    if strip.size == 0 or strip.shape[0] < 2:
        raise ValueError(f"empty colorbar sample in {image_path}")
    top_to_bottom = np.median(strip, axis=1)
    low_to_high = top_to_bottom[::-1] if low_at_bottom else top_to_bottom
    source_x = np.linspace(0.0, 1.0, len(low_to_high))
    target_x = np.linspace(0.0, 1.0, color_count)
    palette = np.column_stack(
        [np.interp(target_x, source_x, low_to_high[:, channel]) for channel in range(3)]
    )
    return np.clip(np.rint(palette), 0, 255).astype(np.uint8)


def rasterize_scalar_field(
    values: FloatArray,
    output_shape: tuple[int, int],
    vmin: float,
    vmax: float,
    flip_vertical: bool = True,
    smooth_vertical: bool = True,
) -> FloatArray:
    """Rasterize a scalar grid with explicit paper-axis orientation."""

    if values.ndim != 2 or vmax <= vmin:
        raise ValueError("values must be 2-D and vmax must exceed vmin")
    height, width = output_shape
    normalized = np.clip((values - vmin) / (vmax - vmin), 0.0, 1.0)
    # Paper panels show time increasing upward.  Bilinear vertical resampling
    # follows the dense time grid; nearest horizontal resampling preserves the
    # physical meaning of one discrete column per qubit.
    oriented = np.flipud(normalized) if flip_vertical else normalized
    source = Image.fromarray(oriented.astype(np.float32))
    vertical_resampling = Image.Resampling.BILINEAR if smooth_vertical else Image.Resampling.NEAREST
    vertical = source.resize((values.shape[1], height), resample=vertical_resampling)
    raster = vertical.resize((width, height), resample=Image.Resampling.NEAREST)
    return np.asarray(raster, dtype=np.float64)


def colorize_scalar_field(normalized: FloatArray, palette: ByteArray) -> ByteArray:
    indices = np.clip(np.rint(normalized * (len(palette) - 1)), 0, len(palette) - 1).astype(int)
    return palette[indices]


def decode_scalar_field(rgb: ByteArray, palette: ByteArray) -> tuple[FloatArray, FloatArray]:
    """Invert a rasterized paper colorbar by nearest RGB palette matching."""

    flat = rgb.reshape(-1, 3).astype(np.float64)
    colors = palette.astype(np.float64)
    decoded = np.empty(len(flat), dtype=np.float64)
    distance = np.empty(len(flat), dtype=np.float64)
    chunk_size = 8192
    for start in range(0, len(flat), chunk_size):
        chunk = flat[start : start + chunk_size]
        squared = np.sum((chunk[:, None, :] - colors[None, :, :]) ** 2, axis=2)
        indices = np.argmin(squared, axis=1)
        decoded[start : start + len(chunk)] = indices / (len(palette) - 1)
        distance[start : start + len(chunk)] = np.sqrt(squared[np.arange(len(chunk)), indices])
    shape = rgb.shape[:2]
    return decoded.reshape(shape), distance.reshape(shape)


def digitize_uniform_grid(
    rgb: ByteArray,
    palette: ByteArray,
    grid_shape: tuple[int, int],
    inset_fraction: float = 0.25,
    flip_vertical: bool = False,
) -> tuple[FloatArray, FloatArray]:
    """Recover one scalar per displayed physics cell.

    Only the central part of each cell is sampled. This deliberately removes
    plot spines, antialiased cell boundaries and other layout pixels before
    the source colorbar is inverted.
    """

    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgb must have shape (height, width, 3)")
    rows, columns = grid_shape
    if rows <= 0 or columns <= 0:
        raise ValueError("grid dimensions must be positive")
    if not 0.0 <= inset_fraction < 0.5:
        raise ValueError("inset_fraction must be in [0, 0.5)")

    y_edges = np.linspace(0.0, rgb.shape[0], rows + 1)
    x_edges = np.linspace(0.0, rgb.shape[1], columns + 1)
    cell_colors = np.empty((rows, columns, 3), dtype=np.uint8)
    for row in range(rows):
        for column in range(columns):
            y0, y1 = y_edges[row : row + 2]
            x0, x1 = x_edges[column : column + 2]
            top = int(np.ceil(y0 + inset_fraction * (y1 - y0)))
            bottom = int(np.floor(y1 - inset_fraction * (y1 - y0)))
            left = int(np.ceil(x0 + inset_fraction * (x1 - x0)))
            right = int(np.floor(x1 - inset_fraction * (x1 - x0)))
            if bottom <= top or right <= left:
                raise ValueError("grid cells are too small for the requested inset")
            median_rgb = np.median(rgb[top:bottom, left:right], axis=(0, 1))
            cell_colors[row, column] = np.clip(np.rint(median_rgb), 0, 255).astype(np.uint8)

    values, palette_distance = decode_scalar_field(cell_colors, palette)
    if flip_vertical:
        values = np.flipud(values)
        palette_distance = np.flipud(palette_distance)
    return values, palette_distance


def comparison_mask(
    shape: tuple[int, int],
    exclude_boxes: Iterable[Sequence[int]],
) -> NDArray[np.bool_]:
    mask = np.ones(shape, dtype=bool)
    height, width = shape
    for box in exclude_boxes:
        left, top, right, bottom = (int(value) for value in box)
        if top < 0:
            top = height + top
        if bottom <= 0:
            bottom = height + bottom
        left = max(0, left)
        top = max(0, top)
        right = min(width, right)
        bottom = min(height, bottom)
        mask[top:bottom, left:right] = False
    return mask


def normalized_off_diagonal_correlator(values: FloatArray) -> FloatArray:
    """Apply the paper's S20 display rule and normalize the remaining field."""

    if values.ndim != 2 or values.shape[0] != values.shape[1]:
        raise ValueError("correlator must be a square matrix")
    result = np.array(values, dtype=np.float64, copy=True)
    np.fill_diagonal(result, 0.0)
    maximum = float(np.max(result))
    return result / maximum if maximum else result


def _correlation(left: FloatArray, right: FloatArray) -> float:
    left_centered = left - np.mean(left)
    right_centered = right - np.mean(right)
    denominator = np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    if denominator < 1.0e-15:
        # Correlation is undefined for flat fields.  Use their absolute
        # agreement so identical or palette-quantized flat gradients are not
        # incorrectly scored as unrelated.
        return float(np.clip(1.0 - 10.0 * np.mean(np.abs(left - right)), -1.0, 1.0))
    return float(np.dot(left_centered, right_centered) / denominator)


def _global_ssim(left: FloatArray, right: FloatArray) -> float:
    mean_left = float(np.mean(left))
    mean_right = float(np.mean(right))
    variance_left = float(np.var(left))
    variance_right = float(np.var(right))
    covariance = float(np.mean((left - mean_left) * (right - mean_right)))
    c1 = 0.01**2
    c2 = 0.03**2
    numerator = (2.0 * mean_left * mean_right + c1) * (2.0 * covariance + c2)
    denominator = (mean_left**2 + mean_right**2 + c1) * (
        variance_left + variance_right + c2
    )
    return numerator / denominator if denominator else 1.0


def compare_digitized_grids(
    reference: FloatArray,
    generated: FloatArray,
    mask: NDArray[np.bool_] | None = None,
) -> DigitizedGridMetrics:
    """Compare source-digitized and generated physics cells directly."""

    if reference.shape != generated.shape or reference.ndim != 2:
        raise ValueError("reference and generated must be equally shaped 2-D grids")
    selected = np.ones(reference.shape, dtype=bool) if mask is None else mask
    if selected.shape != reference.shape or not np.any(selected):
        raise ValueError("mask must select at least one cell from the grid")
    ref_values = reference[selected]
    gen_values = generated[selected]
    absolute_error = np.abs(ref_values - gen_values)
    pearson = _correlation(ref_values, gen_values)
    ssim = _global_ssim(ref_values, gen_values)
    components = np.asarray(
        [
            1.0 - float(np.mean(absolute_error)),
            (pearson + 1.0) / 2.0,
            (ssim + 1.0) / 2.0,
        ]
    )
    weights = np.asarray([0.40, 0.30, 0.30])
    return DigitizedGridMetrics(
        valid_cell_count=int(np.sum(selected)),
        mae=float(np.mean(absolute_error)),
        rmse=float(np.sqrt(np.mean((ref_values - gen_values) ** 2))),
        pearson_r=pearson,
        global_ssim=ssim,
        pattern_similarity_percent=100.0
        * float(np.dot(np.clip(components, 0.0, 1.0), weights)),
    )


def compare_scalar_field(
    reference_rgb: ByteArray,
    generated_normalized: FloatArray,
    palette: ByteArray,
    mask: NDArray[np.bool_],
) -> tuple[PixelMetrics, FloatArray, ByteArray]:
    """Compare literal colors and colorbar-decoded scalar patterns."""

    if reference_rgb.shape[:2] != generated_normalized.shape or reference_rgb.shape[:2] != mask.shape:
        raise ValueError("reference, generated field, and mask must share a shape")
    decoded_reference, palette_distance = decode_scalar_field(reference_rgb, palette)
    generated_rgb = colorize_scalar_field(generated_normalized, palette)
    ref_values = decoded_reference[mask]
    gen_values = generated_normalized[mask]
    absolute_error = np.abs(ref_values - gen_values)
    rgb_error = np.abs(reference_rgb.astype(np.float64) - generated_rgb.astype(np.float64))
    literal_similarity = 1.0 - float(np.mean(rgb_error[mask])) / 255.0
    pearson = _correlation(ref_values, gen_values)
    ssim = _global_ssim(ref_values, gen_values)

    ref_gradient = np.hypot(*np.gradient(decoded_reference))
    gen_gradient = np.hypot(*np.gradient(generated_normalized))
    gradient_r = _correlation(ref_gradient[mask], gen_gradient[mask])
    components = np.asarray(
        [
            literal_similarity,
            1.0 - float(np.mean(absolute_error)),
            (pearson + 1.0) / 2.0,
            (ssim + 1.0) / 2.0,
            (gradient_r + 1.0) / 2.0,
        ]
    )
    weights = np.asarray([0.15, 0.25, 0.25, 0.25, 0.10])
    similarity = 100.0 * float(np.dot(np.clip(components, 0.0, 1.0), weights))
    metrics = PixelMetrics(
        valid_pixel_count=int(np.sum(mask)),
        literal_rgb_similarity=literal_similarity,
        decoded_mae=float(np.mean(absolute_error)),
        decoded_rmse=float(np.sqrt(np.mean((ref_values - gen_values) ** 2))),
        decoded_pearson_r=pearson,
        decoded_global_ssim=ssim,
        decoded_gradient_r=gradient_r,
        pattern_similarity_percent=similarity,
        mean_palette_distance_rgb=float(np.mean(palette_distance[mask])),
    )
    return metrics, decoded_reference, generated_rgb


def crop_reference(target: ScalarFieldTarget) -> ByteArray:
    page = Image.open(target.reference_image).convert("RGB")
    return np.asarray(page.crop(target.data_box), dtype=np.uint8)


def compare_target(
    target: ScalarFieldTarget,
    palette: ByteArray,
) -> tuple[PixelMetrics, ByteArray, FloatArray, FloatArray, ByteArray]:
    reference_rgb = crop_reference(target)
    generated = rasterize_scalar_field(
        target.values,
        reference_rgb.shape[:2],
        target.vmin,
        target.vmax,
        flip_vertical=target.flip_vertical,
        smooth_vertical=target.smooth_vertical,
    )
    mask = comparison_mask(reference_rgb.shape[:2], target.exclude_boxes)
    metrics, decoded_reference, generated_rgb = compare_scalar_field(
        reference_rgb,
        generated,
        palette,
        mask,
    )
    return metrics, reference_rgb, decoded_reference, generated, generated_rgb
