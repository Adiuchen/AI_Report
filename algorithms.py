"""Tree-search strategies for the route-finding problem.

The four required methods share one tree search. Only the number used to
pick the next node changes:

    BFS   uninformed        expand the shallowest node (fewest edges)
    AS    informed          A*: f = g + h, h = straight-line distance
    CUS1  custom uninformed uniform-cost search: expand the lowest path cost g
    CUS2  custom informed   A* on move count: f = moves + estimated moves left

ALL is an optional extra (see the research note in the report). It finds a
shortest-cost walk that starts at the origin and visits every destination.
"""

from __future__ import annotations

import heapq
import itertools
import math
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

from problem import Number, Problem

# Names the marker will pass on the command line, plus a few aliases.
METHOD_NAMES = {
    "BFS": "BFS",
    "AS": "AS",
    "A*": "AS",
    "ASTAR": "AS",
    "CUS1": "CUS1",
    "UCS": "CUS1",
    "CUS2": "CUS2",
    "ALL": "ALL",
}


class SearchResult:
    """One successful search. `created` is what the program prints."""

    def __init__(
        self,
        goal: int,
        created: int,
        expanded: int,
        path: List[int],
        cost: Number,
        hops: int,
    ) -> None:
        self.goal = goal
        self.created = created
        self.expanded = expanded
        self.path = path
        self.cost = cost
        self.hops = hops


class _Node:
    """One node in the search tree (not the same as a graph node).

    The same graph node can appear many times, once per path that reaches it.
    That is what makes this tree search rather than graph search.
    """

    def __init__(self, state: int, parent: Optional["_Node"], g: Number, depth: int) -> None:
        self.state = state
        self.parent = parent
        self.g = g  # total edge cost from the origin along this path
        self.depth = depth  # number of edges on this path

    def __repr__(self) -> str:
        return f"_Node(state={self.state}, g={self.g}, depth={self.depth})"


def canonical_method(name: str) -> str:
    key = name.strip().upper()
    if key not in METHOD_NAMES:
        known = "BFS, AS, CUS1, CUS2, ALL"
        raise ValueError(f"Unknown method {name!r}. Use one of: {known}")
    return METHOD_NAMES[key]


def euclidean(a: Tuple[Number, Number], b: Tuple[Number, Number]) -> float:
    return math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))


def _on_path(node: _Node, state: int) -> bool:
    """True if `state` is already on the branch from the root to `node`.

    Skipping those children stops a cycle from making the tree infinite.
    The same graph node may still be created on a different branch.
    """
    current: Optional[_Node] = node
    while current is not None:
        if current.state == state:
            return True
        current = current.parent
    return False


def _reconstruct(node: _Node) -> List[int]:
    path: List[int] = []
    current: Optional[_Node] = node
    while current is not None:
        path.append(current.state)
        current = current.parent
    path.reverse()
    return path


def _heuristics(problem: Problem) -> Tuple[Callable[[int], float], Callable[[int], float]]:
    """Return (h_cost, h_moves) for the informed methods.

    h_cost(n) is the straight-line distance to the nearest destination.
    It is admissible for path cost when every edge costs at least as much
    as its own straight-line length (a shorter path cannot exist).

    h_moves(n) estimates remaining moves. One move can cover at most L,
    the longest straight-line edge in the graph, so distance / L cannot
    be larger than the true number of moves still needed.
    """
    goals = list(problem.goals)
    coords = problem.coords

    def straight_to_goal(state: int) -> float:
        if state in problem.goals:
            return 0.0
        here = coords[state]
        return min(euclidean(here, coords[goal]) for goal in goals)

    longest_edge = 0.0
    for src, edges in problem.adj.items():
        for dst, _cost in edges:
            longest_edge = max(longest_edge, euclidean(coords[src], coords[dst]))

    def moves_left(state: int) -> float:
        if longest_edge <= 0.0:
            return 0.0
        return straight_to_goal(state) / longest_edge

    return straight_to_goal, moves_left


