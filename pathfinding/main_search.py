"""
main_search.py
─────────────────────────────────────────────────────────────
Runs UCS, A*, Weighted A*, and Theta* on 5 building scenarios,
each under two profiles (fastest, min_effort).  Prints a
comparative performance table and a detailed A* route breakdown
per scenario/profile combination.

Usage
-----
    python main_search.py                     # run all scenarios
    python main_search.py --scenario 1        # run scenario 1 only
    python main_search.py --list              # list available scenarios
"""

import sys
import time
import math
from pathlib import Path

# Proje kökünü sys.path'e ekle (doğrudan çalıştırma için)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Map ──────────────────────────────────────────────────────
from data.building_data import build_campus_map
campus_map = build_campus_map()
MAP_SOURCE = "building_data.py (real LaMB map)"

# ── Search components ────────────────────────────────────────
from pathfinding.indoor_search import BuildingProblem, find_cells
from pathfinding.heuristics    import make_heuristic, make_euclidean_heuristic
from pathfinding.costs         import path_duration, route_breakdown

from pathfinding.common    import failure, path_states, path_actions
from pathfinding.astar     import (uniform_cost_search,
                                   astar_search,
                                   weighted_astar_search)
from pathfinding.theta_star import theta_star_search

from poi.user_profile import PROFILES


# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

WEIGHTED_ASTAR_W = 1.5

FLOOR_NAMES = [
    "Lower Ground", "Ground", "First",
    "Second", "Third", "Fourth"
]

POI_NAMES = {
    '#': 'Wall',          '.': 'Corridor',
    'S': 'Stairs',        'E': 'Elevator',
    'A': 'Group study room','N': 'Main entrance',
    'X': 'Fire exit',     'V': 'Courtyard',
    'T': 'Toilets',       'O': 'Office',
    'P': 'Support lab',   'K': 'EP testing',
    'B': 'Breakout space','J': 'Biology lab',
    'Q': 'Atrium terrace','D': 'Terrace',
    'F': 'Cafe',          'W': 'Workshop',
    'L': 'Shared lab',    'I': 'Imaging suite',
    'U': 'Library',       'M': 'Seminar room',
    'C': 'Computer lab',  'H': 'Lecture theatre',
    'G': 'Teaching lab',  'Z': 'Study space',
    'Y': 'Herbarium',     'R': 'Reception',
    'q': 'Glasshouse',    'j': 'Dining hall',
    'z': 'Plant room',    'e': 'Conference room',
}

TRANSITION_ICONS = {
    "elevator": "🛗 Elevator",
    "stair":    "🪜 Stairs  ",
}

ARROW = {"up": "↑", "down": "↓"}


# ─────────────────────────────────────────────────────────────
# SCENARIOS
# ─────────────────────────────────────────────────────────────

SCENARIOS = {
    1: {
        "name"       : "S1 — Same floor, open area",
        "desc"       : "Library 2 → Small Lecture Theatre (Lower Ground, open layout)",
        "start_state": (0, 203, 27),
        "start_label": "Library 2 (Lower Ground, 203,27)",
        "goal_state" : (0, 86, 94),
        "goal_label" : "Small Lecture Theatre (Lower Ground, 86,94)",
        "note"       : "Theta* vs A* line-of-sight advantage on open floor",
    },
    2: {
        "name"       : "S2 — Same floor, narrow corridors",
        "desc"       : "EP Testing → Small Shared Lab Space 1 (Lower Ground, winding path)",
        "start_state": (0, 41, 108),
        "start_label": "EP Testing (Lower Ground, 41,108)",
        "goal_state" : (0, 148, 11),
        "goal_label" : "Small Shared Lab Space 1 (Lower Ground, 148,11)",
        "note"       : "Theta* ≈ A* when LoS blocked by corridor walls",
    },
    3: {
        "name"      : "S3 — Maximum floor span",
        "desc"      : "4th floor → lower ground floor lecture theatre",
        "start_char": "q",
        "goal_char" : "H",
        "note"      : "UCS vs A* node expansion; heuristic tightness depends on profile cost scale",
    },
    4: {
        "name"       : "S4 — Same floor, maximum office distance",
        "desc"       : "EP Testing Lab Manager's Office → Biology Lab Manager's Office (Second floor)",
        "start_state": (3, 64, 117),
        "start_label": "EP Testing Lab Manager's Office (Second, 64,117)",
        "goal_state" : (3, 215, 6),
        "goal_label" : "Biology Lab Manager's Office (Second, 215,6)",
        "note"       : "Weighted A* speed vs optimality tradeoff on wide floor",
    },
}

