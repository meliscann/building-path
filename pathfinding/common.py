"""
common.py
─────────────────────────────────────────────────────────────
AIMA 4th edition (Russell & Norvig, 2020) core data structures,
adapted for multi-floor campus navigation.

Source: S. Russell and P. Norvig, "AIMA-Python," GitHub.
        https://github.com/aimacode/aima-python
"""

import heapq
import math
from collections import deque


# ─────────────────────────────────────────────────────────────
# 1. PROBLEM AND NODE
# ─────────────────────────────────────────────────────────────

class Problem:
    """
    Abstract class for a formal search problem (AIMA 4e).

    Subclasses must implement:
        actions(state)        -> iterable of valid actions
        result(state, action) -> next state

    Override as needed:
        action_cost(s, a, s1) -> cost  (default: 1)
        is_goal(state)        -> bool  (default: state == self.goal)
        h(node)               -> float (default: 0)
    """

    def __init__(self, initial=None, goal=None, **kwds):
        self.initial = initial
        self.goal    = goal
        self.__dict__.update(**kwds)

    def actions(self, state):         raise NotImplementedError
    def result(self, state, action):  raise NotImplementedError
    def is_goal(self, state):         return state == self.goal
    def action_cost(self, s, a, s1):  return 1
    def h(self, node):                return 0

    def __str__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.initial, self.goal)


class Node:
    """
    A node in a search tree (AIMA 4e).

    Attributes:
        state     : state in the problem space
        parent    : Node that generated this one (None for root)
        action    : action applied to parent.state to reach this node
        path_cost : cumulative cost g(n) from initial state to here
    """

    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state     = state
        self.parent    = parent
        self.action    = action
        self.path_cost = path_cost

    def __repr__(self):
        return '<{}>'.format(self.state)

    def __len__(self):
        """Depth of this node in the search tree."""
        return 0 if self.parent is None else (1 + len(self.parent))

    def __lt__(self, other):
        """Tie-breaking for priority queue: lower cost wins."""
        return self.path_cost < other.path_cost


# Sentinel nodes (AIMA 4e convention)
failure = Node('failure', path_cost=math.inf)  # algorithm found no solution
cutoff  = Node('cutoff',  path_cost=math.inf)  # depth / cost limit reached


# ─────────────────────────────────────────────────────────────
# 2. CORE HELPERS
# ─────────────────────────────────────────────────────────────

def expand(problem, node):
    """Expand a node, yielding all valid child nodes."""
    s = node.state
    for action in problem.actions(s):
        s1   = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action, s1)
        yield Node(s1, node, action, cost)


def path_states(node):
    """Return the list of states from root to this node."""
    if node in (cutoff, failure, None):
        return []
    return path_states(node.parent) + [node.state]


def path_actions(node):
    """Return the list of actions from root to this node."""
    if node.parent is None:
        return []
    return path_actions(node.parent) + [node.action]


def is_cycle(node, k=30):
    """
    Return True if this node's path contains a cycle of length <= k.
    Limits recursion to k steps to keep overhead bounded.
    """
    def find_cycle(ancestor, k):
        return (ancestor is not None and k > 0 and
                (ancestor.state == node.state or
                 find_cycle(ancestor.parent, k - 1)))
    return find_cycle(node.parent, k)


def g(node):
    """Shorthand: path cost g(n)."""
    return node.path_cost


# ─────────────────────────────────────────────────────────────
# 3. DATA STRUCTURES
# ─────────────────────────────────────────────────────────────

FIFOQueue = deque   # breadth-first frontier
LIFOQueue = list    # depth-first frontier


class PriorityQueue:
    """
    Min-priority queue (AIMA 4e).
    Always pops the item with minimum key(item) value.
    Backed by a binary heap.
    """

    def __init__(self, items=(), key=lambda x: x):
        self.key   = key
        self.items = []
        for item in items:
            self.add(item)

    def add(self, item):
        heapq.heappush(self.items, (self.key(item), item))

    def pop(self):
        return heapq.heappop(self.items)[1]

    def top(self):
        return self.items[0][1]

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return bool(self.items)


# ─────────────────────────────────────────────────────────────
# 4. BEST-FIRST GRAPH SEARCH  (AIMA 4e, Figure 3.7)
# ─────────────────────────────────────────────────────────────

def best_first_search(problem, f):
    """
    Best-first graph search: explores nodes in non-decreasing order of f(node).

    Instantiations:
        UCS   ->  f = g
        A*    ->  f = g + h
        GBFS  ->  f = h

    Returns:
        (solution_node, stats)

        solution_node  Node  goal node if found; `failure` otherwise
        stats          dict  {
            "nodes_expanded" : int   nodes popped and processed,
            "nodes_generated": int   nodes pushed onto frontier,
        }
    """
    stats = {"nodes_expanded": 0, "nodes_generated": 1}

    node     = Node(problem.initial)
    frontier = PriorityQueue([node], key=f)
    reached  = {problem.initial: node}

    while frontier:
        node = frontier.pop()
        stats["nodes_expanded"] += 1

        if problem.is_goal(node.state):
            return node, stats

        for child in expand(problem, node):
            s = child.state
            if s not in reached or child.path_cost < reached[s].path_cost:
                reached[s] = child
                frontier.add(child)
                stats["nodes_generated"] += 1

    return failure, stats
