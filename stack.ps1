param(
  [Parameter(Position = 0)]
  [string]$Command = "help",
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$PkgRoot = $PSScriptRoot
$Install = Join-Path $PkgRoot "install.ps1"
$McpServer = Join-Path $PkgRoot "mcp_server.py"
$Bench = Join-Path $PkgRoot "benchmark\run_benchmark.py"

function Show-Help {
@"
agent-hub-stack CLI

  stack.ps1 go              install + deploy Cursor config
  stack.ps1 doctor          health check
  stack.ps1 benchmark       A/B API benchmark (baseline vs stack)
  stack.ps1 md <file>       PDF/Office -> Markdown
  stack.ps1 guide           print README

Package: $PkgRoot
"@
}

switch ($Command.ToLowerInvariant()) {
  "help" { Show-Help }
  "go" { & $Install @Rest }
  "install" { & $Install @Rest }
  "doctor" {
    python -c @"
import json, importlib.util
from pathlib import Path
p = Path(r'$McpServer')
spec = importlib.util.spec_from_file_location('hub_stack', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(json.dumps(mod._component_status(), ensure_ascii=False, indent=2))
"@
  }
  "benchmark" {
    python (Join-Path $PkgRoot "benchmark\generate_fixtures.py")
    python $Bench both
  }
  "md" {
    if (-not $Rest -or $Rest.Count -lt 1) { throw "Usage: stack.ps1 md <input> [output.md]" }
    if ($Rest.Count -ge 2) { python -m markitdown $Rest[0] -o $Rest[1] }
    else { python -m markitdown $Rest[0] }
  }
  "guide" { Get-Content (Join-Path $PkgRoot "README.md") }
  default { throw "Unknown: $Command" }
}
