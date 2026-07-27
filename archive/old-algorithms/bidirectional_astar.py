"""
bidirectional_astar.py
─────────────────────────────────────────────────────────────
Bidirectional A* Search.

Two simultaneous searches — one forward from the initial state,
one backward from the goal — that terminate when their frontiers
meet, typically after expanding far fewer nodes than one-directional A*.

Algorithm
---------
Based on: Kaindl, H. & Kainz, G. (1997).
          "Bidirectional Heuristic Search Reconsidered." JAIR 7.
          Adapted from AIMA 4e bidirectional_best_first_search.

At each step the frontier with the smaller top-f value is expanded.
A candidate solution is updated whenever the two `reached` dicts
share a state.  Search terminates when the best candidate is
guaranteed optimal:

    solution.path_cost <= g(top_f) + g(top_b)

where top_f / top_b are the cheapest unexpanded nodes on each frontier.

Vertical transitions (elevators, stairs)
-----------------------------------------
The backward search starts at the goal and expands using the same
action set.  Because the campus graph is symmetric for horizontal
movement and elevator costs, this is correct.  Stair costs are
asymmetric (UP=12, DOWN=6); the backward search uses reversed
stair costs via `_reversed_action_cost`.

Returns
-------
(solution_node, stats)

solution_node  Node  a node whose path reconstructs the full route;
                      path_cost holds the optimal cost.
stats          dict  {nodes_expanded, nodes_generated}
"""

import math
from common import (Node, PriorityQueue, expand, failure,
                    path_states, path_actions, g)
from costs  import (COST_MOVE_CARDINAL, COST_MOVE_DIAGONAL,
                    COST_ELEVATOR_UP, COST_ELEVATOR_DOWN,
                    COST_STAIR_UP, COST_STAIR_DOWN,
                    COST_LIFT_UP, COST_LIFT_DOWN)


# ─────────────────────────────────────────────────────────────
# REVERSED ACTION COSTS
# For the backward search, UP and DOWN stair actions swap costs.
# ─────────────────────────────────────────────────────────────

def _reversed_action_cost(action: str) -> float:
    """Cost of `action` when traversed in reverse direction."""
    if action in ("MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W"):
        return COST_MOVE_CARDINAL
    if action in ("MOVE_NE", "MOVE_NW", "MOVE_SE", "MOVE_SW"):
        return COST_MOVE_DIAGONAL
    if action in ("ELEVATOR_UP", "ELEVATOR_DOWN"):
        return COST_ELEVATOR_UP
    if action == "STAIR_UP":    # reversed: was going up -> now going down
        return COST_STAIR_DOWN
    if action == "STAIR_DOWN":  # reversed: was going down -> now going up
        return COST_STAIR_UP
    if action in ("LIFT_UP", "LIFT_DOWN"):
        return COST_LIFT_UP
    return COST_MOVE_CARDINAL


# ─────────────────────────────────────────────────────────────
# NODE JOINING
# ─────────────────────────────────────────────────────────────

def _join_nodes(nf: Node, nb: Node) -> Node:
    """
    Concatenate the backward path (nb -> goal) onto the forward
    path (start -> nf) to produce a single solution node.

    The backward path is reversed: we walk from nb back toward
    the goal, re-parenting each step onto the growing forward path.
    """
    join = nf
    while nb.parent is not None:
        cost = join.path_cost + nb.path_cost - nb.parent.path_cost
        join = Node(nb.parent.state, join, nb.action, cost)
        nb   = nb.parent
    return join


# ─────────────────────────────────────────────────────────────
# BACKWARD EXPANSION
# ─────────────────────────────────────────────────────────────

def _expand_backward(problem, node: Node):
    """
    Expand `node` for the backward search.

    We use the same `actions()` and `result()` as the forward
    problem — the graph is treated as undirected for horizontal
    moves.  Only stair costs are swapped via _reversed_action_cost.
    """
    s = node.state
    for action in problem.actions(s):
        s1   = problem.result(s, action)
        cost = node.path_cost + _reversed_action_cost(action)
        yield Node(s1, node, action, cost)


# ─────────────────────────────────────────────────────────────
# BIDIRECTIONAL A* SEARCH
# ─────────────────────────────────────────────────────────────

def bidirectional_astar_search(problem, h_f=None, h_b=None):
    """
    Bidirectional A* search.

    Parameters
    ----------
    problem : CampusProblem  (must have a single goal in problem.goals)
    h_f     : callable Node -> float  forward heuristic  (h(n, goal))
    h_b     : callable Node -> float  backward heuristic (h(n, start))
              If None, zero heuristic is used (reduces to Bidirectional UCS).

    Returns
    -------
    (solution_node, stats)
    """
    # Bidirectional A* requires exactly one goal
    if not problem.goals:
        return failure, {"nodes_expanded": 0, "nodes_generated": 0}
    goal = next(iter(problem.goals))

    stats     = {"nodes_expanded": 0, "nodes_generated": 2}
    h_f       = h_f or (lambda n: 0)
    h_b       = h_b or (lambda n: 0)

    # Forward frontier: start -> goal
    node_f    = Node(problem.initial)
    ff        = lambda n: g(n) + h_f(n)
    frontier_f = PriorityQueue([node_f], key=ff)
    reached_f  = {problem.initial: node_f}

    # Backward frontier: goal -> start
    node_b     = Node(goal)
    fb         = lambda n: g(n) + h_b(n)
    frontier_b = PriorityQueue([node_b], key=fb)
    reached_b  = {goal: node_b}

    solution   = failure

    while frontier_f and frontier_b:
        # Termination condition: best candidate <= min frontier cost
        if solution.path_cost <= g(frontier_f.top()) + g(frontier_b.top()):
            return solution, stats

        # Expand the frontier with the smaller top f-value
        if ff(frontier_f.top()) <= fb(frontier_b.top()):
            solution = _proceed_forward(
                problem, frontier_f, reached_f, reached_b, solution, stats)
        else:
            solution = _proceed_backward(
                problem, frontier_b, reached_b, reached_f, solution, stats)

    return solution, stats


def _proceed_forward(problem, frontier, reached_f, reached_b, solution, stats):
    """Expand one node from the forward frontier."""
    node = frontier.pop()
    stats["nodes_expanded"] += 1

    for child in expand(problem, node):
        s = child.state
        if s not in reached_f or child.path_cost < reached_f[s].path_cost:
            reached_f[s] = child
            frontier.add(child)
            stats["nodes_generated"] += 1

            if s in reached_b:
                candidate = _join_nodes(child, reached_b[s])
                if candidate.path_cost < solution.path_cost:
                    solution = candidate

    return solution


def _proceed_backward(problem, frontier, reached_b, reached_f, solution, stats):
    """Expand one node from the backward frontier."""
    node = frontier.pop()
    stats["nodes_expanded"] += 1

    for child in _expand_backward(problem, node):
        s = child.state
        if s not in reached_b or child.path_cost < reached_b[s].path_cost:
            reached_b[s] = child
            frontier.add(child)
            stats["nodes_generated"] += 1

            if s in reached_f:
                candidate = _join_nodes(reached_f[s], child)
                if candidate.path_cost < solution.path_cost:
                    solution = candidate

    return solution
