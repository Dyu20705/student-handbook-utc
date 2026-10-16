$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'local-server-state.ps1')
$RuntimeDir = Join-Path $ProjectDir 'data\runtime'
$PidFile = Join-Path $RuntimeDir 'server.pid'
$ControlLock = Open-ServerLock $RuntimeDir
try {
    if (-not (Test-Path -LiteralPath $PidFile)) { Write-Output 'No managed server PID file.'; return }
    Stop-ServerProcess (Get-ServerProcess $PidFile) (Join-Path $ProjectDir '.venv\Scripts\python.exe')
    Remove-Item -LiteralPath $PidFile
    Write-Output 'UTC RAG stopped.'
} finally { $ControlLock.Dispose() }
