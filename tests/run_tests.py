"""Independent small references, semantic witnesses, and reproducible full-limit tests.

Only standard-library Python is required. Run from any directory; Java 17+ must
be on PATH. Full generated inputs/outputs live in ignored tests/generated/.
"""
import argparse
import copy
import hashlib
import itertools
import json
import pathlib
import random
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / 'tests'
sys.path.insert(0, str(ROOT / 'tools'))
from public_validate import check


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows),
                    encoding='utf-8')


def partition(n, edges):
    """Naive relabelling, intentionally independent of the Java DSU."""
    labels = list(range(n))
    for u, v, *_ in edges:
        old, new = labels[v], labels[u]
        labels = [new if label == old else label for label in labels]
    return labels


def reference(x):
    task = x['task']
    if task == 'ping':
        return {'status': 'ready'}
    n = x['n']
    if task == 'dsu':
        labels, states = list(range(n)), []
        for u, v in x['operations']:
            old, new = labels[v], labels[u]
            labels = [new if label == old else label for label in labels]
            states.append([len(set(labels)), max(labels.count(a) for a in labels)])
        return {'states': states}
    edges = x['edges']
    if task in ('kruskal', 'prim'):
        original = partition(n, edges)
        components = len(set(original))
        best = None
        # Enumerate all spanning forest candidates; no greedy MST reference.
        for ids in itertools.combinations(range(len(edges)), n - components):
            chosen = [edges[i] for i in ids]
            labels = partition(n, chosen)
            if any(labels[u] != labels[v] for u, v, _ in edges):
                continue
            cost = sum(edge[2] for edge in chosen)
            if best is None or cost < best:
                best = cost
        assert best is not None
        return {'cost': best, 'components': components}
    reach = [[False] * n for _ in range(n)]
    for u, v, *_ in edges:
        reach[u][v] = True
    for k in range(n):
        for u in range(n):
            for v in range(n):
                reach[u][v] |= reach[u][k] and reach[k][v]
    if task == 'scc':
        labels = [min(v for v in range(n) if v == u or (reach[u][v] and reach[v][u]))
                  for u in range(n)]
        return {'component': labels}
    acyclic = not any(reach[v][v] for v in range(n))
    if task == 'topo':
        return {'acyclic': acyclic}
    if not acyclic:
        return {'acyclic': False}
    # Bellman-Ford over all edges, independent of topological DFS/relaxation.
    distance = [None] * n
    distance[x['source']] = 0
    for _ in range(n - 1):
        for u, v, w in edges:
            if distance[u] is not None and (distance[v] is None or distance[u] + w < distance[v]):
                distance[v] = distance[u] + w
    return {'acyclic': True, 'distance': distance}


def validate(x, y, expected):
    fields = {'ping': {'status'}, 'dsu': {'states'},
              'kruskal': {'cost', 'edge_ids', 'components'},
              'prim': {'cost', 'edge_ids', 'components'},
              'scc': {'component', 'condensation'}, 'topo': {'acyclic', 'order'},
              'dag': {'acyclic', 'distance', 'parent_edge'}}
    return set(y) == fields[x['task']] and check(x, y, expected)


