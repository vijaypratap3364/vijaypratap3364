from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunabot.pathfinding import (
    GridPoint,
    build_route,
    choose_priority_targets,
    expand_route_to_steps,
    extract_deposits,
    manhattan,
)


class PathfindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.calendar = json.loads(
            (ROOT / "output/contributions.json").read_text(encoding="utf-8")
        )
        cls.deposits = extract_deposits(cls.calendar)
        cls.targets = choose_priority_targets(cls.deposits, max_targets=12)

    def test_target_selection_is_bounded(self) -> None:
        self.assertEqual(len(self.targets), 12)
        self.assertTrue(all(target.count > 0 for target in self.targets))

    def test_route_returns_to_base(self) -> None:
        start = GridPoint(-4, 5)
        route = build_route(start, self.targets, return_to_base=True)
        self.assertEqual(route[0], start)
        self.assertEqual(route[-1], start)

    def test_expanded_route_moves_one_cell_at_a_time(self) -> None:
        start = GridPoint(-4, 5)
        route = build_route(start, self.targets, return_to_base=True)
        steps = expand_route_to_steps(route)
        for left, right in zip(steps, steps[1:]):
            self.assertEqual(manhattan(left, right), 1)


if __name__ == "__main__":
    unittest.main()
