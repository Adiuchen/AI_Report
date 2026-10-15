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

A state is the id of the current graph node. An action is “follow one outgoing edge”. The path cost is the sum of edge costs. For BFS and CUS2 we also care about the number of edges, called moves or hops. The goal test succeeds when the current node is any member of the destination set. The search may stop at the first success. It does not have to visit the other destinations. Section 6 removes that shortcut.

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
| CUS2 | Custom informed | Number of moves | f = depth + h_moves |

**BFS** expands the shallowest node. With the tie-break above, nodes at the same depth come out in order of node id, and only then in the order they were added. The first destination removed from the frontier is a minimum-move destination. BFS does not read edge costs, so a one-edge toll road is preferred to a three-edge cheap road.

**AS** is A*. `g` is the cost of the path from the origin. `h(n)` is the straight-line (Euclidean) distance from `n` to the nearest destination. On the sample map:

- distance(2, 4) = √((6−2)² + (3−2)²) = √17 ≈ 4.123
- distance(2, 5) = √((5−2)² + (6−2)²) = 5
- so h(2) = 4.123, the smaller of the two

`h` is admissible, and in fact consistent, when every edge costs at least as much as its own straight-line length. A step cannot then be a shortcut through the plane, so `h` never overestimates the cost still to pay. Under that condition A* returns a minimum-cost path. Every edge in our test maps satisfies the condition. The longest straight-line edge on the sample map is about 3.162 (for example node 3 to node 6).

**CUS1** is uniform-cost search (Dijkstra’s algorithm written as tree search). It expands the smallest `g` and uses no heuristic, so it is uninformed. With non-negative edge costs it returns a minimum-cost path, the same optimum as A*, usually after creating more nodes. It is a better custom uninformed method for this problem than a second blind traversal, because the specification defines “optimal” as lowest cost.

**CUS2** is A* aimed at moves rather than cost. Each edge counts as one move, so `g` is the depth. The heuristic is

h_moves(n) = (straight-line distance to the nearest destination) / L

where L is the longest straight-line length of any edge on that map. One move covers at most L, so the number of moves still required is at least distance / L. The heuristic does not overestimate, and the first destination expanded has the fewest moves. On the sample map L ≈ 3.162 and h_moves(2) ≈ 4.123 / 3.162 ≈ 1.30, so A* expects a little more than one move even though two moves are actually needed. That is a legal underestimate.

# 3. Features, bugs, and missing parts

**Implemented**

- Parser for `Nodes`, `Edges`, `Origin`, and `Destinations`, including one-way edges, several destinations separated by semicolons, blank lines, and a repeated edge with a different cost.
- BFS, A* (`AS`), uniform-cost search (`CUS1`), and move-count A* (`CUS2`).
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

None. `python run_tests.py` passed on all 17 maps on Windows with Python 3.14.

# 4. Testing

## 4.1 How the tests are judged

`run_tests.py` does not trust the search code to mark its own homework. A separate Dijkstra routine computes the cheapest path and the fewest-move path on the graph. For `AS` and `CUS1` the path cost must equal the Dijkstra cost. For `BFS` and `CUS2` the number of moves must equal the fewest-move distance. Each step of the printed path must be a real edge. The command-line text must match the value returned inside the program. Maps that were worked out by hand also check the exact node sequence, which is how the tie-break is tested.

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

## 4.3 Results where the path is the same

On these maps every required method returns the same nodes. Cost and moves match the independent shortest-path check. “Created” is the number printed as `number_of_nodes`.

| Map | Path | Cost | Moves | Created BFS | AS | CUS1 | CUS2 |
|---|---|---:|---:|---:|---:|---:|---:|
| 01 sample | 2 1 4 | 10 | 2 | 11 | 8 | 11 | 8 |
| 02 only node 5 | 2 3 5 | 10 | 2 | 13 | 8 | 13 | 6 |
| 03 origin is goal | 1 | 0 | 0 | 1 | 1 | 1 | 1 |
| 06 one-way detour | 1 4 3 2 | 3 | 3 | 4 | 4 | 4 | 4 |
| 07 smaller id | 1 2 4 | 4 | 2 | 5 | 5 | 5 | 5 |
| 09 chain | 1 2 3 4 5 | 4 | 4 | 5 | 5 | 5 | 5 |
| 10 dead end | 1 3 4 | 2 | 2 | 4 | 4 | 4 | 4 |
| 11 cycle | 1 2 3 | 2 | 2 | 3 | 3 | 3 | 3 |
| 14 one edge | 1 2 | 4 | 1 | 2 | 2 | 2 | 2 |
| 15 self-loop | 1 2 | 2 | 1 | 2 | 2 | 2 | 2 |
| 16 parallel edges | 1 2 3 | 4 | 2 | 5 | 4 | 4 | 5 |

