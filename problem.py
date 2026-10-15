"""Load a route-finding text file into a directed graph.

File layout (blank lines are ignored):

    Nodes:
    1: (4,1)
    Edges:
    (2,1): 4
    Origin:
    2
    Destinations:
    5; 4

Edges are directed: (2,1): 4 allows 2 -> 1 only. The same pair may appear
more than once; each copy is a separate edge with its own cost.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Union

Number = Union[int, float]

# Node ids are integers. Coordinates and costs may be integers or decimals.
_NODE_RE = re.compile(
    r"^(\d+)\s*:\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)$"
)
_EDGE_RE = re.compile(
    r"^\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*:\s*(-?\d+(?:\.\d+)?)$"
)
_SECTION_NAMES = ("nodes:", "edges:", "origin:", "destinations:")


class ParseError(Exception):
    """The text file does not follow the route-finding format."""


def _number(text: str) -> Number:
    """Keep whole numbers as int so later tie-breaks stay exact."""
    if "." in text:
        return float(text)
    return int(text)


class Problem:
    """One route-finding instance: coordinates, directed edges, start, goals."""

    def __init__(
        self,
        coords: Dict[int, Tuple[Number, Number]],
        adj: Dict[int, List[Tuple[int, Number]]],
        origin: int,
        destinations: List[int],
    ) -> None:
        self.coords = coords
        self.adj = adj
        self.origin = origin
        # Order is kept for display. Search treats this as a set: any one goal is enough.
        self.destinations = list(destinations)
        self.goals = set(destinations)

    def neighbors(self, node: int) -> List[Tuple[int, Number]]:
        """Outgoing edges, sorted by destination id then cost.

        Sorting makes the program ignore the order of lines in the file.
        When two search nodes are still tied, the one added earlier is
        expanded earlier, so a stable add-order matters.
        """
        return sorted(self.adj.get(node, []), key=lambda item: (item[0], item[1]))


def load_problem(path: str) -> Problem:
    """Read a problem file. Raise ParseError if a required part is missing or malformed."""
    try:
        handle = open(path, "r", encoding="utf-8-sig")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ParseError(f"could not open {path}: {exc}") from exc

    with handle:
        lines = handle.readlines()

    section = None
    seen = set()
    coords: Dict[int, Tuple[Number, Number]] = {}
    raw_edges: List[Tuple[int, int, Number, int]] = []
    origin = None
    destinations: List[int] | None = None

    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered in _SECTION_NAMES:
            if lowered in seen:
                raise ParseError(f"line {lineno}: section {line} appears twice")
            seen.add(lowered)
            section = lowered
            continue
        if section is None:
            raise ParseError(f"line {lineno}: expected a section name, found {line!r}")

        if section == "nodes:":
            match = _NODE_RE.match(line)
            if not match:
                raise ParseError(f"line {lineno}: bad node line {line!r}")
            node_id = int(match.group(1))
            if node_id in coords:
                raise ParseError(f"line {lineno}: node {node_id} is listed twice")
            coords[node_id] = (_number(match.group(2)), _number(match.group(3)))
        elif section == "edges:":
            match = _EDGE_RE.match(line)
            if not match:
                raise ParseError(f"line {lineno}: bad edge line {line!r}")
            raw_edges.append(
                (int(match.group(1)), int(match.group(2)), _number(match.group(3)), lineno)
            )
        elif section == "origin:":
            if origin is not None:
                raise ParseError(f"line {lineno}: only one origin is allowed")
            if not re.fullmatch(r"\d+", line):
                raise ParseError(f"line {lineno}: bad origin {line!r}")
            origin = int(line)
        elif section == "destinations:":
            if destinations is not None:
                raise ParseError(f"line {lineno}: only one destinations line is allowed")
            parts = [part.strip() for part in line.split(";")]
            parts = [part for part in parts if part]
            if not parts or any(not re.fullmatch(r"\d+", part) for part in parts):
                raise ParseError(f"line {lineno}: bad destinations {line!r}")
            # Same goal written twice does not change the task.
            unique: List[int] = []
            for part in parts:
                node_id = int(part)
                if node_id not in unique:
                    unique.append(node_id)
            destinations = unique

    missing = [name for name in _SECTION_NAMES if name not in seen]
    if missing:
        names = ", ".join(name[:-1] for name in missing)
        raise ParseError(f"missing section(s): {names}")
    if origin is None or destinations is None:
        raise ParseError("origin and destinations are required")

    if origin not in coords:
        raise ParseError(f"origin {origin} is not listed under Nodes")
    unknown_goals = [goal for goal in destinations if goal not in coords]
    if unknown_goals:
        raise ParseError(f"destination(s) not listed under Nodes: {unknown_goals}")

    adj: Dict[int, List[Tuple[int, Number]]] = {node_id: [] for node_id in coords}
    for src, dst, cost, lineno in raw_edges:
        if src not in coords or dst not in coords:
            raise ParseError(f"line {lineno}: edge ({src},{dst}) uses an unknown node")
        adj[src].append((dst, cost))

    return Problem(coords, adj, origin, destinations)