PROFILE_NAMES = ["fastest", "min_effort"]


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def find_start_char(char):
    """Return first cell matching char, or raise."""
    cells = find_cells(campus_map, char)
    if not cells:
        raise RuntimeError(f"No cells found for char '{char}'.")
    return cells[0]


def count_walkable(campus_map):
    return sum(
        1 for floor in campus_map
        for row in floor
        for ch in row
        if ch != '#'
    )


def floor_name(f):
    return FLOOR_NAMES[f] if f < len(FLOOR_NAMES) else f"Floor {f}"


# ─────────────────────────────────────────────────────────────
# RUN ONE ALGORITHM
# ─────────────────────────────────────────────────────────────

def run_algorithm(name, fn, *args, **kwargs):
    t0 = time.perf_counter()
    try:
        node, stats = fn(*args, **kwargs)
    except Exception as e:
        return {
            "name": name, "found": False, "error": str(e),
            "cost": None, "steps": None,
            "distance_m": None, "duration_min": None,
            "expanded": None, "generated": None, "time_s": None,
            "segments": None,
        }
    t1 = time.perf_counter()

    found    = (node is not failure)
    states   = path_states(node)  if found else []
    acts     = path_actions(node) if found else []
    duration = path_duration(states, acts) if found else {}
    segments = route_breakdown(states, acts) if found else []

    return {
        "name"        : name,
        "found"       : found,
        "error"       : None,
        "cost"        : round(node.path_cost, 2) if found else None,
        "steps"       : len(states) - 1          if found else None,
        "distance_m"  : duration.get("distance_m"),
        "duration_min": duration.get("duration_min"),
        "expanded"    : stats.get("nodes_expanded"),
        "generated"   : stats.get("nodes_generated"),
        "time_s"      : round(t1 - t0, 4),
        "segments"    : segments,
    }


# ─────────────────────────────────────────────────────────────
# PRINT COMPARISON TABLE
# ─────────────────────────────────────────────────────────────

