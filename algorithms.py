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


# 搜索成功后的结果：goal 目标、path 路线、cost 成本、hops 步数。
# created 统计实际加入 frontier 的搜索树节点（包括起点）；expanded 统计取出次数。
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


# 一个 _Node 表示“沿某条路径到达某地点”，不是地图地点本身。
# 同一地点可出现在不同分支；parent 用于回溯，g 是累计成本，depth 是累计步数。
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
    # 去除空白并统一大写；非法名称在这里被拒绝，A* 等别名统一为 AS。
    key = name.strip().upper()
    if key not in METHOD_NAMES:
        known = "BFS, AS, CUS1, CUS2, ALL"
        raise ValueError(f"Unknown method {name!r}. Use one of: {known}")
    return METHOD_NAMES[key]


def euclidean(a: Tuple[Number, Number], b: Tuple[Number, Number]) -> float:
    # 两点直线距离 sqrt((x2-x1)^2 + (y2-y1)^2)，不是输入文件中的边成本。
    return math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))


def _on_path(node: _Node, state: int) -> bool:
    """True if `state` is already on the branch from the root to `node`.

    Skipping those children stops a cycle from making the tree infinite.
    The same graph node may still be created on a different branch.
    """
    # 沿 parent 逐个往回检查，仅禁止当前分支重复，不是全局 visited 集合。
    current: Optional[_Node] = node
    while current is not None:
        if current.state == state:
            return True
        current = current.parent
    return False


def _reconstruct(node: _Node) -> List[int]:
    path: List[int] = []
    # 沿 parent 逐个往回检查，仅禁止当前分支重复，不是全局 visited 集合。
    current: Optional[_Node] = node
    while current is not None:
        path.append(current.state)
        current = current.parent
    # 回溯得到的是目标到起点，反转后才是输出所需的起点到目标。
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
    # heuristic 是剩余工作量的估计，不是实际剩余成本或实际最少步数。
    # 坐标与目标在读入地图时已知，但真实路线仍需要搜索。
    goals = list(problem.goals)
    coords = problem.coords

    def straight_to_goal(state: int) -> float:
        # 已经在目标时，剩余距离为 0。
        if state in problem.goals:
            return 0.0
        # state 是节点编号；coords[state] 取出该节点的 (x, y) 坐标。
        here = coords[state]
        # 到各目标分别算直线距离并取最小值，因为到任意一个目标即成功。
        # AS 用它估计剩余成本：若每条边成本 >= 其直线长度，则不会高估。
        return min(euclidean(here, coords[goal]) for goal in goals)

    # 为 CUS2 计算固定的 L：整张地图所有边中，最大的两端直线距离。
    longest_edge = 0.0
    # adj 是邻接表；src 是边的起点，edges 是从 src 出发的 (终点, 成本) 列表。
    for src, edges in problem.adj.items():
        # dst 是这条边的终点（未必是搜索目标）；_cost 不参与长度计算。
        for dst, _cost in edges:
            # 逐条比较并保留最大直线长度；L 不是最大成本，也不是最长路线。
            longest_edge = max(longest_edge, euclidean(coords[src], coords[dst]))

    # CUS2 的 heuristic：把距离转换成剩余步数的下限估计。
    def moves_left(state: int) -> float:
        # L 为 0 时返回 0，避免除零；CUS2 此时仅按 depth 排序。
        if longest_edge <= 0.0:
            return 0.0
        # 每一步最多跨越 L；若实际还需 k 步，则直线距离 <= k*L。
        # 因此 distance/L <= k，不高估步数；例如 10/4=2.5，实际至少 3 步。
        # 保留小数仅用于优先级排序，不代表实际能走半步。
        return straight_to_goal(state) / longest_edge

    # 返回两个函数而不是两个固定数字，供不同候选节点调用。
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

    # 四种方法都会执行这行，但只有 AS/CUS2 在优先级中使用 heuristic。
    h_cost, h_moves = _heuristics(problem)

    # 共用搜索框架的主要变化点：返回值越小，候选节点越优先。
    def primary(node: _Node) -> float:
        if method == "BFS":
            return node.depth
        if method == "CUS1":
            return node.g
        # AS：累计真实成本 g + 估计剩余成本，目标是最低总成本。
        # 非负成本及上述 heuristic 条件满足时具有相应的最优保证。
        if method == "AS":
            return node.g + h_cost(node.state)
        # CUS2: cheapest estimated move-count. `depth` is moves already made.
        # 方法名已校验，ALL 已排除，前三个分支已 return，剩下只能是 CUS2。
        # CUS2：真实已走步数 + 估计剩余步数；边成本仍记录，但不用于排序。
        return node.depth + h_moves(node.state)

    # Monotonic counter. A smaller value means "added earlier".
    added_at = itertools.count()
    created = 0
    expanded = 0
    # frontier 保存已发现但尚未取出检查的候选路径节点；其他分支不会被忘掉。
    frontier: List[Tuple[float, int, int, _Node]] = []

    def enqueue(node: _Node) -> None:
        # Heap order is: strategy value, then node id, then insertion time.
        # 元组前三项依次排序：分数小优先；同分时编号小优先；再同则先加入优先。
        # 第四项 node 是实际数据；唯一加入序号也避免 Python 比较节点对象。
        # heapq 不保证列表整体有序，但 heappop 会取出当前最小的一项。
        heapq.heappush(frontier, (primary(node), node.state, next(added_at), node))

    created += 1
    # 起点没有 parent；成本为 0，步数为 0；起点也计入 created。
    enqueue(_Node(problem.origin, None, 0, 0))

    while frontier:
        # 从整个 frontier 取最优先的候选，不一定是上次节点的邻居。
        _priority, _state, _when, node = heapq.heappop(frontier)
        expanded += 1
        # 取出后才检查目标，首次生成目标时可能还有更好的候选路径。
        if node.state in problem.goals:
            return SearchResult(
                goal=node.state,
                created=created,
                expanded=expanded,
                path=_reconstruct(node),
                cost=node.g,
                hops=node.depth,
            )
        # 仅沿当前地点的出边移动；nxt 为下一节点，step_cost 为边成本。
        for nxt, step_cost in problem.neighbors(node.state):
            if _on_path(node, nxt):
                continue
            created += 1
            # 创建子节点：父节点为 node，累计成本加边成本，步数加 1。
            # enqueue 会按所选公式算分并加入 frontier；更便宜的其他分支不会被全局去重。
            enqueue(_Node(nxt, node, node.g + step_cost, node.depth + 1))

    # 候选全部耗尽仍未找到目标，返回 None，由 search.py 输出 No path found。
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
    # 调用链：search.py main -> load_problem -> solve -> tree_search -> 返回并打印。
    # ALL 记录已访问目标集合，使用独立函数；其余四种方法共用 tree_search。
    name = canonical_method(method)
    if name == "ALL":
        return visit_all(problem)
    return tree_search(problem, name)
