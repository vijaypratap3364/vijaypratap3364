from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


LEVEL_TO_INT = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


@dataclass(frozen=True)
class ContributionDay:
    date: str
    weekday: int
    count: int
    level: int
    color: str

    @classmethod
    def from_graphql(cls, payload: dict[str, Any]) -> "ContributionDay":
        level_name = str(payload.get("contributionLevel", "NONE"))
        if level_name not in LEVEL_TO_INT:
            raise ValueError(f"Unknown GitHub contribution level: {level_name}")

        value = cls(
            date=str(payload["date"]),
            weekday=int(payload["weekday"]),
            count=int(payload["contributionCount"]),
            level=LEVEL_TO_INT[level_name],
            color=str(payload["color"]),
        )
        value.validate()
        return value

    def validate(self) -> None:
        date.fromisoformat(self.date)
        if self.weekday not in range(7):
            raise ValueError(f"weekday must be 0..6, got {self.weekday}")
        if self.count < 0:
            raise ValueError("contribution count cannot be negative")
        if self.level not in range(5):
            raise ValueError("contribution level must be 0..4")
        if not self.color.startswith("#") or len(self.color) not in {4, 7}:
            raise ValueError(f"invalid hex color: {self.color}")


def _longest_streak(days: list[ContributionDay]) -> int:
    best = 0
    current = 0
    for day in days:
        if day.count > 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _current_streak(days: list[ContributionDay]) -> int:
    current = 0
    for day in reversed(days):
        if day.count > 0:
            current += 1
        else:
            break
    return current


def normalize_graphql_response(payload: dict[str, Any], username: str) -> dict[str, Any]:
    errors = payload.get("errors")
    if errors:
        messages = "; ".join(str(item.get("message", item)) for item in errors)
        raise RuntimeError(f"GitHub GraphQL returned errors: {messages}")

    try:
        collection = payload["data"]["user"]["contributionsCollection"]
        calendar = collection["contributionCalendar"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Response does not contain a GitHub contribution calendar") from exc

    weeks_out: list[dict[str, Any]] = []
    flat_days: list[ContributionDay] = []

    for week_index, week in enumerate(calendar["weeks"]):
        week_days = [
            ContributionDay.from_graphql(raw_day)
            for raw_day in week["contributionDays"]
        ]
        flat_days.extend(week_days)
        weeks_out.append(
            {
                "index": week_index,
                "firstDay": str(week["firstDay"]),
                "days": [
                    {
                        "date": day.date,
                        "weekday": day.weekday,
                        "count": day.count,
                        "level": day.level,
                        "color": day.color,
                    }
                    for day in week_days
                ],
            }
        )

    flat_days.sort(key=lambda item: item.date)
    calculated_total = sum(day.count for day in flat_days)
    api_total = int(calendar["totalContributions"])

    if calculated_total != api_total:
        raise ValueError(
            f"Calendar total mismatch: days sum to {calculated_total}, "
            f"GitHub reports {api_total}"
        )

    active_days = [day for day in flat_days if day.count > 0]
    peak = max(flat_days, key=lambda item: item.count, default=None)

    normalized = {
        "schemaVersion": 1,
        "username": username,
        "source": "github-graphql",
        "range": {
            "from": str(collection["startedAt"]),
            "to": str(collection["endedAt"]),
        },
        "totalContributions": api_total,
        "colors": list(calendar["colors"]),
        "stats": {
            "dayCount": len(flat_days),
            "activeDays": len(active_days),
            "maxDailyContributions": peak.count if peak else 0,
            "maxContributionDate": peak.date if peak else None,
            "longestActiveStreak": _longest_streak(flat_days),
            "currentActiveStreak": _current_streak(flat_days),
        },
        "weeks": weeks_out,
    }
    validate_normalized_calendar(normalized)
    return normalized


def validate_normalized_calendar(calendar: dict[str, Any]) -> None:
    if calendar.get("schemaVersion") != 1:
        raise ValueError("Unsupported contribution calendar schema")

    weeks = calendar.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        raise ValueError("Calendar must contain at least one week")

    seen_dates: set[str] = set()
    total = 0

    for week in weeks:
        date.fromisoformat(str(week["firstDay"]))
        for raw_day in week["days"]:
            day = ContributionDay(
                date=str(raw_day["date"]),
                weekday=int(raw_day["weekday"]),
                count=int(raw_day["count"]),
                level=int(raw_day["level"]),
                color=str(raw_day["color"]),
            )
            day.validate()
            if day.date in seen_dates:
                raise ValueError(f"Duplicate contribution date: {day.date}")
            seen_dates.add(day.date)
            total += day.count

    if total != int(calendar["totalContributions"]):
        raise ValueError(
            f"Normalized total mismatch: days sum to {total}, "
            f"metadata reports {calendar['totalContributions']}"
        )


def calendar_grid(calendar: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Return a week-major grid with seven weekday rows per week."""
    grid: list[list[dict[str, Any]]] = []
    for week in calendar["weeks"]:
        rows: list[dict[str, Any]] = [
            {
                "date": "",
                "weekday": weekday,
                "count": 0,
                "level": 0,
                "color": "#161b22",
            }
            for weekday in range(7)
        ]
        for day in week["days"]:
            rows[int(day["weekday"])] = dict(day)
        grid.append(rows)
    return grid
