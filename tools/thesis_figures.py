"""
thesis_figures.py
─────────────────────────────────────────────────────────────
Generates cropped route visuals for thesis figures.

Usage:
    python tools/thesis_figures.py

Output: grid_visuals/thesis_figures/
"""

import sys, math, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data import build_campus_map
from pathfinding.indoor_search import BuildingProblem, find_cells
from pathfinding.heuristics    import make_heuristic, make_euclidean_heuristic
from pathfinding.costs         import path_duration, route_breakdown
from pathfinding.common        import failure, path_states, path_actions
from pathfinding.astar         import (uniform_cost_search,
                                       astar_search,
                                       weighted_astar_search)
from pathfinding.theta_star    import theta_star_search
from poi.user_profile          import PROFILES

campus_map = build_campus_map()

MAPS_DIR = _ROOT / "static" / "maps"
OUT_DIR  = _ROOT / "grid_visuals" / "thesis_figures"

MAP_FILES = {
    0: "lower-ground-floor.png",
    1: "ground-floor.png",
    2: "first-floor.png",
    3: "second-floor.png",
    4: "third-floor.png",
    5: "fourth-floor.png",
}
FLOOR_NAMES = ["Lower Ground", "Ground", "First", "Second", "Third", "Fourth"]

MAP_SCALE  = 10
WEIGHTED_W = 1.5
MAX_W      = 1200
MAX_H      = 800
DPI        = 150
PAD_PCT    = 0.30
MIN_PAD    = 80   # minimum padding in image pixels

_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
try:
    _font_label = ImageFont.truetype(_FONT_PATH, size=20)
    _font_small = ImageFont.truetype(_FONT_PATH, size=14)
except Exception:
    _font_label = ImageFont.load_default()
    _font_small = _font_label


# ── Core helpers ─────────────────────────────────────────────

def px(v):
    return v * MAP_SCALE + MAP_SCALE // 2


def run_algo(fn, *args, **kwargs):
    try:
        node, stats = fn(*args, **kwargs)
    except Exception as e:
        print(f"    ⚠️  {fn.__name__}: {e}")
        return None, None, None, None
    if node is failure:
        return None, None, None, None
    return node, path_states(node), path_actions(node), stats


def make_problem(start, goals, profile_name="fastest"):
    return BuildingProblem(start, campus_map, goals=list(goals),
                           diagonal=True, profile=PROFILES[profile_name])


def load_floor_img(floor_idx):
    fname = MAP_FILES.get(floor_idx, "")
    fpath = MAPS_DIR / fname
    if fname and fpath.exists():
        img = Image.open(fpath).convert("RGB")
        return img.resize((img.width * MAP_SCALE, img.height * MAP_SCALE),
                          Image.NEAREST)
    rows = len(campus_map[floor_idx])
    cols = len(campus_map[floor_idx][0]) if rows else 230
    return Image.new("RGB", (cols * MAP_SCALE, rows * MAP_SCALE), (50, 50, 50))


def draw_route(img, states, floor_idx, start_state=None, end_state=None):
    """Draw route on img for the given floor. Returns pixel point list."""
    draw = ImageDraw.Draw(img)
    pts  = [(px(x), px(y)) for (f, x, y) in states if f == floor_idx]

    if len(pts) > 1:
        draw.line(pts, fill=(0, 0, 0),       width=7)   # shadow
        draw.line(pts, fill=(255, 255, 255),  width=4)   # route

    if start_state and start_state[0] == floor_idx:
        sx, sy = start_state[1], start_state[2]
        r = MAP_SCALE + 3
        draw.ellipse([px(sx)-r, px(sy)-r, px(sx)+r, px(sy)+r],
                     fill=(56, 142, 60), outline=(255, 255, 255), width=2)

    if end_state and end_state[0] == floor_idx:
        ex, ey = end_state[1], end_state[2]
        r = MAP_SCALE + 3
        draw.ellipse([px(ex)-r, px(ey)-r, px(ex)+r, px(ey)+r],
                     fill=(211, 47, 47), outline=(255, 255, 255), width=2)

    return pts


def add_label(img, text, font=None):
    if font is None:
        font = _font_label
    draw = ImageDraw.Draw(img)
    try:
        bbox = draw.textbbox((12, 12), text, font=font)
    except AttributeError:
        bbox = (12, 12, 12 + len(text) * 10, 32)
    pad = 5
    draw.rectangle([bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad],
                   fill=(0, 0, 0))
    draw.text((12, 12), text, font=font, fill=(255, 255, 255))


def crop_to_route(img, pts):
    if not pts:
        return img
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    span_x = max(max(xs) - min(xs), 1)
    span_y = max(max(ys) - min(ys), 1)
    pad_x  = max(int(span_x * PAD_PCT), MIN_PAD)
    pad_y  = max(int(span_y * PAD_PCT), MIN_PAD)
    l = max(0,           min(xs) - pad_x)
    t = max(0,           min(ys) - pad_y)
    r = min(img.width,   max(xs) + pad_x)
    b = min(img.height,  max(ys) + pad_y)
    return img.crop((int(l), int(t), int(r), int(b)))


