# Multi-AI compatibility

## Summary

| Product | context-mode | agent-hub-stack MCP | markitdown | Notes |
|---------|:------------:|:-------------------:|:----------:|-------|
| **Cursor** | Yes (hooks + MCP) | Yes | CLI / MCP | Primary target; full stack |
| **Claude Code** | Yes (plugin) | Partial (MCP only) | CLI | `/plugin install context-mode@context-mode` |
| **Codex CLI** | Yes | Partial | CLI | context-mode OpenCode/Codex configs |
| **GitHub Copilot CLI** | Yes (plugin bundle) | Partial | CLI | `copilot plugin install mksglu/context-mode:configs/copilot-cli` |
| **Gemini CLI** | Yes (hooks) | Partial | CLI | See context-mode README |
| **Kimi / Kiro / Trae / Qoder** | Varies | Partial | CLI | If they support MCP stdio + hooks, copy `templates/cursor/` patterns |
| **Work Buddy** | Check vendor | Partial | CLI | Use `stack_go` + markitdown if MCP host supported |

**agent-hub-stack MCP** is standard MCP stdio — any host that runs `python mcp_server.py` can use `stack_doctor`, `markdown_convert`.

**context-mode** is the cross-platform layer (17+ clients). agent-hub-stack adds install orchestration + benchmark + hub templates.

## Recommended per tool

### Cursor (you)
`install.ps1` — done. Use `/stack` or MCP `stack_go`.

### Claude Code
```bash
npm install -g context-mode markitdown
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
```

### Codex / OpenCode
```bash
npm install -g context-mode
# opencode.json: "plugin": ["context-mode"]
```

### Others without MCP
Keep **markitdown** CLI + **lean-agent-output** rules copied manually from `templates/cursor/rules/`.

## What does NOT transfer

- Cursor-specific `hooks.json` matchers — rewrite for each host
- DSH / OmniRoute / second harness — not part of this stack
