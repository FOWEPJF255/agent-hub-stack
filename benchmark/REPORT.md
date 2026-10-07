# Benchmark report (auto-generated)

Run: see `results/latest.json` for raw JSON.

## Method

- **API**: OpenAI-compatible chat completions (`AES/.env` `AGENT_API_*`)
- **Modes**:
  - `baseline` — full fixture embedded in user prompt
  - `stack` — pre-compute summary (simulates context-mode "think in code")
- **Scenarios**: git log stats, JSON error count, py file count
- **Quality**: JSON field match vs ground truth

## How to re-run

```powershell
cd agent-hub-stack
.\stack.ps1 benchmark
```

## Latest run (2026-10-07 UTC)

| Metric | Baseline | Stack | Delta |
|--------|----------|-------|-------|
| Total tokens | 38,081 | 627 | **-98.35%** |
| Wall latency (API) | 18,450 ms | 3,079 ms | **-83.3%** |
| Quality pass | 3/3 | 3/3 | Same |

Model: `deepseek-flash` via `api.deepseek.com`

Raw: `results/latest.json`