def tree_search(problem: Problem, method: str) -> Optional[SearchResult]:
    """General tree search used by BFS, AS, CUS1 and CUS2.

    The goal is tested when a node is taken off the frontier, not when it
    is first generated. For A* and uniform-cost search that is what makes
    the first goal we expand an optimal one: a cheaper path would still be
    waiting in the frontier with a better priority.

    Tie-break, used only when the strategy's own number is equal:
      1. smaller graph-node id first
      2. the node that was added to the frontier earlier first
    """
    method = canonical_method(method)
    if method == "ALL":
        raise ValueError("ALL uses visit_all(), not tree_search()")

    h_cost, h_moves = _heuristics(problem)

    def primary(node: _Node) -> float:
        if method == "BFS":
            return node.depth
        if method == "CUS1":
            return node.g
        if method == "AS":
            return node.g + h_cost(node.state)
        # CUS2: cheapest estimated move-count. `depth` is moves already made.
        return node.depth + h_moves(node.state)

    # Monotonic counter. A smaller value means "added earlier".
    added_at = itertools.count()
    created = 0
    expanded = 0
    frontier: List[Tuple[float, int, int, _Node]] = []

    def enqueue(node: _Node) -> None:
        # Heap order is: strategy value, then node id, then insertion time.
        heapq.heappush(frontier, (primary(node), node.state, next(added_at), node))

    created += 1
    enqueue(_Node(problem.origin, None, 0, 0))

    while frontier:
        _priority, _state, _when, node = heapq.heappop(frontier)
        expanded += 1
        if node.state in problem.goals:
            return SearchResult(
                goal=node.state,
                created=created,
                expanded=expanded,
                path=_reconstruct(node),
                cost=node.g,
                hops=node.depth,
            )
        for nxt, step_cost in problem.neighbors(node.state):
            if _on_path(node, nxt):
                continue
            created += 1
            enqueue(_Node(nxt, node, node.g + step_cost, node.depth + 1))

    return None


class _VisitNode:
    """State for the visit-all search: where we are, and which goals we already touched."""

    def __init__(
        self,
        state: int,
        visited: FrozenSet[int],
        parent: Optional["_VisitNode"],
        g: Number,
    ) -> None:
        self.state = state
        self.visited = visited
        self.parent = parent
        self.g = g


def visit_all(problem: Problem) -> Optional[SearchResult]:
    """Shortest-cost walk from the origin that visits every destination.

    The search state is (current node, set of destinations already visited).
    Edge costs are non-negative, so Dijkstra on that state space is optimal.
    Graph nodes may be entered again when the visited-set is different;
    the same pair (node, visited-set) is not expanded twice.
    """
    goals = set(problem.goals)
    start_visited = frozenset(node for node in goals if node == problem.origin)
    added_at = itertools.count()
    created = 0
    expanded = 0
    frontier: List[Tuple[Number, int, int, _VisitNode]] = []
    # Best cost known for each augmented state. Equal cost does not replace
    # the earlier node, which keeps the "added earlier" tie-break.
    best: Dict[Tuple[int, FrozenSet[int]], Number] = {}
    closed = set()

    def enqueue(node: _VisitNode) -> None:
        best[(node.state, node.visited)] = node.g
        heapq.heappush(frontier, (node.g, node.state, next(added_at), node))

    created += 1
    enqueue(_VisitNode(problem.origin, start_visited, None, 0))

    while frontier:
        g, _state, _when, node = heapq.heappop(frontier)
        key = (node.state, node.visited)
        if g != best.get(key):
            continue
        if key in closed:
            continue
        closed.add(key)
        expanded += 1
        if goals.issubset(node.visited):
            path: List[int] = []
            current: Optional[_VisitNode] = node
            while current is not None:
                path.append(current.state)
                current = current.parent
            path.reverse()
            return SearchResult(
                goal=node.state,
                created=created,
                expanded=expanded,
                path=path,
                cost=node.g,
                hops=len(path) - 1,
            )
        for nxt, step_cost in problem.neighbors(node.state):
            visited = node.visited
            if nxt in goals:
                visited = node.visited | frozenset((nxt,))
            new_g = g + step_cost
            next_key = (nxt, visited)
            old = best.get(next_key)
            if old is not None and new_g >= old:
                continue
            created += 1
            enqueue(_VisitNode(nxt, visited, node, new_g))

    return None


def solve(problem: Problem, method: str) -> Optional[SearchResult]:
    """Run one named method. Returns None when no path exists."""
    name = canonical_method(method)
    if name == "ALL":
        return visit_all(problem)
    return tree_search(problem, name)
