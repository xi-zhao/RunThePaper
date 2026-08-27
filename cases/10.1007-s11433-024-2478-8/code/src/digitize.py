"""Digitize the published Fig. 3 curves from the raster page image.

The paper's figures are raster (no vector paths), so curves are recovered by
colour segmentation inside each panel's plot box, then mapped from pixels to data
coordinates using axis-tick anchors detected on the high-resolution image
(2559x2399). Tick pixel positions and their known data values are recorded below;
`scripts/detect_fig3_axes.py` re-derives them from the image for reproducibility.

Reference image: internal-paper-reference/page5_img56.png
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


def _lin(p0, v0, p1, v1):
    """Return a function mapping pixel -> data value from two tick anchors."""
    slope = (v1 - v0) / (p1 - p0)
    return lambda px: v0 + (px - p0) * slope


@dataclass
class Axis:
    px_to_val: object


# Plot boxes (x0, y0, x1, y1) in pixels, and axis calibrations per panel.
# x anchors: left-column ticks 215->0.0, 1136->0.25; right-column 1475->0.0, 2396->0.25.
_XL = _lin(215, 0.0, 1136, 0.25)
_XR = _lin(1475, 0.0, 2396, 0.25)

PANELS = {
    # hybrid column (a,b,c)
    "a": {"box": (170, 83, 1181, 721), "x": _XL,
          "yL": _lin(164, 15.0, 721, 0.0), "yR": _lin(192, 15.0, 644, -5.0)},
    "b": {"box": (170, 856, 1181, 1494), "x": _XL,
          "yL": _lin(884, 1.0, 1375, 0.2)},
    "c": {"box": (170, 1629, 1181, 2267), "x": _XL,
          "yL": _lin(1670, 3.0, 2226, -3.0)},
    # amplitude column (d,e,f)
    "d": {"box": (1430, 83, 2441, 721), "x": _XR,
          "yL": _lin(128, 30.0, 721, 0.0), "yR": _lin(158, 9.0, 588, 6.0)},
    "e": {"box": (1430, 856, 2441, 1494), "x": _XR,
          "yL": _lin(884, 1.0, 1466, 0.0)},
    "f": {"box": (1430, 1629, 2441, 2267), "x": _XR,
          "yL": _lin(1670, 3.0, 2226, -3.0)},
}

# Reference RGB colours per curve (sampled from the image).
COLORS = {
    "omega1": (10, 100, 175),    # blue solid
    "omega2": (230, 110, 10),    # orange dash-dot
    "delta1": (30, 150, 30),     # green dash-dot
    "delta2": (200, 25, 25),     # dark-red dashed
    "P00":    (135, 85, 175),    # purple solid
    "P01":    (110, 55, 50),     # brown dashed
    "P11":    (215, 110, 190),   # pink dash-dot
}


def load_image(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def _color_mask(rgb, ref, tol=55):
    d = np.abs(rgb - np.array(ref)).sum(2)
    mx = rgb.max(2); mn = rgb.min(2)
    sat = mx - mn
    return (d < tol) & (sat > 35)


def digitize_curve(img, panel, curve, axis="yL", tol=55, min_pts=4):
    """Return (x_data, y_data) for one coloured curve in a panel.

    For each pixel column inside the plot box, take the median row of matching
    pixels and convert to data coordinates. Columns with too few matches are
    skipped (handles dashed lines).
    """
    p = PANELS[panel]
    x0, y0, x1, y1 = p["box"]
    ref = COLORS[curve]
    mask = _color_mask(img[y0:y1, x0:x1], ref, tol)
    xmap, ymap = p["x"], p[axis]
    xs, ys = [], []
    for col in range(mask.shape[1]):
        rows = np.nonzero(mask[:, col])[0]
        if rows.size < 2:
            continue
        py = y0 + float(np.median(rows))
        xs.append(xmap(x0 + col))
        ys.append(ymap(py))
    xs, ys = np.array(xs), np.array(ys)
    if xs.size < min_pts:
        return xs, ys
    order = np.argsort(xs)
    return xs[order], ys[order]
