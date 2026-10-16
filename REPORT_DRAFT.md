# COS30019 Assignment 2 Part A — Report draft

> **Delete this box before you submit.**
> This is a draft, not a finished submission. Before handing it in:
> 1. Put it in Word or PDF. File name = your Team ID, for example `123.pdf`.
> 2. Add both full names, student IDs, and real signatures on the cover.
> 3. Replace the contribution table with what each person actually did.
> 4. Add a header, a footer, and page numbers. Body text about 12 pt, line spacing 1.5.
> 5. The body (everything after the contents page) must be **8 to 10 pages**. If Word comes out short, add a labelled figure of the sample map. If it comes out long, shorten Section 6.
> 6. Both people need to be able to explain the code in the progress meetings. Read `algorithms.py` before you talk to the tutor.
> 7. Keep the AI acknowledgement. The specification requires it.

---

# Cover page

**COS30019 Introduction to Artificial Intelligence**

**Assignment 2 Part A — Tree-Based Search for Route Finding**

| | |
|---|---|
| Team ID | [team id] |
| Unit | COS30019, Semester 2 2026 |
| Due | 11:59 pm, Sunday 25 October 2026 |

**Team members**

| Full name | Student ID | Signature |
|---|---|---|
| Kian Xiu | [id] | |
| [second member] | [id] | |

**Statement of contribution**

| Member | Contribution |
|---|---|
| [name] | [files, algorithms, tests, or report sections this person actually did] |
| [name] | [files, algorithms, tests, or report sections this person actually did] |

Both members have read the program and this report, and can explain the four search methods.

---

# Contents

1. Instructions
2. Introduction
3. Features, bugs, and missing parts
4. Testing
5. Insights
6. Research
7. Conclusion
8. Acknowledgements
9. References

---

# 1. Instructions

The program is written in Python 3 and uses only the standard library. Unzip the folder, open a command prompt in that folder, and run:

```text
python search.py <filename> <method>
```

`<filename>` is a route map. `<method>` is one of `BFS`, `AS`, `CUS1`, `CUS2`. An optional research method, `ALL`, is described in Section 6. `DFS` and `GBFS` are not accepted: the tutor reduced this team to four algorithms.

Example, using the map from the assignment sheet:

```text
python search.py tests/01_pdf_example.txt BFS
```

Output:

```text
tests/01_pdf_example.txt BFS
4 11
2 1 4
```

The three lines are:

1. The file name, as typed, and the method name.
2. The destination that was reached, then the number of search nodes created.
3. The path as node ids, from the origin to that destination, separated by spaces.

“Nodes created” means nodes in the **search tree**: the start node, plus every successor that was placed on the frontier. It is not the number of nodes drawn on the map. A child that would repeat a node already on the current branch is not created.

If no destination can be reached, the program prints the file and method, then `No path found`. The specification only defines the success format, so this failure line is our own.

To re-run the checks in this report:

```text
python run_tests.py
```

There is no GUI.

# 2. Introduction

## 2.1 The route-finding problem

The agent starts at an origin on a directed graph and must reach **one** of the destination nodes. Each edge has a cost and may be one-way. On the sample map, `(2,1): 4` allows a move from node 2 to node 1 at cost 4, and there is no matching edge back from 1 to 2.

A state is the id of the current graph node. An action is “follow one outgoing edge”. The path cost is the sum of edge costs. BFS minimises the number of edges, called moves or hops; AS, CUS1, and the revised CUS2 minimise path cost. The goal test succeeds when the current node is any member of the destination set. The search may stop at the first success. It does not have to visit the other destinations. Section 6 removes that shortcut.

The sample map is the one printed in the specification.

| Node | Coordinate |
|---|---|
| 1 | (4, 1) |
| 2 | (2, 2) |
| 3 | (4, 4) |
| 4 | (6, 3) |
| 5 | (5, 6) |
| 6 | (7, 5) |

