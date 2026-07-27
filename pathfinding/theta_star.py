"""
theta_star.py
─────────────────────────────────────────────────────────────
Theta* — Any-Angle Path Planning on Grids.

Standard A* is constrained to grid edges: paths can only turn at
grid cell centres, producing characteristic "staircase" routes that
are longer than necessary.  Theta* breaks this constraint by checking
line-of-sight (LoS) between a node and its grandparent.  When LoS
exists, the grandparent becomes the parent directly — the path
"shortcuts" across the grid at any angle.

Algorithm
---------
Identical to A* except for update_vertex():
    - Path 1 (standard A*): parent = direct grid neighbour
    - Path 2 (Theta*):      if LoS(grandparent, neighbour)
                                parent = grandparent  (any angle)

Line-of-sight is checked using Bresenham's line algorithm, visiting
every grid cell along the straight segment and rejecting if any wall
('#') is encountered.

Multi-floor note
----------------
LoS is only meaningful within a single floor.  When two states are on
different floors, Path 2 is skipped and the algorithm falls back to
standard A* expansion (Path 1 only).

Reference
---------
Daniel, K., Nash, A., Koenig, S., & Felner, A. (2010).
"Theta*: Any-Angle Path Planning on Grids."
Journal of Artificial Intelligence Research, 39, 533-579.

Properties
----------
Complete    : Yes
Optimal     : Approximately optimal (may deviate slightly from true
              Euclidean shortest path due to LoS discretisation).
              In practice paths are shorter and smoother than A*.
Time        : O(n log n)  similar to A*, LoS check is O(max(w,h))
Space       : O(n)
"""

import math
from .common import Node, PriorityQueue, failure, g


# ─────────────────────────────────────────────────────────────
# LINE-OF-SIGHT  (Bresenham's algorithm)
# ─────────────────────────────────────────────────────────────

def line_of_sight(campus_map, floor, x0, y0, x1, y1) -> bool:
    """
    Return True if a straight line from (x0,y0) to (x1,y1) on
    `floor` passes through no wall ('#') cells.

    Uses Bresenham's line algorithm for integer grid traversal.
    """
    n_rows = len(campus_map[floor])
    n_cols = len(campus_map[floor][0])

    def in_bounds(x, y):
        return 0 <= x < n_cols and 0 <= y < n_rows

    def is_wall(x, y):
        return campus_map[floor][y][x] == '#'

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    cx, cy = x0, y0

    while True:
        if not in_bounds(cx, cy) or is_wall(cx, cy):
            return False
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx  += sx
        if e2 < dx:
            err += dx
            cy  += sy

    return True


# ─────────────────────────────────────────────────────────────
# EUCLIDEAN DISTANCE  (used as move cost in Theta*)
# ─────────────────────────────────────────────────────────────

def _euclidean(x0, y0, x1, y1) -> float:
    return math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)


# ─────────────────────────────────────────────────────────────
# THETA* SEARCH
# ─────────────────────────────────────────────────────────────

def theta_star_search(problem, h=None):
    """
    Theta* any-angle path planning.

    Parameters
    ----------
    problem : BuildingProblem  (diagonal=True recommended for smooth paths)
    h       : callable Node -> float
              Admissible heuristic.  Euclidean-based heuristics work
              best here.  Defaults to problem.h (returns 0).

    Returns
    -------
    (solution_node, stats)

    solution_node  Node  goal node if found; `failure` otherwise
    stats          dict  {
        "nodes_expanded" : int,
        "nodes_generated": int,
        "los_checks"     : int  number of line-of-sight queries,
    }
    """
    h     = h or problem.h
    stats = {"nodes_expanded": 0, "nodes_generated": 1, "los_checks": 0}

    campus_map = problem.campus_map
    start      = Node(problem.initial)

    frontier   = PriorityQueue([start], key=lambda n: g(n) + h(n))
    reached    = {problem.initial: start}   # state -> best Node so far

    while frontier:
        node = frontier.pop()
        stats["nodes_expanded"] += 1

        if problem.is_goal(node.state):
            return node, stats

        for child in _expand(problem, node):
            s            = child.state
            f_child, x_child, y_child = s

            # ── Theta* update_vertex ──────────────────────────
            # Try Path 2: connect directly to grandparent via LoS
            grandparent = node.parent
            updated     = False

            if grandparent is not None:
                gf, gx, gy = grandparent.state
                stats["los_checks"] += 1

                if (gf == f_child and                       # same floor
                        line_of_sight(campus_map, gf,
                                      gx, gy, x_child, y_child)):
                    # Direct path cost: grandparent -> child (Euclidean)
                    d2 = _euclidean(gx, gy, x_child, y_child)
                    gp_cost = grandparent.path_cost + d2

                    if s not in reached or gp_cost < reached[s].path_cost:
                        shortcut = Node(s, grandparent, child.action, gp_cost)
                        reached[s] = shortcut
                        frontier.add(shortcut)
                        stats["nodes_generated"] += 1
                        updated = True

            # ── Path 1 (standard A* fallback) ─────────────────
            if not updated:
                if s not in reached or child.path_cost < reached[s].path_cost:
                    reached[s] = child
                    frontier.add(child)
                    stats["nodes_generated"] += 1

    return failure, stats


def _expand(problem, node):
    """
    Yield child nodes using the problem's action / result / cost model.
    (Identical to common.expand; reproduced here for self-containment.)
    """
    s = node.state
    for action in problem.actions(s):
        s1   = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s1)
        yield Node(s1, node, action, cost)
