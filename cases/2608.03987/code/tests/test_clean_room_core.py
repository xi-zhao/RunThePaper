from __future__ import annotations

import sys
import unittest
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT / "src"))

from independent_tn import (  # noqa: E402
    ContractionTree,
    build_qsim_network,
    exact_optimum,
    optimize_network,
)


class CleanRoomCostModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.network = build_qsim_network(
            "tiny",
            "random",
            """2
0 h 0
0 h 1
1 t 0
2 cz 0 1
3 x_1_2 1
""",
        )

    def test_exact_cost_obeys_realification_law(self) -> None:
        optimum, tree = exact_optimum(self.network, "real")
        stats = tree.statistics()
        self.assertEqual(optimum, stats.real_volume)
        self.assertAlmostEqual(stats.overhead, 1.0 + 2.0 * stats.m + stats.r, 15)
        self.assertEqual(stats.merge_nodes, self.network.green_leaves - 1)

    def test_nni_preserves_tree_and_best_objective(self) -> None:
        tree = ContractionTree.greedy(self.network, "real", seed=7)
        initial = tree.real_total
        trace = tree.anneal("real", steps=5_000, seed=11)
        tree.validate()
        self.assertLessEqual(tree.real_total, initial)
        self.assertEqual(tree.real_total, trace["best"])

    def test_seeded_optimizer_is_plan_deterministic(self) -> None:
        kwargs = dict(
            greedy_trials=2,
            anneal_steps=2_000,
            polish_steps=500,
            seed=42,
        )
        first = optimize_network(self.network, **kwargs)
        second = optimize_network(self.network, **kwargs)
        for strategy in ("convert_only", "polished", "full_anneal"):
            self.assertEqual(
                first["plans"][strategy]["sha256"],
                second["plans"][strategy]["sha256"],
            )


if __name__ == "__main__":
    unittest.main()