Origin 2. Destinations 5 and 4. There are 14 directed edges, including several cycles (for example 1–3–1 and 3–2–3).

**Figure 1.** Sample route map from the specification. Insert the diagram from the assignment sheet here and keep this caption.

## 2.2 Graph and search tree

The map is a graph: each town appears once. The search builds a **tree**. Each tree node stores a graph node, a parent pointer, the cost `g` paid so far, and the depth (moves so far). The same town can appear in several places in the tree if several paths reach it. That is tree search, which is what this assignment asks for. Graph search, which keeps a closed set and never expands a town twice, is not used for the four required methods.

Cycles would make a pure tree infinite, because the branch 2–3–2–3–… never stops. A child is rejected when its graph node is already on the branch from the root to the current node. Other branches may still enter that town. Every path the program returns is therefore simple, and the search finishes on a finite map.

## 2.3 The four methods

All four methods use the same loop. A frontier (priority queue) holds the leaves of the tree. The loop takes out the best leaf, tests whether it is a destination, and if not, adds one child per unused outgoing edge. Only the number used to rank the frontier changes.

The goal is tested when a node is **removed** from the frontier, not when it is first generated. For A* and uniform-cost search this is the rule that makes the first destination we expand an optimal one: any cheaper path would still be sitting in the frontier with a better rank.

When that rank is tied, the program uses two further rules from the specification, in this order:

1. The smaller node id is expanded first.
2. If the node id is also the same, the copy that was added to the frontier earlier is expanded first.

| Method | Kind | What it minimises | Rank of a tree node |
|---|---|---|---|
| BFS | Uninformed, from the lectures | Number of moves | depth |
| AS | Informed, from the lectures | Path cost | f = g + h |
| CUS1 | Custom uninformed | Path cost | g |
| CUS2 | Custom informed | Path cost | f = g + 0.8 h |

**BFS** expands the shallowest node. With the tie-break above, nodes at the same depth come out in order of node id, and only then in the order they were added. The first destination removed from the frontier is a minimum-move destination. BFS does not read edge costs, so a one-edge toll road is preferred to a three-edge cheap road.

**AS** is A*. `g` is the cost of the path from the origin. `h(n)` is the straight-line (Euclidean) distance from `n` to the nearest destination. On the sample map:

- distance(2, 4) = √((6−2)² + (3−2)²) = √17 ≈ 4.123
- distance(2, 5) = √((5−2)² + (6−2)²) = 5
- so h(2) = 4.123, the smaller of the two

`h` is admissible, and in fact consistent, when every edge costs at least as much as its own straight-line length. A step cannot then be a shortcut through the plane, so `h` never overestimates the cost still to pay. Under that condition A* returns a minimum-cost path. Every edge in our test maps satisfies the condition. The longest straight-line edge on the sample map is about 3.162 (for example node 3 to node 6).

**CUS1** is uniform-cost search (Dijkstra’s algorithm written as tree search). It expands the smallest `g` and uses no heuristic, so it is uninformed. With non-negative edge costs it returns a minimum-cost path, the same optimum as A*, usually after creating more nodes. It is a better custom uninformed method for this problem than a second blind traversal, because the specification defines “optimal” as lowest cost.

**CUS2** is now A* with a scaled cost heuristic, f(n) = g(n) + w h(n), with w = 0.8. It uses the same nearest-goal straight-line cost estimate as AS. It no longer minimises moves and does not divide by the longest edge length.

The purpose of the weight is to control the influence of estimated remaining cost relative to accumulated actual cost. At w = 0 the ranking is uniform-cost search, at w = 1 it is standard A*, and at w = 0.8 it retains 80% of the heuristic estimate. The actual edge costs and reported path cost are unchanged. This is a deliberately conservative experimental setting, not a literature-derived optimal value.

If h is non-negative and admissible, 0.8 h <= h <= h*, so the scaled heuristic remains admissible. Under our finite-map, non-negative-cost assumptions, tree search with path-cycle rejection and goal testing on removal retains minimum-cost solutions. Scaling an arbitrary overestimating heuristic by 0.8 does not automatically repair it. The sufficient edge-cost condition described for AS is still used in the tests.

