"""
costs.py
─────────────────────────────────────────────────────────────
Action cost model and real-world distance / time conversion
for the Oxford Life and Mind Building navigation system.

Scale factor derived from architectural floor plans:
    1 pixel = 0.32 metres  (128 px height == 41 m building depth)

Walking speed: 1.4 m/s (average adult pedestrian).
"""

import math

# ─────────────────────────────────────────────────────────────
# REAL-WORLD SCALE
# ─────────────────────────────────────────────────────────────

METERS_PER_PIXEL  = 0.32   # 1 grid cell = 0.32 m
WALKING_SPEED_MPS = 1.4    # m/s  (average adult)

# ─────────────────────────────────────────────────────────────
# ACTION COSTS  (abstract units used by pathfinding)
# ─────────────────────────────────────────────────────────────
# Cardinal move          : 1 unit  (horizontal or vertical step)
# Diagonal move          : sqrt(2) units  (Euclidean distance)
# Elevator up/down       : 2 units per floor  (fast, may wait)
# Stair up               : 12 units per floor (slow, effort)
# Stair down             : 6 units per floor  (less effort)
# Accessible lift up/down: 3 units per floor  (slower than elevator)

COST_MOVE_CARDINAL   = 1
COST_MOVE_DIAGONAL   = math.sqrt(2)   # ~1.414

COST_ELEVATOR_UP     = 2
COST_ELEVATOR_DOWN   = 2

COST_STAIR_UP        = 12
COST_STAIR_DOWN      = 6

COST_LIFT_UP         = 3   # accessible lift ('A')
COST_LIFT_DOWN       = 3


def action_cost(action: str) -> float:
    """
    Return the abstract cost of a single action.

    Actions:
        MOVE_N, MOVE_S, MOVE_E, MOVE_W          cardinal
        MOVE_NE, MOVE_NW, MOVE_SE, MOVE_SW      diagonal
        ELEVATOR_UP, ELEVATOR_DOWN
        STAIR_UP, STAIR_DOWN
        LIFT_UP, LIFT_DOWN
    """
    if action in ("MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W"):
        return COST_MOVE_CARDINAL
    if action in ("MOVE_NE", "MOVE_NW", "MOVE_SE", "MOVE_SW"):
        return COST_MOVE_DIAGONAL
    if action in ("ELEVATOR_UP", "ELEVATOR_DOWN"):
        return COST_ELEVATOR_UP
    if action == "STAIR_UP":
        return COST_STAIR_UP
    if action == "STAIR_DOWN":
        return COST_STAIR_DOWN
    if action in ("LIFT_UP", "LIFT_DOWN"):
        return COST_LIFT_UP
    return COST_MOVE_CARDINAL   # fallback


# ─────────────────────────────────────────────────────────────
# REAL-WORLD CONVERSION
# ─────────────────────────────────────────────────────────────

def pixels_to_metres(pixels: float) -> float:
    """Convert a pixel distance to metres."""
    return pixels * METERS_PER_PIXEL


def metres_to_seconds(metres: float) -> float:
    """Estimate walking time in seconds for a given distance."""
    return metres / WALKING_SPEED_MPS


def path_duration(path: list) -> dict:
    """
    Given a path as a list of (floor, x, y) states, compute
    real-world distance and estimated walking time.

    Vertical transitions (elevator, stairs) are excluded from the
    pixel count but add a fixed time penalty.

    Returns:
        {
            "distance_m"  : float  total horizontal distance in metres,
            "duration_s"  : float  estimated time in seconds,
            "duration_min": float  estimated time in minutes,
        }
    """
    FLOOR_CHANGE_SECONDS = {
        "elevator": 20,   # wait + travel per floor
        "stair":    15,   # climb / descend per floor
        "lift":     25,   # accessible lift per floor
    }

    horizontal_pixels = 0.0
    floor_penalties   = 0.0

    for i in range(len(path) - 1):
        f0, x0, y0 = path[i]
        f1, x1, y1 = path[i + 1]

        if f0 == f1:
            # Same floor: Euclidean pixel distance
            horizontal_pixels += math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        else:
            # Floor change: add fixed time penalty (type unknown here;
            # caller can override if they track action labels)
            floor_penalties += FLOOR_CHANGE_SECONDS["stair"]

    distance_m  = pixels_to_metres(horizontal_pixels)
    duration_s  = metres_to_seconds(distance_m) + floor_penalties

    return {
        "distance_m"  : round(distance_m, 1),
        "duration_s"  : round(duration_s, 1),
        "duration_min": round(duration_s / 60, 2),
    }
