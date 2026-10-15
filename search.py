"""COS30019 Assignment 2 Part A — route finding from the command line.

    python search.py <filename> <method>

Methods for this team (2 people, as agreed with the tutor):
    BFS    breadth-first search                         (uninformed)
    AS     A* with straight-line distance               (informed)
    CUS1   uniform-cost search                          (custom uninformed)
    CUS2   A* that minimises the number of moves        (custom informed)

Optional research method:
    ALL    shortest-cost walk that visits every destination

When a goal is reached the program prints three lines:
    filename method
    goal number_of_nodes
    path

number_of_nodes counts search-tree nodes that were created (the start node,
plus every successor that was actually added to the frontier). It is not the
number of nodes in the map.

The path is the sequence of graph-node ids from the origin to the goal,
separated by spaces. Reaching any one destination is enough for BFS/AS/CUS1/CUS2.
"""

from __future__ import annotations

import sys

from algorithms import canonical_method, solve
from problem import ParseError, load_problem


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python search.py <filename> <method>", file=sys.stderr)
        print("Methods: BFS, AS, CUS1, CUS2", file=sys.stderr)
        print("Optional research method: ALL", file=sys.stderr)
        return 1

    filename = argv[1]
    try:
        method = canonical_method(argv[2])
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        problem = load_problem(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}", file=sys.stderr)
        return 1
    except ParseError as exc:
        print(f"Could not read problem file: {exc}", file=sys.stderr)
        return 1

    result = solve(problem, method)
    # The method name printed is the official one (BFS, AS, CUS1, CUS2, ALL).
    print(f"{filename} {method}")
    if result is None:
        print("No path found")
        return 0

    print(f"{result.goal} {result.created}")
    print(" ".join(str(node) for node in result.path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
