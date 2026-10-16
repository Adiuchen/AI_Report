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


# Entry flow: parse arguments -> load_problem (problem.py) -> solve (algorithms.py) -> print.
def main(argv: list[str]) -> int:
    # argv includes the script name, so exactly three entries are required.
    if len(argv) != 3:
        print("Usage: python search.py <filename> <method>", file=sys.stderr)
        print("Methods: BFS, AS, CUS1, CUS2", file=sys.stderr)
        print("Optional research method: ALL", file=sys.stderr)
        return 1

    # argv[1] is the map path; argv[2] selects BFS, AS, CUS1, CUS2, or ALL.
    filename = argv[1]
    try:
        # Validate the method and normalize aliases such as A* to AS.
        method = canonical_method(argv[2])
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        # Build a Problem containing coordinates, outgoing edges, origin, and goals.
        problem = load_problem(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}", file=sys.stderr)
        return 1
    except ParseError as exc:
        print(f"Could not read problem file: {exc}", file=sys.stderr)
        return 1

    # solve dispatches to the shared tree search, or the separate ALL extension.
    result = solve(problem, method)
    # The method name printed is the official one (BFS, AS, CUS1, CUS2, ALL).
    print(f"{filename} {method}")
    # An unreachable goal is a completed search, not an invalid invocation.
    if result is None:
        print("No path found")
        return 0

    # Print the goal and CREATED search-node count, followed by the reconstructed path.
    print(f"{result.goal} {result.created}")
    print(" ".join(str(node) for node in result.path))
    # The three lines above are the format the marker's batch test reads.
    # The lines below only name those numbers so the path is easier to read.
    print(f"node (goal): {result.goal}")
    print(f"nodes created: {result.created}")
    print(f"cost: {result.cost}")
    print(f"steps: {result.hops}")
    print("path: " + " -> ".join(str(node) for node in result.path))
    return 0


# Direct execution starts here; importing this module does not run main.
if __name__ == "__main__":
    # Pass command-line arguments to main; 0 signals normal completion, 1 an input error.
    sys.exit(main(sys.argv))