Weighted A* literature commonly discusses *inflation* with w > 1, to trade optimality for stronger goal direction. Our w < 1 setting instead weakens the estimate and can expand more nodes than standard A*. Ebendt and Drechsler (2009) provides context for heuristic weighting; it does not establish 0.8 as a preferred value. The admissibility argument above is our direct application of the standard A* condition described by Poole and Mackworth.

This is a team-requested algorithm revision. Eligibility as the assignment's custom informed method and any requirement for a move-minimising CUS2 must be checked against the original assignment/tutor instructions; this report does not establish approval. The separate Word draft has not been regenerated for this revision.

# 3. Features, bugs, and missing parts

**Implemented**

- Parser for `Nodes`, `Edges`, `Origin`, and `Destinations`, including one-way edges, several destinations separated by semicolons, blank lines, and a repeated edge with a different cost.
- BFS, A* (`AS`), uniform-cost search (`CUS1`), and scaled-heuristic cost A* (`CUS2`, w = 0.8).
- Command-line output in the three-line format required for batch testing.
- The two tie-break rules.
- Rejection of a node that already appears on the current branch, so cycles terminate.
- Seventeen maps and `run_tests.py`, which checks paths, costs, hop counts, and the command-line text.
- Optional `ALL` method (Section 6).

**Required features we did not implement**

The full specification lists six algorithms. Our tutor approved a two-person team and reduced the set to four: one informed method, one uninformed method, one custom informed method, and one custom uninformed method. We therefore did **not** implement depth-first search or greedy best-first search. There is no graphical interface.

**Known limits**

- If some edge costs less than its straight-line length, the A* heuristic can overestimate and the path from `AS` may not be a cheapest path. `CUS1` would still be cheapest, because it never uses `h`.
- Negative edge costs are outside the tested problem. Uniform-cost search and A* are stated for non-negative costs.
- The printed node count will not match a marker program that counts expanded nodes, or that also counts children rejected for being on the current path. Our definition is stated in Section 1 so it can be marked against the code.
- `No path found` is not specified in the assignment sheet.

**Known bugs**

The revised `python run_tests.py` passed on all 17 maps in the current local validation. This is coverage of these fixtures, not proof that no bugs exist.

# 4. Testing

## 4.1 How the tests are judged

`run_tests.py` does not trust the search code to mark its own homework. A separate Dijkstra routine computes the cheapest path and the fewest-move path on the graph. For `AS`, `CUS1`, and the revised `CUS2`, path cost must equal the Dijkstra cost. Only `BFS` is checked against the minimum-move distance. CUS2 is no longer tested against its old move-count objective. Each step of the printed path must be a real edge. The command-line text must match the value returned inside the program. Maps that were worked out by hand also check the exact node sequence, which is how the tie-break is tested.

## 4.2 The maps

| # | File | Situation |
|---|---|---|
| 1 | `01_pdf_example.txt` | The specification map. Two destinations, one-way edges, cycles. |
| 2 | `02_single_destination.txt` | Same map, but the only destination is node 5. |
| 3 | `03_origin_is_goal.txt` | The origin is already a destination. The path should be that single node. |
| 4 | `04_unreachable.txt` | The destination is in another component. |
| 5 | `05_hops_vs_cost.txt` | One direct edge of cost 100, or three edges of cost 1. |
| 6 | `06_one_way_detour.txt` | The arrow into the goal points the wrong way, so the agent must go the long way around. |
| 7 | `07_tie_smaller_node.txt` | Two equal paths. The smaller node id must be used. |
| 8 | `08_chronological_tie.txt` | Two paths of equal cost and equal length. Which copy of the goal was added first decides the path. |
| 9 | `09_linear_chain.txt` | A single path of four edges. Every method should agree. |
| 10 | `10_dead_end.txt` | One child has no way onward. |
| 11 | `11_cycle.txt` | An edge runs back to the previous node. The search must stop instead of looping. |
| 12 | `12_any_destination.txt` | Two destinations: a costly one-move goal and a cheap two-move goal. |
| 13 | `13_larger_map.txt` | Eight nodes. A two-move toll path and a three-move cheap path. |
| 14 | `14_single_edge.txt` | One edge. Also checks that a space inside `(0, 0)` still parses. |
| 15 | `15_self_loop.txt` | An edge from a node to itself must not cause an infinite loop. |
| 16 | `16_parallel_edges.txt` | Two edges from node 1 to node 2, costs 10 and 3. The search should pay 3. |
| 17 | `17_visit_all.txt` | Two destinations that sit on different branches. Reaching either one is enough for the four main methods. `ALL` must reach both. |

