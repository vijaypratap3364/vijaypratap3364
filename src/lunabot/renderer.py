from __future__ import annotations

from pathlib import Path
import hashlib
import math
import random

from PIL import Image, ImageDraw, ImageFont

from .contributions import calendar_grid
from .pathfinding import (
    Deposit,
    GridPoint,
    build_route,
    choose_priority_targets,
    expand_route_to_steps,
    extract_deposits,
    first_visit_steps,
)


WIDTH = 1000
HEIGHT = 466
GRID_X = 478
GRID_Y = 261
GRID_PITCH = 9.25
CELL_SIZE = 7
BASE_POINT = GridPoint(-4, 5)

PALETTE = {
    0: "#182331",
    1: "#174d48",
    2: "#1a7964",
    3: "#21aa7a",
    4: "#48e49e",
}


def _font(size: int, *, mono: bool = False, bold: bool = False) -> ImageFont.ImageFont:
    candidates: list[str] = []
    if mono:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
                if bold
                else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            ]
        )

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_8_MONO = _font(8, mono=True)
FONT_9_MONO = _font(9, mono=True)
FONT_10_MONO = _font(10, mono=True)
FONT_11_MONO = _font(11, mono=True, bold=True)
FONT_12 = _font(12)
FONT_13 = _font(13)
FONT_14 = _font(14)
FONT_16_BOLD = _font(16, bold=True)
FONT_22_BOLD = _font(22, bold=True)
FONT_28_BOLD = _font(28, bold=True)


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _blend(
    left: tuple[int, int, int],
    right: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    return tuple(
        round(left[index] * (1.0 - ratio) + right[index] * ratio)
        for index in range(3)
    )


def _gradient_background() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    top = _hex("#070b12")
    middle = _hex("#0d1117")
    bottom = _hex("#111827")
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)
        if ratio < 0.58:
            color = _blend(top, middle, ratio / 0.58)
        else:
            color = _blend(middle, bottom, (ratio - 0.58) / 0.42)
        for x in range(WIDTH):
            pixels[x, y] = color
    return image


def _grid_center(point: GridPoint) -> tuple[float, float]:
    return (
        GRID_X + point.col * GRID_PITCH + CELL_SIZE / 2,
        GRID_Y + point.row * GRID_PITCH + CELL_SIZE / 2,
    )


def _draw_stars(draw: ImageDraw.ImageDraw, username: str) -> None:
    seed = int(hashlib.sha256(username.encode("utf-8")).hexdigest()[:8], 16)
    randomizer = random.Random(seed)
    for _ in range(72):
        x = randomizer.randint(8, WIDTH - 8)
        y = randomizer.randint(8, 250)
        radius = randomizer.choice([1, 1, 1, 2])
        shade = randomizer.choice(["#6e8496", "#a7bac8", "#d9f7ff"])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=shade)


def _panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    radius: int = 14,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill="#0c1420",
        outline="#26364a",
        width=1,
    )


