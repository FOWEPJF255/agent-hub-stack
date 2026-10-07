#!/usr/bin/env python3
"""Generate benchmark fixtures (run once)."""

from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)


def gen_git_log():
    authors = ["alice", "bob", "carol", "bob", "bob"]
    lines = []
    for i in range(500):
        a = authors[i % len(authors)]
        lines.append(f"commit {i:040x}\nAuthor: {a} <{a}@example.com>\nDate: 2026-01-{(i % 28) + 1:02d}\n\n    fix: item {i}\n")
    (FIX / "git_log_500.txt").write_text("\n".join(lines), encoding="utf-8")
    (FIX / "git_log_500.ground_truth.json").write_text(
        json.dumps({"commit_count": 500, "top_author": "bob"}),
        encoding="utf-8",
    )


def gen_access_log():
    levels = ["INFO", "INFO", "WARN", "ERROR", "INFO", "FATAL", "DEBUG"]
    rows = []
    err = 0
    for i in range(500):
        lvl = levels[i % len(levels)]
        if lvl in ("ERROR", "FATAL"):
            err += 1
        rows.append(json.dumps({"i": i, "level": lvl, "msg": f"req-{i}"}))
    (FIX / "access_log_500.jsonl").write_text("\n".join(rows), encoding="utf-8")
    (FIX / "access_log_500.ground_truth.json").write_text(
        json.dumps({"error_count": err}),
        encoding="utf-8",
    )


def gen_file_tree(hub_root: Path):
    proc = subprocess.run(
        ["git", "-C", str(hub_root / "AES"), "ls-files", "*.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        py_count = 42
        tree = "fallback tree\n" + "\n".join(f"src/module_{i}.py" for i in range(py_count))
    else:
        files = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        py_count = len(files)
        tree = "\n".join(files)
    (FIX / "file_tree.txt").write_text(tree, encoding="utf-8")
    (FIX / "file_tree.ground_truth.json").write_text(
        json.dumps({"py_files": py_count}),
        encoding="utf-8",
    )


if __name__ == "__main__":
    hub = Path(__file__).resolve().parents[2]
    gen_git_log()
    gen_access_log()
    gen_file_tree(hub)
    print("fixtures OK", FIX)
