"""
ucs.py | astar.py | weighted_astar.py  — combined for clarity
─────────────────────────────────────────────────────────────
All three are thin wrappers around best_first_search() from common.py,
differing only in the priority function f(node).

Uniform-Cost Search  (UCS)
    f(n) = g(n)
    Properties: complete, cost-optimal, no heuristic needed.
    Source: AIMA 4e Figure 3.14 (uniform_cost_search).

A* Search
    f(n) = g(n) + h(n)
    Properties: complete, cost-optimal when h is admissible.
    Source: AIMA 4e Section 3.5.2 (astar_search).

Weighted A*
    f(n) = g(n) + w * h(n),  w >= 1
    Properties: complete, w-admissible (solution cost <= w * optimal).
    Trades optimality for speed by inflating the heuristic.
    Source: AIMA 4e Section 3.5.3 (weighted_astar_search).
"""

from .common import best_first_search, g


# ─────────────────────────────────────────────────────────────
# UNIFORM-COST SEARCH
# ─────────────────────────────────────────────────────────────

def uniform_cost_search(problem):
    """
    Uniform-cost search: expand the node with lowest path cost first.
    Equivalent to Dijkstra's algorithm on the search graph.

    Returns
    -------
    (solution_node, stats)
    """
    return best_first_search(problem, f=g)


# ─────────────────────────────────────────────────────────────
# A* SEARCH
# ─────────────────────────────────────────────────────────────

def astar_search(problem, h=None):
    """
    A* search: expand nodes with lowest f(n) = g(n) + h(n) first.

    Parameters
    ----------
    problem : Problem subclass
    h       : callable Node -> float
              Admissible heuristic.  Defaults to problem.h (returns 0).

    Returns
    -------
    (solution_node, stats)
    """
    h = h or problem.h
    return best_first_search(problem, f=lambda n: g(n) + h(n))


# ─────────────────────────────────────────────────────────────
# WEIGHTED A* SEARCH
# ─────────────────────────────────────────────────────────────

def weighted_astar_search(problem, h=None, weight=1.5):
    """
    Weighted A* search: f(n) = g(n) + weight * h(n).

    A weight of 1.0 reduces to standard A*.
    A weight > 1 inflates the heuristic, directing search more
    aggressively toward the goal at the cost of strict optimality.
    The solution cost is guaranteed to be at most `weight` times
    the optimal cost (w-admissible).

    Parameters
    ----------
    problem : Problem subclass
    h       : callable Node -> float
    weight  : float  >= 1.0  (default 1.5)

    Returns
    -------
    (solution_node, stats)
    """
    h = h or problem.h
    return best_first_search(problem, f=lambda n: g(n) + weight * h(n))