A malformed file (`99_bad_format.txt`), a missing file, an unknown method, and a command with no arguments are also checked. Each of those must exit with an error on the standard error stream and must not print a fake path.

## 4.3 Results after the CUS2 revision

The following table was generated from the updated test run. Created includes the start; expanded counts nodes removed, including a successful goal.

| Map | Method | Goal | Cost | Moves | Created | Expanded | Path |
|---|---|---:|---:|---:|---:|---:|---|
| 01_pdf_example.txt | BFS | 4 | 10 | 2 | 11 | 6 | 2 1 4 |
| 01_pdf_example.txt | AS | 4 | 10 | 2 | 8 | 4 | 2 1 4 |
| 01_pdf_example.txt | CUS1 | 4 | 10 | 2 | 11 | 6 | 2 1 4 |
| 01_pdf_example.txt | CUS2 | 4 | 10 | 2 | 8 | 4 | 2 1 4 |
| 02_single_destination.txt | BFS | 5 | 10 | 2 | 13 | 7 | 2 3 5 |
| 02_single_destination.txt | AS | 5 | 10 | 2 | 8 | 4 | 2 3 5 |
| 02_single_destination.txt | CUS1 | 5 | 10 | 2 | 13 | 7 | 2 3 5 |
| 02_single_destination.txt | CUS2 | 5 | 10 | 2 | 8 | 4 | 2 3 5 |
| 03_origin_is_goal.txt | BFS | 1 | 0 | 0 | 1 | 1 | 1 |
| 03_origin_is_goal.txt | AS | 1 | 0 | 0 | 1 | 1 | 1 |
| 03_origin_is_goal.txt | CUS1 | 1 | 0 | 0 | 1 | 1 | 1 |
| 03_origin_is_goal.txt | CUS2 | 1 | 0 | 0 | 1 | 1 | 1 |
| 04_unreachable.txt | BFS | - | - | - | - | - | NO PATH |
| 04_unreachable.txt | AS | - | - | - | - | - | NO PATH |
| 04_unreachable.txt | CUS1 | - | - | - | - | - | NO PATH |
| 04_unreachable.txt | CUS2 | - | - | - | - | - | NO PATH |
| 05_hops_vs_cost.txt | BFS | 4 | 100 | 1 | 4 | 3 | 1 4 |
| 05_hops_vs_cost.txt | AS | 4 | 3 | 3 | 5 | 4 | 1 2 3 4 |
| 05_hops_vs_cost.txt | CUS1 | 4 | 3 | 3 | 5 | 4 | 1 2 3 4 |
| 05_hops_vs_cost.txt | CUS2 | 4 | 3 | 3 | 5 | 4 | 1 2 3 4 |
| 06_one_way_detour.txt | BFS | 2 | 3 | 3 | 4 | 4 | 1 4 3 2 |
| 06_one_way_detour.txt | AS | 2 | 3 | 3 | 4 | 4 | 1 4 3 2 |
| 06_one_way_detour.txt | CUS1 | 2 | 3 | 3 | 4 | 4 | 1 4 3 2 |
| 06_one_way_detour.txt | CUS2 | 2 | 3 | 3 | 4 | 4 | 1 4 3 2 |
| 07_tie_smaller_node.txt | BFS | 4 | 4 | 2 | 5 | 4 | 1 2 4 |
| 07_tie_smaller_node.txt | AS | 4 | 4 | 2 | 5 | 4 | 1 2 4 |
| 07_tie_smaller_node.txt | CUS1 | 4 | 4 | 2 | 5 | 4 | 1 2 4 |
| 07_tie_smaller_node.txt | CUS2 | 4 | 4 | 2 | 5 | 4 | 1 2 4 |
| 08_chronological_tie.txt | BFS | 4 | 6 | 2 | 5 | 4 | 1 2 4 |
| 08_chronological_tie.txt | AS | 4 | 6 | 2 | 5 | 4 | 1 3 4 |
| 08_chronological_tie.txt | CUS1 | 4 | 6 | 2 | 5 | 4 | 1 3 4 |
| 08_chronological_tie.txt | CUS2 | 4 | 6 | 2 | 5 | 4 | 1 3 4 |
| 09_linear_chain.txt | BFS | 5 | 4 | 4 | 5 | 5 | 1 2 3 4 5 |
| 09_linear_chain.txt | AS | 5 | 4 | 4 | 5 | 5 | 1 2 3 4 5 |
| 09_linear_chain.txt | CUS1 | 5 | 4 | 4 | 5 | 5 | 1 2 3 4 5 |
| 09_linear_chain.txt | CUS2 | 5 | 4 | 4 | 5 | 5 | 1 2 3 4 5 |
| 10_dead_end.txt | BFS | 4 | 2 | 2 | 4 | 4 | 1 3 4 |
| 10_dead_end.txt | AS | 4 | 2 | 2 | 4 | 3 | 1 3 4 |
| 10_dead_end.txt | CUS1 | 4 | 2 | 2 | 4 | 4 | 1 3 4 |
| 10_dead_end.txt | CUS2 | 4 | 2 | 2 | 4 | 3 | 1 3 4 |
| 11_cycle.txt | BFS | 3 | 2 | 2 | 3 | 3 | 1 2 3 |
| 11_cycle.txt | AS | 3 | 2 | 2 | 3 | 3 | 1 2 3 |
| 11_cycle.txt | CUS1 | 3 | 2 | 2 | 3 | 3 | 1 2 3 |
| 11_cycle.txt | CUS2 | 3 | 2 | 2 | 3 | 3 | 1 2 3 |
| 12_any_destination.txt | BFS | 6 | 8 | 1 | 4 | 3 | 1 6 |
| 12_any_destination.txt | AS | 4 | 2 | 2 | 4 | 3 | 1 2 4 |
| 12_any_destination.txt | CUS1 | 4 | 2 | 2 | 4 | 3 | 1 2 4 |
| 12_any_destination.txt | CUS2 | 4 | 2 | 2 | 4 | 3 | 1 2 4 |
| 13_larger_map.txt | BFS | 7 | 23 | 2 | 18 | 9 | 1 6 7 |
| 13_larger_map.txt | AS | 7 | 11 | 3 | 16 | 8 | 1 2 4 7 |
| 13_larger_map.txt | CUS1 | 7 | 11 | 3 | 24 | 12 | 1 2 4 7 |
| 13_larger_map.txt | CUS2 | 7 | 11 | 3 | 20 | 10 | 1 2 4 7 |
| 14_single_edge.txt | BFS | 2 | 4 | 1 | 2 | 2 | 1 2 |
| 14_single_edge.txt | AS | 2 | 4 | 1 | 2 | 2 | 1 2 |
| 14_single_edge.txt | CUS1 | 2 | 4 | 1 | 2 | 2 | 1 2 |
| 14_single_edge.txt | CUS2 | 2 | 4 | 1 | 2 | 2 | 1 2 |
| 15_self_loop.txt | BFS | 2 | 2 | 1 | 2 | 2 | 1 2 |
| 15_self_loop.txt | AS | 2 | 2 | 1 | 2 | 2 | 1 2 |
| 15_self_loop.txt | CUS1 | 2 | 2 | 1 | 2 | 2 | 1 2 |
| 15_self_loop.txt | CUS2 | 2 | 2 | 1 | 2 | 2 | 1 2 |
| 16_parallel_edges.txt | BFS | 3 | 4 | 2 | 5 | 4 | 1 2 3 |
| 16_parallel_edges.txt | AS | 3 | 4 | 2 | 4 | 3 | 1 2 3 |
| 16_parallel_edges.txt | CUS1 | 3 | 4 | 2 | 4 | 3 | 1 2 3 |
| 16_parallel_edges.txt | CUS2 | 3 | 4 | 2 | 4 | 3 | 1 2 3 |
| 17_visit_all.txt | BFS | 3 | 2 | 2 | 4 | 3 | 1 2 3 |
| 17_visit_all.txt | AS | 3 | 2 | 2 | 4 | 3 | 1 2 3 |
| 17_visit_all.txt | CUS1 | 3 | 2 | 2 | 4 | 3 | 1 2 3 |
| 17_visit_all.txt | CUS2 | 3 | 2 | 2 | 4 | 3 | 1 2 3 |
| 17_visit_all.txt | ALL | 3 | 4 | 4 | 8 | 7 | 1 2 4 2 3 |

