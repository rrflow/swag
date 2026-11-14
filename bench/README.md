# Competitor bench

Sends the same SystemOne requests to SWAG and its competitors, then scores them on accuracy,
calibration and latency. Background and results are in [docs/competitors.md](../docs/competitors.md).

```sh
python bench/public_rows.py
cp bench/arms.example.json bench/arms.json
python bench/run.py --arms bench/arms.json --rows bench/data/public_rows.jsonl --out bench/results --limit 300
python bench/score.py --rows bench/data/public_rows.jsonl bench/results/*.jsonl
```

| File | Purpose |
|---|---|
| `public_rows.py` | Rebuilds CRUXEval (570) and When2Call (3,652) rows from pinned public sources into `data/`. Checks row counts and the source digest |
| `arms.example.json` | One entry per competitor: a `/v1/systemone` URL, a model name, and the environment variable holding its key |
| `run.py` | Sends every row to every arm. Accepts only `https` or local `http`, refuses redirects, keeps keys out of results |
| `score.py` | Accuracy with a 95% interval, calibration error, Brier score, latency, and paired McNemar tests |

`data/`, `results/` and `arms.json` stay local and are never committed.

When a model has been tuned on some rows, report results on rows it has not seen. Print only
aggregate results for held-out rows, and read individual failures only on development rows.