def _draw_static_layout(
    calendar: dict,
    route_steps: list[GridPoint],
    target_keys: set[tuple[int, int]],
) -> Image.Image:
    image = _gradient_background()
    draw = ImageDraw.Draw(image)
    _draw_stars(draw, str(calendar["username"]))

    # Faint engineering grid
    for x in range(0, WIDTH, 28):
        draw.line((x, 0, x, HEIGHT), fill="#111b2a", width=1)
    for y in range(0, HEIGHT, 28):
        draw.line((0, y, WIDTH, y), fill="#111b2a", width=1)

    draw.text(
        (36, 27),
        "LUNABOT // CONTRIBUTION MINING SYSTEM",
        font=FONT_11_MONO,
        fill="#7ee7ff",
    )
    draw.ellipse((922, 26, 932, 36), fill="#2ee6a6")
    draw.text((940, 25), "ONLINE", font=FONT_10_MONO, fill="#a9bac8")

    _panel(draw, (34, 55, 438, 218))
    draw.line((34, 74, 34, 95), fill="#55d9ff", width=2)
    draw.line((34, 55, 142, 55), fill="#55d9ff", width=2)

    draw.text((56, 76), "Vijay Pratap Singh", font=FONT_28_BOLD, fill="#f4f8fb")
    draw.text(
        (56, 112),
        "Computer Science Student @ Illinois Tech",
        font=FONT_13,
        fill="#90a7b8",
    )
    draw.text(
        (56, 134),
        "AI/ML  •  Backend  •  Robotics",
        font=FONT_11_MONO,
        fill="#62ddff",
    )
    draw.text((56, 169), "CURRENT MISSION", font=FONT_9_MONO, fill="#b690ff")
    draw.text(
        (56, 190),
        "Building real-world AI/ML and software systems",
        font=FONT_12,
        fill="#d8e4ec",
    )

    _panel(draw, (457, 55, 966, 218))
    draw.text((480, 78), "MISSION TELEMETRY", font=FONT_10_MONO, fill="#9bb0bf")
    draw.text(
        (480, 108),
        str(calendar["totalContributions"]),
        font=FONT_28_BOLD,
        fill="#f4f8fb",
    )
    draw.text((555, 112), "PUBLIC CONTRIBUTIONS", font=FONT_10_MONO, fill="#7f95a7")

    draw.line((730, 95, 730, 146), fill="#2a394a", width=1)
    draw.text((754, 103), "ROVER", font=FONT_9_MONO, fill="#61ddff")
    draw.text((754, 125), "VPS-1", font=FONT_16_BOLD, fill="#f4f8fb")

    draw.line((842, 95, 842, 146), fill="#2a394a", width=1)
    draw.text((866, 103), "ACTIVE DAYS", font=FONT_9_MONO, fill="#b690ff")
    draw.text(
        (866, 125),
        str(calendar["stats"]["activeDays"]),
        font=FONT_16_BOLD,
        fill="#f4f8fb",
    )

    chips = [
        ("ISSUE LOCALIZER", 480, 169, 111),
        ("FRAUD DETECTION", 598, 169, 113),
        ("MLOPS ROUTER", 718, 169, 98),
        ("ROBOTICS", 823, 169, 77),
    ]
    for label, x, y, width in chips:
        draw.rounded_rectangle(
            (x, y, x + width, y + 24),
            radius=12,
            fill="#111d2a",
            outline="#2a4d63",
        )
        draw.ellipse((x + 10, y + 10, x + 16, y + 16), fill="#56dfff")
        draw.text((x + 23, y + 7), label, font=FONT_8_MONO, fill="#bdd0dc")

    # Moon surface
    moon = [
        (0, 322),
        (130, 295),
        (265, 316),
        (390, 300),
        (540, 282),
        (700, 314),
        (850, 289),
        (1000, 274),
        (1000, HEIGHT),
        (0, HEIGHT),
    ]
    draw.polygon(moon, fill="#172130")
    draw.line(moon[:8], fill="#34465d", width=2)
    draw.ellipse((92, 375, 194, 398), fill="#0b1018")
    draw.ellipse((834, 381, 956, 407), fill="#0b1018")
    draw.ellipse((612, 413, 680, 430), fill="#0b1018")

    # Base station
    base_x, base_y = _grid_center(BASE_POINT)
    bx, by = int(base_x - 18), int(base_y + 20)
    draw.rounded_rectangle((bx - 31, by - 17, bx + 35, by + 20), radius=7, fill="#0b1320", outline="#355069")
    draw.rounded_rectangle((bx - 23, by - 9, bx - 5, by + 2), radius=3, fill="#111d2a", outline="#56ddff")
    draw.rounded_rectangle((bx + 1, by - 9, bx + 27, by + 2), radius=3, fill="#111d2a", outline="#8f7cff")
    draw.line((bx - 21, by + 12, bx + 27, by + 12), fill="#4a5f74", width=3)
    draw.ellipse((bx + 28, by - 15, bx + 36, by - 7), fill="#2ee6a6")
    draw.text((bx - 11, by - 32), "BASE", font=FONT_8_MONO, fill="#8fa7b9")

    # Full contribution grid
    grid = calendar_grid(calendar)
    for col, week in enumerate(grid):
        for row, day in enumerate(week):
            x = int(GRID_X + col * GRID_PITCH)
            y = int(GRID_Y + row * GRID_PITCH)
            level = int(day["level"])
            fill = PALETTE.get(level, PALETTE[0])
            draw.rounded_rectangle(
                (x, y, x + CELL_SIZE, y + CELL_SIZE),
                radius=2,
                fill=fill,
            )
            if (col, row) in target_keys:
                draw.rounded_rectangle(
                    (x - 1, y - 1, x + CELL_SIZE + 1, y + CELL_SIZE + 1),
                    radius=3,
                    outline="#5addff",
                    width=1,
                )

    # Faint complete route
    route_pixels = [_grid_center(point) for point in route_steps]
    if len(route_pixels) > 1:
        draw.line(route_pixels, fill="#33566a", width=1)

    # Lower panels
    _panel(draw, (38, 384, 300, 446))
    _panel(draw, (316, 384, 610, 446))
    _panel(draw, (626, 384, 962, 446))

    draw.text((58, 400), "MINING PAYLOAD", font=FONT_9_MONO, fill="#8aa3b4")
    draw.text((338, 400), "ROUTE INTELLIGENCE", font=FONT_9_MONO, fill="#8aa3b4")
    draw.text((648, 400), "BASE MODULES", font=FONT_9_MONO, fill="#8aa3b4")

    return image


