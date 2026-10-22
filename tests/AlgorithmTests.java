import java.util.Arrays;
import java.util.List;
import java.util.Map;

/** Direct calls exercise the helper, which is deliberately not a JSON task. */
public final class AlgorithmTests {
    private static void route(String name, Map<String, Object> input, int target,
                              List<Integer> expected, Long expectedCost) {
        Map<String, Object> result = Algorithms.dag(input);
        if (!Boolean.TRUE.equals(result.get("acyclic"))) throw new AssertionError(name);
        int source = Input.source(input);
        int[][] edges = Input.edges(input);
        int[] parents = (int[]) result.get("parent_edge");
        List<Integer> path = Algorithms.reconstructRoute(source, target, edges, parents);
        if (!path.equals(expected)) throw new AssertionError(name + ": " + path);
        long cost = 0;
        for (int i = 1; i < path.size(); i++) {
            int[] edge = edges[parents[path.get(i)]];
            if (edge[0] != path.get(i - 1) || edge[1] != path.get(i)) {
                throw new AssertionError("Wrong direction");
            }
            cost += edge[2];
        }
        Long distance = ((Long[]) result.get("distance"))[target];
        if (!java.util.Objects.equals(distance, expectedCost)
                || (expectedCost != null && cost != expectedCost)) throw new AssertionError(name);
        System.out.println(name + ": parent_edge=" + Arrays.toString(parents)
                + ", route=" + path + ", cost=" + (path.isEmpty() ? "no route" : cost));
    }

    public static void main(String[] args) {
        Map<String, Object> graph = Json.parseRequest(
                "{\"n\":6,\"source\":0,\"edges\":[[0,1,4],[1,2,-6],[0,2,9],[2,3,3],[4,5,-8]]}");
        route("reachable", graph, 3, List.of(0, 1, 2, 3), 1L);
        route("source", graph, 0, List.of(0), 0L);
        route("unreachable", graph, 5, List.of(), null);
        Map<String, Object> ties = Json.parseRequest(
                "{\"n\":4,\"source\":0,\"edges\":[[0,1,2],[0,1,2],[0,2,2],[1,3,-1],[2,3,-1]]}");
        route("parallel", ties, 1, List.of(0, 1), 2L);
        route("tied", ties, 3, List.of(0, 2, 3), 1L);
        Map<String, Object> nonzero = Json.parseRequest(
                "{\"n\":4,\"source\":2,\"edges\":[[2,0,-1],[0,1,5]]}");
        route("nonzero source", nonzero, 1, List.of(2, 0, 1), 4L);
        int n = 100000;
        int[][] edges = new int[n - 1][3];
        int[] parents = new int[n];
        parents[0] = -1;
        for (int i = 1; i < n; i++) {
            edges[i - 1] = new int[] {i - 1, i, 1};
            parents[i] = i - 1;
        }
        List<Integer> deep = Algorithms.reconstructRoute(0, n - 1, edges, parents);
        if (deep.size() != n) throw new AssertionError("Deep route length");
        for (int i = 0; i < n; i++) if (deep.get(i) != i) throw new AssertionError("Deep route");
        System.out.println("PASS: 6 route cases and a 100000-vertex route");
    }
}
