"""Citation-recall evaluation for a deployed or local KnowledgeOps API.

Seed the evaluation corpus first, then run:
    python evals/run_evals.py --base-url http://localhost:8000 --min-score 1.0
"""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import httpx


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(base_url: str, cases: list[dict]) -> dict:
    results = []
    for case in cases:
        started = perf_counter()
        response = httpx.post(f"{base_url.rstrip('/')}/v1/chat", json={"question": case["question"]}, timeout=90)
        elapsed_ms = round((perf_counter() - started) * 1000)
        response.raise_for_status()
        body = response.json()
        actual_sources = {citation["source"] for citation in body["citations"]}
        expected_sources = set(case["expected_sources"])
        results.append(
            {
                "question": case["question"],
                "expected_sources": sorted(expected_sources),
                "actual_sources": sorted(actual_sources),
                "citation_recall": len(expected_sources & actual_sources) / len(expected_sources),
                "latency_ms": elapsed_ms,
            }
        )
    score = sum(result["citation_recall"] for result in results) / len(results) if results else 0.0
    return {"citation_recall": score, "cases": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.jsonl"))
    parser.add_argument("--min-score", type=float, default=1.0)
    args = parser.parse_args()

    report = evaluate(args.base_url, load_cases(args.dataset))
    print(json.dumps(report, indent=2))
    return 0 if report["citation_recall"] >= args.min_score else 1


if __name__ == "__main__":
    sys.exit(main())

