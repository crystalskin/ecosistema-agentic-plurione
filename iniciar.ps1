# iniciar.ps1 — Levanta el ecosistema completo de Modulo 7

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "   Ecosistema Agentic PluriOne - M7     " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# ─── 1. VERIFICAR DOCKER DESKTOP ─────────────────────────────────────────────
Write-Host "[1/5] Verificando Docker Desktop..." -ForegroundColor Cyan
$null = docker ps
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Docker Desktop no esta corriendo o no responde." -ForegroundColor Red
    Write-Host "  Abrelo manualmente y vuelve a ejecutar este script." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host "  OK Docker Desktop activo." -ForegroundColor Green

# ─── 2. LEVANTAR DOCKER COMPOSE ──────────────────────────────────────────────
Write-Host "[2/5] Levantando contenedores (PostgreSQL, RabbitMQ, MLflow)..." -ForegroundColor Cyan
Set-Location $Root
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: docker-compose up -d fallo. Revisa los mensajes anteriores." -ForegroundColor Red
    exit 1
}
Write-Host "  OK Contenedores lanzados." -ForegroundColor Green

# ─── 3. ESPERAR A QUE POSTGRESQL RESPONDA ────────────────────────────────────
Write-Host "[3/5] Esperando a que PostgreSQL acepte conexiones..." -ForegroundColor Cyan

$maxWait = 30
$elapsed = 0
$pgReady = $false

while ($elapsed -lt $maxWait) {
    $null = docker exec agentic_postgres pg_isready -U usuario_learning
    if ($LASTEXITCODE -eq 0) { $pgReady = $true; break }
    Start-Sleep -Seconds 2
    $elapsed += 2
    Write-Host "  ... ${elapsed}s / ${maxWait}s" -ForegroundColor DarkGray
}

if ($pgReady) {
    Write-Host "  OK PostgreSQL listo (tardo ${elapsed}s)." -ForegroundColor Green
} else {
    Write-Host "  AVISO: PostgreSQL no respondio en ${maxWait}s. Continuando de todas formas..." -ForegroundColor Yellow
}

# ─── 4. LANZAR SERVICIOS EN TERMINALES SEPARADAS ─────────────────────────────
Write-Host "[4/5] Iniciando servicios en terminales separadas..." -ForegroundColor Cyan

# FastAPI — ml-cognitive-engine / .venv / uvicorn app.main:app --port 8000
Write-Host "  -> FastAPI  (puerto 8000)..." -ForegroundColor White
$fastApiPath = Join-Path $Root "ml-cognitive-engine"
$cmdFastApi  = "Write-Host '=== FastAPI ===' -ForegroundColor Yellow; Set-Location '$fastApiPath'; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmdFastApi

Start-Sleep -Seconds 3

# NestJS — backend-nestjs / npm run start:dev
Write-Host "  -> NestJS   (puerto 3000)..." -ForegroundColor White
$nestPath = Join-Path $Root "backend-nestjs"
$cmdNest  = "Write-Host '=== NestJS ===' -ForegroundColor Blue; Set-Location '$nestPath'; npm run start:dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmdNest

Start-Sleep -Seconds 3

# React — frontend-chat / npm run dev
Write-Host "  -> React    (puerto 5173)..." -ForegroundColor White
$reactPath = Join-Path $Root "frontend-chat"
$cmdReact  = "Write-Host '=== React (Vite) ===' -ForegroundColor Green; Set-Location '$reactPath'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmdReact

# ─── 5. ESPERAR A VITE Y ABRIR NAVEGADOR ─────────────────────────────────────
Write-Host "[5/5] Esperando a que Vite este listo en localhost:5173..." -ForegroundColor Cyan

$viteReady = $false
$viteWait  = 0
$viteMax   = 60

while ($viteWait -lt $viteMax) {
    Start-Sleep -Seconds 2
    $viteWait += 2
    $tcp = Test-NetConnection -ComputerName localhost -Port 5173 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($tcp) { $viteReady = $true; break }
    Write-Host "  ... ${viteWait}s / ${viteMax}s" -ForegroundColor DarkGray
}

if ($viteReady) {
    Write-Host "  OK Vite listo (tardo ${viteWait}s). Abriendo navegador..." -ForegroundColor Green
    Start-Process "http://localhost:5173"
} else {
    Write-Host "  AVISO: Vite no respondio en ${viteMax}s." -ForegroundColor Yellow
    Write-Host "  Abre el navegador manualmente en: http://localhost:5173" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Ecosistema en marcha" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  FastAPI   -> http://localhost:8000/docs" -ForegroundColor White
Write-Host "  NestJS    -> http://localhost:3000" -ForegroundColor White
Write-Host "  React     -> http://localhost:5173" -ForegroundColor White
Write-Host "  RabbitMQ  -> http://localhost:15672  (invitado / invitado_pass)" -ForegroundColor White
Write-Host "  MLflow    -> http://localhost:5000" -ForegroundColor White
Write-Host ""
