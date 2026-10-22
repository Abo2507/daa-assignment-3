# Assignment 3: Graph Algorithms (Java 17)

## Scope and implementation

The six methods in `src/Java/Algorithms.java` implement the algorithms required
by the supplied English README and `docs/Assignment_3_EN.pdf`. The manifest
selects Java. The original `Main.java`, `Input.java`, `Json.java`, public cases,
checker, launcher and GitHub workflow are unchanged.

All vertices and edge IDs fit `int`. Costs and distances use `long`: a forest
or simple DAG path has at most 99,999 edges, so its absolute total is at most
99,999,000,000,000. This exceeds 32 bits but is safely within signed 64 bits.
Weight comparisons use `comparingInt`, rather than subtracting weights.

The adjacency helper counts degrees, allocates one integer array per vertex,
then fills those arrays with original edge IDs. Directed outgoing lists use
endpoint 0, transpose lists use endpoint 1, and undirected lists include both
endpoints. Input edges are never sorted or modified in place. This preserves
the IDs needed for forest and shortest-path witnesses.

## 1. Disjoint-set union

**Purpose and steps.** Initially each vertex is its own component. `find`
follows parent pointers and performs path halving (a form of path compression).
`union` finds both roots and attaches the smaller component to the larger one.
On a successful merge it adds their sizes, decreases the component count and
updates the largest size. The method records a new `[components, largest]`
row after every operation, including operations that make no change.

**Invariant and correctness.** Vertices have the same root exactly when the
processed operations connect them. Root sizes equal their component sizes.
Path halving changes only the representation, preserving membership. A union
of different roots combines exactly two components, so the count decreases by
one and the combined size is their sum. Equal roots require no update.
Induction over the operations proves every returned state is correct.

**Boundaries.** Repeated unions and self-unions still produce a state. Isolated
vertices remain singleton components. With `n=0`, largest is zero and no valid
operation exists, so the returned states array is empty. There is no initial
state in the result.

**Complexity.** Initialization is O(n); union by size and path compression give
O(q alpha(n)) amortized time. Total time is O(n + q alpha(n)). Memory is O(n+q),
including the returned states.

## 2. Kruskal minimum spanning forest

**Purpose and steps.** Sort a separate array of original edge IDs by weight,
breaking ties by ID. Use a fresh DSU and accept an edge only when its endpoints
have different roots. Sum accepted weights in a `long`, retain their IDs and
return the final component count.

**Invariant and correctness.** Accepted edges are acyclic and can be extended
to a minimum spanning forest. The next accepted edge is a minimum-weight edge
crossing the relevant cut between current DSU components. By the cut/exchange
argument, some optimum contains that edge together with all earlier choices.
After all edges are considered, endpoints of every input edge are connected
in the selected forest; each original connected component is spanned.
Each successful union contributes one edge and decreases the component count
once, proving the edge count is exactly n-c.

**Boundaries.** Loops always join equal roots and are rejected, even when their
weight is negative. Parallel edges compete normally. Ties may admit several
optima. Disconnected components and isolates are retained. For an empty graph,
the result is zero cost, zero components and no IDs. Negative and large totals
are accumulated without integer overflow.

**Complexity.** O(n + m log(m+1)) time, including sorting and DSU work;
O(n+m) memory, including the sorted ID array and output.

## 3. Prim minimum spanning forest

**Purpose and steps.** Build undirected adjacency lists and a priority queue
of original edge IDs, ordered by weight and then ID. Start at each unvisited
vertex, count a new component, and add edges from that vertex to unvisited
neighbors. Repeatedly discard heap edges with both endpoints already visited,
take the cheapest remaining edge, and visit its unvisited endpoint. An empty
heap completes this component; the outer loop finds the next one.

**Invariant and correctness.** Each heap edge had a visited endpoint when
inserted, which stays visited. Every edge crossing the visited/unvisited cut
is in the heap. After stale edges are discarded, the chosen edge is a minimum
crossing edge. The cut property preserves optimality, and adding a new vertex
prevents cycles. When the heap empties, there is no edge to an unvisited vertex
of this component. Restarting therefore produces an optimum forest spanning
all components, with exactly n-c selected edges.

