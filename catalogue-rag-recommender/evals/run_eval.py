"""Measure retrieval hit-rate for each chunking strategy.

  python -m evals.run_eval
hit@k = share of queries where an expected product appears in the top k results.
"""
import json
import time
from pathlib import Path

from rag.chunking import STRATEGIES
from rag.recommender import Recommender

HERE = Path(__file__).resolve().parent
KS = (1, 3, 5)


def load_queries(path=None):
    path = Path(path) if path else HERE / "queries.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(strategy: str, queries=None) -> dict:
    queries = queries or load_queries()
    recommender = Recommender(strategy)
    hits = {k: 0 for k in KS}
    started = time.perf_counter()
    misses = []
    for item in queries:
        ranked = [p["sku"] for p in recommender.recommend(item["query"], k=max(KS))]
        for k in KS:
            if set(item["expected"]) & set(ranked[:k]):
                hits[k] += 1
        if not set(item["expected"]) & set(ranked[:3]):
            misses.append({"query": item["query"], "expected": item["expected"], "got": ranked[:3]})
    total = len(queries)
    return {
        "strategy": strategy,
        "queries": total,
        **{f"hit@{k}_pct": round(100 * hits[k] / total, 1) for k in KS},
        "avg_latency_ms": round(1000 * (time.perf_counter() - started) / total, 2),
        "misses_at_3": misses,
    }


def main():
    results = [evaluate(s) for s in STRATEGIES]
    print(f"{'strategy':<8} {'queries':>7} {'hit@1':>7} {'hit@3':>7} {'hit@5':>7} {'ms/query':>9}")
    for r in results:
        print(f"{r['strategy']:<8} {r['queries']:>7} {r['hit@1_pct']:>6}% {r['hit@3_pct']:>6}% {r['hit@5_pct']:>6}% {r['avg_latency_ms']:>9}")
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / "latest.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for r in results:
        for miss in r["misses_at_3"]:
            print(f"  [{r['strategy']}] miss: {miss['query']!r} expected {miss['expected']} got {miss['got']}")


if __name__ == "__main__":
    main()