def small_cases():
    cases = [('ping', {'task': 'ping'})]

    def add(name, task, n, edges=None, **extra):
        x = dict(task=task, n=n, **extra)
        if edges is not None:
            x['edges'] = edges
        cases.append((name, x))

    for n in (0, 1, 7):
        add(f'dsu-no-operations-{n}', 'dsu', n, operations=[])
        for task in ('kruskal', 'prim', 'scc', 'topo'):
            add(f'{task}-isolates-{n}', task, n, [])
    add('dsu-self-repeat-merge', 'dsu', 7,
        operations=[[0, 0], [0, 1], [1, 0], [2, 3], [4, 5], [3, 4], [0, 5], [6, 6]])
    for task in ('kruskal', 'prim'):
        add(task + '-negative-loop-parallel-disconnected', task, 7,
            [[0, 0, -999], [0, 1, 4], [1, 0, -2], [1, 2, -2], [0, 2, -2], [3, 4, 8]])
        add(task + '-positive-overflow', task, 5, [[i, i + 1, 10**9] for i in range(4)])
        add(task + '-negative-overflow', task, 5, [[i, i + 1, -10**9] for i in range(4)])
    for task in ('scc', 'topo'):
        add(task + '-finished-neighbor', task, 5, [[0, 1], [0, 2], [2, 1], [2, 1]])
        add(task + '-cycles-duplicates-isolate', task, 7,
            [[0, 1], [1, 0], [1, 2], [0, 2], [2, 3], [3, 2], [4, 4], [3, 5]])
    add('dag-single', 'dag', 1, [], source=0)
    add('dag-unreachable-negative', 'dag', 6,
        [[0, 1, 4], [1, 2, -6], [0, 2, 9], [2, 3, 3], [4, 5, -8]], source=0)
    add('dag-unreachable-cycle', 'dag', 6, [[0, 1, 1], [3, 4, 0], [4, 3, 0]], source=0)
    add('dag-self-loop', 'dag', 1, [[0, 0, -1]], source=0)
    add('dag-ties-parallel', 'dag', 4,
        [[0, 1, 2], [0, 1, 2], [0, 2, 2], [1, 3, -1], [2, 3, -1]], source=0)
    for w in (-10**9, 10**9):
        add(f'dag-long-{w}', 'dag', 5, [[i, i + 1, w] for i in range(4)], source=0)
    add('dag-nonzero-source', 'dag', 4, [[2, 0, -1], [0, 1, 5]], source=2)
    rng = random.Random(20261021)
    for i in range(80):
        n = rng.randrange(1, 8)
        weighted = [[rng.randrange(n), rng.randrange(n), rng.randrange(-9, 10)]
                    for _ in range(rng.randrange(12))]
        unweighted = [edge[:2] for edge in weighted]
        for task in ('kruskal', 'prim'):
            add(f'random-{i}-{task}', task, n, weighted)
        for task in ('scc', 'topo'):
            add(f'random-{i}-{task}', task, n, unweighted)
        add(f'random-{i}-dsu', 'dsu', n, operations=unweighted)
        add(f'random-{i}-dag-general', 'dag', n, weighted, source=rng.randrange(n))
        permutation = list(range(n))
        rng.shuffle(permutation)
        dag_edges = [[permutation[u], permutation[v], w] for u, v, w in weighted if u < v]
        add(f'random-{i}-dag-acyclic', 'dag', n, dag_edges, source=rng.randrange(n))
    return cases


def checker_self_tests():
    examples = [
        ({'task': 'kruskal', 'n': 3, 'edges': [[0, 1, 1], [1, 2, 1], [0, 2, 1]]},
         {'cost': 2, 'components': 1, 'edge_ids': [0, 2]},
         {'cost': 2, 'components': 1, 'edge_ids': [0, 0]}),
        ({'task': 'scc', 'n': 3, 'edges': [[0, 1], [1, 0], [1, 2]]},
         {'component': [91, 91, 7], 'condensation': [[91, 7]]},
         {'component': [91, 91, 7], 'condensation': [[7, 91]]}),
        ({'task': 'topo', 'n': 3, 'edges': [[0, 2], [1, 2]]},
         {'acyclic': True, 'order': [1, 0, 2]},
         {'acyclic': True, 'order': [2, 0, 1]}),
        ({'task': 'dag', 'n': 3, 'source': 0, 'edges': [[0, 1, 1], [0, 1, 1], [1, 2, 2]]},
         {'acyclic': True, 'distance': [0, 1, 3], 'parent_edge': [-1, 1, 2]},
         {'acyclic': True, 'distance': [0, 1, 3], 'parent_edge': [-1, 2, 1]})]
    for request, good, bad in examples:
        expected = reference(request)
        assert validate(request, good, expected), request
        assert not validate(request, bad, expected), request
    request, good, bad = copy.deepcopy(examples[0])
    request['task'] = 'prim'
    assert validate(request, good, reference(request))
    assert not validate(request, bad, reference(request))
    # A consistent zero-weight predecessor cycle must still be rejected.
    request = {'task': 'dag', 'n': 3, 'source': 0,
               'edges': [[0, 1, 0], [1, 2, 0], [2, 1, 0]]}
    bad = {'acyclic': True, 'distance': [0, 0, 0], 'parent_edge': [-1, 2, 1]}
    assert not check(request, bad, {'acyclic': True, 'distance': [0, 0, 0]})
    return 'PASS: alternative valid witnesses accepted and invalid witnesses rejected for MST/SCC/topo/DAG; parent cycle rejected'


