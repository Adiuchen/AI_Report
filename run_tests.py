"""Check the four search methods against the maps in tests/.

    python run_tests.py

Prints one row per map and method, then FAIL lines if a result is wrong.
This file is for the team. The marker runs search.py, not this script.
"""

from __future__ import annotations

import heapq
import itertools
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

from algorithms import euclidean, solve
from problem import Number, Problem, load_problem

# Resolve map and script paths relative to this file, not the terminal working directory.
ROOT = os.path.dirname(os.path.abspath(__file__))
METHODS = ("BFS", "AS", "CUS1", "CUS2")

# Paths that the tie-break rules fix completely. Other maps are checked
# for "optimal cost / optimal hops" rather than one exact path.
EXPECTED_PATHS = {
    "03_origin_is_goal.txt": {"BFS": [1], "AS": [1], "CUS1": [1], "CUS2": [1]},
    "05_hops_vs_cost.txt": {
        "BFS": [1, 4],
        "CUS2": [1, 4],
        "AS": [1, 2, 3, 4],
        "CUS1": [1, 2, 3, 4],
    },
    "06_one_way_detour.txt": {
        "BFS": [1, 4, 3, 2],
        "AS": [1, 4, 3, 2],
        "CUS1": [1, 4, 3, 2],
        "CUS2": [1, 4, 3, 2],
    },
    "07_tie_smaller_node.txt": {
        "BFS": [1, 2, 4],
        "AS": [1, 2, 4],
        "CUS1": [1, 2, 4],
        "CUS2": [1, 2, 4],
    },
    "08_chronological_tie.txt": {
        "BFS": [1, 2, 4],
        "CUS2": [1, 2, 4],
        "AS": [1, 3, 4],
        "CUS1": [1, 3, 4],
    },
    "09_linear_chain.txt": {
        "BFS": [1, 2, 3, 4, 5],
        "AS": [1, 2, 3, 4, 5],
        "CUS1": [1, 2, 3, 4, 5],
        "CUS2": [1, 2, 3, 4, 5],
    },
    "10_dead_end.txt": {
        "BFS": [1, 3, 4],
        "AS": [1, 3, 4],
        "CUS1": [1, 3, 4],
        "CUS2": [1, 3, 4],
    },
    "11_cycle.txt": {
        "BFS": [1, 2, 3],
        "AS": [1, 2, 3],
        "CUS1": [1, 2, 3],
        "CUS2": [1, 2, 3],
    },
    "12_any_destination.txt": {
        "BFS": [1, 6],
        "CUS2": [1, 6],
        "AS": [1, 2, 4],
        "CUS1": [1, 2, 4],
    },
    "14_single_edge.txt": {
        "BFS": [1, 2],
        "AS": [1, 2],
        "CUS1": [1, 2],
        "CUS2": [1, 2],
    },
    "15_self_loop.txt": {
        "BFS": [1, 2],
        "AS": [1, 2],
        "CUS1": [1, 2],
        "CUS2": [1, 2],
    },
    "16_parallel_edges.txt": {
        "BFS": [1, 2, 3],
        "AS": [1, 2, 3],
        "CUS1": [1, 2, 3],
        "CUS2": [1, 2, 3],
    },
}


# Independent reference solver: this does not call the production tree-search loop.
def dijkstra(problem: Problem, source: int, target: int, hop: bool = False) -> Optional[Tuple[List[int], Number]]:
    """Shortest path on the graph itself. Independent of tree_search."""
    if source == target:
        return [source], 0
    best: Dict[int, Number] = {source: 0}
    parent: Dict[int, int] = {}
    heap: List[Tuple[Number, int]] = [(0, source)]
    closed = set()
    while heap:
        g, node = heapq.heappop(heap)
        if node in closed:
            continue
        if g != best.get(node):
            continue
        closed.add(node)
        if node == target:
            path = [node]
            while node != source:
                node = parent[node]
                path.append(node)
            path.reverse()
            return path, g
        for nxt, cost in problem.neighbors(node):
            # hop=True treats every edge as one move; otherwise use its actual cost.
            step: Number = 1 if hop else cost
            new_g = g + step
            # Relax an edge only when it improves the best known value for that node.
            if new_g < best.get(nxt, float("inf")):
                best[nxt] = new_g
                parent[nxt] = node
                heapq.heappush(heap, (new_g, nxt))
    return None


# Find the best reachable goal value, independently for cost and for moves.
def optimal_to_any_goal(problem: Problem, hop: bool = False) -> Optional[Number]:
    """Best cost, or best hop count, from the origin to any destination."""
    best: Optional[Number] = None
    for goal in problem.destinations:
        found = dijkstra(problem, problem.origin, goal, hop=hop)
        if found is None:
            continue
        _path, value = found
        if best is None or value < best:
            best = value
    return best


