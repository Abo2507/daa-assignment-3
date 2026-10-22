# Defence notes: explain the code in your own words

Read `Algorithms.java` alongside these notes. Practise tracing examples rather
than memorizing the wording. These notes were prepared with AI assistance;
they do not replace your own understanding or the syllabus requirements.

## DSU: maintain groups as connections arrive

`parent[v]` points towards a representative. A root points to itself. `size`
is meaningful at roots and counts members, not tree height. `find` shortens
paths by pointing a node at its grandparent. `union` attaches the smaller
component under the larger one and updates `components` and `largest`.

Why it works: shortening pointers never moves a vertex to another group. A
successful union combines exactly two groups. Self/repeated unions do nothing
but still produce an output state. Amortized time is O(n + q alpha(n)); space
is O(n+q) including the saved states. Alpha grows extremely slowly, but it is
not literally a constant in the theoretical bound.

## Kruskal: choose cheap edges globally

Sort original IDs by weight; use DSU to reject cycles. Keep each accepted ID
and add its weight to a `long`. The cut property says a cheapest edge joining
two current components can be included in an optimum. A forest with c
components has n-c edges because every accepted edge reduces the count once.

Time: O(n + m log(m+1)); space: O(n+m). Sorting IDs preserves the original
edge order, which is essential because the output IDs refer to input positions.

## Prim: grow one component at a time

`visited` marks vertices already in the growing tree. Adjacency lists find
incident edges without scanning the whole graph. The priority queue contains
candidate edges, including some that have become stale. Remove stale edges
with both endpoints visited; the next minimum edge crosses the current cut.
Add its new endpoint. Restart from an unvisited vertex when the queue empties.

This also uses the cut property. An isolate counts as a component. A loop's
other endpoint is already visited, so it never enters the queue. Time is
O(n + m log(m+1)) for this lazy heap; space is O(n+m).

## Kosaraju: identify mutually reachable groups

First run DFS to get decreasing finish times. Then reverse every edge using
transpose adjacency and run DFS in that order. Each second-pass traversal
labels exactly one SCC. The finish order selects a component whose reversed
outgoing edges cannot lead into another unassigned component.

`component[v]` stores the label. For condensation, scan original edges,
discard pairs with equal labels and deduplicate the remaining label pairs.
Packed `long` keys store both labels exactly. Time is O(n+m) expected with
hash-based deduplication; space is O(n+m).

## Topological order: finish dependencies before returning

DFS states are 0=unvisited, 1=active, 2=finished. An edge to state 1 closes a
cycle along the current path. An edge to state 2 is harmless. Reverse finish
order puts the start of every edge before its end when the graph is acyclic.
`next[u]` remembers the next neighbor when a DFS frame is suspended. Without
that index, rescanning neighbors could destroy the linear running time.

Visit all components. Any cycle requires an empty order. Time and space are
O(n+m). This implementation is DFS, not Kahn's indegree algorithm.

## DAG shortest paths: solve predecessors first

Check the whole graph for cycles, then visit vertices in topological order.
By the time u is processed, all paths into u have already been considered.
Relax u -> v by trying `distance[u] + weight`. Skip u if its distance is null.
Negative weights work because there is no cycle and no later predecessor.

`distance` is a nullable `Long[]`; null means unreachable, while -1 can be a
real answer. `parentEdge[v]` is the ID of an incoming edge, not a vertex ID.
It is -1 for source/unreachable vertices. Follow each selected edge's source
backwards and reverse the collected vertices to reconstruct a route. The
parent always lies earlier in topological order, preventing parent cycles.

Time and space: O(n+m); reconstruction: O(L) for L vertices in the path.

## Questions to practise

- **Why `long`?** Up to 99,999 edges times a weight magnitude of one billion
  gives 99,999,000,000,000. That is outside signed `int`, but inside `long`.
- **Why iterative DFS?** A 100,000-vertex chain can overflow Java's call stack.
  Explicit arrays store the traversal on the heap and preserve neighbor progress.
- **Why may Prim and Kruskal choose different edges?** Equal weights can give
  multiple optimum forests. Their cost and component count must agree, while
  IDs need only describe valid optimum forests.
- **Can a negative loop improve an MST?** No. A loop is a cycle and cannot be
  part of any spanning forest, regardless of its weight.
- **Why check unreachable cycles for DAG paths?** The contract asks whether
  the entire input graph is acyclic, not just the source-reachable subgraph.
- **Why not Dijkstra?** Negative edges are allowed, and the required algorithm
  is topological relaxation. A DAG needs only one ordered pass.
- **What happens to ties in shortest paths?** Only strict improvement changes
  the parent. The existing equally short route remains valid.
- **Can every incoming parent edge be locally valid while the chains fail?**
  Yes, an invalid witness could contain a zero-weight predecessor cycle. Our
  checker follows complete chains; our algorithm's topological order prevents it.
- **Why store edge IDs instead of predecessors?** Parallel edges can have
  different weights. The ID identifies the exact edge that realizes the distance.
- **What is an SCC?** A maximal group in which every vertex reaches every
  other vertex. A single isolated vertex is an SCC.
- **Why is condensation acyclic?** A cycle of distinct SCCs would make them
  mutually reachable and therefore one SCC, contradicting their distinctness.
- **How do you know the tests are independent?** Small MST optima are enumerated;
  SCCs/cycles use transitive closure; DAG distances use Bellman-Ford; DSU uses
  naive relabelling. Large graphs have mathematically known answers.
- **What does the benchmark prove?** It records behavior on three particular
  graph sizes and one graph family. It does not prove a universal speed ranking
  or replace asymptotic reasoning. Every forest is verified before its sample
  is reported.
- **What resets between requests?** All arrays, heaps, sets, counters and DSU
  objects are local to the current method call. No mutable static state persists.
- **Does passing public checks guarantee 50/50?** No. They are pass/fail examples;
  the separate grading process and defence still apply.

Trace the reachable example in `tests/AlgorithmTests.java`: parent IDs
`[-1,0,1,3,-1,-1]` reconstruct 0 -> 1 -> 2 -> 3 with cost 4-6+3=1.
Then explain why vertex 5 remains unreachable despite the negative edge 4 -> 5.
