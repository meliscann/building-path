"""
heuristics.py
─────────────────────────────────────────────────────────────
Admissible heuristic functions for multi-floor campus navigation.

All heuristics are admissible (never over-estimate) and consistent
(monotone) for their respective cost models, making them suitable
for A*, Weighted A*, and Bidirectional A*.
"""

import math


# ─────────────────────────────────────────────────────────────
# LOW-LEVEL DISTANCE FUNCTIONS
# ─────────────────────────────────────────────────────────────

def manhattan_2d(x0, y0, x1, y1) -> float:
    """Manhattan distance on a 2-D grid (4-directional movement)."""
    return abs(x0 - x1) + abs(y0 - y1)


def euclidean_2d(x0, y0, x1, y1) -> float:
    """Euclidean distance on a 2-D grid (8-directional movement)."""
    return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)


def chebyshev_2d(x0, y0, x1, y1) -> float:
    """
    Chebyshev (L-infinity) distance.
    Admissible lower bound for 8-directional unit-cost grids.
    """
    return max(abs(x0 - x1), abs(y0 - y1))


# ─────────────────────────────────────────────────────────────
# VERTICAL CELL INDEX
# ─────────────────────────────────────────────────────────────

def build_vertical_index(campus_map):
    """
    For each floor, collect (x, y) positions of vertical-transition
    cells (elevators 'E', stairs 'S', accessible lifts 'A').

    Returns:
        list[set[tuple[int,int]]]   one set per floor
    """
    vertical = []
    for floor in campus_map:
        cells = set()
        for y, row in enumerate(floor):
            for x, ch in enumerate(row):
                if ch in ('E', 'S', 'A'):
                    cells.add((x, y))
        vertical.append(cells)
    return vertical


# ─────────────────────────────────────────────────────────────
# COST-AWARE MULTI-FLOOR HEURISTIC
# ─────────────────────────────────────────────────────────────

def make_heuristic(goals, campus_map,
                   move_cost=1, min_vertical_cost=2,
                   diagonal=True):
    """
    Build an admissible, cost-aware heuristic for multi-floor
    campus navigation with multiple possible goal states.

    The heuristic lower-bounds the true path cost by considering:
      - 2-D distance to the nearest goal on the same floor, or
      - 2-D distance to the nearest vertical-transfer cell +
        floor-change cost + 2-D distance from transfer to goal.

    Parameters
    ----------
    goals             : iterable of (floor, x, y)
    campus_map        : 3-D grid list
    move_cost         : cost of a single cardinal step (default 1)
    min_vertical_cost : cheapest floor-change cost (elevator = 2)
    diagonal          : True -> use Euclidean 2-D distance
                        False -> use Manhattan 2-D distance

    Returns
    -------
    h : callable  Node -> float
    """
    goals         = list(goals)
    vertical_idx  = build_vertical_index(campus_map)
    dist_2d       = euclidean_2d if diagonal else manhattan_2d

    def dist_to_nearest_vertical(f, x, y):
        cells = vertical_idx[f]
        if not cells:
            return 0.0
        return min(dist_2d(x, y, cx, cy) for (cx, cy) in cells)

    def h(node):
        f, x, y = node.state
        d_vert   = move_cost * dist_to_nearest_vertical(f, x, y)
        best     = math.inf

        for (gf, gx, gy) in goals:
            d_xy   = move_cost * dist_2d(x, y, gx, gy)
            df     = abs(f - gf)

            if df == 0:
                cost_lb = d_xy
            else:
                cost_lb = d_xy + d_vert + min_vertical_cost * df

            best = min(best, cost_lb)

        return best

    return h


# ─────────────────────────────────────────────────────────────
# EUCLIDEAN HEURISTIC  (for Theta* / any-angle)
# ─────────────────────────────────────────────────────────────

def make_euclidean_heuristic(goals, move_cost=1, min_vertical_cost=2):
    """
    Lightweight Euclidean heuristic for Theta*.
    Uses straight-line 2-D distance; ignores floor-change detail.

    Returns
    -------
    h : callable  Node -> float
    """
    goals = list(goals)

    def h(node):
        f, x, y = node.state
        best = math.inf
        for (gf, gx, gy) in goals:
            d_xy = euclidean_2d(x, y, gx, gy) * move_cost
            df   = abs(f - gf)
            cost_lb = d_xy + min_vertical_cost * df
            best = min(best, cost_lb)
        return best

    return h
