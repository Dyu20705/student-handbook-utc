# Shared single-server state. The exclusive handle serializes start/stop across shells.
function Open-ServerLock([string]$RuntimeDir) {
    New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
    try {
        return [IO.File]::Open((Join-Path $RuntimeDir 'server.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    } catch { throw 'Another start/stop operation is running; retry after it finishes.' }
}

function Get-ServerProcess([string]$PidFile) {
    if (-not (Test-Path -LiteralPath $PidFile)) { return $null }
    $Value = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    if ($Value -notmatch '^[1-9][0-9]*$') { throw 'Invalid server.pid; inspect it before retrying.' }
    return Get-CimInstance Win32_Process -Filter "ProcessId = $Value"
}

function Stop-ServerProcess($ServerProcess, [string]$PythonExe) {
    if (-not $ServerProcess) { return }
    if ($ServerProcess.ExecutablePath -ne $PythonExe -or $ServerProcess.CommandLine -notmatch 'student_handbook_rag.api') {
        throw 'PID belongs to another process; refusing to stop or overwrite it.'
    }
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $($ServerProcess.ProcessId)" |
        Where-Object { $_.CommandLine -match 'student_handbook_rag.api' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
    Stop-Process -Id $ServerProcess.ProcessId -ErrorAction SilentlyContinue
}