# 5. Insights

## 5.1 Cost and moves

On map 05, BFS returns 1 4, cost 100, one move. AS, CUS1, and revised CUS2 return 1 2 3 4, cost 3, three moves. This is the intended change: CUS2 now optimises cost. On map 12 it likewise chooses node 4 at cost 2 rather than node 6 at cost 8.

## 5.2 Heuristic influence

On map 13, AS, CUS2, and CUS1 all return 1 2 4 7 at cost 11. AS creates 16 nodes and removes 8, CUS2 creates 20 and removes 10, and CUS1 creates 24 and removes 12. In this fixture, weakening the heuristic places CUS2's work between AS and UCS. The sample map produces identical AS/CUS2 counts (8 created, 4 removed). A weight change need not change a path or a node count.

## 5.3 Purpose and limits of 0.8

The research question for this revision is: how does reducing the cost heuristic's weight affect node creation and expansion while preserving the minimum-cost objective? These tests support a more conservative search, not a speed advantage over AS. A larger controlled study could compare w = 0, 0.5, 0.8, and 1 over more maps and measure elapsed time as well as node counts. 0.8 is an experimental choice; it has not been tuned or proven best.

For minimum cost with the admissible straight-line heuristic, AS remains the stronger baseline. CUS1 provides the heuristic-free cost baseline. BFS provides the minimum-move baseline. Revised CUS2 studies heuristic scaling rather than a different objective.