def edge_is_admissible(problem: Problem) -> bool:
    """True when every edge costs at least its straight-line length."""
    for src, edges in problem.adj.items():
        for dst, cost in edges:
            length = euclidean(problem.coords[src], problem.coords[dst])
            # A tiny tolerance avoids rejecting equality due to floating-point rounding.
            if float(cost) + 1e-9 < length:
                return False
    return True


def path_cost(problem: Problem, path: List[int]) -> Optional[Number]:
    """Sum of the cheapest edge on each step. None if a step has no edge."""
    total: Number = 0
    # Pair consecutive path nodes to inspect each traversed edge.
    for src, dst in zip(path, path[1:]):
        costs = [cost for nxt, cost in problem.adj.get(src, []) if nxt == dst]
        if not costs:
            return None
        total += min(costs)
    return total


def visit_all_cost(problem: Problem) -> Optional[Number]:
    """Optimal cost of visiting every destination, via the metric closure.

    Non-negative edge costs: try every order of the destinations and join
    the pairwise shortest paths. The origin stays fixed as the start.
    """
    remaining = []
    for goal in problem.destinations:
        if goal != problem.origin and goal not in remaining:
            remaining.append(goal)
    if problem.origin in problem.goals and not remaining:
        return 0
    best: Optional[Number] = None
    # Try every goal order; feasible for these small tests, but factorial in goal count.
    for order in itertools.permutations(remaining):
        cursor = problem.origin
        total: Number = 0
        ok = True
        for goal in order:
            found = dijkstra(problem, cursor, goal, hop=False)
            if found is None:
                ok = False
                break
            _path, cost = found
            total += cost
            cursor = goal
        if ok and (best is None or total < best):
            best = total
    return best


# Run the actual entry script in a subprocess to check its public command-line behavior.
def run_cli(filename: str, method: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        # Use the same Python interpreter that is running this test harness.
        [sys.executable, os.path.join(ROOT, "search.py"), filename, method],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )


