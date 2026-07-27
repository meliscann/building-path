"""
bfs.py
─────────────────────────────────────────────────────────────
Breadth-First Search (AIMA 4e, Figure 3.9).

Properties
----------
Complete    : Yes (finite graph)
Optimal     : Yes  — minimises number of steps (not cost)
Time        : O(b^d)
Space       : O(b^d)  (must keep entire frontier in memory)

BFS finds the shallowest (fewest-step) goal.
It ignores action costs, so it is NOT cost-optimal when costs differ.
Use UCS or A* when cost optimality is required.
"""

from common import Node, FIFOQueue, failure, expand


def breadth_first_search(problem):
    """
    Breadth-first graph search (AIMA 4e).

    Returns
    -------
    (solution_node, stats)

    solution_node : Node   goal node if found; `failure` otherwise
    stats         : dict   {
        "nodes_expanded" : int   nodes popped and processed,
        "nodes_generated": int   nodes pushed onto frontier,
    }
    """
    stats = {"nodes_expanded": 0, "nodes_generated": 1}

    node = Node(problem.initial)

    # Early goal check at the root
    if problem.is_goal(problem.initial):
        return node, stats

    frontier = FIFOQueue([node])
    reached  = {problem.initial}          # states seen (no cost tracking needed)

    while frontier:
        node = frontier.pop()              # pop from the RIGHT (FIFO: append-left)
        stats["nodes_expanded"] += 1

        for child in expand(problem, node):
            s = child.state

            # Early goal test: check before adding to frontier
            if problem.is_goal(s):
                return child, stats

            if s not in reached:
                reached.add(s)
                frontier.appendleft(child)
                stats["nodes_generated"] += 1

    return failure, stats
