$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectDir 'data\runtime\server.pid'
if (-not (Test-Path -LiteralPath $PidFile)) { Write-Output 'No managed server PID file.'; exit 0 }
$ServerPid = [int](Get-Content -LiteralPath $PidFile)
$ServerProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $ServerPid"
if ($ServerProcess) {
    $ExpectedExe = Join-Path $ProjectDir '.venv\Scripts\python.exe'
    if ($ServerProcess.ExecutablePath -ne $ExpectedExe -or $ServerProcess.CommandLine -notmatch 'student_handbook_rag.api') {
        throw 'PID belongs to another process; refusing to stop it.'
    }
    # Stop only this server and its Python launcher child. It never writes the index.
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $ServerPid" |
        Where-Object { $_.CommandLine -match 'student_handbook_rag.api' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId }
    Stop-Process -Id $ServerPid -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $PidFile
Write-Output 'UTC RAG stopped.'
