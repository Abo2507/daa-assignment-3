# Your tests / Ваши тесты

## Completed Java test suite

Run from the repository root with JDK 17+ and Python 3.12+ on PATH:

```powershell
python tools/run.py --setup
python tools/run.py --check
python -m unittest discover -s tools -p "test_*.py"
python tools/run.py --input tests/cases.jsonl
python tests/run_tests.py --stress --benchmark
```

`run_tests.py` uses only Python's standard library. It compiles the original
Java sources plus `AlgorithmTests.java` and `Benchmark.java` with `--release 17`.
It enforces the 60-second build timeout and the 20-second input-batch timeout,
and launches Java with the official `-Xmx384m` heap cap. Omit both options for
only the small semantic suite and direct route-helper checks.

The 595 cases have corresponding rows in `case_names.txt`, `cases.jsonl`,
`expected.jsonl` and `actual.jsonl`. The expected file records reference values,
not a forced choice of non-unique witnesses. The generator in `run_tests.py`
is the source of truth and rewrites those files on a successful run.

Expected values come from exhaustive spanning-forest enumeration, transitive
closure, Bellman-Ford and naive component relabelling. The unchanged official
semantic checker validates witnesses against those independent values; an
additional check requires exactly the contract's field names. Self-tests
demonstrate acceptance of alternative valid witnesses and rejection of wrong
ones, including parent chains with a zero-weight cycle.

Boundary cases cover empty/singleton/isolated/disconnected graphs, repeated and
self unions, loops, parallel/equal edges, negatives and totals outside 32 bits,
unreachable vertices, nonzero sources, cycles and unreachable cycles. Seeded
random cases use seed 20261021. The small batch is repeated in one Java process.

Full-limit stress includes 100,000 vertices, 250,000 edges or unions, deep
chains, a giant SCC, disconnected forests, dense 708-vertex graphs with 250,000
edges, and edgeless maximum-n graphs. Expected results follow directly from
the construction (chain/ring reachability, provable negative spanning trees,
and telescoping weights). Every large request is repeated with ping between.

Complete generated stress inputs and actual outputs are saved under
`tests/generated/` (ignored by Git). Compact evidence intended for Git in `results/`
includes hashes, exact sizes and elapsed times. Regenerate rather than commit
these large raw files. `results/summary.txt`, `routes.txt`, `official.txt`,
`stress.json` and `benchmark.txt` record actual executed results.

Direct helper tests cover reachable/source/unreachable targets, tied paths,
parallel edges, a nonzero source and a 100,000-vertex route. Each short route's
direction and total weight are checked. See the root `ANALYSIS.md` for observed
calls/results, independent expected-value reasoning, the full rubric audit,
benchmark methodology and submission commands.

After compilation, run just the Java checks or benchmark with:

```powershell
java -Xmx384m -cp .build/Java AlgorithmTests
java -Xmx384m -cp .build/Java Benchmark
```

## Original template guidance

Create your own JSON Lines inputs here, together with expected and actual outputs and an explanation of each test. Run a file from the repository root:

```sh
python tools/run.py --input tests/my_cases.jsonl
```

Create `my_cases.jsonl` before running this example command. The launcher prints actual results; compare them with independently justified expected answers. Your files are not discovered automatically. Call your route helper directly in your test code. See the root README for all requirements.

Создайте здесь свои входы JSON Lines, ожидаемые и фактические результаты и объяснения тестов. Команда выше запускает созданный вами файл, но не сравнивает ответы автоматически. Функцию восстановления пути вызывайте непосредственно из своего тестового кода. Полные требования приведены в README в корне репозитория.
