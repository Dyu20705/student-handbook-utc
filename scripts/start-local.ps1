param([ValidateRange(1, 65535)][int]$Port = 8000, [switch]$Background)
$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectDir
. (Join-Path $PSScriptRoot 'local-server-state.ps1')
$PythonExe = Join-Path $ProjectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Run uv sync --locked --python 3.12 first.' }
$RuntimeDir = Join-Path $ProjectDir 'data\runtime'
$PidFile = Join-Path $RuntimeDir 'server.pid'
$ControlLock = Open-ServerLock $RuntimeDir
try {
    $Existing = Get-ServerProcess $PidFile
    if ($Existing) { throw "Managed server PID $($Existing.ProcessId) is still running. Stop it before starting another port." }
    if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile }
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { throw "Port $Port is already in use." }
    $env:PYTHONIOENCODING = 'utf-8'
    & $PythonExe -m student_handbook_rag.doctor
    if ($LASTEXITCODE -ne 0) { throw 'Readiness check failed; check Ollama and run utc-ingest.' }
    if (-not $Background) {
        & $PythonExe -m student_handbook_rag.api --port $Port
        if ($LASTEXITCODE -ne 0) { throw "Server exited with code $LASTEXITCODE" }
        return
    }
    $Process = Start-Process -FilePath $PythonExe -ArgumentList '-m', 'student_handbook_rag.api', '--port', $Port `
        -WorkingDirectory $ProjectDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $RuntimeDir 'server.stdout.log') `
        -RedirectStandardError (Join-Path $RuntimeDir 'server.stderr.log')
    try {
        $Process.Id | Set-Content -LiteralPath $PidFile
        for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
            $Process.Refresh()
            if ($Process.HasExited) { throw "Server exited; inspect $RuntimeDir\server.stderr.log" }
            try {
                $Ready = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/ready" -TimeoutSec 3
                if ($Ready.status -eq 'ready') {
                    Write-Output "UTC RAG ready, PID $($Process.Id); API http://127.0.0.1:$Port/docs; logs: $RuntimeDir"
                    return
                }
            } catch { Write-Verbose 'Waiting for readiness.' }
            Start-Sleep -Seconds 1
        }
        throw "Server did not become ready; inspect $RuntimeDir\server.stderr.log."
    } catch {
        Stop-ServerProcess (Get-CimInstance Win32_Process -Filter "ProcessId = $($Process.Id)") $PythonExe
        if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile }
        throw
    }
} finally { $ControlLock.Dispose() }
