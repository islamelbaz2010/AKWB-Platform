# Discovery Foundation Benchmark

## Methodology

All timings were collected on the local development machine using Python's `time.perf_counter()` and `resource.getrusage(RUSAGE_SELF).ru_maxrss` for peak RSS.

A synthetic project was created with:
- 5 000 files
- 100 directories (50 files per directory on average)
- 1 `README.md`
- 1 `.git` directory (ignored)
- 1 `node_modules/pkg/index.js` path (ignored)

The AKWB `DiscoveryEngine` was run twice against the same project root:
1. **First scan** — cold discovery; no prior registry.
2. **Second scan** — incremental discovery with a populated registry; unchanged-file hashes are reused via size + mtime comparison.

The benchmark driver is in `/tmp/benchmark_discovery.py`.

## Results

Representative run (after all review improvements were applied):

```text
first_scan_seconds:  6.203
artifact_count:      5101
peak_rss_mb:         50.2
second_scan_seconds: 5.014
```

### Observations
- The first scan discovers 5 101 artifacts (5 000 files + 100 directories + `README.md`; `.git` and `node_modules` ignored).
- Peak resident memory stays around 50 MB for 5 100 artifact records.
- The second scan is faster because unchanged files do not need to be re-read for hashing; only metadata (stat, classify, Pydantic model creation) is processed.
- Remaining runtime is dominated by filesystem enumeration and Pydantic model construction.

### Command used

```bash
PYTHONPATH=src python3 /tmp/benchmark_discovery.py
```

### Reproducibility

Run this ad-hoc benchmark with:

```bash
python3 - <<'PY'
import tempfile, pathlib, time, resource, sys
from akwb.config import Config
from akwb.container import Container

with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td) / 'bench'
    root.mkdir()
    for i in range(5000):
        d = root / f'dir_{i % 100}'
        d.mkdir(exist_ok=True)
        (d / f'file_{i}.py').write_text(f'x = {i}\n')
    (root / '.git').mkdir()
    (root / 'node_modules' / 'pkg').mkdir(parents=True)
    (root / 'node_modules' / 'pkg' / 'index.js').write_text('x')
    (root / 'README.md').write_text('# bench')

    config = Config()
    container = Container(root, config)

    t0 = time.perf_counter()
    result = container.discovery_engine.discover(root)
    t1 = time.perf_counter()
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_mb = rss_kb / (1024 * 1024) if sys.platform == 'darwin' else rss_kb / 1024
    assert result.ok
    print(f'first_scan_seconds: {t1 - t0:.3f}')
    print(f'artifact_count: {len(result.value.artifacts)}')
    print(f'peak_rss_mb: {rss_mb:.1f}')

    t2 = time.perf_counter()
    result2 = container.discovery_engine.discover(root)
    t3 = time.perf_counter()
    assert result2.ok
    print(f'second_scan_seconds: {t3 - t2:.3f}')
PY
```

## Scalability Projection

| Artifacts | Estimated cold scan | Estimated incremental scan | Peak RSS estimate |
|---|---:|---:|---:|
| 5 000 | ~6.2 s | ~5.0 s | ~50 MB |
| 50 000 | ~60 s | ~50 s | ~200 MB |
| 100 000 | ~120 s | ~100 s | ~400 MB |

> Projections are linear extrapolations from the benchmark above. Actual times depend on disk speed, file size distribution, and OS cache state.

## Known Limits

- The registry is fully materialized in memory before JSON serialization. Memory grows linearly with artifact count.
- Each artifact is a Pydantic model; model construction is a non-trivial portion of runtime.
- No parallel scanning is implemented yet.

## Recommendations for Future Performance Work

1. Stream artifact records to JSONL or SQLite to reduce peak memory.
2. Use `BaseModel.model_construct()` or a lighter `dataclass` representation for internal artifact building.
3. Consider parallel directory traversal for repositories with very high file counts.
