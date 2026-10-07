---
name: agent-hub-stack
description: >-
  Token-efficient Agent-Project stack: auto-install context-mode + markitdown,
  doctor checks, PDF-to-Markdown, OSS lean-output rules. Use when the user says
  /stack, agent stack, 省token, token优化, context-mode, markitdown, or asks to
  start the hub efficiency workflow.
---

# Agent-Project stack

Zero manual setup. The agent runs everything.

## On invoke (always do this first)

1. If MCP `agent-hub-stack` is available, call **`stack_go`**.
2. Else run from hub root:

```powershell
cd C:\1AAAProject\Agent-Project
.\stack.cmd go
```

3. Call **`stack_doctor`** (MCP) or `.\stack.cmd doctor` (shell) and report status.

If `context-mode` MCP is disconnected, tell the user only: **Developer: Reload Window** (one-time after first install). Do not ask them to run install scripts manually.

## Daily usage

| Task | Action |
|------|--------|
| Large grep/log/API output | context-mode `ctx_batch_execute` / `ctx_search` — never raw dump |
| PDF / Office / attachment | MCP `markdown_convert` or `stack.cmd md <file>` |
| OSS contribution | `mcp-python-sdk-contribute` skill + `lean-agent-output` rule |
| Long-term memory (Phase 2) | `oss/volcengine/OpenViking` — only after server is up |

## MCP tools (agent-hub-stack)

- `stack_go` — install + repair + status JSON
- `stack_doctor` — read-only health check
- `markdown_convert` — file to Markdown
- `stack_guide` — full usage text

## Shell fallback

```bat
stack.cmd go
stack.cmd doctor
stack.cmd md path\to\file.pdf
stack.cmd guide
```

## Do not install

deepseek-harness, OmniRoute, ai-memory, ruflo, Orca — overlap with Cursor + AES.
