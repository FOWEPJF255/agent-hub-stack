# agent-hub-stack

Token-efficient Cursor / Agent workflow: **context-mode** + **markitdown** + MCP + Skill + hooks.

One command install. A/B benchmark included.

## Quick install (any machine)

```powershell
git clone https://github.com/FOWEPJF255/agent-hub-stack.git
cd agent-hub-stack
.\install.ps1          # deploy into current folder, or Agent-Project parent if detected
# or from Agent-Project hub:
.\install.ps1 -TargetRoot C:\1AAAProject\Agent-Project
```

Then **Developer: Reload Window** in Cursor once.

```bat
stack.cmd go
stack.cmd doctor
stack.cmd benchmark
```

## Package layout

| Path | Purpose |
|------|---------|
| `install.ps1` | npm + pip + deploy `.cursor/` templates |
| `stack.ps1` / `stack.cmd` | CLI: go, doctor, benchmark, md |
| `mcp_server.py` | MCP tools: `stack_go`, `stack_doctor`, `markdown_convert` |
| `templates/cursor/` | mcp.json, hooks.json, rules, skill |
| `benchmark/` | DeepSeek/OpenAI-compatible A/B tests |

## Cursor integration

After install, `.cursor/mcp.json` registers:

- `context-mode` — sandbox tool output (`ctx_*`)
- `agent-hub-stack` — install, doctor, markdown

Skill: `.cursor/skills/agent-hub-stack/SKILL.md` — trigger: `/stack`, `省token`

## Benchmark

Uses `AGENT_API_KEY` / `DEEPSEEK_API_KEY` from env or `../AES/.env`.

```powershell
.\stack.ps1 benchmark
```

Reports: `benchmark/results/latest.json` — tokens, latency, quality pass rate, baseline vs stack.

## Multi-AI support

See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## License

MIT (hub tooling). context-mode is ELv2 — install separately via npm.