**Boundaries.** Self-loops are never inserted because the vertex is already
visited. Parallel edges can enter the heap separately; obsolete entries are
discarded. Negative and equal weights need no special case. Isolates count as
components even though they add no edges. Empty input returns the empty forest.
Prim calls neither Kruskal nor its sorting logic.

**Complexity.** Each edge is scanned twice and inserted at most once. The lazy
heap can hold O(m) entries. Time is O(n + m log(m+1)); memory is O(n+m).

## 4. Kosaraju strongly connected components

**Purpose and steps.** The first DFS visits the original directed graph and
records vertices in decreasing finishing order. Construct transpose adjacency
using the same original edge IDs. Visit the transpose from each still-unlabelled
vertex in that order; assign the same label to all vertices reached in that
second-pass traversal. Finally scan all original edges and add each distinct
cross-component pair to the condensation graph. A `HashSet<Long>` deduplicates
pairs: the source label occupies the upper 32 bits and the target the lower 32.
This encoding is injective; ordinary hash collisions do not merge distinct keys.

**Invariant and correctness.** The first-pass explicit stack mirrors suspended
recursive DFS calls and records a vertex only after all its outgoing edges.
For a condensation edge C -> D, the maximum original-graph finishing time in
C is larger than that in D. Thus, when the next unassigned SCC is reached in
decreasing order on the transpose, traversal cannot escape into a different
unassigned SCC. It reaches all vertices of its own SCC by mutual reachability.
Every vertex is assigned once. Scanning every edge after labelling includes
every cross-component pair, and the set excludes duplicates while the label
comparison excludes internal edges.

**Boundaries.** Isolates receive separate labels. Loops and duplicate edges do
not alter the partition. Disconnected structures are included by both outer
loops. Empty input yields two empty arrays. Marking a vertex when it is pushed
keeps each second-pass vertex on the stack at most once.

**Complexity.** Both DFS passes and graph construction take O(n+m). Hash-based
deduplication gives O(n+m) expected total time under the usual hash-table
assumption. Memory is O(n+m), including both adjacency representations,
explicit stacks, labels and condensation. Hash collisions may affect constants;
full-limit and dense condensation inputs are included in the tests.

## 5. DFS topological ordering

**Purpose and steps.** Run the shared DFS with cycle rejection enabled. Each
vertex has state 0 (unvisited), 1 (active), or 2 (finished). `stack` stores the
current path and `next[u]` remembers which outgoing edge to examine next.
Advance `next[u]` before pushing a child. An edge to an active vertex immediately
returns failure; otherwise each finished vertex is written from the end of the
order array towards its beginning. The outer loop covers all components.

**Invariant and correctness.** Active vertices are exactly the current DFS
path. An edge to an active ancestor completes a directed cycle, including a
self-loop. Edges to finished vertices do not imply cycles. Conversely, DFS of
a directed cycle must encounter an active endpoint. If no cycle is found,
every edge u -> v has v finish before u, so reverse finishing order places u
before v. Each vertex appears once. Failure returns exactly `acyclic=false`
and an empty order, even if other components were already processed.

**Boundaries.** Empty graphs are acyclic with an empty order. Disconnected
cycles invalidate the entire result. Duplicate edges and edges to finished
vertices are handled without false cycle reports.

**Complexity.** Each vertex is pushed once and each edge is examined once:
O(n+m) time and memory. Suspended traversal progress is retained, avoiding
quadratic rescanning on high-degree vertices.

## 6. DAG shortest paths

**Purpose and steps.** First run the three-state DFS on the whole graph.
Any cycle returns `acyclic=false`, `distance=[]`, `parent_edge=[]`.
Otherwise initialize a nullable `Long[]` with only the source equal to zero,
and fill `parentEdge` with -1. Process vertices in topological order. Skip
unreachable vertices; relax each outgoing edge, replacing the destination's
distance and parent edge only on a strict improvement or first discovery.

**Invariant and correctness.** When a vertex is processed, every possible
predecessor has already been processed, so its shortest distance is final.
Relaxation considers every possible last edge of a source path. Induction on
the topological order proves optimal distances, including negative weights.
Each recorded parent edge ends at the destination and satisfies
`distance[u] + weight == distance[v]`. Its predecessor is reachable and earlier
in the topological order, so following parents cannot cycle and must terminate
at the source. Ties retain an existing valid witness.

