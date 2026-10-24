"""Run the eval set and print pass rate, tool accuracy, latency and token use.

  python -m evals.run_evals --backend mock        # offline pipeline check
  python -m evals.run_evals --backend anthropic   # real numbers for your resume
"""
import argparse
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent.agent import SupportAgent
from agent.llm import get_backend

HERE = Path(__file__).resolve().parent


def load_cases(path=None):
    path = Path(path) if path else HERE / "cases.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_case(case: dict, result) -> list:
    """Return a list of failure reasons (empty list = pass)."""
    failures = []
    expected_tool = case.get("expect_tool")
    if expected_tool and expected_tool not in result.tools_used:
        failures.append(f"expected tool {expected_tool}, got {result.tools_used}")
    if not expected_tool and result.tools_used:
        failures.append(f"expected no tool, got {result.tools_used}")
    text = result.text.lower()
    for phrase in case.get("must_contain", []):
        if phrase.lower() not in text:
            failures.append(f"missing '{phrase}'")
    for phrase in case.get("must_not_contain", []):
        if phrase.lower() in text:
            failures.append(f"should not contain '{phrase}'")
    if bool(case.get("expect_handoff")) != bool(result.handoff):
        failures.append(f"handoff expected {case.get('expect_handoff')}, got {result.handoff}")
    return failures


def run(backend_kind: str, cases=None):
    agent = SupportAgent(get_backend(backend_kind))
    rows = []
    for case in cases or load_cases():
        result = agent.reply(case["message"], history=[])
        failures = check_case(case, result)
        rows.append({"id": case["id"], "passed": not failures, "failures": failures, "tools": result.tools_used,
                     "latency_s": result.latency_s, "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                     "reply": result.text})
    return rows


def summarise(rows: list) -> dict:
    total = len(rows)
    passed = sum(r["passed"] for r in rows)
    latencies = sorted(r["latency_s"] for r in rows)
    p95 = latencies[min(total - 1, int(0.95 * total))] if total else 0
    in_tok = sum(r["input_tokens"] for r in rows)
    out_tok = sum(r["output_tokens"] for r in rows)
    summary = {"cases": total, "passed": passed, "pass_rate_pct": round(100 * passed / total, 1) if total else 0,
               "avg_latency_s": round(sum(latencies) / total, 3) if total else 0, "p95_latency_s": p95,
               "input_tokens": in_tok, "output_tokens": out_tok}
    price_in = float(os.getenv("INPUT_PRICE_INR_PER_M", "0") or 0)
    price_out = float(os.getenv("OUTPUT_PRICE_INR_PER_M", "0") or 0)
    if total and (price_in or price_out):
        summary["avg_cost_inr_per_chat"] = round((in_tok * price_in + out_tok * price_out) / 1_000_000 / total, 4)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["mock", "anthropic"], default="mock")
    args = parser.parse_args()
    rows = run(args.backend)
    for row in rows:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"[{mark}] {row['id']}" + ("" if row["passed"] else f"  -> {'; '.join(row['failures'])}"))
    summary = summarise(rows)
    print("\nSummary:", json.dumps(summary, indent=2))
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / f"latest_{args.backend}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    raise SystemExit(0 if summary["passed"] == summary["cases"] else 1)


if __name__ == "__main__":
    main()