def stress_cases():
    n, m = 100000, 250000
    operations = [[i - 1, i] for i in range(1, n)]
    operations += [[0, 0] if i % 2 else [n - 1, 0] for i in range(m - n + 1)]
    yield ('dsu-full', {'task': 'dsu', 'n': n, 'operations': operations},
           {'states': [[n - i - 1, i + 2] for i in range(n - 1)] + [[1, n]] * (m - n + 1)})
    chain = [[i - 1, i] for i in range(1, n)]
    forward = chain + [[0, 1 + i % (n - 1)] for i in range(m - n + 1)]
    yield 'scc-full-chain', dict(task='scc', n=n, edges=forward), {'component': list(range(n))}
    yield 'topo-full-chain', dict(task='topo', n=n, edges=forward), {'acyclic': True}
    ring = chain + [[n - 1, 0]] * (m - n + 1)
    yield 'scc-full-ring', dict(task='scc', n=n, edges=ring), {'component': [0] * n}
    yield 'topo-full-cycle', dict(task='topo', n=n, edges=ring), {'acyclic': False}
    weights = [[u, v, -10**9] for u, v in forward]
    yield ('dag-full-negative', dict(task='dag', n=n, edges=weights, source=0),
           {'acyclic': True, 'distance': [-v * 10**9 for v in range(n)]})
    positive = [[u, v, 10**9] for u, v in chain]
    yield ('dag-deep-positive', dict(task='dag', n=n, edges=positive, source=0),
           {'acyclic': True, 'distance': [v * 10**9 for v in range(n)]})
    unreachable = [[u, v, -10**9] for u, v in ring if u != 0]
    yield ('dag-large-unreachable-cycle', dict(task='dag', n=n, source=0,
                                             edges=unreachable + [[n - 1, 1]]), {'acyclic': False})
    rng = random.Random(20261021)
    for disconnected in (False, True):
        active = n - 1 if disconnected else n
        tree = [[i - 1, i, -10**9] for i in range(1, active) if not (disconnected and i == n // 2)]
        weighted = tree.copy()
        while len(weighted) < m:
            u = rng.randrange(active)
            if disconnected:
                lo, hi = (0, n // 2) if u < n // 2 else (n // 2, active)
                v = rng.randrange(lo, hi)
            else:
                v = rng.randrange(active)
            weighted.append([u, v, rng.randrange(10**9 + 1)])
        for task in ('kruskal', 'prim'):
            yield (f'{task}-full-disconnected-{disconnected}', dict(task=task, n=n, edges=weighted),
                   {'cost': -len(tree) * 10**9, 'components': n - len(tree)})
    dense_n = 708
    dense = [[u, v] for u in range(dense_n) for v in range(u + 1, dense_n)][:m]
    for task in ('scc', 'topo', 'dag'):
        edges = [[u, v, u - v] for u, v in dense] if task == 'dag' else dense
        expected = {'component': list(range(dense_n))} if task == 'scc' else {'acyclic': True}
        if task == 'dag':
            expected['distance'] = [-v for v in range(dense_n)]
        yield f'{task}-dense', dict(task=task, n=dense_n, edges=edges, source=0), expected
    for task in ('kruskal', 'prim', 'scc', 'topo', 'dag'):
        expected = ({'cost': 0, 'components': n} if task in ('kruskal', 'prim') else
                    {'component': list(range(n))} if task == 'scc' else {'acyclic': True})
        if task == 'dag':
            expected['distance'] = [None] * (n - 1) + [0]
        yield f'{task}-max-isolates', dict(task=task, n=n, edges=[], source=n - 1), expected


def execute(requests, command):
    data = ''.join(json.dumps(x, separators=(',', ':')) + '\n' for x in requests)
    start = time.perf_counter()
    result = subprocess.run(command, input=data, text=True, encoding='utf-8',
                            capture_output=True, timeout=20, check=True, cwd=ROOT)
    elapsed = time.perf_counter() - start
    assert not result.stderr.strip(), result.stderr
    lines = result.stdout.splitlines()
    assert len(lines) == len(requests), 'JSON Lines count mismatch'
    outputs = [json.loads(line) for line in lines]
    return outputs, elapsed, data, result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stress', action='store_true')
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    output = ROOT / '.build' / 'Java'
    output.mkdir(parents=True, exist_ok=True)
    reports = TESTS / 'results'
    reports.mkdir(exist_ok=True)
    generated = TESTS / 'generated'
    generated.mkdir(exist_ok=True)
    sources = sorted((ROOT / 'src' / 'Java').glob('*.java')) + list(TESTS.glob('*.java'))
    start = time.perf_counter()
    subprocess.run(['javac', '--release', '17', '-encoding', 'UTF-8', '-d', str(output),
                    *map(str, sources)], check=True, timeout=60)
    build_seconds = time.perf_counter() - start
    command = ['java', '-Xmx384m', '-cp', str(output), 'Main']
    cases = small_cases()
    inputs = [x for _, x in cases]
    expected = [reference(x) for x in inputs]
    outputs, elapsed, _, _ = execute(inputs * 2, command)
    for index, (x, y, e) in enumerate(zip(inputs * 2, outputs, expected * 2)):
        assert validate(x, y, e), (cases[index % len(cases)][0], x, y, e)
    write_jsonl(TESTS / 'cases.jsonl', inputs)
    write_jsonl(TESTS / 'expected.jsonl', expected)
    write_jsonl(TESTS / 'actual.jsonl', outputs[:len(inputs)])
    (TESTS / 'case_names.txt').write_text('\n'.join(name for name, _ in cases) + '\n', encoding='utf-8')
    summary = [f'PASS compilation: {build_seconds:.3f}s (limit 60s)',
               f'PASS {len(cases)} original cases, repeated in one process: {2 * len(cases)} responses in {elapsed:.3f}s (limit 20s)',
               checker_self_tests()]
    direct = subprocess.run(command[:-1] + ['AlgorithmTests'], check=True, capture_output=True,
                            text=True, encoding='utf-8', timeout=20)
    (reports / 'routes.txt').write_text(direct.stdout, encoding='utf-8')
    summary.append(direct.stdout.strip())
    if args.stress:
        stress_results = []
        for name, x, e in stress_cases():
            # Each large case is also repeated in the same process with ping between.
            batch = [x, {'task': 'ping'}, x]
            actual, seconds, data, stdout = execute(batch, command)
            assert validate(x, actual[0], e) and validate(x, actual[2], e), name
            assert actual[1] == {'status': 'ready'}, name
            (generated / (name + '.jsonl')).write_text(data, encoding='utf-8', newline='\n')
            (generated / (name + '.actual.jsonl')).write_text(stdout, encoding='utf-8', newline='\n')
            record = dict(name=name, n=x['n'], m_or_q=len(x.get('edges', x.get('operations', []))),
                          seconds=seconds, status='PASS',
                          input_sha256=hashlib.sha256(data.encode()).hexdigest(),
                          output_sha256=hashlib.sha256(stdout.encode()).hexdigest())
            stress_results.append(record)
            print(f'PASS {name}: {seconds:.3f}s', flush=True)
        (reports / 'stress.json').write_text(json.dumps(stress_results, indent=2) + '\n', encoding='utf-8')
        summary.append(f'PASS {len(stress_results)} stress batches (each large request repeated with ping), all under 20s at -Xmx384m')
    if args.benchmark:
        benchmark = subprocess.run(command[:-1] + ['Benchmark'], check=True, capture_output=True,
                                   text=True, encoding='utf-8', timeout=60)
        (reports / 'benchmark.txt').write_text(benchmark.stdout, encoding='utf-8')
        summary.append('PASS benchmark: 3 graph sizes, 3 measured samples per algorithm, every forest verified')
        print(benchmark.stdout)
    (reports / 'summary.txt').write_text('\n'.join(summary) + '\n', encoding='utf-8')
    print('\n'.join(summary))


if __name__ == '__main__':
    main()