# 6. Research

The specification suggests one extension: visit **every** destination, on a shortest path, and report what was hard about it. The command is

```text
python search.py tests/17_visit_all.txt ALL
```

Output from the test run:

```text
tests/17_visit_all.txt ALL
3 8
1 2 4 2 3
```

The walk costs 4 and enters node 2 twice. It visits destination 4 and destination 3. The four required methods stop at `1 2 3` and never enter node 4. That path is legal for them, because any one destination is enough. It is not legal for this extension.

## 6.1 Why the old state is not enough

A state that is only “the current node” cannot tell a finished tour from a tour that has seen one stop. We changed the state to a pair:

(current node, set of destinations already visited)

The start state is (origin, {origin} if the origin itself is a destination, otherwise the empty set). A move follows a graph edge, adds its cost, and inserts the new node into the set when that node is a destination. The goal test is “the set contains every destination”.

This is Dijkstra’s algorithm on that larger graph, still ordered by g, with the same node-id and “added earlier” tie-breaks. The first time a goal state is expanded, its cost is minimal, provided edge costs are non-negative. The same town may be entered again when the set has grown. The same pair (town, set) is not expanded twice.

## 6.2 Difficulties

Four things had to be handled.

1. **Stopping rule.** Re-using BFS or A* unchanged fails the new task even when the code is correct for Part A. On map 17 those methods have already succeeded at node 3.
2. **Memory of the tour.** The set has to be part of the state. Remembering only the current node, or only the parent pointer, cannot answer “have we seen both stops?”.
3. **Repeated towns.** Forbidding every repeated graph node makes map 17 unsolvable. After `1 2 3` the agent must return through node 2 to reach node 4. The ban we use in tree search (“not on the current branch”) is the wrong ban here. The right ban is “do not repeat the same town with the same set of stops already made”.
4. **Size.** If there are n towns and d destinations, there are up to n × 2^d states. The specification’s maps have few destinations, so trying every order is also possible. The test harness does that second computation independently: all orders of the destinations, joined by ordinary shortest paths, origin fixed at the front. `ALL` must match that cost. On map 17 both give cost 4.

