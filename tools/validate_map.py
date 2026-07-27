"""
validate_map.py
─────────────────────────────────────────────────────────────
Validates the building_data.py grid output from pixel_converter.py.

Checks:
  1. Grid dimensions are consistent across all floors
  2. Vertical infrastructure (E, S, A) aligns across floors
  3. BFS reachability — what fraction of walkable cells can be
     reached from the main entrance ('N') or the first walkable cell
  4. POI summary — lists how many cells of each type exist per floor

Usage:
    python validate_map.py
"""

import sys
from pathlib import Path
from collections import deque

# Proje kökünü sys.path'e ekle (doğrudan çalıştırma için)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ─────────────────────────────────────────────────────────────
# LOAD MAP
# ─────────────────────────────────────────────────────────────

try:
    from data.building_data import build_campus_map, LOWER_GROUND, GROUND
    campus_map = build_campus_map()
    print("✅ building_data.py loaded successfully.\n")
except ImportError:
    print("⚠️  building_data.py not found.")
    print("    Run pixel_converter.py first to generate it.\n")
    sys.exit(1)

from poi.poi_index import POI_REGISTRY


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

WALL = '#'

VERTICAL_CHARS = {'E', 'S'}

ALL_DIRECTIONS = [
    (0, -1), (0, +1), (-1, 0), (+1, 0),  # cardinal
    (-1,-1), (+1,-1), (-1,+1), (+1,+1),  # diagonal
]

FLOOR_NAMES = [
    "Lower Ground", "Ground", "First",
    "Second", "Third", "Fourth"
]


def cell(campus_map, f, x, y):
    return campus_map[f][y][x]


def is_walkable(campus_map, f, x, y):
    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])
    return (0 <= f < n_floors and
            0 <= x < n_cols  and
            0 <= y < n_rows  and
            campus_map[f][y][x] != WALL)


# ─────────────────────────────────────────────────────────────
# CHECK 1 — DIMENSIONS
# ─────────────────────────────────────────────────────────────

def check_dimensions(campus_map):
    print("=" * 60)
    print("CHECK 1 — Grid dimensions")
    print("=" * 60)

    n_floors = len(campus_map)
    ref_rows = len(campus_map[0])
    ref_cols = len(campus_map[0][0])

    print(f"  Floors : {n_floors}")
    print(f"  Expected grid per floor: {ref_cols} × {ref_rows} (W × H)\n")

    ok = True
    for f, floor in enumerate(campus_map):
        name  = FLOOR_NAMES[f] if f < len(FLOOR_NAMES) else f"Floor {f}"
        rows  = len(floor)
        cols  = len(floor[0]) if floor else 0
        match = "✅" if rows == ref_rows and cols == ref_cols else "❌"
        if rows != ref_rows or cols != ref_cols:
            ok = False
        print(f"  {match} {name:<15} {cols} × {rows}")

    print()
    return ok


# ─────────────────────────────────────────────────────────────
# CHECK 2 — VERTICAL ALIGNMENT
# ─────────────────────────────────────────────────────────────

def check_vertical_alignment(campus_map):
    print("=" * 60)
    print("CHECK 2 — Vertical infrastructure alignment (E, S, A)")
    print("=" * 60)

    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])

    issues = 0

    for ch in VERTICAL_CHARS:
        positions = set()
        for f in range(n_floors):
            for y in range(n_rows):
                for x in range(n_cols):
                    if campus_map[f][y][x] == ch:
                        positions.add((x, y))

        if not positions:
            print(f"  ⚠️  '{ch}' not found in any floor.")
            continue

        for (x, y) in sorted(positions):
            floors_present = [f for f in range(n_floors)
                              if campus_map[f][y][x] == ch]
            if len(floors_present) == 1:
                name = FLOOR_NAMES[floors_present[0]] \
                    if floors_present[0] < len(FLOOR_NAMES) \
                    else f"Floor {floors_present[0]}"
                print(f"  ⚠️  '{ch}' at ({x},{y}) only on {name} — "
                      f"vertical transition may be isolated.")
                issues += 1
            else:
                print(f"  ✅ '{ch}' at ({x},{y}) spans floors: "
                      f"{[FLOOR_NAMES[f] if f < len(FLOOR_NAMES) else f for f in floors_present]}")

    print(f"\n  {issues} alignment issue(s) found.\n")
    return issues == 0


# ─────────────────────────────────────────────────────────────
# CHECK 3 — BFS REACHABILITY
# ─────────────────────────────────────────────────────────────

