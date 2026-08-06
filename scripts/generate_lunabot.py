#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lunabot.contributions import validate_normalized_calendar
from lunabot.renderer import render_lunabot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the production Lunabot GIF and static fallback."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "output" / "contributions.json",
    )
    parser.add_argument(
        "--gif",
        type=Path,
        default=REPO_ROOT / "assets" / "lunabot.gif",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=REPO_ROOT / "assets" / "lunabot-static.png",
    )
    parser.add_argument(
        "--mission",
        type=Path,
        default=REPO_ROOT / "output" / "mission.json",
    )
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--frame-duration-ms", type=int, default=170)
    args = parser.parse_args()

    calendar = json.loads(args.input.read_text(encoding="utf-8"))
    validate_normalized_calendar(calendar)

    mission = render_lunabot(
        calendar,
        gif_path=args.gif,
        png_path=args.png,
        mission_path=args.mission,
        frame_count=args.frames,
        frame_duration_ms=args.frame_duration_ms,
    )
    print(json.dumps(mission, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
