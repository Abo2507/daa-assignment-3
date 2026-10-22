import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;

public final class Benchmark {
    private static Map<String, Object> graph(int n, int m) {
        Random random = new Random(20261021L + n);
        List<List<Integer>> edges = new ArrayList<>();
        for (int v = 1; v < n; v++) {
            edges.add(List.of(random.nextInt(v), v, -1 - random.nextInt(1000000)));
        }
        while (edges.size() < m) {
            edges.add(List.of(random.nextInt(n), random.nextInt(n), random.nextInt(1000001)));
        }
        return Map.of("n", n, "edges", edges);
    }

    // Negative edges form a tree; every other edge is nonnegative. Replacing any
    // tree edge by a non-tree edge strictly increases the weight (cut property).
    private static void verify(Map<String, Object> input, Map<String, Object> result) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        List<?> ids = (List<?>) result.get("edge_ids");
        if (ids.size() != n - 1 || ((Number) result.get("components")).intValue() != 1) {
            throw new AssertionError("Forest size/components");
        }
        boolean[] seen = new boolean[n - 1];
        long expected = 0, actual = 0;
        for (int id = 0; id < n - 1; id++) expected += edges[id][2];
        for (Object value : ids) {
            int id = ((Number) value).intValue();
            if (id < 0 || id >= n - 1 || seen[id]) throw new AssertionError("Invalid forest");
            seen[id] = true;
            actual += edges[id][2];
        }
        if (actual != expected || ((Number) result.get("cost")).longValue() != expected) {
            throw new AssertionError("Wrong optimum cost");
        }
    }

    private static double measure(Map<String, Object> input, boolean prim) {
        long start = System.nanoTime();
        Map<String, Object> result = prim ? Algorithms.prim(input) : Algorithms.kruskal(input);
        long elapsed = System.nanoTime() - start;
        verify(input, result);
        return elapsed / 1000000.0;
    }

    private static double median(double[] samples) {
        double[] copy = samples.clone();
        Arrays.sort(copy);
        return copy[copy.length / 2];
    }

    public static void main(String[] args) {
        System.out.println("Java: " + System.getProperty("java.runtime.version")
                + "; VM: " + System.getProperty("java.vm.name"));
        System.out.println("OS: " + System.getProperty("os.name") + " "
                + System.getProperty("os.version") + " " + System.getProperty("os.arch")
                + "; processors: " + Runtime.getRuntime().availableProcessors()
                + "; max heap: " + Runtime.getRuntime().maxMemory());
        Map<String, Object> warmup = graph(10000, 40000);
        for (int i = 0; i < 5; i++) {
            measure(warmup, false);
            measure(warmup, true);
        }
        for (int[] size : new int[][] {{1000, 4000}, {10000, 40000}, {100000, 250000}}) {
            Map<String, Object> input = graph(size[0], size[1]);
            for (int i = 0; i < 2; i++) {
                measure(input, false);
                measure(input, true);
            }
            double[] kruskal = new double[3], prim = new double[3];
            for (int i = 0; i < 3; i++) {
                // Alternate which algorithm runs first to reduce ordering bias.
                if (i % 2 == 0) {
                    kruskal[i] = measure(input, false);
                    prim[i] = measure(input, true);
                } else {
                    prim[i] = measure(input, true);
                    kruskal[i] = measure(input, false);
                }
            }
            System.out.println(Json.write(Map.of("n", size[0], "m", size[1],
                    "kruskal_ms", kruskal, "prim_ms", prim,
                    "kruskal_median_ms", median(kruskal), "prim_median_ms", median(prim),
                    "verified", true)));
        }
    }
}
