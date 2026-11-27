#!/usr/bin/env python3
"""
A/B benchmark: baseline (raw fixture in prompt) vs stack (pre-compress via code).

Reads API config from env or AES/.env (AGENT_API_* or DEEPSEEK_*).
Writes JSON report under benchmark/results/.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path(__file__).parent
FIX = BENCH / "fixtures"
RES = BENCH / "results"
HUB = BENCH.parent.parent
AES_ENV = HUB / "AES" / ".env"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def api_config() -> dict[str, str]:
    load_env_file(AES_ENV)
    base = (
        os.environ.get("AGENT_API_BASE_URL")
        or os.environ.get("DEEPSEEK_API_BASE")
        or "https://api.deepseek.com/v1"
    ).rstrip("/")
    key = os.environ.get("AGENT_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or ""
    model = (
        os.environ.get("AGENT_API_MODEL")
        or os.environ.get("DEEPSEEK_MODEL")
        or "deepseek-chat"
    )
    if not key:
        raise SystemExit(
            "No API key. Set AGENT_API_KEY or DEEPSEEK_API_KEY in AES/.env or environment."
        )
    return {"base": base, "key": key, "model": model}


def stack_preprocess(fixture_name: str, raw: str) -> tuple[str, int, int]:
    """Simulate context-mode 'think in code' — only summary enters the prompt."""
    name = fixture_name.lower()
    if "git_log" in name:
        commits = len(re.findall(r"^commit ", raw, re.M))
        authors: dict[str, int] = {}
        for m in re.finditer(r"^Author: (.+?) <", raw, re.M):
            authors[m.group(1)] = authors.get(m.group(1), 0) + 1
        top = max(authors, key=authors.get) if authors else "unknown"
        summary = json.dumps(
            {"commit_count": commits, "top_author": top, "unique_authors": len(authors)},
            ensure_ascii=False,
        )
    elif "access_log" in name:
        err = 0
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("level") in ("ERROR", "FATAL"):
                err += 1
        summary = json.dumps({"error_count": err, "lines": len(raw.splitlines())})
    elif "file_tree" in name:
        py = sum(1 for ln in raw.splitlines() if ln.strip().endswith(".py"))
        summary = json.dumps({"py_files": py, "total_lines": len(raw.splitlines())})
    else:
        summary = raw[:2000] + ("..." if len(raw) > 2000 else "")
    return summary, len(raw.encode("utf-8")), len(summary.encode("utf-8"))


def chat(cfg: dict[str, str], system: str, user: str) -> dict:
    url = f"{cfg['base']}/chat/completions"
    body = json.dumps(
        {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {cfg['key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    choice = data["choices"][0]["message"]["content"]
    usage = data.get("usage") or {}
    return {
        "answer": choice,
        "latency_ms": elapsed_ms,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


def score_answer(answer: str, ground: dict, checks: list[str]) -> dict:
    out: dict = {"passed": True, "details": {}}
    try:
        parsed = json.loads(answer)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", answer, re.S)
        parsed = json.loads(m.group(0)) if m else {}
    for key in checks:
        expected = ground.get(key)
        actual = parsed.get(key)
        ok = actual == expected
        out["details"][key] = {"expected": expected, "actual": actual, "ok": ok}
        if not ok:
            out["passed"] = False
    return out


def run_mode(cfg: dict[str, str], mode: str, scenarios: list) -> list[dict]:
    system = "You are a precise analyst. Answer using valid JSON only."
    rows = []
    for sc in scenarios:
        raw = (FIX / sc["fixture"]).read_text(encoding="utf-8", errors="replace")
        ground = json.loads(
            (FIX / sc["fixture"].replace(".txt", ".ground_truth.json").replace(".jsonl", ".ground_truth.json")).read_text(
                encoding="utf-8"
            )
        )
        raw_bytes = len(raw.encode("utf-8"))
        if mode == "baseline":
            user = f"{sc['task']}\n\n--- DATA ---\n{raw}"
            sent_bytes = raw_bytes
            preprocess_ms = 0
        else:
            t0 = time.perf_counter()
            summary, _, sent_bytes = stack_preprocess(sc["fixture"], raw)
            preprocess_ms = int((time.perf_counter() - t0) * 1000)
            user = (
                f"{sc['task']}\n\n"
                f"--- STACK SUMMARY (pre-computed; do not ask for raw data) ---\n{summary}"
            )
        try:
            result = chat(cfg, system, user)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:500]
            rows.append({"id": sc["id"], "mode": mode, "error": f"HTTP {e.code}: {err}"})
            continue
        quality = score_answer(result["answer"], ground, sc["quality_checks"])
        rows.append(
            {
                "id": sc["id"],
                "mode": mode,
                "fixture_bytes": raw_bytes,
                "sent_bytes": sent_bytes,
                "context_reduction_pct": round((1 - sent_bytes / raw_bytes) * 100, 2)
                if raw_bytes
                else 0,
                "preprocess_ms": preprocess_ms,
                "latency_ms": result["latency_ms"],
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "total_tokens": result["total_tokens"],
                "quality": quality,
                "answer_preview": result["answer"][:300],
            }
        )
        time.sleep(0.5)
    return rows


def main() -> None:
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "both"
    RES.mkdir(parents=True, exist_ok=True)
    if not (FIX / "git_log_500.txt").is_file():
        import generate_fixtures

        generate_fixtures.gen_git_log()
        generate_fixtures.gen_access_log()
        generate_fixtures.gen_file_tree(HUB)

    cfg = api_config()
    scenarios = json.loads((BENCH / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report: dict = {
        "timestamp_utc": stamp,
        "api_base": cfg["base"],
        "model": cfg["model"],
        "modes": {},
    }
    modes = ["baseline", "stack"] if mode_arg == "both" else [mode_arg]
    for m in modes:
        print(f"Running mode={m} ...")
        report["modes"][m] = run_mode(cfg, m, scenarios)

    if len(report["modes"]) == 2:
        b = report["modes"]["baseline"]
        s = report["modes"]["stack"]
        def tot(rows, k):
            return sum(r.get(k, 0) for r in rows if "error" not in r)
        report["comparison"] = {
            "baseline_total_tokens": tot(b, "total_tokens"),
            "stack_total_tokens": tot(s, "total_tokens"),
            "token_savings_pct": round(
                (1 - tot(s, "total_tokens") / tot(b, "total_tokens")) * 100, 2
            )
            if tot(b, "total_tokens")
            else 0,
            "baseline_total_latency_ms": tot(b, "latency_ms"),
            "stack_total_latency_ms": tot(s, "latency_ms") + tot(s, "preprocess_ms"),
            "baseline_quality_pass": sum(1 for r in b if r.get("quality", {}).get("passed")),
            "stack_quality_pass": sum(1 for r in s if r.get("quality", {}).get("passed")),
            "scenarios": len(scenarios),
        }

    out = RES / f"benchmark_{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = RES / "latest.json"
    latest.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {out}")
    if "comparison" in report:
        print(json.dumps(report["comparison"], indent=2))


if __name__ == "__main__":
    main()
