param([int]$Port = 8000, [switch]$Background)
$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectDir
$PythonExe = Join-Path $ProjectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Run uv sync --locked --python 3.12 first.' }
$env:PYTHONIOENCODING = 'utf-8'
& $PythonExe -m student_handbook_rag.doctor
if ($LASTEXITCODE -ne 0) { throw 'Readiness check failed; check Ollama and run utc-ingest.' }
if (-not $Background) {
    & $PythonExe -m student_handbook_rag.api --port $Port
    exit $LASTEXITCODE
}
$RuntimeDir = Join-Path $ProjectDir 'data\runtime'
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use."
}
$Process = Start-Process -FilePath $PythonExe -ArgumentList '-m', 'student_handbook_rag.api', '--port', $Port `
    -WorkingDirectory $ProjectDir -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $RuntimeDir 'server.stdout.log') `
    -RedirectStandardError (Join-Path $RuntimeDir 'server.stderr.log')
$Process.Id | Set-Content (Join-Path $RuntimeDir 'server.pid')
for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
    $Process.Refresh()
    if ($Process.HasExited) { throw "Server exited; inspect $RuntimeDir\server.stderr.log" }
    try {
        $Ready = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/ready" -TimeoutSec 3
        if ($Ready.status -eq 'ready') {
            Write-Output "UTC RAG ready, PID $($Process.Id); API http://127.0.0.1:$Port/docs; logs: $RuntimeDir"
            exit 0
        }
    } catch { Write-Verbose 'Waiting for readiness.' }
    Start-Sleep -Seconds 1
}
throw "Server did not become ready; inspect $RuntimeDir\server.stderr.log. Use stop-local.ps1 to stop it."
