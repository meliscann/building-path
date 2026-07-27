"""
grid_visualizer.py
─────────────────────────────────────────────────────────────
Renders ASCII grids from building_data.py as colour-coded PNG images.

Usage:
    python grid_visualizer.py                        # All floors
    python grid_visualizer.py lower_ground ground    # Selected floors
    python grid_visualizer.py lower_ground --show    # Display on screen
    python grid_visualizer.py --scale 4              # 4 px per cell
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Proje kökünü sys.path'e ekle (doğrudan çalıştırma için)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ─────────────────────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────────────────────
CELL_SIZE   = 4      # Her grid hücresi kaç piksel olacak
OUTPUT_DIR  = str(_ROOT / "grid_visuals")
# ─────────────────────────────────────────────────────────────

# Character → colour mapping (31 POI types + wall)
CHAR_COLORS = {
    "#":  (0,   0,   0),      # Wall — black
    ".":  (255, 236, 179),    # Corridor — cream
    "S":  (255, 193, 7),      # Stairs — amber
    "E":  (118, 255, 3),      # Elevator — bright green
    "N":  (213, 0,   0),      # Main entrance — red
    "X":  (230, 81,  0),      # Fire exit — deep orange
    "V":  (70,  70,  70),     # Courtyard — dark grey
    "T":  (158, 158, 158),    # Toilets — grey
    "O":  (3,   169, 244),    # Office — light blue
    "P":  (213, 0,   249),    # Support lab — purple
    "K":  (233, 30,  99),     # EP testing — pink
    "B":  (158, 157, 36),     # Breakout space — olive green
    "A":  (136, 14,  79),     # Group study room — dark magenta
    "J":  (237, 157, 206),    # Biology lab — light pink
    "Q":  (220, 231, 117),    # Atrium terrace — light yellow
    "D":  (255, 129, 53),     # Terrace — orange
    "F":  (146, 143, 184),    # Cafe — mauve
    "W":  (229, 115, 115),    # Workshop — light red
    "L":  (244, 143, 177),    # Shared lab — pink
    "I":  (179, 136, 255),    # Imaging suite — lavender
    "U":  (93,  64,  55),     # Library — brown
    "M":  (0,   150, 136),    # Seminar room — teal
    "C":  (105, 240, 174),    # Computer lab — mint
    "H":  (27,  94,  32),     # Lecture theatre — dark green
    "G":  (63,  81,  181),    # Teaching lab — indigo
    "Z":  (0,   77,  64),     # Study space — dark teal
    "Y":  (178, 235, 242),    # Herbarium — light blue
    "R":  (255, 171, 145),    # Reception — peach
    "q":  (255, 79,  155),    # Glasshouse — neon pink
    "j":  (66,  144, 88),     # Dining hall — green
    "z":  (158, 215, 149),    # Plant room — light green
    "e":  (98,  0,   234),    # Conference room — deep purple
}

UNKNOWN_COLOR = (255, 0, 255)   # Unknown character → magenta


def get_floor_grids():
    """Load floor grids from building_data.py."""
    try:
        from data import building_data
    except ImportError:
        print("[ERROR] data/building_data.py not found.")
        print("Run tools/pixel_converter.py first.")
        sys.exit(1)

    return {
        "lower_ground": building_data.LOWER_GROUND,
        "ground":       building_data.GROUND,
        "first":        building_data.FIRST,
        "second":       building_data.SECOND,
        "third":        building_data.THIRD,
        "fourth":       building_data.FOURTH,
    }


def render_grid(grid, floor_name, cell_size=CELL_SIZE):
    """Render an ASCII grid as a PIL Image."""
    rows   = len(grid)
    cols   = max(len(row) for row in grid)

    img_w  = cols * cell_size
    img_h  = rows * cell_size

    img    = Image.new("RGB", (img_w, img_h), (200, 200, 200))
    pixels = img.load()

    unknown_chars = set()

    for y, row in enumerate(grid):
        for x, char in enumerate(row):
            color = CHAR_COLORS.get(char)
            if color is None:
                color = UNKNOWN_COLOR
                unknown_chars.add(char)

            # Her hücreyi cell_size x cell_size piksel olarak çiz
            for dy in range(cell_size):
                for dx in range(cell_size):
                    px = x * cell_size + dx
                    py = y * cell_size + dy
                    if px < img_w and py < img_h:
                        pixels[px, py] = color

    if unknown_chars:
        print(f"  ⚠️  Unknown characters (magenta): {sorted(unknown_chars)}")

    return img


def add_legend(img, cell_size=CELL_SIZE):
    """Append a colour legend to the right side of the image."""
    from tools.floor_configs import (
        GLOBAL_COLORS,
        _LOWER_GROUND_COLORS, _GROUND_COLORS,
        _FIRST_FLOOR_COLORS, _SECOND_FLOOR_COLORS,
        _THIRD_FLOOR_COLORS, _FOURTH_FLOOR_COLORS,
    )

    # Build char → name map from all floor definitions
    all_defs = (
        GLOBAL_COLORS
        + _LOWER_GROUND_COLORS + _GROUND_COLORS
        + _FIRST_FLOOR_COLORS  + _SECOND_FLOOR_COLORS
        + _THIRD_FLOOR_COLORS  + _FOURTH_FLOOR_COLORS
    )
    name_map = {entry["char"]: entry["name"] for entry in all_defs}

    legend_w    = 220
    box_size    = 14
    line_height = 18
    x_start     = img.width + 10
    y_start     = 10

    # Make canvas tall enough to fit all legend entries
    needed_h = y_start + len(CHAR_COLORS) * line_height + 10
    canvas_h = max(img.height, needed_h)

    combined = Image.new("RGB", (img.width + legend_w, canvas_h), (240, 240, 240))
    combined.paste(img, (0, 0))

    draw = ImageDraw.Draw(combined)

    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    y = y_start
    for char, color in CHAR_COLORS.items():
        name = name_map.get(char, char)
        draw.rectangle([x_start, y, x_start + box_size, y + box_size], fill=color, outline=(0, 0, 0))
        draw.text((x_start + box_size + 5, y), f"{char}  {name}", fill=(0, 0, 0), font=font)
        y += line_height

    return combined


def visualize_floor(floor_name, grid, show=False, cell_size=CELL_SIZE, legend=True):
    print(f"► {floor_name.upper()} ({len(grid)}x{len(grid[0]) if grid else 0})")

    img = render_grid(grid, floor_name, cell_size)

    if legend:
        img = add_legend(img, cell_size)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{floor_name}_grid.png")
    img.save(out_path)
    print(f"  Saved: {out_path}")

    if show:
        img.show()

    return img


def main():
    args      = sys.argv[1:]
    show      = "--show" in args
    no_legend = "--no-legend" in args
    args      = [a for a in args if not a.startswith("--")]

    # --scale parametresi
    cell_size = CELL_SIZE
    for i, a in enumerate(args):
        if a == "--scale" and i + 1 < len(args):
            cell_size = int(args[i + 1])
            args = args[:i] + args[i+2:]
            break

    all_grids = get_floor_grids()

    valid   = list(all_grids.keys())
    selected = [f for f in args if f in valid] if args else valid

    if args and not selected:
        print(f"Valid floor names: {valid}")
        sys.exit(1)

    print(f"\nFloors to render: {selected}")
    print(f"Cell size: {cell_size}px  |  Legend: {'on' if not no_legend else 'off'}\n")

    for floor_name in selected:
        grid = all_grids[floor_name]
        visualize_floor(floor_name, grid, show=show, cell_size=cell_size, legend=not no_legend)
        print()

    print(f"✅ Images saved to '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
