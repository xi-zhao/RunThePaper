"""Run the hydration-cost controls with no structure download."""

import json
from pathlib import Path

from generate import assemble, exhaustive


def main():
    config = json.loads(Path("config/protocol.json").read_text())
    results = {}
    for name, density_variance in (("nominal", config["density_variance"]),
                                   ("narrow", config["narrow_density_variance"])):
        points, amplitudes, quadratic, convergence = assemble({**config, "density_variance": density_variance})
        results[name] = {"points": points.tolist(), "amplitudes": amplitudes.tolist(),
                         "matrix": quadratic.tolist(), "numeric": convergence, "exact": exhaustive(quadratic)}
    Path("results/cost-controls.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
