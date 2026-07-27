"""
idastar.py
─────────────────────────────────────────────────────────────
Iterative Deepening A* (IDA*).

IDA* performs a series of depth-first searches with an
increasing cost threshold (the "bound").  Each iteration
expands all nodes whose f(n) = g(n) + h(n) does not exceed
the current bound.  The bound is tightened to the smallest
f-value that exceeded the previous bound.

Properties
----------
Complete    : Yes
Optimal     : Yes  (when h is admissible)
Time        : O(b^d)  (same asymptotic as A*, more constant factor)
Space       : O(d)   — only the current path is stored (key advantage)

Best suited for memory-constrained environments or very large grids
where A*'s reached table would exhaust available RAM.

Reference
---------
Korf, R.E. (1985). "Depth-first iterative-deepening: An optimal
admissible tree search." Artificial Intelligence, 27(1), 97-109.

Adapted from AIMA 4e pseudocode (Russell & Norvig, 2020).
"""

import math
from .common import Node, expand, failure, cutoff


# Sentinel returned by the recursive helper to signal goal found
_FOUND = object()


def idastar_search(problem, h=None):
    """
    IDA* search.

    Parameters
    ----------
    problem : Problem subclass
    h       : callable Node -> float
              Admissible heuristic.  Defaults to problem.h (returns 0,
              making IDA* equivalent to iterative-deepening DFS).

    Returns
    -------
    (solution_node, stats)

    solution_node  Node  goal node if found; `failure` otherwise
    stats          dict  {
        "nodes_expanded" : int,
        "nodes_generated": int,
        "iterations"     : int  number of deepening iterations,
    }
    """
    h     = h or problem.h
    stats = {"nodes_expanded": 0, "nodes_generated": 1, "iterations": 0}

    root  = Node(problem.initial)
    bound = h(root)

    while True:
        stats["iterations"] += 1
        result, new_bound = _search(root, bound, h, problem, stats)

        if result is _FOUND:
            # Solution stored in stats["_solution"]
            return stats.pop("_solution"), stats

        if new_bound == math.inf:
            return failure, stats

        bound = new_bound


def _search(node, bound, h, problem, stats):
    """
    Recursive DFS contour search.

    Returns
    -------
    (_FOUND, bound)        if goal is reached
    (None, next_bound)     otherwise; next_bound is the minimum
                           f-value that exceeded `bound` this pass
    """
    f = node.path_cost + h(node)

    if f > bound:
        return None, f                    # prune this branch

    if problem.is_goal(node.state):
        stats["_solution"] = node
        return _FOUND, bound

    stats["nodes_expanded"] += 1
    minimum = math.inf

    for child in expand(problem, node):
        stats["nodes_generated"] += 1

        # Cycle check: skip if child state already on current path
        if _on_path(child):
            continue

        result, t = _search(child, bound, h, problem, stats)

        if result is _FOUND:
            return _FOUND, bound

        minimum = min(minimum, t)

    return None, minimum


def _on_path(node) -> bool:
    """Return True if node.state appears in its own ancestry."""
    state  = node.state
    cursor = node.parent
    while cursor is not None:
        if cursor.state == state:
            return True
        cursor = cursor.parent
    return False