def check_reachability(campus_map):
    print("=" * 60)
    print("CHECK 3 — BFS reachability from main entrance")
    print("=" * 60)

    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])

    # Find main entrance 'N', fall back to first walkable cell
    start = None
    for f in range(n_floors):
        for y in range(n_rows):
            for x in range(n_cols):
                if campus_map[f][y][x] == 'N':
                    start = (f, x, y)
                    break
            if start: break
        if start: break

    if start is None:
        for f in range(n_floors):
            for y in range(n_rows):
                for x in range(n_cols):
                    if campus_map[f][y][x] != WALL:
                        start = (f, x, y)
                        break
                if start: break
            if start: break

    if start is None:
        print("  ❌ No walkable cell found.\n")
        return False

    sf, sx, sy = start
    sname = FLOOR_NAMES[sf] if sf < len(FLOOR_NAMES) else f"Floor {sf}"
    ch    = campus_map[sf][sy][sx]
    print(f"  Start: ({sx},{sy}) floor={sname} char='{ch}'\n")

    # Count total walkable cells
    total_walkable = sum(
        1
        for f in range(n_floors)
        for y in range(n_rows)
        for x in range(n_cols)
        if campus_map[f][y][x] != WALL
    )

    # BFS
    visited  = {start}
    frontier = deque([start])

    while frontier:
        f, x, y = frontier.popleft()

        # Horizontal neighbours
        for dx, dy in ALL_DIRECTIONS:
            nx, ny = x + dx, y + dy
            if is_walkable(campus_map, f, nx, ny):
                s = (f, nx, ny)
                if s not in visited:
                    visited.add(s)
                    frontier.append(s)

        # Vertical transitions
        ch = campus_map[f][y][x]
        if ch in VERTICAL_CHARS:
            for df in (+1, -1):
                nf = f + df
                if is_walkable(campus_map, nf, x, y):
                    s = (nf, x, y)
                    if s not in visited:
                        visited.add(s)
                        frontier.append(s)

    reached_pct = 100 * len(visited) / total_walkable if total_walkable else 0
    print(f"  Total walkable cells : {total_walkable:,}")
    print(f"  Reachable from start : {len(visited):,} ({reached_pct:.1f}%)")

    # Per-floor breakdown
    print()
    for f in range(n_floors):
        name = FLOOR_NAMES[f] if f < len(FLOOR_NAMES) else f"Floor {f}"
        wk = sum(1 for y in range(n_rows) for x in range(n_cols)
                 if campus_map[f][y][x] != WALL)
        rc = sum(1 for (rf, rx, ry) in visited if rf == f)
        pct = 100 * rc / wk if wk else 0
        ok  = "✅" if pct >= 90 else "⚠️ "
        print(f"  {ok} {name:<15} {rc:>5}/{wk:<5} ({pct:.1f}%)")

    print()
    return reached_pct >= 90


# ─────────────────────────────────────────────────────────────
# CHECK 4 — POI SUMMARY
# ─────────────────────────────────────────────────────────────

def check_poi_summary(campus_map):
    print("=" * 60)
    print("CHECK 4 — POI character counts per floor")
    print("=" * 60)

    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])

    # Collect all characters
    from collections import Counter
    global_counts = Counter()
    floor_counts  = []

    for f, floor in enumerate(campus_map):
        cnt = Counter()
        for row in floor:
            for ch in row:
                cnt[ch] += 1
        floor_counts.append(cnt)
        global_counts.update(cnt)

    # Print header
    floor_labels = [FLOOR_NAMES[f][:6] if f < len(FLOOR_NAMES)
                    else f"F{f}" for f in range(n_floors)]
    header = f"  {'Char':<6} {'Name':<22} " + \
             "  ".join(f"{l:>6}" for l in floor_labels) + "  Total"
    print(header)
    print("  " + "-" * (len(header) - 2))

    CHAR_NAMES = {'#': 'Wall', '.': 'Corridor'}
    CHAR_NAMES.update({c: p.name_en for c, p in POI_REGISTRY.items()})

    for ch in sorted(global_counts.keys()):
        if global_counts[ch] == 0:
            continue
        name   = CHAR_NAMES.get(ch, '???')
        counts = "  ".join(f"{floor_counts[f].get(ch,0):>6}"
                           for f in range(n_floors))
        total  = global_counts[ch]
        print(f"  '{ch}'   {name:<22} {counts}  {total:>6}")

    print()


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nBUILDING DATA VALIDATION\n")

    d_ok = check_dimensions(campus_map)
    v_ok = check_vertical_alignment(campus_map)
    r_ok = check_reachability(campus_map)
    check_poi_summary(campus_map)

    print("=" * 60)
    if d_ok and v_ok and r_ok:
        print("✅  All checks passed. Map is ready for pathfinding.\n")
    else:
        print("⚠️  Some checks failed. Review output above.\n")