Map 4 prints `No path found` for all four methods. Map 3 creates exactly one node: the origin is expanded, it is a goal, and no children are generated. Map 14 creates exactly two: the origin and the goal. Map 11 and map 15 finish, which is the cycle test.

On map 10 the path is the same, but A* and CUS2 expand 3 nodes while BFS and CUS1 expand 4. The dead-end node is created as a child and then left on the frontier, because the heuristic ranks the useful child higher. Section 5 uses this.

On map 16 the path cost is 4, so the edge of cost 3 was used and the edge of cost 10 was not. A* and CUS1 create 4 nodes; BFS and CUS2 create 5, because the extra parallel edge is a separate tree node of equal depth.

## 4.4 Results where the methods disagree

| Map | BFS | AS | CUS1 | CUS2 |
|---|---|---|---|---|
| 05 toll vs cheap | path 1 4, cost 100, 1 move, 4 created | path 1 2 3 4, cost 3, 3 moves, 5 created | same as AS, 5 created | path 1 4, cost 100, 1 move, 3 created |
| 08 equal optima | path 1 2 4, cost 6, 2 moves | path 1 3 4, cost 6, 2 moves | same path as AS | same path as BFS |
| 12 two goals | path 1 6, cost 8, 1 move, 4 created | path 1 2 4, cost 2, 2 moves, 4 created | same as AS | path 1 6, cost 8, 1 move, 3 created |
| 13 larger map | path 1 6 7, cost 23, 2 moves, 18 created | path 1 2 4 7, cost 11, 3 moves, 16 created | same path as AS, 24 created | path 1 6 7, cost 23, 2 moves, 10 created |

Map 8 is a tie, not a disagreement about quality. Both paths cost 6 and both have 2 moves. BFS meets node 2 before node 3 because 2 is the smaller id, so the goal copy that arrives through node 2 is the one expanded. CUS1 meets node 3 first because that branch has g = 1, against g = 2 on the branch through node 2. The goal copy through node 3 is therefore added earlier, and the second tie-break keeps it. A* follows the cost ranking. CUS2 follows the move ranking, which at equal depth falls back to the smaller id, like BFS.

Map 17 is discussed in Section 6. The four required methods all stop at `1 2 3` (cost 2, one destination). `ALL` returns `1 2 4 2 3` (cost 4, both destinations).

# 5. Insights

The useful question is not “which algorithm is best”, but which quantity we asked it to minimise, and how many tree nodes it built while doing that.

## 5.1 Same optimum, less work

On the specification map every method returns `2 1 4`, cost 10, in two moves. The other destination, node 5, also has a two-move path of cost 10 (`2 3 5`). The tie-break selects node 4. Quality is identical. The work is not:

| Method | Nodes created | Nodes expanded |
|---|---:|---:|
| BFS | 11 | 6 |
| CUS1 | 11 | 6 |
| AS | 8 | 4 |
| CUS2 | 8 | 4 |

A* and CUS2 generate the cheap-looking branches first and meet a destination before the rest of the tree exists. With only one destination (map 2, goal 5 only), the gap grows. BFS and CUS1 create 13 nodes. A* creates 8. CUS2 creates 6. The straight-line estimate points at node 3, which really is the right first step toward node 5, so the informed searches barely leave that branch.

Uniform-cost search does not win on this map. The cheapest path is also a shortest-move path, and the edge costs are similar, so ordering by `g` removes the destination at about the same time as ordering by depth. The heuristic is what reduces the tree, not the change from depth to cost.

## 5.2 Cost and moves are different questions

Map 5 is a line of towns. The direct road from 1 to 4 costs 100. The road 1–2–3–4 costs 3. BFS returns `1 4`. That is the correct **fewest-move** answer and a poor **cheapest-path** answer. A* and CUS1 return `1 2 3 4` at cost 3. CUS2 agrees with BFS, and it creates only 3 nodes to do it, because the distance heuristic sees that the goal is one long step away.

Map 12 is the same lesson with two legal goals. BFS and CUS2 go to node 6 in one move and pay 8. A* and CUS1 go to node 4 in two moves and pay 2. Both answers are correct for the objective written in the table in Section 2.3. A marker who wanted the lowest cost would call the BFS path wrong. A marker who wanted the least moves would call the A* path wrong. The specification’s main objective is lowest cost, and it separately asks CUS2 for least moves. The program follows that split on purpose.