def _draw_rover(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    *,
    direction: int,
) -> None:
    cx, cy = center
    scale = 0.72

    def px(value: float) -> float:
        return cx + direction * value * scale

    def py(value: float) -> float:
        return cy + value * scale

    # Shadow
    draw.ellipse(
        (cx - 31 * scale, cy + 24 * scale, cx + 31 * scale, cy + 34 * scale),
        fill="#070b12",
    )

    # Wheels
    for offset_x, offset_y, radius in [(-21, 20, 8), (0, 23, 9), (21, 19, 8)]:
        wheel_x = px(offset_x)
        wheel_y = py(offset_y)
        draw.ellipse(
            (
                wheel_x - radius * scale,
                wheel_y - radius * scale,
                wheel_x + radius * scale,
                wheel_y + radius * scale,
            ),
            fill="#101822",
            outline="#6a8092",
            width=2,
        )
        hub = 3.2 * scale
        draw.ellipse(
            (wheel_x - hub, wheel_y - hub, wheel_x + hub, wheel_y + hub),
            fill="#778c9c",
        )

    # Suspension
    suspension = [
        (px(-21), py(11)),
        (px(-9), py(4)),
        (px(0), py(15)),
        (px(13), py(3)),
        (px(23), py(11)),
    ]
    draw.line(suspension, fill="#8196a6", width=3, joint="curve")

    # Body
    body_left = min(px(-28), px(28))
    body_right = max(px(-28), px(28))
    draw.rounded_rectangle(
        (body_left, py(-6), body_right, py(12)),
        radius=6,
        fill="#91a6b6",
        outline="#dce7ee",
        width=1,
    )
    screen_left = min(px(-21), px(6))
    screen_right = max(px(-21), px(6))
    draw.rounded_rectangle(
        (screen_left, py(-1), screen_right, py(7)),
        radius=3,
        fill="#132635",
        outline="#57ddff",
        width=1,
    )
    draw.text(
        (min(px(-17), px(3)), py(0)),
        "VPS-1",
        font=FONT_8_MONO,
        fill="#74e7ff",
    )

    # Camera mast
    draw.line((px(-4), py(-6), px(-4), py(-18)), fill="#a9bbc8", width=3)
    cam_left = min(px(-13), px(5))
    cam_right = max(px(-13), px(5))
    draw.rounded_rectangle(
        (cam_left, py(-25), cam_right, py(-16)),
        radius=3,
        fill="#90a5b5",
        outline="#dce7ee",
    )
    lens_x = px(1)
    draw.ellipse(
        (lens_x - 2.4, py(-22) - 2.4, lens_x + 2.4, py(-22) + 2.4),
        fill="#56dfff",
    )

    # Solar wing
    wing = [
        (px(-25), py(-2)),
        (px(-49), py(-11)),
        (px(-42), py(-22)),
        (px(-17), py(-8)),
    ]
    draw.polygon(wing, fill="#152c46", outline="#5bbfe8")

    # Mining arm
    arm_start = (px(28), py(0))
    elbow = (px(42), py(7))
    tip = (px(50), py(20))
    draw.line((arm_start, elbow, tip), fill="#c0cfd8", width=4, joint="curve")
    draw.ellipse((elbow[0] - 3, elbow[1] - 3, elbow[0] + 3, elbow[1] + 3), fill="#647b8d")
    draw.line(
        (tip[0], tip[1], px(57), py(25)),
        fill="#62dfff",
        width=2,
    )


