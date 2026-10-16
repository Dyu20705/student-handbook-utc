param([switch]$SkipModelDownload)
$ErrorActionPreference = 'Stop'
$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectDir
$env:UV_CACHE_DIR = Join-Path $ProjectDir '.uv-cache'
$env:PYTHONIOENCODING = 'utf-8'
uv sync --locked --python 3.12
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (-not $SkipModelDownload) {
    $EmbeddingModel = if ($env:RAG_EMBEDDING_MODEL) { $env:RAG_EMBEDDING_MODEL } else { 'qwen3-embedding:0.6b' }
    $GenerationModel = if ($env:RAG_LLM_MODEL) { $env:RAG_LLM_MODEL } else { 'qwen3.5:9b-q4_K_M' }
    ollama pull $EmbeddingModel
    if ($LASTEXITCODE -ne 0) { throw 'Embedding model download failed.' }
    ollama pull $GenerationModel
    if ($LASTEXITCODE -ne 0) { throw 'Generation model download failed.' }
}
& .venv\Scripts\python.exe -m student_handbook_rag.ingest
if ($LASTEXITCODE -ne 0) { throw 'Ingestion failed. For a legacy index, run utc-ingest --force explicitly.' }
& .venv\Scripts\python.exe -m student_handbook_rag.doctor
if ($LASTEXITCODE -ne 0) { throw 'Readiness check failed.' }
Write-Output 'Setup complete. Run .\scripts\start-local.ps1'