**Boundaries.** Unreachable components are checked for cycles before relaxation.
Edges from unreachable vertices cannot create false finite distances. A distance
of -1 is legitimate; only JSON `null` denotes unreachable. Source and unreachable
parents remain -1. In a DAG, a reachable incoming edge to the source would make
a cycle, so relaxation cannot overwrite the source's distance. Parallel/tied
edges retain original IDs. A singleton with no edges has distance `[0]`.

**Complexity.** O(n+m) time and memory, including DFS, adjacency and output.

## State reset, deep DFS and transport

All algorithm state is created inside a request or in a new DSU object. There
are no mutable static caches. The supplied entry point continues reading UTF-8
JSON lines and prints one result per request, including `ping`. Algorithm code
prints nothing. Results contain only the documented fields.

No graph traversal or DSU operation uses recursion. The first DFS stores both
the vertex path and per-vertex neighbor progress; the second SCC pass needs
only a work stack because it does not compute finishing times. A depth of
100,000 therefore consumes heap arrays rather than 100,000 Java call frames.
The original JSON parser is recursive only in JSON nesting depth; these graph
requests have constant nesting depth regardless of graph depth.

## Route reconstruction: calls and observed results

The package-visible helper is
`Algorithms.reconstructRoute(source, target, edges, parentEdge)`.
Its precondition is valid source/target indices and the original edge array
with the parent array from a successful DAG result. It walks incoming parent
IDs backwards, appends vertices, and reverses the list. An unreachable target
returns an empty list; the source returns a singleton. It checks edge direction
and bounds and guards against a cyclic parent chain. It is not a JSON task.
It uses O(L) time and output space for a valid L-vertex path, without scanning
the graph or allocating n-sized scratch space.

`tests/AlgorithmTests.java` directly called the helper with the following
inputs and verified every selected edge's direction and total weight. Full
observed parent arrays and paths are saved in `tests/results/routes.txt`.

For `edges = [[0,1,4],[1,2,-6],[0,2,9],[2,3,3],[4,5,-8]]`, n=6 and source=0,
the observed parent array is `[-1,0,1,3,-1,-1]`:

- `reconstructRoute(0, 3, edges, parentEdge)` returned `[0,1,2,3]`.
  Forward edge IDs `[0,1,3]` describe 0 -> 1 -> 2 -> 3, weight 4-6+3=1.
- `reconstructRoute(0, 0, edges, parentEdge)` returned `[0]`.
  There are no edges and its weight is zero.
- `reconstructRoute(0, 5, edges, parentEdge)` returned `[]`.
  Vertex 5 has distance null and parent -1; the edge 4 -> 5 is unreachable.
  There is no finite route weight.

For `edges = [[0,1,2],[0,1,2],[0,2,2],[1,3,-1],[2,3,-1]]`, n=4 and source=0,
the observed parent array is `[-1,0,2,4]`:

- `reconstructRoute(0, 1, edges, parentEdge)` returned `[0,1]`, using edge 0
  with weight 2; edge 1 is an equally valid parallel choice.
- `reconstructRoute(0, 3, edges, parentEdge)` returned `[0,2,3]`, using IDs
  `[2,4]`, forward weight 2-1=1. IDs `[0,3]` give another optimum.

A nonzero-source test returned `[2,0,1]`, with parent array `[0,1,-1,-1]`
and weight -1+5=4. A direct 100,000-vertex reconstruction checked every vertex
of the returned sequence, demonstrating that reconstruction is iterative too.

## Test strategy and reproducible commands

Requirements: JDK 17+ and Python 3.12+, both on PATH. No third-party dependency
is needed to build or run the solution or tests. From the repository root:

```powershell
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tools -p "test_*.py"
python tools/run.py --input tests/cases.jsonl
python tests/run_tests.py --stress --benchmark
```

On the machine used here, the default PATH contained only Java 8. The installed
JDK 17 and bundled Python were selected for this shell with:

