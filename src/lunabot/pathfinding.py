from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GridPoint:
    col: int
    row: int


@dataclass(frozen=True)
class Deposit:
    col: int
    row: int
    count: int
    level: int


def manhattan(a: GridPoint, b: GridPoint) -> int:
    return abs(a.col - b.col) + abs(a.row - b.row)


def extract_deposits(calendar: dict) -> list[Deposit]:
    deposits: list[Deposit] = []
    for col, week in enumerate(calendar["weeks"]):
        for day in week["days"]:
            count = int(day["count"])
            if count > 0:
                deposits.append(
                    Deposit(
                        col=col,
                        row=int(day["weekday"]),
                        count=count,
                        level=int(day["level"]),
                    )
                )
    return deposits


def choose_priority_targets(
    deposits: Iterable[Deposit],
    max_targets: int = 24,
) -> list[Deposit]:
    """Choose high-value cells while keeping the target count bounded."""
    ranked = sorted(
        deposits,
        key=lambda deposit: (
            -deposit.level,
            -deposit.count,
            deposit.col,
            deposit.row,
        ),
    )
    return ranked[:max_targets]


def build_route(
    start: GridPoint,
    targets: list[Deposit],
    return_to_base: bool = True,
) -> list[GridPoint]:
    """Nearest-neighbor route with value-based tie breaking."""
    remaining = targets[:]
    route: list[GridPoint] = [start]
    current = start

    while remaining:
        best = min(
            remaining,
            key=lambda deposit: (
                manhattan(current, GridPoint(deposit.col, deposit.row)),
                -deposit.level,
                -deposit.count,
                deposit.col,
                deposit.row,
            ),
        )
        current = GridPoint(best.col, best.row)
        route.append(current)
        remaining.remove(best)

    if return_to_base:
        route.append(start)
    return route


def expand_route_to_steps(route: list[GridPoint]) -> list[GridPoint]:
    """Expand route stops into cardinal one-cell movement steps."""
    if not route:
        return []

    steps: list[GridPoint] = [route[0]]
    for start, end in zip(route, route[1:]):
        col, row = start.col, start.row
        while col != end.col:
            col += 1 if end.col > col else -1
            steps.append(GridPoint(col, row))
        while row != end.row:
            row += 1 if end.row > row else -1
            steps.append(GridPoint(col, row))
    return steps


def first_visit_steps(
    route_steps: list[GridPoint],
    targets: list[Deposit],
) -> dict[tuple[int, int], int]:
    target_keys = {(target.col, target.row) for target in targets}
    visits: dict[tuple[int, int], int] = {}
    for step_index, point in enumerate(route_steps):
        key = (point.col, point.row)
        if key in target_keys and key not in visits:
            visits[key] = step_index
    return visits