Map 13 is large enough for the costs to pull apart. The two-move path `1 6 7` costs 23. The three-move path `1 2 4 7` costs 11. There is another three-move path of cost 11 ending at node 8; the tie-break keeps node 7.

| Method | Path | Cost | Moves | Created | Expanded |
|---|---|---:|---:|---:|---:|
| BFS | 1 6 7 | 23 | 2 | 18 | 9 |
| CUS2 | 1 6 7 | 23 | 2 | 10 | 5 |
| AS | 1 2 4 7 | 11 | 3 | 16 | 8 |
| CUS1 | 1 2 4 7 | 11 | 3 | 24 | 12 |

Read down the “Created” column. For the **cost** objective, A* and CUS1 both find cost 11, and A* builds the smaller tree (16 against 24). The heuristic is doing real work: CUS1 has to open the toll road and the cross links before g = 11 is the best thing left in the frontier. For the **move** objective, CUS2 and BFS both find a two-move path, and CUS2 builds the smaller tree (10 against 18). An informed method is better than the matching uninformed method on both objectives. It is not better than a method that was given a different objective.

## 5.3 What we would run on a new map

If the user wants the cheapest route, and edges cost at least their straight-line length, run `AS`. On map 13 it matched CUS1’s cost and created fewer nodes. If the edge costs can undercut the straight-line distance, `AS` is no longer safe and `CUS1` is the method that still minimises cost.

If the user wants the fewest turns, run `CUS2`. It matched BFS on every hop-optimal test and created fewer nodes on maps 2, 5, 12, and 13. BFS remains the simple explanation of “expand one layer at a time”, which is why we kept it as the lecture uninformed method.

We would not use BFS as the only algorithm for this assignment’s cost objective. Maps 5, 12, and 13 are ordinary roads with different tolls, and BFS pays the toll.

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

For the route problem as set — one destination, lowest cost, edges at least as long as the straight-line distance — **A\*** is the method we would keep. It found the same cheapest paths as uniform-cost search in these tests and built smaller trees once the map offered a real choice (16 nodes created against 24 on the eight-node map). Uniform-cost search is the right fallback when a distance heuristic would overestimate.

Breadth-first search is the right lecture example of an uninformed layer-by-layer search, and it is the right answer when every edge is a turn and turns are all that matter. It is a weak answer when the edges have different costs. CUS2 is the version of that move objective we would actually run: same hop counts as BFS, fewer nodes on the maps where a direction toward the goal was available.

The node-count differences are small because the maps are small. The ordering is stable across the tests, and it matches the textbook account: a consistent heuristic does not change the optimum, it changes how much of the tree is built.

Two changes would matter on a larger map. First, graph search (a closed set of expanded states) would stop the tree from rebuilding towns that were already expanded with an equal or better cost. Second, the visit-all search needs a heuristic on the remaining destinations, otherwise each new destination doubles the state space. Both are extensions of the same frontier loop, which is why the four methods were written as one search with four ranking functions.

# 8. Acknowledgements

The route-finding file format, the six-algorithm list, the output format, the tie-break rules, and the visit-all research idea are from the COS30019 Assignment 2 Part A specification (Semester 2, 2026). The reduction from six algorithms to four, for a two-person team, is from an email sent by the unit tutor to Kian Xiu in October 2026.

The definitions of tree search, breadth-first search, uniform-cost search, and A\*, including the rule that an admissible heuristic makes tree-search A* optimal and that the goal is tested on expansion, follow Russell and Norvig, *Artificial Intelligence: A Modern Approach*, Chapter 3.

An AI coding assistant in Cursor (Grok) was used to draft `search.py`, `problem.py`, `algorithms.py`, `run_tests.py`, the test maps, and this report text. The team is responsible for reading the result, checking the test table, editing this report into the submitted PDF, and being able to explain each method in the progress meetings. The test numbers in Sections 4 and 5 were produced by running `python run_tests.py` locally; they were not typed in by hand.

# 9. References

Russell, S & Norvig, P 2021, *Artificial Intelligence: A Modern Approach*, 4th edn, Pearson, Hoboken, NJ.

Swinburne University of Technology 2026, *COS30019 Assignment 2 Part A: Tree Based Search*, assignment specification, Semester 2.

Unit tutor 2026, email to Kian Xiu, October, regarding a reduced set of four search algorithms for a two-person team.