def print_table(results, scenario_name, profile_label):
    print()
    print("=" * 90)
    print(f" Scenario : {scenario_name}   |   Profile: {profile_label}")
    print("=" * 90)

    hdr = (f"  {'Algorithm':<22} {'Found':<6} {'Cost':>8} {'Steps':>6} "
           f"{'Dist(m)':>8} {'Time(min)':>10} "
           f"{'Expanded':>10} {'Generated':>10} {'Time(s)':>8}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    for r in results:
        found_s = "Yes" if r["found"] else ("ERR" if r["error"] else "No")

        def fmt(v, fmt_str):
            return fmt_str.format(v) if v is not None else "  —"

        line = (
            f"  {r['name']:<22} {found_s:<6} "
            f"{fmt(r['cost'],       '{:>8.1f}'):>8} "
            f"{fmt(r['steps'],      '{:>6d}'):>6} "
            f"{fmt(r['distance_m'], '{:>8.1f}'):>8} "
            f"{fmt(r['duration_min'],'{:>10.2f}'):>10} "
            f"{fmt(r['expanded'],   '{:>10,}'):>10} "
            f"{fmt(r['generated'],  '{:>10,}'):>10} "
            f"{fmt(r['time_s'],     '{:>8.4f}'):>8}"
        )
        print(line)

    print("=" * 90)


# ─────────────────────────────────────────────────────────────
# PRINT ROUTE SUMMARY
# ─────────────────────────────────────────────────────────────

def print_route_summary(result):
    segments = result.get("segments")
    if not segments:
        return

    print(f"\n  Route breakdown  ({result['name']})")
    print(f"  {'─' * 52}")

    total_dist = 0.0
    total_time = 0.0
    n = len(segments)

    for i, seg in enumerate(segments):
        is_last = (i == n - 1)
        prefix  = "  └─" if is_last else "  ├─"

        if seg["kind"] == "walk":
            fn = floor_name(seg["floor"])
            print(f"{prefix} 🚶 {fn:<15}  "
                  f"{seg['distance_m']:>5.1f} m   "
                  f"{seg['duration_s']:>4.0f} s")
            total_dist += seg["distance_m"]
            total_time += seg["duration_s"]
        else:
            icon   = TRANSITION_ICONS.get(seg["kind"], "↕ Transition")
            f_from = floor_name(seg["from_floor"])
            f_to   = floor_name(seg["to_floor"])
            arr    = ARROW[seg["direction"]]
            print(f"{prefix} {icon}  "
                  f"{f_from} {arr} {f_to:<15}  "
                  f"{seg['duration_s']:>4.0f} s")
            total_time += seg["duration_s"]

    print(f"  {'─' * 52}")
    print(f"  Total  {total_dist:.1f} m walking  •  "
          f"{total_time:.0f} s  ({total_time / 60:.2f} min)\n")


# ─────────────────────────────────────────────────────────────
# RUN ALL ALGORITHMS FOR ONE SCENARIO + PROFILE
# ─────────────────────────────────────────────────────────────

def run_scenario_profile(start, goals, scenario_name, profile_name):
    profile = PROFILES[profile_name]

    # Filter forbidden goals (e.g. accessible profile forbids stairs)
    # Goals are already POI cells, not transition-type; keep all.
    if len(goals) > 50:
        sf, sx, sy = start
        goals = sorted(goals,
            key=lambda g: math.sqrt((g[1]-sx)**2 + (g[2]-sy)**2))[:50]

    h_std  = make_heuristic(goals, campus_map, diagonal=True)
    h_eucl = make_euclidean_heuristic(goals)

    prob = BuildingProblem(start, campus_map, goals=goals,
                           diagonal=True, profile=profile)

    results = []
    results.append(run_algorithm("UCS",
        uniform_cost_search, prob))
    results.append(run_algorithm("A*",
        astar_search, prob, h_std))
    results.append(run_algorithm(f"Weighted A* (w={WEIGHTED_ASTAR_W})",
        weighted_astar_search, prob, h_std, WEIGHTED_ASTAR_W))
    results.append(run_algorithm("Theta*",
        theta_star_search, prob, h_eucl))

    print_table(results, scenario_name, profile.label)

    astar_result = next((r for r in results if r["name"] == "A*"), None)
    if astar_result and astar_result["found"]:
        print_route_summary(astar_result)

    return results


def run_scenario(scenario):
    name = scenario["name"]
    desc = scenario["desc"]
    note = scenario["note"]

    # Resolve start
    if "start_state" in scenario:
        start       = scenario["start_state"]
        start_label = scenario.get("start_label", str(start))
    else:
        start_char = scenario["start_char"]
        try:
            start = find_start_char(start_char)
        except RuntimeError as e:
            print(f"\n  ⚠️  {e}")
            return
        start_label = f"'{start_char}' {start}"

    # Resolve goal
    if "goal_state" in scenario:
        goals      = [scenario["goal_state"]]
        goal_label = scenario.get("goal_label", str(scenario["goal_state"]))
    else:
        goal_char  = scenario["goal_char"]
        goals      = find_cells(campus_map, goal_char)
        if not goals:
            print(f"\n  ⚠️  No '{goal_char}' cells found "
                  f"({POI_NAMES.get(goal_char, '?')}) — skipped.")
            return
        goal_label = f"{len(goals)} '{goal_char}' ({POI_NAMES.get(goal_char, '?')}) cells"

    print(f"\n{'━' * 90}")
    print(f"  {name}")
    print(f"  {desc}")
    print(f"  Note: {note}")
    print(f"  Start: {start_label}   Goal: {goal_label}")
    print(f"{'━' * 90}")

    for pname in PROFILE_NAMES:
        run_scenario_profile(start, list(goals), name, pname)


# ─────────────────────────────────────────────────────────────
# LIST / MAIN
# ─────────────────────────────────────────────────────────────

def list_scenarios():
    print("\nAvailable scenarios:")
    for k, s in SCENARIOS.items():
        print(f"  {k}. {s['name']}")
        print(f"       {s['desc']}")
    print()


def main():
    print(f"\n🗺️  LaMB BUILDING NAVIGATION — ALGORITHM COMPARISON")
    print(f"   Map source : {MAP_SOURCE}")
    print(f"   Floors     : {len(campus_map)}")
    print(f"   Grid size  : {len(campus_map[0][0])} × {len(campus_map[0])}")
    print(f"   Walkable   : {count_walkable(campus_map):,} cells")
    print(f"   Profiles   : {', '.join(PROFILE_NAMES)}")
    print(f"   Algorithms : UCS, A*, Weighted A* (w={WEIGHTED_ASTAR_W}), Theta*")

    args = sys.argv[1:]

    if "--list" in args:
        list_scenarios()
        return

    if "--scenario" in args:
        idx = args.index("--scenario")
        if idx + 1 < len(args):
            try:
                s_num = int(args[idx + 1])
                if s_num in SCENARIOS:
                    run_scenario(SCENARIOS[s_num])
                else:
                    print(f"Unknown scenario {s_num}.")
                    list_scenarios()
            except ValueError:
                print("--scenario requires an integer argument.")
        return

    print("\nRunning all scenarios...\n")
    for s_num, scenario in SCENARIOS.items():
        run_scenario(scenario)


if __name__ == "__main__":
    main()
