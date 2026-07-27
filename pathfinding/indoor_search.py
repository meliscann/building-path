"""
indoor_search.py
─────────────────────────────────────────────────────────────
BuildingProblem: formal search problem for multi-floor indoor
navigation in any multi-storey building.

State space  : (floor, x, y)  — integer 3-tuple
Actions      : 8 cardinal/diagonal moves + vertical transitions
               via elevator ('E'), stairs ('S'), accessible lift ('A')

Adapted from AIMA 4e Problem class (Russell & Norvig, 2020).

UserProfile support
───────────────────
BuildingProblem accepts an optional UserProfile. The profile:
  - filters forbidden actions (e.g. accessible lift for standard users,
    stairs for wheelchair users)
  - applies cost multipliers (e.g. stairs are more costly for mobility
    impaired users, making the algorithm prefer elevator routes)
"""

import math
from .common         import Problem
from .costs          import action_cost as _base_action_cost
from poi.user_profile import UserProfile, DEFAULT_PROFILE


# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

WALL = '#'

VERTICAL = {
    'E': ('ELEVATOR_UP',   'ELEVATOR_DOWN'),
    'S': ('STAIR_UP',      'STAIR_DOWN'),
}

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


# ─────────────────────────────────────────────────────────────
# CAMPUS PROBLEM
# ─────────────────────────────────────────────────────────────

class BuildingProblem(Problem):
    """
    Multi-floor campus navigation problem.

    Parameters
    ----------
    initial : (floor, x, y)
    campus_map : list[list[list[str]]]
        3-D grid: campus_map[floor][y][x]
    goal : (floor, x, y) or None
    goals : iterable of (floor, x, y), optional
    diagonal : bool
        Allow diagonal movement (default True).
    profile : UserProfile, optional
        Accessibility profile.  Controls which vertical transitions
        are permitted and adjusts their costs.
        Defaults to the standard (non-disabled) profile.
    """

    def __init__(self, initial, campus_map,
                 goal=None, goals=None, diagonal=True,
                 profile: UserProfile = None):
        super().__init__(initial=initial, goal=goal)

        self.campus_map = campus_map
        self.diagonal   = diagonal
        self.profile    = profile or DEFAULT_PROFILE

        self.n_floors   = len(campus_map)
        self.n_rows     = len(campus_map[0])
        self.n_cols     = len(campus_map[0][0])

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

        # Vertical transitions — filter by profile
        c = self.cell(floor, x, y)
        if c in VERTICAL:
            up_act, dn_act = VERTICAL[c]
            for act in (up_act, dn_act):
                # Skip actions forbidden by the user's profile
                if not self.profile.allows_action(act):
                    continue
                nf = floor + 1 if "UP" in act else floor - 1
                if self.is_walkable(nf, x, y):
                    acts.append(act)

        return acts

    def result(self, state, action):
        floor, x, y = state

        if action in ALL_MOVES:
            dx, dy = ALL_MOVES[action]
            nx, ny = x + dx, y + dy
            if self.is_walkable(floor, nx, ny):
                return (floor, nx, ny)
            return state

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
        """
        Base cost from costs.py, scaled by the profile's multiplier.

        Elevator boarding cost (COST_ELEVATOR_ENTRY) is charged once when
        a horizontal MOVE lands on an 'E' cell from a non-'E' cell.
        Each subsequent ELEVATOR_UP/DOWN action charges only COST_ELEVATOR_FLOOR,
        correctly amortising the one-time wait across multi-floor rides.
        """
        from pathfinding.costs import COST_ELEVATOR_ENTRY, COST_ELEVATOR_FLOOR
        multiplier = self.profile.action_cost_multiplier(action)

        if action in ("ELEVATOR_UP", "ELEVATOR_DOWN"):
            return COST_ELEVATOR_FLOOR * multiplier

        base = _base_action_cost(action)

        # Charge one-time boarding cost when stepping onto an elevator cell
        if action in ALL_MOVES:
            sf, sx, sy = s
            s1f, s1x, s1y = s1
            if (self.cell(s1f, s1x, s1y) == 'E' and
                    self.cell(sf, sx, sy) != 'E'):
                elev_mult = self.profile.action_cost_multiplier("ELEVATOR_UP")
                return base + COST_ELEVATOR_ENTRY * elev_mult

        return base * multiplier

    def h(self, node):
        """Default heuristic: 0 (makes A* equivalent to UCS)."""
        return 0


# ─────────────────────────────────────────────────────────────
# UTILITY
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