```powershell
$env:PATH = 'C:\Users\Ablaykhan\.jdks\ms-17.0.20.1\bin;C:\Users\Ablaykhan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
```

This changes only the current shell. On another machine use its installed
JDK/Python paths. The sandboxed compiler reported `Cannot close compiler
resources`; the successful recorded runs used the same JDK outside that sandbox.
No source change or checker relaxation was used to resolve that environment issue.

### Independent expected answers and witnesses

`tests/run_tests.py` constructs 35 explicit boundary cases and 560 seeded random
cases (seed 20261021). It computes expectations independently of Java:

- DSU: naive whole-array relabelling and direct component-size counts.
- MST: exhaustive enumeration of all n-c-edge subsets on small graphs. A
  candidate must connect every original component; minimize its weight.
- SCC: all-pairs transitive closure, grouping exactly mutually reachable pairs.
- Cycle detection: the transitive closure diagonal detects nonempty cycles.
- DAG distances: Bellman-Ford edge sweeps, rather than topological relaxation.

The supplied semantic validator checks outputs against these independently
computed values. A wrapper also requires the exact output field set. Forest
checks cover distinct in-range IDs, acyclicity, component coverage and cost.
SCC checks compare partitions up to relabelling and require exact condensation.
Topological checks enforce every edge's precedence. DAG checks validate every
incoming parent ID, weight equality, and all complete chains to the source.
Non-unique arrays are not compared byte-for-byte.

Checker self-tests accept alternative optimum forest IDs, nonconsecutive SCC
labels, an alternative topological order and a parallel shortest-path edge.
They reject repeated forest IDs, reversed condensation, a backward topological
order, invalid incoming parent IDs and a consistent-weight parent cycle.
The latter is a deliberately invalid checker fixture, not an accepted DAG input.

Stored `tests/cases.jsonl`, `expected.jsonl`, `actual.jsonl` and `case_names.txt`
have corresponding rows. Expected files contain the reference fields needed
by the checker; witnesses are validated semantically. The runner regenerates
these files. Large inputs and full actual outputs are reproducibly generated
under ignored `tests/generated/`; hashes, sizes, statuses and batch timings are
retained in `tests/results/stress.json` to avoid committing hundreds of MB.

### Observed results (2026-10-21)

- **PASS:** setup ping, all 36 official public cases, and two complete public
  batches in one process. Exact captured output is in `tests/results/official.txt`.
- **PASS:** official tool unit-test suite: 16 discovered, 12 passed, 4 skipped.
  The skipped tests require unavailable C++/.NET toolchains; Java transport
  and source-helper checks ran and passed. Those four checks are **NOT RUN**.
- **PASS:** 595 original cases repeated in one process: 1,190 responses in
  0.184 seconds, including exact JSON object/field checks.
- **PASS:** all direct route-helper checks and semantic-checker self-tests.
- **PASS:** compilation of solution plus Java tests in 0.921 seconds, below
  the 60-second limit, with `javac --release 17`.
- **PASS:** 20 stress batches, each `[large request, ping, same large request]`,
  at `java -Xmx384m`. Slowest batch: 1.280 seconds; each has a 20-second timeout.
  Timing includes process launch, Java parsing, execution, output serialization
  and pipe I/O; Python input generation and subsequent witness validation are
  outside the measured interval. Successful execution under the heap cap is
  verified; peak process RSS was not measured and is not claimed to equal heap.

Full-limit cases include n=100,000 and q=250,000; n=100,000 and m=250,000 for
both forests, SCC, topo and DAG; a 100,000-vertex positive-distance chain;
negative-distance chains reaching -99,999,000,000,000; a giant SCC; disconnected
forests with an isolate; cycles unreachable from the source; and maximum-n
edgeless graphs. Dense directed cases use n=708 and m=250,000. Large expected
values follow from construction: chain reachability, SCCs of a directed ring,
negative tree backbones with only nonnegative extra edges, or telescoping
weights u-v. These facts do not depend on the Java implementation.

Across the explicit, random, deep and maximum-size cases, coverage includes
all 18 requested boundary categories: empty, singleton, isolated, disconnected,
repeated/self unions, loops, parallel/tied edges, negative and 64-bit totals,
unreachable vertices, cycles (including unreachable ones), deep chains, mixed
repeated requests, full limits, and sparse/dense graphs.

