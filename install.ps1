# Portable install: deps + deploy .cursor templates into target hub root.
param(
  [string]$TargetRoot = ""
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$PkgRoot = $PSScriptRoot
if (-not $TargetRoot) {
  $parent = Split-Path $PkgRoot -Parent
  if ((Test-Path (Join-Path $parent "AES")) -and (Test-Path (Join-Path $parent "_hub"))) {
    $TargetRoot = $parent
  } else {
    $TargetRoot = (Get-Location).Path
  }
}

$Tpl = Join-Path $PkgRoot "templates\cursor"
$Cursor = Join-Path $TargetRoot ".cursor"
$CtxGlobal = Join-Path (npm root -g) "context-mode\configs\cursor"

Write-Host "== agent-hub-stack install ==" -ForegroundColor Cyan
Write-Host "Package: $PkgRoot"
Write-Host "Target:  $TargetRoot"

Write-Host "`n[1/5] context-mode (npm global)..." -ForegroundColor Yellow
npm install -g context-mode

Write-Host "`n[2/5] markitdown (pip)..." -ForegroundColor Yellow
python -m pip install -U "markitdown[all]" mcp

Write-Host "`n[3/5] Deploy .cursor templates..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path (Join-Path $Cursor "rules") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Cursor "skills\agent-hub-stack") | Out-Null

Copy-Item -Force (Join-Path $Tpl "mcp.json") (Join-Path $Cursor "mcp.json")
Copy-Item -Force (Join-Path $Tpl "hooks.json") (Join-Path $Cursor "hooks.json")
Copy-Item -Force (Join-Path $Tpl "rules\lean-agent-output.mdc") (Join-Path $Cursor "rules\lean-agent-output.mdc")
Copy-Item -Force (Join-Path $Tpl "skills\agent-hub-stack\SKILL.md") (Join-Path $Cursor "skills\agent-hub-stack\SKILL.md")

$mdcSrc = Join-Path $CtxGlobal "context-mode.mdc"
$mdcDst = Join-Path $Cursor "rules\context-mode.mdc"
if (Test-Path $mdcSrc) {
  Copy-Item -Force $mdcSrc $mdcDst
} elseif (Test-Path (Join-Path $Tpl "rules\context-mode.mdc")) {
  Copy-Item -Force (Join-Path $Tpl "rules\context-mode.mdc") $mdcDst
}

# Patch MCP path to this package
$mcpPath = Join-Path $Cursor "mcp.json"
$json = Get-Content $mcpPath -Raw | ConvertFrom-Json
$json.mcpServers."agent-hub-stack".args = @((Join-Path $PkgRoot "mcp_server.py"))
$json | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $mcpPath

Write-Host "`n[4/5] stack.cmd launcher..." -ForegroundColor Yellow
$cmd = @"
@echo off
chcp 65001 >nul
set PYTHONUTF8=1
powershell -NoProfile -ExecutionPolicy Bypass -File "$PkgRoot\stack.ps1" %*
"@
Set-Content -Encoding ASCII (Join-Path $TargetRoot "stack.cmd") $cmd

Write-Host "`n[5/5] Smoke..." -ForegroundColor Yellow
python -c "import markitdown; print('  markitdown OK')"
if (-not (Get-Command context-mode -ErrorAction SilentlyContinue)) { throw "context-mode missing" }

Write-Host "`nDone. Reload Cursor. Run: stack.cmd doctor" -ForegroundColor Green