def fit_size(img):
    if img.width <= MAX_W and img.height <= MAX_H:
        return img
    scale = min(MAX_W / img.width, MAX_H / img.height)
    return img.resize((int(img.width * scale), int(img.height * scale)),
                      Image.LANCZOS)


def save_fig(img, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img  = fit_size(img)
    path = OUT_DIR / name
    img.save(str(path), format="PNG", dpi=(DPI, DPI))
    print(f"  ✅  {name}  ({img.width}×{img.height}px)")


def floor_figure(floor_idx, states, label, start_state, end_state, filename):
    img = load_floor_img(floor_idx)
    pts = draw_route(img, states, floor_idx, start_state, end_state)
    add_label(img, label)
    img = crop_to_route(img, pts)
    save_fig(img, filename)


# ─────────────────────────────────────────────────────────────
# S1 — Library 2 → Small Lecture Theatre  (floor 0)
# ─────────────────────────────────────────────────────────────

def gen_s1():
    print("\nS1 — Library 2 → Small Lecture Theatre (Lower Ground)")
    start = (0, 199, 15)
    goals = [(0, 86, 94)]
    h_std  = make_heuristic(goals, campus_map, diagonal=True)
    h_eucl = make_euclidean_heuristic(goals)

    # A*
    node, states, acts, stats = run_algo(astar_search, make_problem(start, goals), h_std)
    if states:
        label = f"A* — cost {node.path_cost:.1f}  ({len(states)-1} steps)"
        floor_figure(0, states, label, start, goals[0], "S1_Astar.png")
    else:
        print("  ⚠️  A* failed")

    # Theta*
    node, states, acts, stats = run_algo(theta_star_search, make_problem(start, goals), h_eucl)
    if states:
        label = f"Theta* — cost {node.path_cost:.1f}  ({len(states)-1} steps)"
        floor_figure(0, states, label, start, goals[0], "S1_Theta.png")
    else:
        print("  ⚠️  Theta* failed")


# ─────────────────────────────────────────────────────────────
# S2 — EP Testing → Small Shared Lab Space 1  (floor 0)
# ─────────────────────────────────────────────────────────────

def gen_s2():
    print("\nS2 — EP Testing → Small Shared Lab Space 1 (Lower Ground)")
    start = (0, 41, 108)
    goals = [(0, 148, 11)]
    h_std = make_heuristic(goals, campus_map, diagonal=True)

    # UCS
    node, states, acts, stats = run_algo(uniform_cost_search, make_problem(start, goals))
    if states:
        exp   = stats.get("nodes_expanded", 0)
        label = f"UCS — cost {node.path_cost:.1f}  |  {exp:,} nodes expanded"
        floor_figure(0, states, label, start, goals[0], "S2_UCS.png")
    else:
        print("  ⚠️  UCS failed")

    # A*
    node, states, acts, stats = run_algo(astar_search, make_problem(start, goals), h_std)
    if states:
        exp   = stats.get("nodes_expanded", 0)
        label = f"A* — cost {node.path_cost:.1f}  |  {exp:,} nodes expanded"
        floor_figure(0, states, label, start, goals[0], "S2_Astar.png")
    else:
        print("  ⚠️  A* failed")


# ─────────────────────────────────────────────────────────────
# S3 — 4th floor (q) → Lower Ground lecture theatre (H)
# ─────────────────────────────────────────────────────────────

def gen_s3():
    print("\nS3 — 4th floor → Lower Ground Lecture Theatre (multi-floor)")
    start_cells = find_cells(campus_map, 'q')
    if not start_cells:
        print("  ⚠️  No 'q' cells"); return
    start = start_cells[0]

    goals = find_cells(campus_map, 'H')
    if not goals:
        print("  ⚠️  No 'H' cells"); return
    if len(goals) > 50:
        goals = sorted(goals, key=lambda g: math.sqrt(
            (g[1]-start[1])**2 + (g[2]-start[2])**2))[:50]

    h_std  = make_heuristic(goals, campus_map, diagonal=True)
    node, states, acts, stats = run_algo(astar_search, make_problem(start, goals), h_std)
    if not states:
        print("  ⚠️  Route not found"); return

    segs = route_breakdown(states, acts) if acts else []

    # Build transition description for label
    trans_parts = []
    for seg in segs:
        if seg["kind"] != "walk":
            fn_s = FLOOR_NAMES[seg["from_floor"]]
            fn_t = FLOOR_NAMES[seg["to_floor"]]
            kind = "Stairs" if seg["kind"] == "stair" else "Elevator"
            trans_parts.append(f"{kind} {fn_s}→{fn_t}")
    base_label = "fastest — " + (", ".join(trans_parts) if trans_parts
                                  else f"cost {node.path_cost:.1f}")

    floors_visited = sorted(set(f for f, x, y in states), reverse=True)

    # Per-floor file name mapping
    floor_fname = {
        5: "S3_floor5_Fourth.png",
        4: "S3_floor4_Third.png",
    }

    for fi in floors_visited:
        pts = [(px(x), px(y)) for (f, x, y) in states if f == fi]
        if not pts:
            continue

        img   = load_floor_img(fi)
        s_st  = states[0]  if states[0][0]  == fi else None
        e_st  = states[-1] if states[-1][0] == fi else None
        draw_route(img, states, fi, s_st, e_st)
        add_label(img, f"{base_label}  |  {FLOOR_NAMES[fi]}")
        img = crop_to_route(img, pts)

        if fi in floor_fname:
            fname = floor_fname[fi]
        elif fi <= 3:
            fname = "S3_floors_0to3.png"   # group lower floors into one
        else:
            fname = f"S3_floor{fi}.png"

        save_fig(img, fname)
        # Only save floor 0 for S3_floors_0to3
        if fi <= 3:
            break

    # Summary schematic
    gen_s3_summary(states, segs, base_label, floors_visited)


def gen_s3_summary(states, segs, base_label, floors_visited):
    W, H = 620, 480
    img  = Image.new("RGB", (W, H), (28, 28, 36))
    draw = ImageDraw.Draw(img)

    BAR_H   = 44
    BAR_GAP = 12
    MX      = 100         # left margin (for start/end markers)
    MR      = W - 40      # right edge
    TOP     = 60          # top offset

    # floor 5 at top → floor 0 at bottom
    def bar_y(fi):
        return TOP + (5 - fi) * (BAR_H + BAR_GAP)

    # Floor bars
    for fi in range(6):
        y      = bar_y(fi)
        active = fi in floors_visited
        fill   = (45, 85, 140)  if active else (42, 42, 52)
        border = (90, 150, 230) if active else (65, 65, 75)
        draw.rectangle([MX, y, MR, y + BAR_H], fill=fill, outline=border, width=2)
        txt_col = (230, 230, 230) if active else (100, 100, 110)
        draw.text((MX + 10, y + 13), FLOOR_NAMES[fi], font=_font_small, fill=txt_col)

    # Transition arrows
    cx = (MX + MR) // 2
    for seg in segs:
        if seg["kind"] == "walk":
            continue
        f_fr = seg["from_floor"]
        f_to = seg["to_floor"]
        y_fr = bar_y(f_fr) + BAR_H // 2
        y_to = bar_y(f_to) + BAR_H // 2
        col  = (255, 200, 60) if seg["kind"] == "stair" else (80, 200, 120)
        draw.line([(cx, y_fr), (cx, y_to)], fill=col, width=3)
        # arrowhead pointing in direction of travel
        tip_y = y_to + (6 if y_to > y_fr else -6)
        draw.polygon([(cx, y_to), (cx-7, tip_y), (cx+7, tip_y)], fill=col)
        kind_str = "🪜 Stairs" if seg["kind"] == "stair" else "🛗 Elevator"
        mid_y = (y_fr + y_to) // 2
        draw.text((cx + 14, mid_y - 8), kind_str, font=_font_small, fill=col)

    # Start dot (green) on top floor, end dot (red) on bottom floor
    r = 9
    f_start = states[0][0]
    f_end   = states[-1][0]
    sy = bar_y(f_start) + BAR_H // 2
    ey = bar_y(f_end)   + BAR_H // 2
    draw.ellipse([MX-r-5, sy-r, MX-5+r, sy+r],
                 fill=(56, 142, 60), outline=(255,255,255), width=2)
    draw.ellipse([MX-r-5, ey-r, MX-5+r, ey+r],
                 fill=(211, 47, 47), outline=(255,255,255), width=2)

    # Title
    draw.text((10, 14), base_label, font=_font_small, fill=(180, 180, 190))

    save_fig(img, "S3_summary.png")


# ─────────────────────────────────────────────────────────────
# S4 — EP Manager → Biology Manager  (floor 3)
# ─────────────────────────────────────────────────────────────

def gen_s4():
    print("\nS4 — EP Testing Lab Manager → Biology Lab Manager (Second floor)")
    start = (3, 64, 117)
    goals = [(3, 215, 6)]
    h_std = make_heuristic(goals, campus_map, diagonal=True)

    runs = [
        ("UCS",                     uniform_cost_search,  [],                   "S4_UCS.png"),
        ("A*",                      astar_search,         [h_std],              "S4_Astar.png"),
        (f"Weighted A* (w={WEIGHTED_W})", weighted_astar_search, [h_std, WEIGHTED_W], "S4_WeightedAstar.png"),
    ]

    for name, fn, extra_args, fname in runs:
        prob = make_problem(start, goals, "fastest")
        node, states, acts, stats = run_algo(fn, prob, *extra_args)
        if not states:
            print(f"  ⚠️  {name} failed"); continue
        exp   = stats.get("nodes_expanded", 0)
        label = f"{name} — cost {node.path_cost:.1f}  |  {exp:,} nodes expanded"
        floor_figure(3, states, label, start, goals[0], fname)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🎓 Thesis Figures Generator")
    print(f"   Output: {OUT_DIR}\n")
    gen_s1()
    gen_s2()
    gen_s3()
    gen_s4()
    print(f"\n✅ Done. Files saved to {OUT_DIR}")