## Kruskal versus Prim benchmark

Command after compiling the tests:

```powershell
java -Xmx384m -cp .build/Java Benchmark
```

Or use `python tests/run_tests.py --stress --benchmark`, which builds first and
captures the benchmark output in `tests/results/benchmark.txt`.

**Inputs and independent verification.** `tests/Benchmark.java` uses
`new Random(20261021L + n)` for each size. For v=1..n-1 it connects a uniformly
chosen earlier vertex to v with a random weight in [-1000000,-1]. These n-1
edges form a tree. Additional edges have independently random endpoints and
weights in [0,1000000], allowing loops and parallels. The negative tree is the
unique minimum spanning tree: removing any of its edges defines a cut whose
other crossing edges are all nonnegative. Every result is checked for exactly
n-1 distinct tree IDs, one component and the independently summed tree weight.
The generator proves that those IDs form a spanning tree. Warm-up outputs and
every measured output are checked; failed verification aborts the benchmark.

**Environment.** Microsoft OpenJDK 17.0.20.1+1-LTS, OpenJDK 64-Bit Server VM;
Windows 11, OS version 10.0, amd64; Intel Core i5-12450H, 8 physical cores and
12 logical processors. Detected physical memory: 16,906,129,408 bytes
(approximately 15.75 GiB); 12 logical processors were also reported to the JVM.
Python 3.12.14 runs the harness. Maximum Java heap is 402,653,184 bytes (384 MiB).
The raw CPU/RAM query is recorded in `tests/results/hardware.txt`.

**Methodology.** Five warm-up calls per algorithm on n=10,000/m=40,000, then two
additional warm-ups per algorithm at each measured size. Three recorded samples
per method follow, alternating which method runs first. `System.nanoTime()`
brackets the entire `Algorithms.kruskal(input)` or `Algorithms.prim(input)` call.
The two calls use the same immutable input values and timing boundary. Input
generation and boxed request construction, JSON parsing, verification, output
serialization, printing and compilation are outside the interval. Supplied
`Input.edges` conversion, allocation of internal arrays/lists, adjacency
construction for Prim, sorting for Kruskal, heap/DSU operations and result-map
construction are inside. GC pauses during the call are included. No manual
garbage collection is forced.

**Observed milliseconds (raw samples and medians).**

- n=1,000, m=4,000: Kruskal [2.0869, 1.8126, 1.8276], median **1.8276**;
  Prim [1.9504, 2.2371, 2.3093], median **2.2371**.
- n=10,000, m=40,000: Kruskal [29.2097, 15.2768, 23.1783], median **23.1783**;
  Prim [23.3712, 24.8768, 25.9634], median **24.8768**.
- n=100,000, m=250,000: Kruskal [193.0255, 148.4032, 144.8149], median **148.4032**;
  Prim [317.2093, 292.1092, 285.1433], median **292.1092**.

**Interpretation and limits.** Kruskal had the lower median at these three
sizes. Prim additionally builds adjacency and manages many heap entries;
the negative backbone also makes many extra edges become stale. The results
describe this graph family on this machine, not a universal ranking. Three
samples in one JVM are sensitive to JIT compilation, GC and background load.
The inputs deliberately have a provable optimum, so they are not an unbiased
sample of all weighted graphs. Timings do not prove asymptotic complexity;
the operation counts above provide that argument. Benchmarks exclude JSON
transport; the separate stress measurements include it.

## Final 18-group rubric audit

This is an evidence audit, not an awarded grade. The private grading tool was
not available and was **NOT RUN**. Public checks report pass/fail only.

1. DSU core (4): path compression, union by size, counts and every state;
   independent relabelling references and public cases passed.
2. DSU edge cases (2): empty, no operations, repeated/self operations, isolates
   and disconnected merging passed.
3. DSU scale (2): 100,000 vertices / 250,000 operations, repeated in one process,
   passed within the limits.
4. Kruskal core (4): actual sorted-edge DSU algorithm; exhaustive small-graph
   optima and constructed large optima passed.