def _ease(value: float) -> float:
    return 3 * value * value - 2 * value * value * value


def render_lunabot(
    calendar: dict,
    *,
    gif_path: Path,
    png_path: Path,
    mission_path: Path,
    frame_count: int = 52,
    frame_duration_ms: int = 105,
    max_targets: int = 24,
) -> dict:
    deposits = extract_deposits(calendar)
    targets = choose_priority_targets(deposits, max_targets=max_targets)
    coarse_route = build_route(BASE_POINT, targets, return_to_base=True)
    route_steps = expand_route_to_steps(coarse_route)
    visits = first_visit_steps(route_steps, targets)
    target_lookup = {(target.col, target.row): target for target in targets}
    target_keys = set(target_lookup)
    crystal = max(targets, key=lambda target: (target.level, target.count), default=None)

    if not route_steps:
        route_steps = [BASE_POINT]

    base_image = _draw_static_layout(calendar, route_steps, target_keys)
    frames: list[Image.Image] = []
    route_pixels = [_grid_center(point) for point in route_steps]

    idle_frames = max(3, frame_count // 10)
    finish_frames = max(5, frame_count // 8)
    travel_frames = frame_count - idle_frames - finish_frames
    total_payload = sum(target.count for target in targets)

    for frame_index in range(frame_count):
        frame = base_image.copy()
        draw = ImageDraw.Draw(frame)

        if frame_index < idle_frames:
            route_index = 0
            phase = "SCANNING"
            finish_ratio = 0.0
        elif frame_index < idle_frames + travel_frames:
            ratio = (frame_index - idle_frames) / max(1, travel_frames - 1)
            route_index = round(_ease(ratio) * (len(route_steps) - 1))
            phase = "MINING"
            finish_ratio = 0.0
        else:
            route_index = len(route_steps) - 1
            phase = "MISSION COMPLETE"
            finish_ratio = (frame_index - idle_frames - travel_frames) / max(1, finish_frames - 1)

        mined_keys = {
            key
            for key, first_step in visits.items()
            if first_step <= route_index
        }

        # Redraw target cells based on mining status
        for key, target in target_lookup.items():
            x = int(GRID_X + target.col * GRID_PITCH)
            y = int(GRID_Y + target.row * GRID_PITCH)
            if key in mined_keys:
                draw.rounded_rectangle(
                    (x, y, x + CELL_SIZE, y + CELL_SIZE),
                    radius=2,
                    fill="#20313a",
                    outline="#3f6571",
                )
            else:
                draw.rounded_rectangle(
                    (x, y, x + CELL_SIZE, y + CELL_SIZE),
                    radius=2,
                    fill=PALETTE[target.level],
                    outline="#5addff",
                )

        # Rare crystal
        if crystal is not None and (crystal.col, crystal.row) not in mined_keys:
            crystal_x, crystal_y = _grid_center(GridPoint(crystal.col, crystal.row))
            pulse = 1 + 0.18 * math.sin(frame_index * 0.8)
            radius = 7 * pulse
            draw.polygon(
                [
                    (crystal_x, crystal_y - radius),
                    (crystal_x + radius * 0.8, crystal_y),
                    (crystal_x + radius * 0.2, crystal_y + radius),
                    (crystal_x - radius * 0.8, crystal_y + 1),
                ],
                fill="#a979ff",
                outline="#e0d0ff",
            )

        # Completed path
        if route_index > 0:
            draw.line(route_pixels[: route_index + 1], fill="#6fe7ff", width=2)

        # Mining sparks at newly reached target
        current_point = route_steps[route_index]
        current_key = (current_point.col, current_point.row)
        if current_key in target_lookup and abs(visits[current_key] - route_index) <= 1:
            spark_x, spark_y = _grid_center(current_point)
            for angle in range(0, 360, 60):
                length = 7 + (frame_index % 3)
                end_x = spark_x + math.cos(math.radians(angle)) * length
                end_y = spark_y + math.sin(math.radians(angle)) * length
                draw.line((spark_x, spark_y, end_x, end_y), fill="#b6f5ff", width=1)

        # Rover orientation
        if route_index < len(route_steps) - 1:
            next_point = route_steps[route_index + 1]
        elif route_index > 0:
            next_point = route_steps[route_index - 1]
        else:
            next_point = current_point
        direction = 1 if next_point.col >= current_point.col else -1
        rover_center = _grid_center(current_point)
        _draw_rover(draw, rover_center, direction=direction)

        # Dynamic status and payload
        mined_payload = sum(
            target_lookup[key].count
            for key in mined_keys
        )
        payload_ratio = mined_payload / max(1, total_payload)
        draw.rounded_rectangle((58, 420, 270, 431), radius=6, fill="#09121c", outline="#32465a")
        draw.rounded_rectangle(
            (58, 420, 58 + round(212 * payload_ratio), 431),
            radius=6,
            fill="#4be39d",
        )
        draw.text(
            (58, 436),
            f"{len(mined_keys):02d}/{len(targets):02d} deposits  •  {mined_payload}/{total_payload} units",
            font=FONT_9_MONO,
            fill="#dbe7ee",
        )

        draw.text(
            (338, 421),
            f"STATUS: {phase}",
            font=FONT_10_MONO,
            fill="#dbe7ee",
        )
        draw.text(
            (338, 438),
            f"ROUTE {route_index:03d}/{len(route_steps)-1:03d}  •  RETURN TO BASE: YES",
            font=FONT_8_MONO,
            fill="#7f94a5",
        )

        modules = [
            ("AI LAB", 648),
            ("ROBOTICS", 724),
            ("BACKEND", 814),
            ("MLOPS", 899),
        ]
        for module_index, (label, x) in enumerate(modules):
            active = finish_ratio >= module_index / max(1, len(modules) - 1)
            outline = "#57ddff" if active else "#2a4d63"
            indicator = "#2ee6a6" if active else "#425566"
            draw.rounded_rectangle((x, 417, x + 70, 438), radius=10, fill="#111d2a", outline=outline)
            draw.ellipse((x + 8, 425, x + 14, 431), fill=indicator)
            draw.text((x + 19, 423), label, font=FONT_8_MONO, fill="#c4d4de")

        frames.append(frame)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    mission_path.parent.mkdir(parents=True, exist_ok=True)

    preview_index = min(len(frames) - 1, idle_frames + max(1, travel_frames // 2))
    frames[preview_index].save(png_path, format="PNG", optimize=True)

    quantized = [
        frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        for frame in frames
    ]
    quantized[0].save(
        gif_path,
        format="GIF",
        save_all=True,
        append_images=quantized[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )

    mission = {
        "username": calendar["username"],
        "totalContributions": calendar["totalContributions"],
        "activeDays": calendar["stats"]["activeDays"],
        "selectedTargets": len(targets),
        "routeStops": max(0, len(coarse_route) - 2),
        "routeSteps": len(route_steps),
        "payloadUnits": total_payload,
        "returnsToBase": coarse_route[-1] == BASE_POINT,
        "heroFormat": "animated-gif",
        "frameCount": frame_count,
        "frameDurationMs": frame_duration_ms,
    }
    mission_path.write_text(
        __import__("json").dumps(mission, indent=2) + "\n",
        encoding="utf-8",
    )
    return mission