We did not put a heuristic on `ALL`. An admissible one exists (for example a minimum spanning tree on the destinations not yet visited, measured with shortest-path distances), and it would cut the 2^d growth. The uninformed version is enough to show a correct shortest tour and to name the obstacle.

# 7. Conclusion

The revised methods comprise BFS for minimum moves, CUS1 for minimum cost without a heuristic, AS for minimum cost with the full straight-line heuristic, and CUS2 for minimum cost with 80% of that heuristic. AS and CUS2 rely on a suitable cost heuristic; CUS1 remains the reference when geometry does not provide an admissible cost estimate.

All revised checks passed on 17 maps. On map 13, CUS2 preserved cost 11 but created more nodes than AS (20 versus 16) and fewer than CUS1 (24). This illustrates the effect of weakening heuristic guidance, without claiming a universal performance ordering. Larger maps, more weights, and repeated timing measurements are needed for broader conclusions.

# 8. Acknowledgements

The route-finding file format, the six-algorithm list, the output format, the tie-break rules, and the visit-all research idea are from the COS30019 Assignment 2 Part A specification (Semester 2, 2026). The reduction from six algorithms to four, for a two-person team, is from an email sent by the unit tutor to Kian Xiu in October 2026.

The definitions of tree search, breadth-first search, uniform-cost search, and A\*, including the rule that an admissible heuristic makes tree-search A* optimal and that the goal is tested on expansion, follow Russell and Norvig, *Artificial Intelligence: A Modern Approach*, Chapter 3.

An AI coding assistant in Cursor (Grok) was used to draft `search.py`, `problem.py`, `algorithms.py`, `run_tests.py`, the test maps, and this report text. The team is responsible for reading the result, checking the test table, editing this report into the submitted PDF, and being able to explain each method in the progress meetings. The test numbers in Sections 4 and 5 were produced by running `python run_tests.py` locally; they were not typed in by hand.

# 9. References

Russell, S & Norvig, P 2021, *Artificial Intelligence: A Modern Approach*, 4th edn, Pearson, Hoboken, NJ.

Swinburne University of Technology 2026, *COS30019 Assignment 2 Part A: Tree Based Search*, assignment specification, Semester 2.

Unit tutor 2026, email to Kian Xiu, October, regarding a reduced set of four search algorithms for a two-person team.


Ebendt, R & Drechsler, R 2009, 'Weighted A* search – unifying view and application', Artificial Intelligence, vol. 173, no. 14, pp. 1310–1342, https://doi.org/10.1016/j.artint.2009.06.004. Author-institution record: https://elib.dlr.de/59485/.

Poole, DL & Mackworth, AK 2017, Artificial Intelligence: Foundations of Computational Agents, 2nd edn, Section 3.6.1, 'A* Search', https://www.cs.ubc.ca/~poole/aibook/2e/html2e/ArtInt2e.Ch3.S6.SS1.html.
