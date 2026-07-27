"""
costs.py
─────────────────────────────────────────────────────────────
Action cost model and real-world distance / time conversion
for the BuildingPath navigation system.

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

# Vertical transitions — time-calibrated.
# 1 abstract unit = 0.32 m / 1.4 m/s ≈ 0.2286 s
COST_ELEVATOR_ENTRY = 109.2  # ≈ 25 s — one-time boarding cost (wait + door cycle)
COST_ELEVATOR_FLOOR =  21.9  # ≈  5 s — per-floor travel cost
COST_STAIR_UP       =  96.2  # ≈ 22 s  (healthy adult, 1 floor ascent)
COST_STAIR_DOWN     =  70.0  # ≈ 16 s  (1 floor descent)
COST_LIFT_UP        = 218.7  # ≈ 50 s  (platform lift, slow door cycle)
COST_LIFT_DOWN      = 218.7  # ≈ 50 s

# ─────────────────────────────────────────────────────────────
# FLOOR-CHANGE TIME PENALTIES  (real-world seconds)
# ─────────────────────────────────────────────────────────────
# elevator_entry: one-time boarding (wait + door cycle).
# elevator_floor: per-floor travel inside the elevator.
# Stair: climbing or descending one floor at moderate pace.
# Accessible lift: slower door cycle and travel.

FLOOR_CHANGE_SECONDS = {
    "elevator_entry": 25,
    "elevator_floor":  5,
    "stair_up"      : 22,
    "stair_down"    : 16,
    "lift"          : 50,
}


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
        return COST_ELEVATOR_ENTRY + COST_ELEVATOR_FLOOR   # single-floor default
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


def _transition_kind(action: str) -> str:
    """Map an action label to a floor-change type string (matches FLOOR_CHANGE_SECONDS keys)."""
    if "ELEVATOR" in action:
        return "elevator_floor"
    if "LIFT" in action:
        return "lift"
    if action == "STAIR_UP":
        return "stair_up"
    return "stair_down"


# ─────────────────────────────────────────────────────────────
# PATH DURATION
# ─────────────────────────────────────────────────────────────

def path_duration(path: list, actions: list = None) -> dict:
    """
    Given a path as a list of (floor, x, y) states, compute
    real-world distance and estimated walking time.

    Parameters
    ----------
    path    : list of (floor, x, y) states
    actions : list of action strings, length == len(path) - 1.
              When provided, used to distinguish elevator / stair / lift
              at each floor transition.  Falls back to 'stair' if absent.

    Returns
    -------
    {
        "distance_m"  : float  total horizontal walking distance in metres,
        "duration_s"  : float  estimated time in seconds,
        "duration_min": float  estimated time in minutes,
    }
    """
    horizontal_pixels = 0.0
    floor_penalties   = 0.0
    elevator_entered  = False   # track whether entry cost was already charged

    for i in range(len(path) - 1):
        f0, x0, y0 = path[i]
        f1, x1, y1 = path[i + 1]

        if f0 == f1:
            horizontal_pixels += math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            elevator_entered = False   # reset once back on a normal floor step
        else:
            # Determine transition type from action label if available
            if actions is not None and i < len(actions):
                kind = _transition_kind(actions[i])
            else:
                kind = "stair_up"   # conservative fallback

            if kind == "elevator_floor":
                if not elevator_entered:
                    floor_penalties  += FLOOR_CHANGE_SECONDS["elevator_entry"]
                    elevator_entered  = True
                floor_penalties += FLOOR_CHANGE_SECONDS["elevator_floor"]
            else:
                elevator_entered = False
                floor_penalties += FLOOR_CHANGE_SECONDS[kind]

    distance_m = pixels_to_metres(horizontal_pixels)
    duration_s = metres_to_seconds(distance_m) + floor_penalties

    return {
        "distance_m"  : round(distance_m, 1),
        "duration_s"  : round(duration_s, 1),
        "duration_min": round(duration_s / 60, 2),
    }


# ─────────────────────────────────────────────────────────────
# ROUTE BREAKDOWN
# ─────────────────────────────────────────────────────────────

def route_breakdown(path: list, actions: list) -> list:
    """
    Decompose a path into human-readable walking segments and
    vertical transitions.

    Parameters
    ----------
    path    : list of (floor, x, y) states
    actions : list of action strings, length == len(path) - 1

    Returns
    -------
    List of segment dicts.  Each dict has a "kind" key:

    Walking segment:
        {
            "kind"      : "walk",
            "floor"     : int,
            "distance_m": float,
            "duration_s": float,
        }

    Vertical transition:
        {
            "kind"      : "elevator" | "stair" | "lift",
            "from_floor": int,
            "to_floor"  : int,
            "direction" : "up" | "down",
            "duration_s": float,
        }
    """
    if not path or not actions:
        return []

    segments         = []
    current_floor    = path[0][0]
    pixel_accum      = 0.0
    elevator_entered = False   # track one-time boarding cost per ride

    def _flush_walk(floor, pixels):
        if pixels > 0:
            dist_m = pixels_to_metres(pixels)
            segments.append({
                "kind"      : "walk",
                "floor"     : floor,
                "distance_m": round(dist_m, 1),
                "duration_s": round(metres_to_seconds(dist_m), 1),
            })

    for i in range(len(path) - 1):
        f0, x0, y0 = path[i]
        f1, x1, y1 = path[i + 1]
        act = actions[i]

        if f0 == f1:
            # Same floor — accumulate horizontal pixels
            pixel_accum += math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            elevator_entered = False   # reset on non-transition step
        else:
            # Floor change — flush any pending walk, then record transition
            _flush_walk(current_floor, pixel_accum)
            pixel_accum = 0.0

            kind_key = _transition_kind(act)

            # Normalize to frontend-expected kind labels
            if kind_key.startswith("stair"):
                kind = "stair"
            elif kind_key.startswith("elevator"):
                kind = "elevator"
            else:
                kind = kind_key   # "lift"

            # Compute duration: elevator charges entry cost only once per ride
            if kind == "elevator":
                dur = FLOOR_CHANGE_SECONDS["elevator_floor"]
                if not elevator_entered:
                    dur += FLOOR_CHANGE_SECONDS["elevator_entry"]
                    elevator_entered = True
            else:
                elevator_entered = False
                dur = FLOOR_CHANGE_SECONDS[kind_key]

            segments.append({
                "kind"      : kind,
                "from_floor": f0,
                "to_floor"  : f1,
                "direction" : "up" if f1 > f0 else "down",
                "duration_s": dur,
            })
            current_floor = f1

    # Flush any remaining walk on the final floor
    _flush_walk(current_floor, pixel_accum)

    return segments