5. Kruskal witness (2): original unique IDs, no cycles/loops, n-c edges,
   total and coverage validated, including alternative witnesses.
6. Kruskal scale (1): connected/disconnected 100,000 / 250,000 cases passed.
7. Prim core (4): independent adjacency/heap algorithm with component restarts;
   same independent optimum checks as Kruskal passed.
8. Prim witness (2): same forest validity checks and alternative-ID checks passed.
9. Prim scale (1): connected/disconnected 100,000 / 250,000 cases passed.
10. SCC core (5): two-pass Kosaraju; partitions agree with mutual reachability.
11. SCC witness (3): exact deduplicated condensation and arbitrary valid labels
    checked; reversed condensation rejected.
12. SCC scale (2): full chain, giant SCC, maximum isolates and dense graph passed.
13. Topo core (4): three-state DFS, suspended progress and reverse finish order;
    cycle classification and every precedence edge checked.
14. Topo edge cases (2): empty, loops, duplicates, finished-neighbor edges,
    disconnected cycles and isolates passed.
15. Topo scale (2): full chain, cycle, dense graph and maximum isolates passed.
16. DAG core (5): whole-graph cycle detection and topological relaxation;
    independent Bellman-Ford distances and nonzero sources passed.
17. DAG witness (3): incoming original IDs, distance equations and complete
    source-reaching chains verified; direct route helper and alternate parents
    passed; invalid/cyclic parent witnesses rejected.
18. DAG scale (2): full negative graph, positive deep chain, unreachable cycle,
    dense graph and maximum isolates passed.

No known implementation failure remains after these checks. Private tests,
GitHub Actions for the eventual submitted commit, and the separate defence quiz
are not included in this local PASS claim. The student must review the code and
verify syllabus rules before submitting; these tests cannot guarantee a grade.

## Sources and academic integrity

The project was developed with help of assistance from OpenAI Codex, which was used for implementing graph algorithms, generating test cases, preparing benchmarks, and drafting technical documentation.

My involvement included setting up the development environment, configuring Java and Python, running the official assignment checks, executing additional stress tests and benchmarks, reviewing their results, and studying the implemented algorithms.

I independently executed the public checks and additional test suite on my local machine. All 36 public cases, 595 custom test cases, and 20 stress-test batches passed.

I am using this project to strengthen my understanding of graph algorithms, Java programming, algorithm complexity, and software testing.

The official assignment repository and its documentation were used as the primary sources for requirements and validation.

AI assistance is acknowledged transparently, and the work remains subject to the course's academic integrity requirements.

## Review, commit and Moodle submission
Update only `ANALYSIS.md`.

Revise the "Sources and academic integrity" section and the outdated statement about the student's independent review.

Preserve an accurate disclosure that OpenAI Codex assisted with implementation, test generation, benchmarking, and documentation.

Also accurately describe my actual contributions: configuring the local environment, running all 36 public checks, independently executing the custom tests and 20 stress batches, reviewing the test results, and studying the implementation for defence.

Make it clear that running tests is not the same as independently writing or fully reviewing the source code.

Update the testing environment information to include my verified Java 25 runs and their recorded benchmark results. Keep the earlier Java 17 measurements accurately labelled as earlier runs.

Keep the writing concise, natural, professional, and appropriate for a university assignment. Do not exaggerate my contributions, fabricate activities, or make false claims about authorship.

Do not change Java source code, tests, benchmarks, or other files. Do not commit or push.
```powershell
git diff --check
git diff
git status --short
git add .gitignore submission.json src/Java/Algorithms.java ANALYSIS.md DEFENSE_NOTES.md tests
git diff --cached --stat
git commit -m "Complete Assignment 3 graph algorithms and verification"
git push origin main
git rev-parse HEAD
```

Use the hash printed by the last command in the exact commit URL:
`https://github.com/Abo2507/daa-assignment-3/commit/<FULL_COMMIT_HASH>`.
Confirm Public checks in this repository's Actions tab. Paste that exact commit
URL into Moodle Online text, click **Submit assignment**, and verify submission
status. The repository homepage alone is insufficient. Provide the instructor
access if the repository is private. Follow the Moodle deadline; no deadline
was inferred here.
