#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lunabot.contributions import normalize_graphql_response


GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

QUERY = """
query LunabotContributionCalendar(
  $login: String!,
  $from: DateTime!,
  $to: DateTime!
) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      startedAt
      endedAt
      contributionCalendar {
        totalContributions
        colors
        weeks {
          firstDay
          contributionDays {
            date
            weekday
            contributionCount
            contributionLevel
            color
          }
        }
      }
    }
  }
}
"""


def iso_range(days: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days - 1)
    return (
        start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat(),
    )


def fetch_calendar(username: str, token: str, days: int) -> dict:
    date_from, date_to = iso_range(days)
    body = json.dumps(
        {
            "query": QUERY,
            "variables": {
                "login": username,
                "from": date_from,
                "to": date_to,
            },
        }
    ).encode("utf-8")

    request = Request(
        GRAPHQL_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "vijaypratap3364-lunabot",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub API returned HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach GitHub GraphQL: {exc.reason}"
        ) from exc

    return normalize_graphql_response(payload, username)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Vijay's public GitHub contribution calendar."
    )
    parser.add_argument("--username", default="vijaypratap3364")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "output" / "contributions.json",
    )
    args = parser.parse_args()

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        parser.error(
            "Set GH_TOKEN or GITHUB_TOKEN. GitHub Actions supplies "
            "GITHUB_TOKEN automatically."
        )

    calendar = fetch_calendar(args.username, token, args.days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(calendar, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {calendar['totalContributions']} contributions "
        f"across {calendar['stats']['activeDays']} active days "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
