"""
campus_search.py
─────────────────────────────────────────────────────────────
CampusProblem: formal search problem for multi-floor indoor
navigation in the Oxford Life and Mind Building.

State space  : (floor, x, y)  — integer 3-tuple
Actions      : 8 cardinal/diagonal moves + vertical transitions
               via elevator ('E'), stairs ('S'), accessible lift ('A')

Adapted from AIMA 4e Problem class (Russell & Norvig, 2020).
"""

import math
from common import Problem
from costs  import action_cost as _action_cost


# ─────────────────────────────────────────────────────────────
# WALKABLE CHARACTER SET
# Any grid cell not containing '#' is considered walkable.
# ─────────────────────────────────────────────────────────────
WALL = '#'

# Vertical transition cells and their action pairs
VERTICAL = {
    'E': ('ELEVATOR_UP',   'ELEVATOR_DOWN'),
    'S': ('STAIR_UP',      'STAIR_DOWN'),
    'A': ('LIFT_UP',       'LIFT_DOWN'),
}

# 8-directional movement: action -> (dx, dy)
CARDINAL_MOVES = {
    'MOVE_N':  ( 0, -1),
    'MOVE_S':  ( 0, +1),
    'MOVE_E':  (+1,  0),
    'MOVE_W':  (-1,  0),
}

DIAGONAL_MOVES = {
    'MOVE_NE': (+1, -1),
    'MOVE_NW': (-1, -1),
    'MOVE_SE': (+1, +1),
    'MOVE_SW': (-1, +1),
}

ALL_MOVES = {**CARDINAL_MOVES, **DIAGONAL_MOVES}


class CampusProblem(Problem):
    """
    Multi-floor campus navigation problem.

    Parameters
    ----------
    initial : (floor, x, y)
        Starting position.
    goal : (floor, x, y) or None
        Single goal state.  Supply `goals` for multi-goal search.
    campus_map : list[list[list[str]]]
        3-D grid: campus_map[floor][y][x] is the cell character.
    goals : iterable of (floor, x, y), optional
        Set of acceptable goal states (nearest-POI search).
    diagonal : bool
        If True (default), allow diagonal movement.
        Set False to restrict to 4-directional movement only.
    """

    def __init__(self, initial, campus_map,
                 goal=None, goals=None, diagonal=True):
        super().__init__(initial=initial, goal=goal)

        self.campus_map  = campus_map
        self.diagonal    = diagonal

        self.n_floors    = len(campus_map)
        self.n_rows      = len(campus_map[0])      # height (y)
        self.n_cols      = len(campus_map[0][0])   # width  (x)

        # Build goal set
        if goals is not None:
            self.goals = set(goals)
        elif goal is not None:
            self.goals = {goal}
        else:
            self.goals = set()

    # ── Bounds and cell access ────────────────────────────────

    def in_bounds(self, f, x, y) -> bool:
        return (0 <= f < self.n_floors and
                0 <= x < self.n_cols  and
                0 <= y < self.n_rows)

    def cell(self, f, x, y) -> str:
        return self.campus_map[f][y][x]

    def is_wall(self, f, x, y) -> bool:
        return self.cell(f, x, y) == WALL

    def is_walkable(self, f, x, y) -> bool:
        return self.in_bounds(f, x, y) and not self.is_wall(f, x, y)

    # ── Problem interface ─────────────────────────────────────

    def is_goal(self, state) -> bool:
        return state in self.goals

    def actions(self, state):
        floor, x, y = state
        acts = []

        # Horizontal movement
        moves = ALL_MOVES if self.diagonal else CARDINAL_MOVES
        for action, (dx, dy) in moves.items():
            nx, ny = x + dx, y + dy
            if self.is_walkable(floor, nx, ny):
                acts.append(action)

        # Vertical transitions
        c = self.cell(floor, x, y)
        if c in VERTICAL:
            up_act, dn_act = VERTICAL[c]
            nf_up = floor + 1
            nf_dn = floor - 1
            if self.is_walkable(nf_up, x, y):
                acts.append(up_act)
            if self.is_walkable(nf_dn, x, y):
                acts.append(dn_act)

        return acts

    def result(self, state, action):
        floor, x, y = state

        if action in ALL_MOVES:
            dx, dy = ALL_MOVES[action]
            nx, ny = x + dx, y + dy
            if self.is_walkable(floor, nx, ny):
                return (floor, nx, ny)
            return state   # blocked; stay put

        # Vertical transitions
        if action in ("ELEVATOR_UP", "STAIR_UP", "LIFT_UP"):
            nf = floor + 1
        elif action in ("ELEVATOR_DOWN", "STAIR_DOWN", "LIFT_DOWN"):
            nf = floor - 1
        else:
            return state

        if self.is_walkable(nf, x, y):
            return (nf, x, y)
        return state

    def action_cost(self, s, action, s1):
        return _action_cost(action)

    def h(self, node):
        """Default heuristic: 0 (makes A* equivalent to UCS)."""
        return 0


# ─────────────────────────────────────────────────────────────
# UTILITY: find all cells of a given character
# ─────────────────────────────────────────────────────────────

def find_cells(campus_map, char):
    """Return list of (floor, x, y) for every cell matching `char`."""
    results = []
    for f, floor in enumerate(campus_map):
        for y, row in enumerate(floor):
            for x, cell in enumerate(row):
                if cell == char:
                    results.append((f, x, y))
    return results
