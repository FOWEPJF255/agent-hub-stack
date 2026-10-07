#!/usr/bin/env python3
"""Agent-hub-stack MCP: doctor, auto-install, markitdown. Portable package."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

PKG_ROOT = Path(__file__).resolve().parent
INSTALL_PS1 = PKG_ROOT / "install.ps1"

# Hub root when installed inside Agent-Project; else use cwd
def hub_root() -> Path:
    parent = PKG_ROOT.parent
    if (parent / "AES").is_dir() and (parent / "_hub").is_dir():
        return parent
    return Path.cwd()


mcp = FastMCP("agent-hub-stack")


def _run_ps1(script: Path, *args: str) -> tuple[int, str]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(hub_root()),
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _component_status() -> dict[str, object]:
    root = hub_root()
    checks: dict[str, object] = {}

    def has_cmd(name: str) -> bool:
        proc = subprocess.run(
            ["where", name],
            capture_output=True,
            text=True,
            shell=True,
        )
        return proc.returncode == 0

    checks["context_mode_cli"] = has_cmd("context-mode")
    try:
        import markitdown  # noqa: F401

        checks["markitdown"] = True
    except ImportError:
        checks["markitdown"] = False

    cursor = root / ".cursor"
    checks["cursor_mcp_json"] = (cursor / "mcp.json").is_file()
    checks["cursor_hooks_json"] = (cursor / "hooks.json").is_file()
    checks["context_mode_rule"] = (cursor / "rules" / "context-mode.mdc").is_file()
    checks["lean_output_rule"] = (cursor / "rules" / "lean-agent-output.mdc").is_file()
    checks["package_root"] = str(PKG_ROOT)
    checks["hub_root"] = str(root)
    checks["ready"] = all(
        checks[k]
        for k in (
            "context_mode_cli",
            "markitdown",
            "cursor_mcp_json",
            "cursor_hooks_json",
            "context_mode_rule",
            "lean_output_rule",
        )
    )
    return checks


@mcp.tool()
def stack_go() -> str:
    """One-shot: install deps, deploy Cursor templates, return doctor summary."""
    code, out = _run_ps1(INSTALL_PS1)
    status = _component_status()
    payload = {
        "install_exit_code": code,
        "install_log_tail": out[-4000:] if out else "",
        "status": status,
        "next": "Reload Cursor window once if MCP was just added.",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def stack_doctor() -> str:
    """Check agent-hub-stack components without installing."""
    status = _component_status()
    if not status["ready"]:
        return json.dumps(
            {"status": status, "fix": "Call stack_go() to auto-install and repair."},
            ensure_ascii=False,
            indent=2,
        )
    return json.dumps(
        {"status": status, "message": "All core components OK."},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def markdown_convert(input_path: str, output_path: str | None = None) -> str:
    """Convert PDF/Office/image file to Markdown via markitdown."""
    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        return json.dumps({"error": f"File not found: {src}"}, ensure_ascii=False)

    dst = (
        Path(output_path).expanduser().resolve()
        if output_path
        else src.with_suffix(src.suffix + ".md")
    )
    dst.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [sys.executable, "-m", "markitdown", str(src), "-o", str(dst)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(hub_root()),
    )
    if proc.returncode != 0:
        return json.dumps(
            {"error": "markitdown failed", "stderr": (proc.stderr or proc.stdout or "")[-2000:]},
            ensure_ascii=False,
            indent=2,
        )
    text = dst.read_text(encoding="utf-8", errors="replace")
    preview = text[:8000] + ("..." if len(text) > 8000 else "")
    return json.dumps(
        {"input": str(src), "output": str(dst), "chars": len(text), "preview": preview},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def stack_guide() -> str:
    """Return how to use the token-efficient agent-hub-stack."""
    return (PKG_ROOT / "README.md").read_text(encoding="utf-8", errors="replace")[:12000]


if __name__ == "__main__":
    mcp.run()
