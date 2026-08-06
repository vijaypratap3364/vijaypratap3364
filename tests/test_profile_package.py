from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunabot.renderer import render_lunabot


class ProfilePackageTests(unittest.TestCase):
    def test_readme_references_existing_hero(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("./assets/lunabot.gif", readme)
        self.assertIn("./assets/mission-telemetry.png", readme)
        self.assertIn("./assets/mission-output.png", readme)
        self.assertIn("singhvijaypratap1011@gmail.com", readme)
        self.assertIn("vijay-pratap-singh-", readme)
        self.assertTrue((ROOT / "assets/lunabot.gif").exists())

    def test_renderer_outputs_animated_gif(self) -> None:
        calendar = json.loads(
            (ROOT / "output/contributions.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_directory:
            temp = Path(temp_directory)
            gif_path = temp / "test.gif"
            png_path = temp / "test.png"
            mission_path = temp / "mission.json"
            telemetry_path = temp / "telemetry.png"
            result_path = temp / "result.png"
            render_lunabot(
                calendar,
                gif_path=gif_path,
                png_path=png_path,
                mission_path=mission_path,
                telemetry_path=telemetry_path,
                result_path=result_path,
                frame_duration_ms=40,
                max_targets=8,
            )
            with Image.open(gif_path) as image:
                self.assertTrue(getattr(image, "is_animated", False))
                self.assertGreaterEqual(image.n_frames, 2)
            self.assertTrue(png_path.exists())
            self.assertTrue(mission_path.exists())
            self.assertTrue(telemetry_path.exists())
            self.assertTrue(result_path.exists())


if __name__ == "__main__":
    unittest.main()