def main() -> int:
    os.chdir(ROOT)
    errors: List[str] = []
    rows: List[str] = []
    header = f"{'map':<28} {'method':<6} {'goal':>4} {'cost':>6} {'hops':>4} {'created':>8} {'expanded':>8} path"
    rows.append(header)

    # Exclude deliberately malformed 99_ fixtures from the normal search cases.
    map_names = sorted(
        name
        for name in os.listdir(os.path.join(ROOT, "tests"))
        if name.endswith(".txt") and not name.startswith("99_")
    )

    for name in map_names:
        rel = f"tests/{name}"
        problem = load_problem(os.path.join(ROOT, rel))
        admissible = edge_is_admissible(problem)
        # Compute reference optima before comparing the methods with different objectives.
        best_cost = optimal_to_any_goal(problem, hop=False)
        best_hops = optimal_to_any_goal(problem, hop=True)
        methods = list(METHODS)
        if name == "17_visit_all.txt":
            methods.append("ALL")

        for method in methods:
            # Compare the in-process result with a separate command-line invocation.
            result = solve(problem, method)
            proc = run_cli(rel, method)
            if proc.returncode != 0:
                errors.append(f"{name} {method}: CLI exit {proc.returncode}: {proc.stderr.strip()}")
                continue
            # Normalize Windows line endings before checking the exact output format.
            stdout = proc.stdout.replace("\r\n", "\n")
            if stdout.endswith("\n"):
                stdout = stdout[:-1]
            lines = stdout.split("\n") if stdout else []

            if result is None:
                if best_cost is not None and method != "ALL":
                    errors.append(f"{name} {method}: reported no path, but a path exists")
                if lines != [f"{rel} {method}", "No path found"]:
                    errors.append(f"{name} {method}: unexpected no-path output {lines!r}")
                rows.append(f"{name:<28} {method:<6} {'-':>4} {'-':>6} {'-':>4} {'-':>8} {'-':>8} NO PATH")
                continue

            official = [
                f"{rel} {method}",
                f"{result.goal} {result.created}",
                " ".join(str(node) for node in result.path),
            ]
            arrow_path = " -> ".join(str(node) for node in result.path)
            if lines[:3] != official:
                errors.append(f"{name} {method}: CLI output does not match the library result: {lines!r}")
            if f"cost: {result.cost}" not in lines or f"path: {arrow_path}" not in lines:
                errors.append(f"{name} {method}: missing cost or arrow path in {lines!r}")

            # Validate endpoints, goal membership, hop count, and edge existence.
            if result.path[0] != problem.origin or result.path[-1] != result.goal:
                errors.append(f"{name} {method}: path endpoints are wrong: {result.path}")
            if result.goal not in problem.goals and method != "ALL":
                errors.append(f"{name} {method}: goal {result.goal} is not a destination")
            if result.hops != len(result.path) - 1:
                errors.append(f"{name} {method}: hop count does not match the path")
            paid = path_cost(problem, result.path)
            if paid is None:
                errors.append(f"{name} {method}: a step in {result.path} has no edge")
            elif method != "ALL" and paid != result.cost:
                # Parallel edges: path_cost uses the cheaper edge. The search
                # may only be wrong if its stored cost is below every real edge.
                step_ok = True
                summed = 0
                for src, dst in zip(result.path, result.path[1:]):
                    costs = [c for nxt, c in problem.adj[src] if nxt == dst]
                    if result.cost < 0:
                        step_ok = False
                    summed += min(costs)
                if not step_ok:
                    errors.append(f"{name} {method}: bad step cost")
                if method in ("AS", "CUS1") and result.cost != summed and result.cost not in _possible_sums(problem, result.path):
                    errors.append(f"{name} {method}: stored cost {result.cost} is not a real path cost")

            # Cost-based methods must match the independent minimum cost.
            if method in ("AS", "CUS1") and best_cost is not None and result.cost != best_cost:
                errors.append(
                    f"{name} {method}: cost {result.cost} is not optimal ({best_cost})"
                )
            # Move-based methods must match the independent minimum number of edges.
            if method in ("BFS", "CUS2") and best_hops is not None and result.hops != best_hops:
                errors.append(
                    f"{name} {method}: hops {result.hops} is not the minimum ({best_hops})"
                )
            if method == "AS" and not admissible:
                errors.append(f"{name}: edge costs are below straight-line length, A* check is not reliable")

            # Exact paths are checked only where fixtures specify deterministic expected results.
            expected = EXPECTED_PATHS.get(name, {}).get(method)
            if expected is not None and result.path != expected:
                errors.append(f"{name} {method}: path {result.path} != expected {expected}")

            if name == "03_origin_is_goal.txt" and result.created != 1:
                errors.append(f"{name} {method}: origin is a goal, created should be 1, got {result.created}")
            if name == "14_single_edge.txt" and result.created != 2:
                errors.append(f"{name} {method}: single edge should create 2 nodes, got {result.created}")
            if name == "16_parallel_edges.txt" and method in ("AS", "CUS1") and result.cost != 4:
                errors.append(f"{name} {method}: should use the cheaper parallel edge, cost {result.cost}")

            # For the extension, validate both total cost and coverage of every goal.
            if method == "ALL":
                needed = visit_all_cost(problem)
                if needed is None:
                    errors.append(f"{name} ALL: brute force found no route but search did")
                elif result.cost != needed:
                    errors.append(f"{name} ALL: cost {result.cost} != optimal {needed}")
                missing = [goal for goal in problem.goals if goal not in result.path]
                if missing:
                    errors.append(f"{name} ALL: path misses destinations {missing}")

            path_text = " ".join(str(node) for node in result.path)
            rows.append(
                f"{name:<28} {method:<6} {result.goal:>4} {result.cost:>6} {result.hops:>4} "
                f"{result.created:>8} {result.expanded:>8} {path_text}"
            )

    # Bad file and bad arguments must fail cleanly, with the error on stderr.
    bad = run_cli("tests/99_bad_format.txt", "BFS")
    if bad.returncode == 0 or not bad.stderr.strip():
        errors.append("bad format file should fail with a message on stderr")
    missing = run_cli("tests/no_such_file.txt", "BFS")
    if missing.returncode == 0:
        errors.append("missing file should fail")
    unknown = run_cli("tests/14_single_edge.txt", "DFS")
    if unknown.returncode == 0:
        errors.append("DFS is not in this team's method list and should be rejected")
    usage = subprocess.run(
        # Use the same Python interpreter that is running this test harness.
        [sys.executable, os.path.join(ROOT, "search.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if usage.returncode == 0:
        errors.append("missing arguments should fail")

    report = "\n".join(rows) + "\n"
    print(report)
    # Save the displayed table and any failures for review and report preparation.
    out_path = os.path.join(ROOT, "test_results.txt")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(report)
        if errors:
            handle.write("\nFAILURES\n")
            handle.write("\n".join(errors) + "\n")

    # A nonzero return code lets callers detect failed checks automatically.
    if errors:
        print(f"{len(errors)} FAILURE(S)")
        for message in errors:
            print(" -", message)
        return 1
    print(f"All checks passed ({len(map_names)} maps).")
    return 0


# Parallel edges can share endpoints but differ in cost; enumerate all valid path totals.
def _possible_sums(problem: Problem, path: List[int]) -> set:
    """Every total cost the path could have if parallel edges are chosen differently."""
    totals = {0}
    # Pair consecutive path nodes to inspect each traversed edge.
    for src, dst in zip(path, path[1:]):
        costs = [c for nxt, c in problem.adj[src] if nxt == dst]
        totals = {total + cost for total in totals for cost in costs}
    return totals


# Run the harness only when invoked directly, not when imported.
if __name__ == "__main__":
    sys.exit(main())
