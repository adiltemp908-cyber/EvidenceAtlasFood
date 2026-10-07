$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $env:EAF_ROOT) { $env:EAF_ROOT = 'E:\EvidenceAtlasFood' }
python -m evidenceatlas.cli serve --port 8765
