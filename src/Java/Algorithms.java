import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

public final class Algorithms {
    private static final class DisjointSet {
        final int[] parent;
        final int[] size;
        int components;
        int largest;

        DisjointSet(int n) {
            parent = new int[n];
            size = new int[n];
            for (int v = 0; v < n; v++) {
                parent[v] = v;
                size[v] = 1;
            }
            components = n;
            largest = n == 0 ? 0 : 1;
        }

        int find(int v) {
            while (parent[v] != v) {
                parent[v] = parent[parent[v]];
                v = parent[v];
            }
            return v;
        }

        boolean union(int u, int v) {
            int a = find(u), b = find(v);
            if (a == b) return false;
            if (size[a] < size[b]) {
                int temporary = a;
                a = b;
                b = temporary;
            }
            parent[b] = a;
            size[a] += size[b];
            components--;
            largest = Math.max(largest, size[a]);
            return true;
        }
    }

    static Map<String, Object> dsu(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] operations = Input.operations(input);
        DisjointSet sets = new DisjointSet(n);
        int[][] states = new int[operations.length][2];
        for (int i = 0; i < operations.length; i++) {
            sets.union(operations[i][0], operations[i][1]);
            states[i][0] = sets.components;
            states[i][1] = sets.largest;
        }
        return Map.of("states", states);
    }

    static Map<String, Object> kruskal(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        Integer[] ids = new Integer[edges.length];
        for (int i = 0; i < ids.length; i++) ids[i] = i;
        Arrays.sort(ids, Comparator.comparingInt((Integer id) -> edges[id][2])
                .thenComparingInt(id -> id));
        DisjointSet sets = new DisjointSet(n);
        List<Integer> selected = new ArrayList<>();
        long cost = 0;
        for (int id : ids) {
            int[] edge = edges[id];
            if (sets.union(edge[0], edge[1])) {
                selected.add(id);
                cost += edge[2];
            }
        }
        return Map.of("cost", cost, "edge_ids", selected, "components", sets.components);
    }

    static Map<String, Object> prim(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        int[][] adjacent = adjacency(n, edges, 0, true);
        boolean[] visited = new boolean[n];
        PriorityQueue<Integer> heap = new PriorityQueue<>(
                Comparator.comparingInt((Integer id) -> edges[id][2]).thenComparingInt(id -> id));
        List<Integer> selected = new ArrayList<>();
        long cost = 0;
        int components = 0;
        for (int start = 0; start < n; start++) {
            if (visited[start]) continue;
            components++;
            int vertex = start;
            while (true) {
                visited[vertex] = true;
                for (int id : adjacent[vertex]) {
                    int[] edge = edges[id];
                    int other = edge[0] == vertex ? edge[1] : edge[0];
                    if (!visited[other]) heap.add(id);
                }
                int nextEdge = -1;
                while (!heap.isEmpty()) {
                    int id = heap.remove();
                    if (!visited[edges[id][0]] || !visited[edges[id][1]]) {
                        nextEdge = id;
                        break;
                    }
                }
                if (nextEdge == -1) break;
                int[] edge = edges[nextEdge];
                selected.add(nextEdge);
                cost += edge[2];
                vertex = visited[edge[0]] ? edge[1] : edge[0];
            }
        }
        return Map.of("cost", cost, "edge_ids", selected, "components", components);
    }

    // Rows hold original edge IDs. endpoint=1 builds the transpose's adjacency.
    private static int[][] adjacency(int n, int[][] edges, int endpoint, boolean undirected) {
        int[] counts = new int[n];
        for (int[] edge : edges) {
            counts[edge[endpoint]]++;
            if (undirected) counts[edge[1]]++;
        }
        int[][] adjacent = new int[n][];
        for (int v = 0; v < n; v++) adjacent[v] = new int[counts[v]];
        Arrays.fill(counts, 0);
        for (int id = 0; id < edges.length; id++) {
            int u = edges[id][endpoint];
            adjacent[u][counts[u]++] = id;
            if (undirected) {
                int v = edges[id][1];
                adjacent[v][counts[v]++] = id;
            }
        }
        return adjacent;
    }

    // Reverse finishing order, or null if rejectCycles is true and a cycle exists.
    private static int[] dfsOrder(int[][] adjacent, int[][] edges, boolean rejectCycles) {
        int n = adjacent.length;
        byte[] state = new byte[n];
        int[] next = new int[n];
        int[] stack = new int[n];
        int[] order = new int[n];
        int remaining = n;
        for (int start = 0; start < n; start++) {
            if (state[start] != 0) continue;
            int top = 0;
            stack[top] = start;
            state[start] = 1;
            while (top >= 0) {
                int u = stack[top];
                if (next[u] == adjacent[u].length) {
                    state[u] = 2;
                    order[--remaining] = u;
                    top--;
                } else {
                    // Advance before suspending u, so each edge is scanned once.
                    int v = edges[adjacent[u][next[u]++]][1];
                    if (state[v] == 1 && rejectCycles) return null;
                    if (state[v] == 0) {
                        state[v] = 1;
                        stack[++top] = v;
                    }
                }
            }
        }
        return order;
    }

    static Map<String, Object> scc(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        int[] order = dfsOrder(adjacency(n, edges, 0, false), edges, false);
        int[][] transpose = adjacency(n, edges, 1, false);
        int[] component = new int[n];
        Arrays.fill(component, -1);
        int[] stack = new int[n];
        int label = 0;
        for (int start : order) {
            if (component[start] != -1) continue;
            int count = 0;
            stack[count++] = start;
            component[start] = label;
            while (count > 0) {
                int u = stack[--count];
                for (int id : transpose[u]) {
                    int v = edges[id][0];
                    if (component[v] == -1) {
                        component[v] = label;
                        stack[count++] = v;
                    }
                }
            }
            label++;
        }
        Set<Long> seen = new HashSet<>();
        List<int[]> condensation = new ArrayList<>();
        for (int[] edge : edges) {
            int a = component[edge[0]], b = component[edge[1]];
            long pair = ((long) a << 32) | (b & 0xffffffffL);
            if (a != b && seen.add(pair)) condensation.add(new int[] {a, b});
        }
        return Map.of("component", component, "condensation", condensation);
    }

    static Map<String, Object> topo(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        int[] order = dfsOrder(adjacency(n, edges, 0, false), edges, true);
        return Map.of("acyclic", order != null, "order", order == null ? new int[0] : order);
    }

    static Map<String, Object> dag(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int source = Input.source(input);
        int[][] edges = Input.edges(input);
        int[][] adjacent = adjacency(n, edges, 0, false);
        int[] order = dfsOrder(adjacent, edges, true);
        if (order == null) {
            return Map.of("acyclic", false, "distance", new Long[0], "parent_edge", new int[0]);
        }
        Long[] distance = new Long[n];
        int[] parentEdge = new int[n];
        Arrays.fill(parentEdge, -1);
        distance[source] = 0L;
        for (int u : order) {
            if (distance[u] == null) continue;
            for (int id : adjacent[u]) {
                int v = edges[id][1];
                long candidate = distance[u] + edges[id][2];
                if (distance[v] == null || candidate < distance[v]) {
                    distance[v] = candidate;
                    parentEdge[v] = id;
                }
            }
        }
        return Map.of("acyclic", true, "distance", distance, "parent_edge", parentEdge);
    }

    /** Uses a successful DAG result and its original edges; unreachable targets return []. */
    static List<Integer> reconstructRoute(int source, int target, int[][] edges, int[] parentEdge) {
        List<Integer> route = new ArrayList<>();
        int vertex = target;
        while (vertex != source) {
            int id = parentEdge[vertex];
            if (id == -1) return List.of();
            if (id < 0 || id >= edges.length || edges[id][1] != vertex
                    || route.size() >= parentEdge.length) {
                throw new IllegalArgumentException("Invalid parent-edge chain");
            }
            route.add(vertex);
            vertex = edges[id][0];
        }
        route.add(source);
        Collections.reverse(route);
        return route;
    }
}
